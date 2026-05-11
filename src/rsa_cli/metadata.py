from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig


PAPER_ID_PATTERN = re.compile(r"^P(?P<number>\d{3})$")
PAPER_FILE_PATTERN = re.compile(r"^P(?P<number>\d{3})\.yaml$")

METADATA_FIELDS = [
    "paper_id",
    "title",
    "authors",
    "year",
    "venue",
    "doi",
    "official_url",
    "source_reliability",
    "verification_status",
    "decision",
    "decision_reason",
    "last_checked",
    "pdf_status",
    "local_pdf",
    "assets",
    "topic_profile",
    "priority_questions",
    "used_for",
    "research_roles",
    "notes",
    "human_confirmed",
    "confirmed_by",
    "confirmed_at",
]

FIELD_DESCRIPTIONS_ZH: dict[str, str] = {
    "paper_id": "正式文献编号，只能在写入 metadata/P###.yaml 成功时分配。",
    "title": "论文标题，用于身份核验。",
    "authors": "作者列表，至少保留一个作者。",
    "year": "发表年份。",
    "venue": "期刊、会议或预印本平台名称。",
    "doi": "DOI；如果没有 DOI，必须提供 official_url。",
    "official_url": "官方页面或可靠来源链接；如果没有官方链接，必须提供 DOI。",
    "source_reliability": "来源可靠性说明，例如 publisher、official、preprint。",
    "verification_status": "身份和来源核验状态；正式记录必须为 verified。",
    "decision": "人工收录决策，例如 include、background、reject。",
    "decision_reason": "收录或暂不收录的原因。",
    "last_checked": "最近一次核验日期或时间。",
    "pdf_status": "PDF 状态，例如 not_acquired、local、authorized。",
    "local_pdf": "本地 PDF 路径；没有合法 PDF 时留空。",
    "assets": "本地截图、图表或结果图路径列表，通常位于 assets/P###/。",
    "topic_profile": "关联的课题 profile。",
    "priority_questions": "该文献服务的优先问题列表。",
    "used_for": "该文献将用于哪些章节、实验、对比或背景说明。",
    "research_roles": "研究角色列表，例如 baseline、theory、method、comparison。",
    "notes": "人工备注。",
    "human_confirmed": "是否已经人工确认可以写入正式记录；正式记录必须为 true。",
    "confirmed_by": "确认人。",
    "confirmed_at": "确认时间。",
}


class MetadataError(ValueError):
    """Raised when formal paper metadata cannot be written safely."""


def load_metadata_record(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MetadataError(f"无法读取元数据文件 {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise MetadataError(f"元数据 YAML 无效 {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise MetadataError(f"元数据必须是 YAML mapping: {path}")
    return loaded


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _require_non_blank(record: dict[str, Any], field: str, errors: list[str]) -> None:
    if _is_blank(record.get(field)):
        errors.append(f"缺少必填字段: {field}")


def _validate_metadata_mapping(
    record: dict[str, Any], *, expected_paper_id: str | None = None
) -> list[str]:
    errors: list[str] = []

    if expected_paper_id is not None:
        if record.get("paper_id") != expected_paper_id:
            errors.append(
                f"paper_id 必须与文件名一致: expected {expected_paper_id}, got {record.get('paper_id')}"
            )
    elif _is_blank(record.get("paper_id")):
        errors.append("缺少必填字段: paper_id")

    for field in [
        "title",
        "year",
        "venue",
        "source_reliability",
        "decision",
        "decision_reason",
        "last_checked",
        "pdf_status",
    ]:
        _require_non_blank(record, field, errors)

    if record.get("verification_status") != "verified":
        errors.append("verification_status 必须为 verified")

    if _is_blank(record.get("doi")) and _is_blank(record.get("official_url")):
        errors.append("doi 和 official_url 至少需要提供一个")

    for field in ["authors", "assets", "priority_questions", "used_for", "research_roles"]:
        if not isinstance(record.get(field), list):
            errors.append(f"{field} 必须是 YAML list")

    authors = record.get("authors")
    if isinstance(authors, list):
        if not authors or any(not isinstance(author, str) or not author.strip() for author in authors):
            errors.append("authors 必须包含至少一个非空作者")

    if record.get("human_confirmed") is not True:
        errors.append("human_confirmed 必须为 true")
    else:
        _require_non_blank(record, "confirmed_by", errors)
        _require_non_blank(record, "confirmed_at", errors)

    return errors


def validate_metadata_record(path: Path) -> list[str]:
    if not path.exists():
        return [f"元数据文件不存在: {path}"]
    if not PAPER_FILE_PATTERN.match(path.name):
        return [f"元数据文件名必须匹配 P###.yaml: {path.name}"]
    try:
        record = load_metadata_record(path)
    except MetadataError as exc:
        return [str(exc)]
    return _validate_metadata_mapping(record, expected_paper_id=path.stem)


def next_paper_id(metadata_root: Path) -> str:
    highest = 0
    if metadata_root.exists():
        for child in metadata_root.iterdir():
            match = PAPER_FILE_PATTERN.match(child.name)
            if match:
                highest = max(highest, int(match.group("number")))
    return f"P{highest + 1:03d}"


def _list_value(value: list[str] | None) -> list[str]:
    return list(value or [])


def _ordered_record(values: dict[str, Any]) -> dict[str, Any]:
    return {field: values.get(field) for field in METADATA_FIELDS}


def build_metadata_record(
    values: dict[str, Any],
    *,
    paper_id: str,
    human_confirmed: bool,
    confirmed_by: str | None,
    confirmed_at: str | None = None,
) -> dict[str, Any]:
    timestamp = confirmed_at or datetime.now(timezone.utc).date().isoformat()
    record = {
        "paper_id": paper_id,
        "title": values.get("title"),
        "authors": _list_value(values.get("authors")),
        "year": values.get("year"),
        "venue": values.get("venue"),
        "doi": values.get("doi"),
        "official_url": values.get("official_url"),
        "source_reliability": values.get("source_reliability"),
        "verification_status": values.get("verification_status", "verified"),
        "decision": values.get("decision"),
        "decision_reason": values.get("decision_reason"),
        "last_checked": values.get("last_checked"),
        "pdf_status": values.get("pdf_status"),
        "local_pdf": values.get("local_pdf"),
        "assets": _list_value(values.get("assets")),
        "topic_profile": values.get("topic_profile"),
        "priority_questions": _list_value(values.get("priority_questions")),
        "used_for": _list_value(values.get("used_for")),
        "research_roles": _list_value(values.get("research_roles")),
        "notes": values.get("notes"),
        "human_confirmed": bool(human_confirmed),
        "confirmed_by": confirmed_by,
        "confirmed_at": timestamp if human_confirmed else confirmed_at,
    }
    return _ordered_record(record)


def write_metadata_record(
    config: ProjectConfig,
    values: dict[str, Any],
    human_confirmed: bool,
    confirmed_by: str | None,
    confirmed_at: str | None = None,
) -> Path:
    if not human_confirmed:
        raise MetadataError(
            "必须提供 --human-confirmed，并使 human_confirmed 为 true 后才会写入正式 metadata/P###.yaml"
        )
    if _is_blank(confirmed_by):
        raise MetadataError("必须提供 --confirmed-by 记录人工确认人")

    preflight = build_metadata_record(
        values,
        paper_id="P000",
        human_confirmed=human_confirmed,
        confirmed_by=confirmed_by,
        confirmed_at=confirmed_at,
    )
    preflight_errors = [
        error
        for error in _validate_metadata_mapping(preflight)
        if "paper_id" not in error
    ]
    if preflight_errors:
        raise MetadataError("; ".join(preflight_errors))

    paper_id = next_paper_id(config.metadata_root)
    record = build_metadata_record(
        values,
        paper_id=paper_id,
        human_confirmed=human_confirmed,
        confirmed_by=confirmed_by,
        confirmed_at=confirmed_at,
    )
    errors = _validate_metadata_mapping(record, expected_paper_id=paper_id)
    if errors:
        raise MetadataError("; ".join(errors))

    config.metadata_root.mkdir(parents=True, exist_ok=True)
    path = config.metadata_root / f"{paper_id}.yaml"
    path.write_text(
        yaml.safe_dump(record, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    asset_dir = config.assets_root / paper_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / ".gitkeep").write_text("", encoding="utf-8")
    return path
