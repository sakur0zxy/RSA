from __future__ import annotations

import csv
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .metadata import load_metadata_record


CAMPAIGN_ID_PATTERN = re.compile(r"^C(?P<number>\d{3})$")
ITEM_ID_PATTERN = re.compile(r"^CI(?P<number>\d{3})$")
CAMPAIGN_STATUSES = {"draft", "active", "paused", "completed", "archived"}
ITEM_STATUSES = {
    "candidate",
    "queued",
    "linked",
    "duplicate",
    "needs_review",
    "blocked",
    "skipped",
}
IMPORT_FIELDS = [
    "title",
    "doi",
    "official_url",
    "year",
    "first_author",
    "topic_profile",
    "priority_question",
    "candidate_key",
    "source_candidate_id",
    "note_zh",
]


class CampaignError(ValueError):
    """Raised when campaign operations cannot safely continue."""


@dataclass(frozen=True)
class CampaignCreateResult:
    campaign_id: str
    path: Path


@dataclass(frozen=True)
class CampaignImportResult:
    campaign_id: str
    path: Path
    imported_count: int
    duplicate_count: int
    linked_count: int
    blocked_count: int


@dataclass(frozen=True)
class CampaignStatus:
    path: Path
    campaign_id: str
    total_count: int
    queued_count: int
    linked_count: int
    duplicate_count: int
    needs_review_count: int
    blocked_count: int


def campaign_path(config: ProjectConfig, campaign_id: str) -> Path:
    if not CAMPAIGN_ID_PATTERN.match(campaign_id):
        raise CampaignError(f"campaign_id 必须匹配 C###: {campaign_id}")
    return config.campaigns_root / f"{campaign_id}.yaml"


def create_campaign(
    config: ProjectConfig,
    *,
    name_zh: str,
    objective_zh: str,
    topic_profile: str | None = None,
    created_by: str | None = None,
) -> CampaignCreateResult:
    if _is_blank(name_zh):
        raise CampaignError("必须提供 --name-zh，说明批量任务名称。")
    if _is_blank(objective_zh):
        raise CampaignError("必须提供 --objective-zh，说明批量任务目标。")
    campaign_id = next_campaign_id(config)
    path = campaign_path(config, campaign_id)
    data = {
        "campaign_id": campaign_id,
        "name_zh": name_zh,
        "objective_zh": objective_zh,
        "topic_profile": topic_profile,
        "status": "active",
        "created_by": created_by,
        "created_at": _now(),
        "updated_at": _now(),
        "automation_boundary_zh": (
            "Phase 8.2 只管理批量候选队列和去重状态；不执行 AI 评分、自动工作流、UI 审核或正式写入。"
        ),
        "items": [],
    }
    _write_yaml(path, data)
    return CampaignCreateResult(campaign_id=campaign_id, path=path)


def import_campaign_items(
    config: ProjectConfig,
    campaign_id: str,
    *,
    source_file: str,
    dedup: bool = True,
) -> CampaignImportResult:
    path = campaign_path(config, campaign_id)
    data = load_campaign(config, campaign_id)
    items = data.setdefault("items", [])
    if not isinstance(items, list):
        raise CampaignError("items 必须是 YAML list。")

    source_path = _resolve_project_path(config, source_file)
    rows = _load_import_rows(source_path)
    existing_keys = _existing_dedup_keys(items)
    imported = 0
    duplicates = 0
    linked = 0
    blocked = 0

    for row in rows:
        item_id = next_item_id([*items])
        item = _normalize_import_row(config, row, item_id=item_id)
        key = str(item.get("dedup_key") or "")
        if dedup and key and key in existing_keys:
            item["status"] = "duplicate"
            item["duplicate_of"] = existing_keys[key]
            item["reason_zh"] = "该候选与当前 campaign 中已有条目重复，默认不进入队列。"
            duplicates += 1
        elif item.get("paper_id"):
            item["status"] = "linked"
            item["reason_zh"] = "该候选已匹配正式 metadata 记录，可进入后续人工审阅或工作流。"
            linked += 1
        elif _is_blank(item.get("title")) and _is_blank(item.get("doi")):
            item["status"] = "blocked"
            item["reason_zh"] = "缺少 title 和 doi，无法形成可追踪候选。"
            blocked += 1
        else:
            item["status"] = "queued"
            item["reason_zh"] = "候选已进入批量队列，等待后续 acquisition / reading / scoring 流程处理。"
        if key and item["status"] != "duplicate":
            existing_keys[key] = item_id
        items.append(item)
        imported += 1

    data["updated_at"] = _now()
    _write_yaml(path, data)
    return CampaignImportResult(
        campaign_id=campaign_id,
        path=path,
        imported_count=imported,
        duplicate_count=duplicates,
        linked_count=linked,
        blocked_count=blocked,
    )


def load_campaign(config: ProjectConfig, campaign_id: str) -> dict[str, Any]:
    path = campaign_path(config, campaign_id)
    if not path.exists():
        raise CampaignError(f"campaign 不存在: {path}")
    return _read_yaml_mapping(path)


def validate_campaign(config: ProjectConfig, campaign_id: str) -> list[str]:
    try:
        path = campaign_path(config, campaign_id)
        if not path.exists():
            return [f"campaign 不存在: {path}"]
        data = _read_yaml_mapping(path)
    except CampaignError as exc:
        return [str(exc)]

    errors: list[str] = []
    if data.get("campaign_id") != campaign_id:
        errors.append(
            f"campaign_id 必须与文件名一致: expected {campaign_id}, got {data.get('campaign_id')}"
        )
    if _is_blank(data.get("name_zh")):
        errors.append("缺少 name_zh：需要中文 campaign 名称。")
    if _is_blank(data.get("objective_zh")):
        errors.append("缺少 objective_zh：需要中文批量任务目标。")
    if data.get("status") not in CAMPAIGN_STATUSES:
        errors.append(f"status 不支持: {data.get('status')}")
    items = data.get("items")
    if not isinstance(items, list):
        return errors + ["items 必须是 YAML list。"]

    seen_ids: set[str] = set()
    seen_keys: dict[str, str] = {}
    for index, item in enumerate(items, start=1):
        prefix = f"items 第 {index} 项"
        if not isinstance(item, dict):
            errors.append(f"{prefix} 必须是 mapping。")
            continue
        item_id = str(item.get("item_id") or "")
        if not ITEM_ID_PATTERN.match(item_id):
            errors.append(f"{prefix} item_id 必须匹配 CI###。")
        elif item_id in seen_ids:
            errors.append(f"{prefix} item_id 重复: {item_id}")
        else:
            seen_ids.add(item_id)
        if item.get("status") not in ITEM_STATUSES:
            errors.append(f"{prefix} status 不支持: {item.get('status')}")
        if _is_blank(item.get("title")) and _is_blank(item.get("doi")):
            errors.append(f"{prefix} 缺少 title 或 doi，无法追踪候选身份。")
        if _is_blank(item.get("dedup_key")):
            errors.append(f"{prefix} 缺少 dedup_key。")
        elif item.get("status") != "duplicate":
            key = str(item["dedup_key"])
            if key in seen_keys:
                errors.append(
                    f"{prefix} dedup_key 与 {seen_keys[key]} 重复，但未标记 duplicate。"
                )
            else:
                seen_keys[key] = item_id
        if item.get("status") in {"blocked", "needs_review", "duplicate"} and _is_blank(
            item.get("reason_zh")
        ):
            errors.append(f"{prefix} status={item.get('status')} 时必须提供 reason_zh。")
        if item.get("paper_id") and not _metadata_path(config, str(item["paper_id"])).exists():
            errors.append(f"{prefix} paper_id 指向的 metadata 不存在: {item['paper_id']}")
    return errors


def campaign_status(config: ProjectConfig, campaign_id: str) -> CampaignStatus:
    path = campaign_path(config, campaign_id)
    if not path.exists():
        return CampaignStatus(path, campaign_id, 0, 0, 0, 0, 0, 0)
    data = _read_yaml_mapping(path)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return CampaignStatus(
        path=path,
        campaign_id=campaign_id,
        total_count=len(items),
        queued_count=sum(1 for item in items if item.get("status") == "queued"),
        linked_count=sum(1 for item in items if item.get("status") == "linked"),
        duplicate_count=sum(1 for item in items if item.get("status") == "duplicate"),
        needs_review_count=sum(1 for item in items if item.get("status") == "needs_review"),
        blocked_count=sum(1 for item in items if item.get("status") == "blocked"),
    )


def next_campaign_id(config: ProjectConfig) -> str:
    highest = 0
    if config.campaigns_root.exists():
        for child in config.campaigns_root.glob("C*.yaml"):
            match = CAMPAIGN_ID_PATTERN.match(child.stem)
            if match:
                highest = max(highest, int(match.group("number")))
    return f"C{highest + 1:03d}"


def next_item_id(items: list[Any]) -> str:
    highest = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        match = ITEM_ID_PATTERN.match(str(item.get("item_id") or ""))
        if match:
            highest = max(highest, int(match.group("number")))
    return f"CI{highest + 1:03d}"


def _normalize_import_row(
    config: ProjectConfig, row: dict[str, Any], *, item_id: str
) -> dict[str, Any]:
    title = _clean(row.get("title") or row.get("candidate_title"))
    doi = _normalize_doi(row.get("doi") or row.get("doi_or_url"))
    official_url = _clean(row.get("official_url") or row.get("url"))
    year = _clean(row.get("year"))
    first_author = _clean(row.get("first_author") or row.get("author"))
    paper_id = _clean(row.get("paper_id")) or _match_formal_metadata(
        config, doi=doi, title=title, year=year
    )
    dedup_key = _dedup_key(
        doi=doi,
        official_url=official_url,
        title=title,
        year=year,
        first_author=first_author,
    )
    return {
        "item_id": item_id,
        "paper_id": paper_id,
        "candidate_key": _clean(row.get("candidate_key")),
        "source_candidate_id": _clean(row.get("source_candidate_id")),
        "title": title,
        "doi": doi,
        "official_url": official_url,
        "year": year,
        "first_author": first_author,
        "topic_profile": _clean(row.get("topic_profile")),
        "priority_question": _clean(row.get("priority_question")),
        "dedup_key": dedup_key,
        "status": "candidate",
        "reason_zh": _clean(row.get("note_zh")) or None,
        "created_at": _now(),
        "source_row": {
            key: _clean(value)
            for key, value in row.items()
            if key not in {"", None} and not _is_blank(value)
        },
    }


def _load_import_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise CampaignError(f"导入文件不存在或不是普通文件: {path}")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            rows = loaded.get("items") or loaded.get("candidates") or []
        else:
            rows = loaded
        if not isinstance(rows, list):
            raise CampaignError("YAML 导入文件必须是 list，或包含 items/candidates list。")
        return [dict(item) for item in rows if isinstance(item, dict)]
    delimiter = "\t" if suffix == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise CampaignError("CSV/TSV 导入文件缺少表头。")
        return [dict(row) for row in reader]


def _existing_dedup_keys(items: list[Any]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("dedup_key")
        item_id = item.get("item_id")
        if key and item_id and item.get("status") != "duplicate":
            keys[str(key)] = str(item_id)
    return keys


def _dedup_key(
    *,
    doi: str | None,
    official_url: str | None,
    title: str | None,
    year: str | None,
    first_author: str | None,
) -> str:
    if doi:
        return "doi:" + doi.lower()
    if official_url:
        parsed = urllib.parse.urlparse(official_url.strip())
        normalized = urllib.parse.urlunparse(
            (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", "")
        )
        return "url:" + normalized
    normalized_title = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()
    normalized_author = re.sub(r"[^a-z0-9]+", " ", (first_author or "").lower()).strip()
    return "title:" + "|".join([normalized_title, str(year or ""), normalized_author])


def _normalize_doi(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    match = re.search(r"10\.\d{4,9}/\S+", text, flags=re.IGNORECASE)
    if match:
        return match.group(0).rstrip(".,;").lower()
    return text.lower() if text.lower().startswith("10.") else None


def _match_formal_metadata(
    config: ProjectConfig, *, doi: str | None, title: str | None, year: str | None
) -> str | None:
    if not config.metadata_root.exists():
        return None
    target_title = re.sub(r"\s+", " ", (title or "").strip().lower())
    for path in sorted(config.metadata_root.glob("P*.yaml")):
        try:
            record = load_metadata_record(path)
        except Exception:
            continue
        if doi and _normalize_doi(record.get("doi")) == doi:
            return str(record.get("paper_id") or path.stem)
        record_title = re.sub(r"\s+", " ", str(record.get("title") or "").strip().lower())
        if target_title and record_title == target_title and str(record.get("year") or "") == str(year or ""):
            return str(record.get("paper_id") or path.stem)
    return None


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


def _resolve_project_path(config: ProjectConfig, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.root / path


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise CampaignError(f"无法读取 YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CampaignError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise CampaignError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
