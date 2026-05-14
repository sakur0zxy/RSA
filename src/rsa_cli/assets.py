from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, validate_metadata_record
from .notes import record_pdf_status


SOURCE_AUTHORIZATIONS = {
    "provided",
    "local",
    "authorized",
    "open_access",
    "user_authorized",
    "direct_access",
    "user_authorized_access",
    "institutional_subscription",
    "personal_subscription",
    "unknown",
    "blocked",
}
SOURCE_TYPES = {"pdf", "supplement", "dataset", "web_page", "other"}
ASSET_KINDS = {"figure", "table", "result", "screenshot", "supplement", "other"}


class AssetError(ValueError):
    """Raised when source or asset operations cannot safely proceed."""


@dataclass(frozen=True)
class AddSourceResult:
    record_path: Path
    local_path: Path
    source_id: str


@dataclass(frozen=True)
class AddAssetResult:
    manifest_path: Path
    local_path: Path
    asset_id: str


@dataclass(frozen=True)
class LedgerStatus:
    path: Path
    total_count: int
    available_count: int
    blocked_count: int


def source_record_path(config: ProjectConfig, paper_id: str) -> Path:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise AssetError(f"paper_id 必须匹配 P###: {paper_id}")
    return config.sources_root / f"{paper_id}.yaml"


def asset_manifest_path(config: ProjectConfig, paper_id: str) -> Path:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise AssetError(f"paper_id 必须匹配 P###: {paper_id}")
    return config.assets_root / paper_id / "manifest.yaml"


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


def _ensure_formal_paper(config: ProjectConfig, paper_id: str) -> None:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise AssetError(f"paper_id 必须匹配 P###: {paper_id}")
    errors = validate_metadata_record(_metadata_path(config, paper_id))
    if errors:
        raise AssetError(f"{paper_id} metadata 无效或不存在: " + "; ".join(errors))


def _resolve_project_path(config: ProjectConfig, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.root / path


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "file"


def _load_mapping(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise AssetError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise AssetError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_mapping(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _next_id(entries: list[Any], *, key: str, prefix: str) -> str:
    highest = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(?P<number>\d{{3}})$")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        match = pattern.match(str(entry.get(key, "")))
        if match:
            highest = max(highest, int(match.group("number")))
    return f"{prefix}{highest + 1:03d}"


def _copy_into_workspace(
    config: ProjectConfig,
    *,
    source_path: Path,
    target_dir: Path,
    entry_id: str,
) -> Path:
    if not source_path.is_file():
        raise AssetError(f"文件不存在或不是普通文件: {_display_path(config, source_path)}")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{entry_id}_{_safe_filename(source_path.name)}"
    shutil.copy2(source_path, target)
    return target


def add_source_record(
    config: ProjectConfig,
    paper_id: str,
    *,
    source_file: str,
    authorization: str,
    source_type: str = "pdf",
    source_url: str | None = None,
    license_note: str | None = None,
    added_by: str | None = None,
) -> AddSourceResult:
    _ensure_formal_paper(config, paper_id)
    if authorization not in SOURCE_AUTHORIZATIONS:
        raise AssetError(
            "authorization 必须是 provided/local/authorized/open_access/user_authorized"
        )
    if source_type not in SOURCE_TYPES:
        raise AssetError("source_type 必须是 pdf/supplement/dataset/web_page/other")
    if _is_blank(license_note):
        raise AssetError("必须提供 --license-note，说明来源授权或本地保存依据")

    record_path = source_record_path(config, paper_id)
    record = _load_mapping(record_path, default={"paper_id": paper_id, "sources": []})
    if record.get("paper_id") not in (None, paper_id):
        raise AssetError(f"source record paper_id 与文件名不一致: {record.get('paper_id')}")
    sources = record.get("sources")
    if not isinstance(sources, list):
        raise AssetError("sources 必须是 YAML list")

    source_path = _resolve_project_path(config, source_file)
    source_id = _next_id(sources, key="source_id", prefix="S")
    local_path = _copy_into_workspace(
        config,
        source_path=source_path,
        target_dir=config.pdfs_root / paper_id,
        entry_id=source_id,
    )
    entry = {
        "source_id": source_id,
        "source_type": source_type,
        "authorization": authorization,
        "source_url": source_url,
        "license_note": license_note,
        "original_path": _display_path(config, source_path),
        "local_path": _display_path(config, local_path),
        "status": "available",
        "added_by": added_by,
        "added_at": datetime.now(timezone.utc).date().isoformat(),
    }
    record["paper_id"] = paper_id
    sources.append(entry)
    record["sources"] = sources
    _write_mapping(record_path, record)

    record_pdf_status(
        config,
        paper_id=paper_id,
        pdf_status="available",
        local_path=entry["local_path"],
        source_or_authorization=authorization,
        notes=str(license_note),
    )
    return AddSourceResult(record_path=record_path, local_path=local_path, source_id=source_id)


def add_asset_record(
    config: ProjectConfig,
    paper_id: str,
    *,
    asset_file: str,
    kind: str,
    label: str | None = None,
    description_zh: str | None = None,
    page: str | None = None,
    figure: str | None = None,
    added_by: str | None = None,
) -> AddAssetResult:
    _ensure_formal_paper(config, paper_id)
    if kind not in ASSET_KINDS:
        raise AssetError("kind 必须是 figure/table/result/screenshot/supplement/other")

    manifest_path = asset_manifest_path(config, paper_id)
    manifest = _load_mapping(manifest_path, default={"paper_id": paper_id, "assets": []})
    if manifest.get("paper_id") not in (None, paper_id):
        raise AssetError(f"asset manifest paper_id 与文件名不一致: {manifest.get('paper_id')}")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise AssetError("assets 必须是 YAML list")

    source_path = _resolve_project_path(config, asset_file)
    asset_id = _next_id(assets, key="asset_id", prefix="A")
    local_path = _copy_into_workspace(
        config,
        source_path=source_path,
        target_dir=config.assets_root / paper_id,
        entry_id=asset_id,
    )
    entry = {
        "asset_id": asset_id,
        "kind": kind,
        "label": label,
        "description_zh": description_zh,
        "page": page,
        "figure": figure,
        "original_path": _display_path(config, source_path),
        "local_path": _display_path(config, local_path),
        "added_by": added_by,
        "added_at": datetime.now(timezone.utc).date().isoformat(),
    }
    manifest["paper_id"] = paper_id
    assets.append(entry)
    manifest["assets"] = assets
    _write_mapping(manifest_path, manifest)
    return AddAssetResult(
        manifest_path=manifest_path,
        local_path=local_path,
        asset_id=asset_id,
    )


def _validate_entries(
    config: ProjectConfig,
    *,
    paper_id: str,
    data: dict[str, Any],
    list_key: str,
    id_key: str,
    allowed_values: set[str],
    value_key: str,
) -> list[str]:
    errors: list[str] = []
    if data.get("paper_id") != paper_id:
        errors.append(f"paper_id 必须与文件名一致: expected {paper_id}, got {data.get('paper_id')}")
    entries = data.get(list_key)
    if not isinstance(entries, list):
        return errors + [f"{list_key} 必须是 YAML list"]
    seen_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"{list_key} 第 {index} 项必须是 mapping")
            continue
        entry_id = entry.get(id_key)
        if _is_blank(entry_id):
            errors.append(f"{list_key} 第 {index} 项缺少 {id_key}")
        elif str(entry_id) in seen_ids:
            errors.append(f"{list_key} 第 {index} 项重复 {id_key}: {entry_id}")
        else:
            seen_ids.add(str(entry_id))
        value = entry.get(value_key)
        if value not in allowed_values:
            errors.append(f"{list_key} 第 {index} 项 {value_key} 不支持: {value}")
        local_path = entry.get("local_path")
        if _is_blank(local_path):
            errors.append(f"{list_key} 第 {index} 项缺少 local_path")
        else:
            resolved = _resolve_project_path(config, str(local_path))
            if not resolved.is_file():
                errors.append(f"{list_key} 第 {index} 项 local_path 不存在: {local_path}")
    return errors


def validate_source_record(config: ProjectConfig, paper_id: str) -> list[str]:
    try:
        _ensure_formal_paper(config, paper_id)
        path = source_record_path(config, paper_id)
        if not path.exists():
            return [f"source record 不存在: {path}"]
        data = _load_mapping(path, default={})
    except AssetError as exc:
        return [str(exc)]
    errors = _validate_entries(
        config,
        paper_id=paper_id,
        data=data,
        list_key="sources",
        id_key="source_id",
        allowed_values=SOURCE_TYPES,
        value_key="source_type",
    )
    sources = data.get("sources")
    if isinstance(sources, list):
        for index, entry in enumerate(sources, start=1):
            if not isinstance(entry, dict):
                continue
            if entry.get("authorization") not in SOURCE_AUTHORIZATIONS:
                errors.append(f"sources 第 {index} 项 authorization 不支持: {entry.get('authorization')}")
            if _is_blank(entry.get("license_note")):
                errors.append(f"sources 第 {index} 项缺少 license_note")
    return errors


def validate_asset_manifest(config: ProjectConfig, paper_id: str) -> list[str]:
    try:
        _ensure_formal_paper(config, paper_id)
        path = asset_manifest_path(config, paper_id)
        if not path.exists():
            return [f"asset manifest 不存在: {path}"]
        data = _load_mapping(path, default={})
    except AssetError as exc:
        return [str(exc)]
    return _validate_entries(
        config,
        paper_id=paper_id,
        data=data,
        list_key="assets",
        id_key="asset_id",
        allowed_values=ASSET_KINDS,
        value_key="kind",
    )


def source_status(config: ProjectConfig, paper_id: str) -> LedgerStatus:
    path = source_record_path(config, paper_id)
    if not path.exists():
        return LedgerStatus(path=path, total_count=0, available_count=0, blocked_count=0)
    data = _load_mapping(path, default={"paper_id": paper_id, "sources": []})
    sources = data.get("sources") if isinstance(data.get("sources"), list) else []
    available = sum(1 for item in sources if isinstance(item, dict) and item.get("status") == "available")
    blocked = sum(1 for item in sources if isinstance(item, dict) and item.get("status") == "blocked")
    return LedgerStatus(path=path, total_count=len(sources), available_count=available, blocked_count=blocked)


def asset_status(config: ProjectConfig, paper_id: str) -> LedgerStatus:
    path = asset_manifest_path(config, paper_id)
    if not path.exists():
        return LedgerStatus(path=path, total_count=0, available_count=0, blocked_count=0)
    data = _load_mapping(path, default={"paper_id": paper_id, "assets": []})
    assets = data.get("assets") if isinstance(data.get("assets"), list) else []
    return LedgerStatus(
        path=path,
        total_count=len(assets),
        available_count=len(assets),
        blocked_count=0,
    )
