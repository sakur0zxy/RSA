from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from .assets import asset_manifest_path, source_record_path
from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, load_metadata_record, validate_metadata_record
from .notes import NoteError, load_reading_note, note_path


VISUAL_TYPES = {"text", "figure", "table", "caption", "equation", "unknown"}
VISUAL_STATUSES = {
    "detected",
    "cropped",
    "ocr_success",
    "ocr_partial",
    "needs_review",
    "blocked",
    "not_run",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
EVIDENCE_LEVELS = {
    "caption_only",
    "visual_only",
    "ocr_text",
    "caption_and_visual",
    "caption_visual_text",
    "blocked",
}

VERSION_PRIORITY = {
    "publisher_version": 0,
    "accepted_manuscript": 1,
    "repository_copy": 2,
    "arxiv_preprint": 3,
}

REQUIRED_CANDIDATE_FIELDS = [
    "candidate_id",
    "paper_id",
    "asset_id",
    "visual_type",
    "page",
    "region_bbox",
    "source_rects",
    "source_text",
    "confidence",
    "evidence_level",
    "status",
    "source_links",
    "advanced_analysis",
    "llm_visual_analysis",
]


class VisualError(ValueError):
    """Raised when visual evidence operations must fail closed."""


@dataclass(frozen=True)
class VisualSource:
    source_id: str
    path: Path
    display_path: str
    authorization: str
    source_hash: str
    source_record: Path | None


@dataclass(frozen=True)
class VisualExtractionResult:
    candidate_path: Path
    manifest_path: Path
    candidates_created: int
    crops_written: int
    context_packets_written: int


@dataclass(frozen=True)
class VisualStatus:
    path: Path
    total_count: int
    cropped_count: int
    ocr_success_count: int
    ocr_partial_count: int
    needs_review_count: int
    blocked_count: int
    not_run_count: int


def visual_candidate_path(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.assets_root / paper_id / "visual_evidence_candidates.yaml"


def visual_context_packet_dir(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.assets_root / paper_id / "visual_context_packets"


def crop_output_dir(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.assets_root / paper_id / "crops"


def parse_pages_spec(value: str | None) -> set[int] | None:
    if value is None or not str(value).strip():
        return None
    pages: set[int] = set()
    for part in str(value).split(","):
        item = part.strip()
        if not item:
            continue
        if "-" in item:
            left, right = item.split("-", 1)
            start = int(left.strip())
            end = int(right.strip())
            if start <= 0 or end < start:
                raise VisualError("--pages 必须使用正整数页码或递增范围，例如 3,5-7")
            pages.update(range(start, end + 1))
        else:
            page = int(item)
            if page <= 0:
                raise VisualError("--pages 必须使用正整数页码，例如 1 或 3,5-7")
            pages.add(page)
    return pages or None


def default_advanced_analysis() -> dict[str, dict[str, Any]]:
    return {
        "curve_extraction": {
            "status": "not_run",
            "result_file": None,
            "note_zh": "Phase 8.1 不做曲线数值自动还原；后续如需扩展，必须保留人工复核和来源定位。",
        },
        "table_structure": {
            "status": "not_run",
            "result_file": None,
            "note_zh": "Phase 8.1 不做高级表格结构重建；这里只保留候选视觉证据定位。",
        },
        "multimodal_interpretation": {
            "status": "not_run",
            "result_file": None,
            "note_zh": "LLM 图像理解留给 Phase 9 或后续扩展，不能在本阶段生成正式学术结论。",
        },
    }


def load_visual_candidates(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    _ensure_metadata(config, paper_id)
    path = visual_candidate_path(config, paper_id)
    if not path.exists():
        return {"paper_id": paper_id, "candidates": []}
    return _read_yaml_mapping(path)


def write_visual_candidates(
    config: ProjectConfig, paper_id: str, data: dict[str, Any]
) -> Path:
    _ensure_metadata(config, paper_id)
    if not isinstance(data, dict):
        raise VisualError("visual_evidence_candidates.yaml 必须是 YAML mapping")
    if data.get("paper_id") not in (None, paper_id):
        raise VisualError(
            f"visual candidate paper_id 必须与文件名一致: expected {paper_id}, got {data.get('paper_id')}"
        )
    if not isinstance(data.get("candidates", []), list):
        raise VisualError("candidates 必须是 YAML list")
    data["paper_id"] = paper_id
    path = visual_candidate_path(config, paper_id)
    _write_yaml(path, data)
    return path


def next_candidate_id(candidates: Iterable[Any]) -> str:
    highest = 0
    pattern = re.compile(r"^V(?P<number>\d{3})$")
    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        match = pattern.match(str(entry.get("candidate_id") or ""))
        if match:
            highest = max(highest, int(match.group("number")))
    return f"V{highest + 1:03d}"


def validate_visual_candidate_file(config: ProjectConfig, paper_id: str) -> list[str]:
    errors: list[str] = []
    if not PAPER_ID_PATTERN.match(paper_id):
        return [f"paper_id 必须匹配 P###: {paper_id}"]

    metadata_errors = validate_metadata_record(_metadata_path(config, paper_id))
    if metadata_errors:
        errors.append(f"{paper_id} metadata 无效: " + "; ".join(metadata_errors))

    path = visual_candidate_path(config, paper_id)
    if not path.exists():
        return errors + [f"visual_evidence_candidates.yaml 不存在: {path}"]
    try:
        data = _read_yaml_mapping(path)
    except VisualError as exc:
        return errors + [str(exc)]

    if data.get("paper_id") != paper_id:
        errors.append(
            f"paper_id 必须与文件名一致: expected {paper_id}, got {data.get('paper_id')}"
        )
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        return errors + ["candidates 必须是 YAML list"]

    seen_ids: set[str] = set()
    for index, entry in enumerate(candidates, start=1):
        prefix = f"candidates 第 {index} 项"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} 必须是 mapping")
            continue
        for field in REQUIRED_CANDIDATE_FIELDS:
            if field not in entry:
                errors.append(f"{prefix} 缺少字段: {field}")

        candidate_id = str(entry.get("candidate_id") or "")
        if not re.match(r"^V\d{3}$", candidate_id):
            errors.append(f"{prefix} candidate_id 必须匹配 V###")
        elif candidate_id in seen_ids:
            errors.append(f"{prefix} candidate_id 重复: {candidate_id}")
        else:
            seen_ids.add(candidate_id)

        if entry.get("paper_id") != paper_id:
            errors.append(f"{prefix} paper_id 必须是 {paper_id}")
        if entry.get("visual_type") not in VISUAL_TYPES:
            errors.append(f"{prefix} visual_type 不支持: {entry.get('visual_type')}")
        if entry.get("status") not in VISUAL_STATUSES:
            errors.append(f"{prefix} status 不支持: {entry.get('status')}")
        if entry.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{prefix} confidence 不支持: {entry.get('confidence')}")
        if entry.get("evidence_level") not in EVIDENCE_LEVELS:
            errors.append(f"{prefix} evidence_level 不支持: {entry.get('evidence_level')}")
        if not _is_valid_optional_bbox(entry.get("region_bbox")):
            errors.append(f"{prefix} region_bbox 必须是 [x0, y0, x1, y1] 或 null")
        if not isinstance(entry.get("source_rects"), list):
            errors.append(f"{prefix} source_rects 必须是 list")
        if not isinstance(entry.get("source_links"), dict) or not entry.get("source_links"):
            errors.append(f"{prefix} 缺少 source_links，无法回链到 PDF/笔记/资产记录")

        status = entry.get("status")
        if status in {"needs_review", "ocr_partial", "blocked"}:
            if _is_blank(entry.get("warning_zh")):
                errors.append(f"{prefix} status={status} 时必须提供 warning_zh")
            if _is_blank(entry.get("repair_hint_zh")):
                errors.append(f"{prefix} status={status} 时必须提供 repair_hint_zh")
        if entry.get("evidence_level") == "visual_only" and _is_blank(
            entry.get("warning_zh")
        ):
            errors.append(f"{prefix} evidence_level=visual_only 时必须提供 warning_zh")

        _validate_advanced_analysis(prefix, entry.get("advanced_analysis"), errors)
        llm = entry.get("llm_visual_analysis")
        if not isinstance(llm, dict) or llm.get("status") != "not_run":
            errors.append(f"{prefix} llm_visual_analysis.status 必须是 not_run")
    return errors


def select_visual_source(config: ProjectConfig, paper_id: str) -> VisualSource:
    _ensure_metadata(config, paper_id)
    ledger_path = source_record_path(config, paper_id)
    ledger = _read_yaml_mapping(ledger_path) if ledger_path.exists() else {}
    raw_sources = ledger.get("sources", [])
    if isinstance(raw_sources, list):
        candidates = [
            item
            for item in raw_sources
            if isinstance(item, dict)
            and item.get("status") == "available"
            and item.get("source_type") == "pdf"
            and item.get("local_path")
        ]
        candidates.sort(key=_source_sort_key)
        for entry in candidates:
            path = _resolve_project_path(config, str(entry["local_path"]))
            if path.is_file():
                return VisualSource(
                    source_id=str(entry.get("source_id") or "source_ledger"),
                    path=path,
                    display_path=_display_path(config, path),
                    authorization=str(entry.get("authorization") or "authorized"),
                    source_hash=_sha256(path),
                    source_record=ledger_path,
                )

    try:
        note = load_reading_note(config, paper_id)
    except NoteError:
        note = None
    if note:
        source_file = note.frontmatter.get("source_file")
        if source_file:
            path = _resolve_project_path(config, str(source_file))
            if path.is_file():
                return VisualSource(
                    source_id=str(note.frontmatter.get("source_id") or "reading_note"),
                    path=path,
                    display_path=_display_path(config, path),
                    authorization=str(note.frontmatter.get("authorization") or "authorized"),
                    source_hash=_sha256(path),
                    source_record=None,
                )

    metadata = load_metadata_record(_metadata_path(config, paper_id))
    local_pdf = metadata.get("local_pdf")
    if local_pdf:
        path = _resolve_project_path(config, str(local_pdf))
        if path.is_file():
            return VisualSource(
                source_id="metadata_local_pdf",
                path=path,
                display_path=_display_path(config, path),
                authorization=str(metadata.get("pdf_status") or "local"),
                source_hash=_sha256(path),
                source_record=None,
            )

    raise VisualError(
        f"{paper_id} 缺少可用 PDF：请先通过 rsa source add / rsa source find 登记本地、用户提供或已授权全文。"
    )


def load_asset_suggestions(config: ProjectConfig, paper_id: str) -> list[dict[str, Any]]:
    try:
        note = load_reading_note(config, paper_id)
    except NoteError:
        return []

    raw = note.frontmatter.get("asset_suggestions")
    suggestions: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for index, item in enumerate(raw, start=1):
            suggestions.append(_normalize_suggestion(item, index=index, note_file=note.path))
    else:
        for index, item in enumerate(_parse_suggestions_from_body(note.body), start=1):
            suggestions.append(_normalize_suggestion(item, index=index, note_file=note.path))
    return suggestions


def build_initial_candidate_from_suggestion(
    config: ProjectConfig,
    paper_id: str,
    suggestion: dict[str, Any],
    candidate_id: str,
) -> dict[str, Any]:
    visual_type = _visual_type_from_hint(
        " ".join(
            str(suggestion.get(key) or "")
            for key in ["label", "figure_or_table", "reason_zh", "raw_text"]
        )
    )
    page = _coerce_int(suggestion.get("page"))
    return {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "asset_id": None,
        "visual_type": visual_type,
        "page": page,
        "region_bbox": suggestion.get("region_bbox"),
        "source_rects": [],
        "source_text": None,
        "caption_zh": None,
        "ocr_summary_zh": "该候选来自阅读草稿的 asset_suggestions，尚未完成 PDF 区域裁图或文本提取。",
        "confidence": _valid_confidence(suggestion.get("confidence"), default="low"),
        "evidence_level": "caption_only" if suggestion.get("reason_zh") else "visual_only",
        "status": "detected",
        "warning_zh": "这是候选视觉证据，不是正式学术结论；需要后续裁图、回源或人工复核。",
        "repair_hint_zh": "运行 rsa visual extract，或人工查看对应 PDF 页面后再决定是否用于 Phase 9 评分。",
        "reason_zh": suggestion.get("reason_zh")
        or "阅读草稿提示该位置可能包含图表或表格证据。",
        "source_links": _base_source_links(config, paper_id)
        | {"suggestion_id": suggestion.get("suggestion_id")},
        "advanced_analysis": default_advanced_analysis(),
        "llm_visual_analysis": {"status": "not_run"},
    }


def extract_visual_evidence(
    config: ProjectConfig,
    paper_id: str,
    *,
    all_detected: bool = False,
    pages: set[int] | None = None,
    asset_suggestions_only: bool = False,
) -> VisualExtractionResult:
    _ensure_metadata(config, paper_id)
    source = select_visual_source(config, paper_id)
    data = load_visual_candidates(config, paper_id)
    candidates = data.setdefault("candidates", [])
    if not isinstance(candidates, list):
        raise VisualError("candidates 必须是 YAML list，无法继续写入视觉证据候选。")

    fitz = _load_fitz()
    suggestions = [
        suggestion
        for suggestion in load_asset_suggestions(config, paper_id)
        if pages is None or suggestion.get("page") in pages or suggestion.get("page") is None
    ]
    created: list[dict[str, Any]] = []
    source_links = _base_source_links(config, paper_id) | {
        "source_id": source.source_id,
        "source_file": source.display_path,
    }

    doc = None
    try:
        doc = fitz.open(str(source.path))
        for suggestion in suggestions:
            candidate_id = next_candidate_id([*candidates, *created])
            candidate = build_initial_candidate_from_suggestion(
                config, paper_id, suggestion, candidate_id
            )
            candidate["source_links"].update(source_links)
            if not asset_suggestions_only:
                _bind_suggestion_to_pdf(
                    fitz,
                    doc,
                    config=config,
                    paper_id=paper_id,
                    candidate=candidate,
                    suggestion=suggestion,
                )
            created.append(candidate)

        if not asset_suggestions_only:
            suggestion_pages = {
                int(item["page"])
                for item in suggestions
                if isinstance(item.get("page"), int)
            }
            for page_number, page in _iter_pages(doc, pages):
                page_regions = _detect_page_regions(page, page_number)
                captions = [
                    item for item in page_regions if item["visual_type"] == "caption"
                ]
                for region in page_regions:
                    if region["visual_type"] == "caption" and not all_detected:
                        continue
                    if (
                        not all_detected
                        and page_number not in suggestion_pages
                        and not captions
                        and region.get("confidence") != "high"
                    ):
                        continue
                    if _is_duplicate_region(created, page_number, region["region_bbox"]):
                        continue
                    candidate_id = next_candidate_id([*candidates, *created])
                    candidate = _candidate_from_region(
                        config,
                        paper_id,
                        candidate_id=candidate_id,
                        region=region,
                        source_links=source_links,
                    )
                    _finalize_candidate_with_pdf(
                        fitz,
                        page,
                        config=config,
                        paper_id=paper_id,
                        candidate=candidate,
                        captions=captions,
                    )
                    created.append(candidate)
    except VisualError:
        raise
    except Exception as exc:
        raise VisualError(f"视觉证据提取失败：{exc}") from exc
    finally:
        if doc is not None:
            doc.close()

    candidates.extend(created)
    path = write_visual_candidates(config, paper_id, data)
    manifest_path = asset_manifest_path(config, paper_id)
    return VisualExtractionResult(
        candidate_path=path,
        manifest_path=manifest_path,
        candidates_created=len(created),
        crops_written=sum(1 for item in created if item.get("asset_id")),
        context_packets_written=sum(1 for item in created if item.get("visual_context_packet")),
    )


def visual_status(config: ProjectConfig, paper_id: str) -> VisualStatus:
    path = visual_candidate_path(config, paper_id)
    if not path.exists():
        return VisualStatus(path, 0, 0, 0, 0, 0, 0, 0)
    try:
        data = _read_yaml_mapping(path)
    except VisualError:
        return VisualStatus(path, 0, 0, 0, 0, 0, 0, 0)
    candidates = data.get("candidates") if isinstance(data.get("candidates"), list) else []
    return VisualStatus(
        path=path,
        total_count=len(candidates),
        cropped_count=sum(1 for item in candidates if item.get("status") == "cropped"),
        ocr_success_count=sum(1 for item in candidates if item.get("status") == "ocr_success"),
        ocr_partial_count=sum(1 for item in candidates if item.get("status") == "ocr_partial"),
        needs_review_count=sum(1 for item in candidates if item.get("status") == "needs_review"),
        blocked_count=sum(1 for item in candidates if item.get("status") == "blocked"),
        not_run_count=sum(1 for item in candidates if item.get("status") == "not_run"),
    )


def _require_paper_id(paper_id: str) -> None:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise VisualError(f"paper_id 必须匹配 P###: {paper_id}")


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


def _ensure_metadata(config: ProjectConfig, paper_id: str) -> None:
    _require_paper_id(paper_id)
    errors = validate_metadata_record(_metadata_path(config, paper_id))
    if errors:
        raise VisualError(f"{paper_id} metadata 无效，无法处理视觉证据: " + "; ".join(errors))


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise VisualError(f"无法读取 YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise VisualError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise VisualError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _source_sort_key(entry: dict[str, Any]) -> tuple[int, int, str]:
    primary = 0 if entry.get("is_primary") is True else 1
    version = str(entry.get("version_label") or "")
    priority = VERSION_PRIORITY.get(version, 50)
    return primary, priority, str(entry.get("source_id") or "")


def _is_valid_optional_bbox(value: Any) -> bool:
    if value in (None, []):
        return True
    if not isinstance(value, list) or len(value) != 4:
        return False
    return all(isinstance(item, (int, float)) for item in value)


def _validate_advanced_analysis(
    prefix: str, value: Any, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} advanced_analysis 必须是 mapping")
        return
    for key in ["curve_extraction", "table_structure", "multimodal_interpretation"]:
        item = value.get(key)
        if not isinstance(item, dict):
            errors.append(f"{prefix} advanced_analysis.{key} 必须是 mapping")
            continue
        if item.get("status") != "not_run":
            errors.append(f"{prefix} advanced_analysis.{key}.status 必须是 not_run")


def _valid_confidence(value: Any, *, default: str) -> str:
    return str(value) if value in CONFIDENCE_LEVELS else default


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group(0))
    return None


def _normalize_suggestion(
    item: Any, *, index: int, note_file: Path
) -> dict[str, Any]:
    if isinstance(item, dict):
        raw = dict(item)
        reason = raw.get("reason_zh") or raw.get("reason") or raw.get("evidence_basis")
        page = raw.get("page") or raw.get("evidence_page")
        label = raw.get("label") or raw.get("figure_or_table") or raw.get("asset_request_type")
        confidence = raw.get("confidence")
    else:
        raw_text = str(item)
        reason = raw_text
        page = _page_from_text(raw_text)
        label = _label_from_text(raw_text)
        confidence = "low"
        raw = {"raw_text": raw_text}
    return {
        "suggestion_id": f"SUG{index:03d}",
        "page": _coerce_int(page),
        "label": str(label or f"候选图表 {index}"),
        "reason_zh": str(reason or "阅读草稿建议检查该图表/表格候选。"),
        "confidence": _valid_confidence(confidence, default="low"),
        "note_file": str(note_file),
        **raw,
    }


def _parse_suggestions_from_body(body: str) -> list[str]:
    lines = body.splitlines()
    inside = False
    suggestions: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped.lstrip("#").strip()
            inside = (
                ("候选" in heading or "Candidate" in heading)
                and ("图" in heading or "表" in heading or "asset" in heading.lower())
            )
            continue
        if inside and stripped.startswith("-"):
            suggestions.append(stripped.lstrip("-").strip())
    return suggestions


def _page_from_text(text: str) -> int | None:
    for pattern in [r"page\s*[:=]?\s*(\d+)", r"第\s*(\d+)\s*页", r"页\s*(\d+)"]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _label_from_text(text: str) -> str | None:
    match = re.search(r"(Fig(?:ure)?\.?\s*\d+|Table\s*\d+|图\s*\d+|表\s*\d+)", text)
    return match.group(1) if match else None


def _visual_type_from_hint(text: str) -> str:
    lowered = text.lower()
    if "table" in lowered or "表" in text:
        return "table"
    if "fig" in lowered or "figure" in lowered or "图" in text:
        return "figure"
    return "unknown"


def _base_source_links(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    return {
        "metadata": _display_path(config, _metadata_path(config, paper_id)),
        "reading_note": _display_path(config, note_path(config, paper_id)),
        "source_ledger": _display_path(config, source_record_path(config, paper_id)),
        "asset_manifest": _display_path(config, asset_manifest_path(config, paper_id)),
    }


def _load_fitz():
    try:
        import fitz
    except ImportError as exc:
        raise VisualError(
            "缺少 PyMuPDF，无法执行视觉证据提取；请安装基础依赖后重试。"
        ) from exc
    return fitz


def _iter_pages(doc: Any, pages: set[int] | None):
    selected = pages or set(range(1, len(doc) + 1))
    for page_number in sorted(selected):
        if page_number < 1 or page_number > len(doc):
            continue
        yield page_number, doc[page_number - 1]


def _detect_page_regions(page: Any, page_number: int) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    try:
        blocks = page.get_text("dict").get("blocks", [])
    except Exception:
        blocks = []
    for block in blocks:
        bbox = _bbox_from_block(block)
        if not bbox:
            continue
        block_type = block.get("type")
        if block_type == 1:
            regions.append(
                {
                    "visual_type": "figure",
                    "page": page_number,
                    "region_bbox": bbox,
                    "source_text": None,
                    "confidence": "medium",
                }
            )
            continue
        text = _block_text(block)
        if text and _is_caption_text(text):
            visual_type = "table" if "table" in text.lower() or text.startswith("表") else "caption"
            regions.append(
                {
                    "visual_type": visual_type,
                    "page": page_number,
                    "region_bbox": bbox,
                    "source_text": _limit_text(text),
                    "caption_zh": _limit_text(text),
                    "confidence": "high",
                }
            )
    return regions


def _bbox_from_block(block: dict[str, Any]) -> list[float] | None:
    bbox = block.get("bbox")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    try:
        return [round(float(item), 2) for item in bbox]
    except (TypeError, ValueError):
        return None


def _block_text(block: dict[str, Any]) -> str:
    lines = block.get("lines")
    if not isinstance(lines, list):
        return ""
    spans: list[str] = []
    for line in lines:
        for span in line.get("spans", []) if isinstance(line, dict) else []:
            text = span.get("text") if isinstance(span, dict) else None
            if text:
                spans.append(str(text))
    return re.sub(r"\s+", " ", " ".join(spans)).strip()


def _is_caption_text(text: str) -> bool:
    return bool(
        re.match(
            r"^\s*(Fig\.?|Figure|Table|图|表)\s*[\d一二三四五六七八九十IVX]",
            text,
            flags=re.IGNORECASE,
        )
    )


def _is_duplicate_region(
    candidates: list[dict[str, Any]], page_number: int, bbox: list[float]
) -> bool:
    rounded = [round(float(item), 1) for item in bbox]
    for candidate in candidates:
        if candidate.get("page") != page_number:
            continue
        other = candidate.get("region_bbox")
        if isinstance(other, list) and [round(float(item), 1) for item in other] == rounded:
            return True
    return False


def _candidate_from_region(
    config: ProjectConfig,
    paper_id: str,
    *,
    candidate_id: str,
    region: dict[str, Any],
    source_links: dict[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "asset_id": None,
        "visual_type": region.get("visual_type", "unknown"),
        "page": region.get("page"),
        "region_bbox": region.get("region_bbox"),
        "source_rects": [region.get("region_bbox")],
        "source_text": region.get("source_text"),
        "caption_zh": region.get("caption_zh"),
        "ocr_summary_zh": None,
        "confidence": _valid_confidence(region.get("confidence"), default="medium"),
        "evidence_level": "blocked",
        "status": "detected",
        "warning_zh": None,
        "repair_hint_zh": None,
        "source_links": dict(source_links),
        "advanced_analysis": default_advanced_analysis(),
        "llm_visual_analysis": {"status": "not_run"},
    }


def _bind_suggestion_to_pdf(
    fitz: Any,
    doc: Any,
    *,
    config: ProjectConfig,
    paper_id: str,
    candidate: dict[str, Any],
    suggestion: dict[str, Any],
) -> None:
    page_number = suggestion.get("page")
    if not isinstance(page_number, int) or page_number < 1 or page_number > len(doc):
        return
    page = doc[page_number - 1]
    regions = _detect_page_regions(page, page_number)
    chosen = _choose_region_for_suggestion(regions, suggestion)
    if chosen:
        candidate.update(
            {
                "visual_type": chosen.get("visual_type") or candidate["visual_type"],
                "region_bbox": chosen.get("region_bbox"),
                "source_rects": [chosen.get("region_bbox")],
                "source_text": chosen.get("source_text"),
                "caption_zh": chosen.get("caption_zh") or candidate.get("caption_zh"),
            }
        )
        captions = [item for item in regions if item.get("caption_zh")]
        _finalize_candidate_with_pdf(
            fitz,
            page,
            config=config,
            paper_id=paper_id,
            candidate=candidate,
            captions=captions,
        )


def _choose_region_for_suggestion(
    regions: list[dict[str, Any]], suggestion: dict[str, Any]
) -> dict[str, Any] | None:
    preferred = _visual_type_from_hint(str(suggestion.get("label") or ""))
    for region in regions:
        if preferred != "unknown" and region.get("visual_type") == preferred:
            return region
    for region in regions:
        if region.get("visual_type") in {"figure", "table"}:
            return region
    return regions[0] if regions else None


def _finalize_candidate_with_pdf(
    fitz: Any,
    page: Any,
    *,
    config: ProjectConfig,
    paper_id: str,
    candidate: dict[str, Any],
    captions: list[dict[str, Any]],
) -> None:
    bbox = candidate.get("region_bbox")
    if not _is_valid_optional_bbox(bbox) or not bbox:
        candidate.update(
            {
                "status": "needs_review",
                "evidence_level": "blocked",
                "warning_zh": "该候选缺少可裁剪的 PDF 区域坐标。",
                "repair_hint_zh": "请人工查看 PDF 页面，或使用 --all-detected / --pages 重新检测。",
            }
        )
        return
    rect = fitz.Rect(bbox)
    if rect.is_empty or rect.is_infinite:
        candidate.update(
            {
                "status": "needs_review",
                "evidence_level": "blocked",
                "warning_zh": "检测到的图表区域无效，无法安全裁图。",
                "repair_hint_zh": "请人工核对页面区域后再作为视觉证据候选。",
            }
        )
        return

    try:
        crop_dir = crop_output_dir(config, paper_id)
        crop_dir.mkdir(parents=True, exist_ok=True)
        crop_path = crop_dir / f"{candidate['candidate_id']}.png"
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect)
        pix.save(str(crop_path))
        asset_id = _upsert_manifest_entry(
            config,
            paper_id,
            candidate=candidate,
            crop_path=crop_path,
        )
        candidate["asset_id"] = asset_id
    except Exception as exc:
        candidate.update(
            {
                "status": "needs_review",
                "evidence_level": "blocked",
                "warning_zh": f"裁图失败：{exc}",
                "repair_hint_zh": "请人工查看 PDF，确认该页面是否为扫描页、加密页或异常版式。",
            }
        )
        return

    if not candidate.get("source_text"):
        try:
            candidate["source_text"] = _limit_text(page.get_textbox(rect))
        except Exception:
            candidate["source_text"] = None
    if not candidate.get("caption_zh"):
        caption = _nearest_caption(candidate.get("region_bbox"), captions)
        if caption:
            candidate["caption_zh"] = caption.get("caption_zh") or caption.get("source_text")

    source_text = candidate.get("source_text")
    caption = candidate.get("caption_zh")
    if source_text and caption:
        candidate["status"] = "ocr_success"
        candidate["evidence_level"] = "caption_visual_text"
        candidate["ocr_summary_zh"] = "已从 PDF 图表区域提取到嵌入文本，并绑定到附近 caption。"
    elif source_text:
        candidate["status"] = "ocr_success"
        candidate["evidence_level"] = "ocr_text"
        candidate["ocr_summary_zh"] = "已从 PDF 图表区域提取到嵌入文本，但未绑定明确 caption。"
    elif caption:
        candidate["status"] = "cropped"
        candidate["evidence_level"] = "caption_and_visual"
        candidate["ocr_summary_zh"] = "已裁图并绑定 caption，但该区域没有可提取嵌入文本。"
    else:
        candidate["status"] = "cropped"
        candidate["evidence_level"] = "visual_only"
        candidate["warning_zh"] = "该候选只有裁图，没有可提取文本或明确 caption，不能直接用于学术判断。"
        candidate["repair_hint_zh"] = "请人工查看截图，或在后续 OCR/LLM 图像分析阶段补充解释。"
        candidate["ocr_summary_zh"] = "未能从该区域提取嵌入文本；可能需要后续 OCR 或人工查看。"

    packet_path = _write_context_packet(config, paper_id, candidate)
    candidate["visual_context_packet"] = _display_path(config, packet_path)


def _nearest_caption(
    bbox: list[float] | None, captions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not bbox or not captions:
        return None
    _, y0, _, y1 = bbox
    best: tuple[float, dict[str, Any]] | None = None
    for caption in captions:
        cbbox = caption.get("region_bbox")
        if not isinstance(cbbox, list) or len(cbbox) != 4:
            continue
        distance = min(abs(float(cbbox[1]) - float(y1)), abs(float(cbbox[3]) - float(y0)))
        if best is None or distance < best[0]:
            best = (distance, caption)
    return best[1] if best and best[0] <= 180 else None


def _upsert_manifest_entry(
    config: ProjectConfig,
    paper_id: str,
    *,
    candidate: dict[str, Any],
    crop_path: Path,
) -> str:
    manifest_path = asset_manifest_path(config, paper_id)
    manifest = (
        _read_yaml_mapping(manifest_path)
        if manifest_path.exists()
        else {"paper_id": paper_id, "assets": []}
    )
    assets = manifest.setdefault("assets", [])
    if not isinstance(assets, list):
        raise VisualError("asset manifest 的 assets 必须是 YAML list")

    existing = next(
        (
            item
            for item in assets
            if isinstance(item, dict)
            and item.get("source_candidate_id") == candidate.get("candidate_id")
        ),
        None,
    )
    if existing:
        asset_id = str(existing.get("asset_id"))
        entry = existing
    else:
        asset_id = _next_asset_id(assets)
        entry = {"asset_id": asset_id}
        assets.append(entry)

    kind = candidate.get("visual_type") if candidate.get("visual_type") in {"figure", "table"} else "screenshot"
    entry.update(
        {
            "asset_id": asset_id,
            "kind": kind,
            "label": candidate.get("caption_zh") or candidate.get("candidate_id"),
            "description_zh": "由 rsa visual extract 自动裁剪的视觉证据候选；仅供 staging/review 使用。",
            "page": str(candidate.get("page") or ""),
            "figure": candidate.get("candidate_id"),
            "original_path": candidate.get("source_links", {}).get("source_file"),
            "local_path": _display_path(config, crop_path),
            "added_by": "rsa visual extract",
            "added_at": datetime.now(timezone.utc).date().isoformat(),
            "generated_by": "rsa visual extract",
            "source_candidate_id": candidate.get("candidate_id"),
        }
    )
    manifest["paper_id"] = paper_id
    _write_yaml(manifest_path, manifest)
    return asset_id


def _next_asset_id(entries: list[Any]) -> str:
    highest = 0
    pattern = re.compile(r"^A(?P<number>\d{3})$")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        match = pattern.match(str(entry.get("asset_id") or ""))
        if match:
            highest = max(highest, int(match.group("number")))
    return f"A{highest + 1:03d}"


def _write_context_packet(
    config: ProjectConfig, paper_id: str, candidate: dict[str, Any]
) -> Path:
    packet_dir = visual_context_packet_dir(config, paper_id)
    packet_path = packet_dir / f"{candidate['candidate_id']}.yaml"
    data = {
        "paper_id": paper_id,
        "candidate_id": candidate.get("candidate_id"),
        "asset_id": candidate.get("asset_id"),
        "crop_path": _asset_crop_path(config, paper_id, candidate.get("candidate_id")),
        "page": candidate.get("page"),
        "region_bbox": candidate.get("region_bbox"),
        "caption_candidate": candidate.get("caption_zh"),
        "nearby_text": _limit_text(candidate.get("source_text")),
        "reference_sentence_candidates": [],
        "ocr_or_region_text": _limit_text(candidate.get("source_text")),
        "source_links": candidate.get("source_links"),
        "llm_visual_analysis": {"status": "not_run"},
    }
    _write_yaml(packet_path, data)
    return packet_path


def _asset_crop_path(
    config: ProjectConfig, paper_id: str, candidate_id: Any
) -> str | None:
    if not candidate_id:
        return None
    path = crop_output_dir(config, paper_id) / f"{candidate_id}.png"
    return _display_path(config, path)


def _limit_text(value: Any, limit: int = 500) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
