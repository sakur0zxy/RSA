from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .campaign import (
    FORMAL_WRITE_REQUEST_STATUSES,
    METADATA_REQUEST_STATUSES,
    REVIEW_QUEUE_GROUPS,
    campaign_metadata_requests_path,
    campaign_path,
    campaign_review_queue_path,
    campaign_run_path,
    validate_campaign,
    validate_campaign_run,
)
from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, validate_metadata_record
from .notes import NoteError, load_reading_note, note_path, validate_reading_note
from .scoring import scoring_path, validate_scoring_record
from .visual import validate_visual_candidate_file, visual_candidate_path


SAFETY_SCHEMA_VERSION = "phase13-safety-v1"
CITATION_REVIEW_VERSION = "claim-ref-v1"
CAMPAIGN_SAFETY_SCHEMA_VERSION = "phase13-campaign-safety-v1"
SAFETY_STATUSES = {"passed", "needs_review", "blocked", "missing"}


class SafetyError(ValueError):
    """Raised when safety checks cannot produce a reliable result."""


@dataclass(frozen=True)
class SafetyCheckResult:
    paper_id: str
    safety_status: str
    path: Path
    report_path: Path
    claim_count: int
    warning_count: int
    blocked_count: int


@dataclass(frozen=True)
class SafetyStatus:
    path: Path
    report_path: Path
    target_id: str
    exists: bool
    safety_status: str
    claim_count: int
    warning_count: int
    blocked_count: int
    generated_at: str | None


@dataclass(frozen=True)
class CampaignSafetyResult:
    campaign_id: str
    safety_status: str
    path: Path
    report_path: Path
    check_count: int
    warning_count: int
    blocked_count: int


def safety_record_path(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.safety_root / f"{paper_id}_safety.yaml"


def safety_report_path(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.safety_root / f"{paper_id}_safety_report.md"


def campaign_safety_record_path(config: ProjectConfig, campaign_id: str) -> Path:
    _require_campaign_id(campaign_id)
    return config.safety_root / f"{campaign_id}_campaign_safety.yaml"


def campaign_safety_report_path(config: ProjectConfig, campaign_id: str) -> Path:
    _require_campaign_id(campaign_id)
    return config.safety_root / f"{campaign_id}_campaign_safety_report.md"


def check_paper_safety(config: ProjectConfig, paper_id: str) -> SafetyCheckResult:
    _require_paper_id(paper_id)
    config.safety_root.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    claim_refs: list[dict[str, Any]] = []

    metadata_path = config.metadata_root / f"{paper_id}.yaml"
    metadata_errors = validate_metadata_record(metadata_path)
    if metadata_errors:
        checks.append(
            _check(
                "metadata_valid",
                "blocked",
                "正式 metadata 无效，无法进行可靠的写作安全检查。",
                "先修复 metadata/P###.yaml，再重新运行 rsa safety check。",
                [metadata_path],
                metadata_errors,
            )
        )
    else:
        checks.append(
            _check(
                "metadata_valid",
                "passed",
                "正式 metadata 可读取，paper_id 已进入正式文献库。",
                None,
                [metadata_path],
            )
        )

    note_errors = validate_reading_note(config, paper_id)
    note = None
    if note_errors:
        checks.append(
            _check(
                "reading_note_valid",
                "blocked",
                "reading note 缺失或结构无效，不能生成 claim-level citation review。",
                "先生成或修复 P###_reading_note.md，并确保其中有可追溯证据字段。",
                [note_path(config, paper_id)],
                note_errors,
            )
        )
    else:
        try:
            note = load_reading_note(config, paper_id)
        except NoteError as exc:
            checks.append(
                _check(
                    "reading_note_valid",
                    "blocked",
                    "reading note 无法读取。",
                    "修复 reading note YAML frontmatter 后重新检查。",
                    [note_path(config, paper_id)],
                    [str(exc)],
                )
            )
        else:
            checks.append(
                _check(
                    "reading_note_valid",
                    "passed",
                    "reading note 可读取，可抽取 source_grounded_claims 和 short_quotes。",
                    None,
                    [note_path(config, paper_id)],
                )
            )
            claim_refs.extend(_claim_refs_from_note(config, paper_id, note.frontmatter))

    if note is not None and not claim_refs:
        checks.append(
            _check(
                "claim_refs_present",
                "needs_review",
                "reading note 中没有可检查的 claim 或短引用。",
                "补充 source_grounded_claims 或 short_quotes，并填写页码、章节和证据片段。",
                [note_path(config, paper_id)],
            )
        )
    elif any(ref.get("status") == "needs_review" for ref in claim_refs):
        checks.append(
            _check(
                "claim_refs_present",
                "needs_review",
                "部分 claim 的证据链不完整，需要人工补页码、章节、chunk 或引用定位。",
                "优先修复 warning_zh 不为空的 claim_ref。",
                [note_path(config, paper_id)],
            )
        )
    elif claim_refs:
        checks.append(
            _check(
                "claim_refs_present",
                "passed",
                "已找到可回链的 claim_ref。",
                None,
                [note_path(config, paper_id)],
            )
        )

    scoring_file = scoring_path(config, paper_id)
    if scoring_file.exists():
        scoring_errors = validate_scoring_record(config, paper_id)
        if scoring_errors:
            checks.append(
                _check(
                    "scoring_provenance_valid",
                    "needs_review",
                    "scoring YAML 存在但结构或 provenance 需要复核。",
                    "先运行 rsa score validate P### 并修复评分记录。",
                    [scoring_file],
                    scoring_errors,
                )
            )
        else:
            scoring_data = _read_yaml_mapping(scoring_file)
            provenance = scoring_data.get("provenance") or {}
            source_chunks = provenance.get("source_chunks") or []
            if not isinstance(source_chunks, list) or not source_chunks:
                checks.append(
                    _check(
                        "scoring_provenance_valid",
                        "needs_review",
                        "scoring YAML 缺少 source_chunks，评分与原文 claim 的回链较弱。",
                        "重新运行或修复 rsa score P###，确保 provenance.source_chunks 可读。",
                        [scoring_file],
                    )
                )
            else:
                checks.append(
                    _check(
                        "scoring_provenance_valid",
                        "passed",
                        "scoring YAML 存在并保留 source_chunks provenance。",
                        None,
                        [scoring_file],
                    )
                )
    else:
        checks.append(
            _check(
                "scoring_provenance_valid",
                "passed",
                "未发现 scoring YAML；本次只检查 reading note claim 证据链。",
                None,
                [scoring_file],
            )
        )

    visual_file = visual_candidate_path(config, paper_id)
    if visual_file.exists():
        visual_errors = validate_visual_candidate_file(config, paper_id)
        checks.append(
            _check(
                "visual_candidates_valid",
                "needs_review" if visual_errors else "passed",
                "视觉证据候选已纳入安全检查。" if not visual_errors else "视觉证据候选存在结构或 trace 问题。",
                None if not visual_errors else "先运行 rsa visual validate P### 并修复候选 trace。",
                [visual_file],
                visual_errors,
            )
        )
    else:
        checks.append(
            _check(
                "visual_candidates_valid",
                "passed",
                "未发现视觉证据候选；本次不把图表证据作为 claim 依据。",
                None,
                [visual_file],
            )
        )

    checks.append(
        _check(
            "formal_boundary_intact",
            "passed",
            "safety check 只写入 01_literature/safety/，不会写 formal records。",
            None,
            [config.safety_root],
        )
    )

    safety_status = _overall_status(checks, claim_refs)
    record = {
        "schema_version": SAFETY_SCHEMA_VERSION,
        "citation_review_version": CITATION_REVIEW_VERSION,
        "paper_id": paper_id,
        "generated_at": _now(),
        "user_language": "zh",
        "safety_status": safety_status,
        "status_meaning_zh": _status_meaning(safety_status),
        "check_scope": [
            "metadata",
            "reading_note",
            "source_grounded_claims",
            "short_quotes",
            "scoring_provenance",
            "visual_candidates_if_present",
            "formal_boundary",
        ],
        "claim_refs": claim_refs,
        "checks": checks,
        "warnings_zh": _warnings(checks, claim_refs),
        "repair_hints_zh": _repair_hints(checks, claim_refs),
        "formal_record_policy_zh": (
            "本文件只是写作安全与引用链检查结果，不是 formal approval。"
            "任何写入 metadata、literature_map 或 agent_research_notes 的动作仍必须通过 formal write gate 和人工确认。"
        ),
        "future_interfaces": _future_interfaces(),
    }
    path = safety_record_path(config, paper_id)
    report = safety_report_path(config, paper_id)
    _write_yaml(path, record)
    report.write_text(_render_paper_report(record, path), encoding="utf-8")
    return SafetyCheckResult(
        paper_id=paper_id,
        safety_status=safety_status,
        path=path,
        report_path=report,
        claim_count=len(claim_refs),
        warning_count=len(record["warnings_zh"]),
        blocked_count=sum(1 for check in checks if check.get("status") == "blocked"),
    )


def validate_safety_record(config: ProjectConfig, paper_id: str) -> list[str]:
    _require_paper_id(paper_id)
    path = safety_record_path(config, paper_id)
    if not path.exists():
        return [f"safety 记录不存在: {path}"]
    try:
        data = _read_yaml_mapping(path)
    except SafetyError as exc:
        return [str(exc)]
    errors: list[str] = []
    if data.get("schema_version") != SAFETY_SCHEMA_VERSION:
        errors.append("schema_version 必须是 phase13-safety-v1")
    if data.get("citation_review_version") != CITATION_REVIEW_VERSION:
        errors.append("citation_review_version 必须是 claim-ref-v1")
    if data.get("paper_id") != paper_id:
        errors.append(f"paper_id 必须与文件名一致: {paper_id}")
    if data.get("safety_status") not in SAFETY_STATUSES:
        errors.append(f"safety_status 不支持: {data.get('safety_status')}")
    for field in ["claim_refs", "checks", "warnings_zh", "repair_hints_zh"]:
        if not isinstance(data.get(field), list):
            errors.append(f"{field} 必须是 YAML list")
    if not isinstance(data.get("future_interfaces"), dict):
        errors.append("future_interfaces 必须是 YAML mapping")
    for index, ref in enumerate(data.get("claim_refs") or [], start=1):
        if not isinstance(ref, dict):
            errors.append(f"claim_refs 第 {index} 项必须是 mapping")
            continue
        for field in ["claim_id", "claim_text_zh", "source_type", "paper_id", "status"]:
            if _is_blank(ref.get(field)):
                errors.append(f"claim_refs 第 {index} 项缺少 {field}")
    for index, check in enumerate(data.get("checks") or [], start=1):
        if not isinstance(check, dict):
            errors.append(f"checks 第 {index} 项必须是 mapping")
            continue
        if check.get("status") not in {"passed", "needs_review", "blocked", "missing"}:
            errors.append(f"checks 第 {index} 项 status 不支持: {check.get('status')}")
        if _is_blank(check.get("message_zh")):
            errors.append(f"checks 第 {index} 项缺少 message_zh")
    return errors


def safety_status(config: ProjectConfig, paper_id: str) -> SafetyStatus:
    _require_paper_id(paper_id)
    path = safety_record_path(config, paper_id)
    report = safety_report_path(config, paper_id)
    if not path.exists():
        return SafetyStatus(path, report, paper_id, False, "missing", 0, 0, 0, None)
    data = _read_yaml_mapping(path)
    checks = data.get("checks") if isinstance(data.get("checks"), list) else []
    warnings = data.get("warnings_zh") if isinstance(data.get("warnings_zh"), list) else []
    claims = data.get("claim_refs") if isinstance(data.get("claim_refs"), list) else []
    return SafetyStatus(
        path=path,
        report_path=report,
        target_id=paper_id,
        exists=True,
        safety_status=str(data.get("safety_status") or "missing"),
        claim_count=len(claims),
        warning_count=len(warnings),
        blocked_count=sum(1 for check in checks if isinstance(check, dict) and check.get("status") == "blocked"),
        generated_at=data.get("generated_at"),
    )


def check_campaign_safety(config: ProjectConfig, campaign_id: str) -> CampaignSafetyResult:
    _require_campaign_id(campaign_id)
    config.safety_root.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []

    campaign_errors = validate_campaign(config, campaign_id)
    checks.append(
        _check(
            "campaign_valid",
            "blocked" if campaign_errors else "passed",
            "campaign 结构有效。" if not campaign_errors else "campaign 结构无效，批量安全检查不可靠。",
            None if not campaign_errors else "先运行 rsa campaign validate C### 并修复 campaign YAML。",
            [campaign_path(config, campaign_id)],
            campaign_errors,
        )
    )

    run_path = campaign_run_path(config, campaign_id)
    run_data = _read_yaml_mapping(run_path) if run_path.exists() else {}
    if run_path.exists():
        run_errors = validate_campaign_run(config, campaign_id)
        checks.append(
            _check(
                "campaign_run_valid",
                "needs_review" if run_errors else "passed",
                "campaign run ledger 可读取。" if not run_errors else "campaign run ledger 有需要复核的问题。",
                None if not run_errors else "先运行 rsa campaign run/resume 或修复 run ledger。",
                [run_path],
                run_errors,
            )
        )
    else:
        checks.append(
            _check(
                "campaign_run_valid",
                "needs_review",
                "尚未发现 campaign run ledger，无法确认 blocked/partial 和 completed-item non-rerun 语义。",
                "先运行 rsa campaign run C### 或 dry-run 生成 run ledger。",
                [run_path],
            )
        )

    queue_path = campaign_review_queue_path(config, campaign_id)
    queue_data = _read_yaml_mapping(queue_path) if queue_path.exists() else {}
    queue_items = _list_of_mappings(queue_data.get("queue_items"))
    if queue_path.exists():
        checks.append(_review_queue_order_check(queue_path, queue_items))
        checks.append(_blocked_partial_aggregation_check(run_data, queue_items, run_path, queue_path))
        checks.append(_priority_confidence_queue_check(queue_items, queue_path))
    else:
        checks.append(
            _check(
                "review_queue_present",
                "needs_review",
                "尚未发现 review queue，无法确认排序和异常聚合。",
                "运行 rsa campaign queue C### 生成 review queue。",
                [queue_path],
            )
        )

    requests_path = campaign_metadata_requests_path(config, campaign_id)
    request_data = _read_yaml_mapping(requests_path) if requests_path.exists() else {}
    checks.extend(_metadata_request_checks(config, campaign_id, request_data, requests_path))
    checks.extend(_formal_request_checks(request_data, requests_path))
    checks.append(_completed_item_non_rerun_check(run_data, run_path))
    checks.append(_campaign_policy_check(run_data, run_path))

    safety_status = _overall_status(checks, [])
    record = {
        "schema_version": CAMPAIGN_SAFETY_SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "generated_at": _now(),
        "user_language": "zh",
        "safety_status": safety_status,
        "status_meaning_zh": _status_meaning(safety_status),
        "checks": checks,
        "warnings_zh": _warnings(checks, []),
        "repair_hints_zh": _repair_hints(checks, []),
        "monitored_failure_scenarios": [
            "authorization_errors",
            "blocked_partial_aggregation",
            "review_queue_ordering_regression",
            "formal_request_non_execution",
            "metadata_intake_not_writing_formal_metadata",
            "completed_item_non_rerun",
            "low_confidence_high_priority_queue_admission",
            "campaign_error_policy_semantics",
        ],
        "formal_record_policy_zh": (
            "campaign safety 只检查批量监管语义，不会执行 formal write，也不会创建 metadata/P###.yaml。"
        ),
        "future_interfaces": {
            "failure_detector_plugins": {"status": "not_run"},
            "worker_health_monitor": {"status": "not_run", "phase": "Phase 14"},
        },
    }
    path = campaign_safety_record_path(config, campaign_id)
    report = campaign_safety_report_path(config, campaign_id)
    _write_yaml(path, record)
    report.write_text(_render_campaign_report(record, path), encoding="utf-8")
    return CampaignSafetyResult(
        campaign_id=campaign_id,
        safety_status=safety_status,
        path=path,
        report_path=report,
        check_count=len(checks),
        warning_count=len(record["warnings_zh"]),
        blocked_count=sum(1 for check in checks if check.get("status") == "blocked"),
    )


def validate_campaign_safety_record(config: ProjectConfig, campaign_id: str) -> list[str]:
    _require_campaign_id(campaign_id)
    path = campaign_safety_record_path(config, campaign_id)
    if not path.exists():
        return [f"campaign safety 记录不存在: {path}"]
    try:
        data = _read_yaml_mapping(path)
    except SafetyError as exc:
        return [str(exc)]
    errors: list[str] = []
    if data.get("schema_version") != CAMPAIGN_SAFETY_SCHEMA_VERSION:
        errors.append("schema_version 必须是 phase13-campaign-safety-v1")
    if data.get("campaign_id") != campaign_id:
        errors.append(f"campaign_id 必须与文件名一致: {campaign_id}")
    if data.get("safety_status") not in SAFETY_STATUSES:
        errors.append(f"safety_status 不支持: {data.get('safety_status')}")
    if not isinstance(data.get("checks"), list):
        errors.append("checks 必须是 YAML list")
    if not isinstance(data.get("monitored_failure_scenarios"), list):
        errors.append("monitored_failure_scenarios 必须是 YAML list")
    return errors


def _claim_refs_from_note(
    config: ProjectConfig, paper_id: str, frontmatter: dict[str, Any]
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    note_display_path = _display_path(config, note_path(config, paper_id))
    for index, claim in enumerate(_list_of_mappings(frontmatter.get("source_grounded_claims")), start=1):
        missing = [
            label
            for label, value in {
                "evidence_page": claim.get("evidence_page"),
                "evidence_section": claim.get("evidence_section"),
                "source_chunk_id": claim.get("source_chunk_id"),
                "evidence_snippet": claim.get("evidence_snippet"),
            }.items()
            if _is_blank(value)
        ]
        refs.append(
            {
                "claim_id": str(claim.get("claim_id") or f"CL{index:03d}"),
                "claim_text_zh": str(claim.get("claim_zh") or ""),
                "source_type": "source_grounded_claim",
                "source_path": note_display_path,
                "paper_id": paper_id,
                "page": claim.get("evidence_page"),
                "section": claim.get("evidence_section"),
                "source_chunk_id": claim.get("source_chunk_id"),
                "quote_id": None,
                "visual_candidate_id": claim.get("visual_candidate_id"),
                "region_bbox": claim.get("region_bbox"),
                "evidence_level": claim.get("evidence_level") or "text_claim",
                "status": "needs_review" if missing else "linked",
                "warning_zh": "缺少证据定位字段: " + ", ".join(missing) if missing else None,
                "repair_hint_zh": "补充页码、章节、source_chunk_id 和 evidence_snippet。" if missing else None,
                "future": {
                    "doi": None,
                    "paragraph_id": None,
                    "sentence_id": None,
                    "figure_id": claim.get("figure_id"),
                    "table_id": claim.get("table_id"),
                    "confidence": claim.get("confidence"),
                    "llm_claim_review": {"status": "not_run"},
                },
            }
        )
    offset = len(refs)
    for index, quote in enumerate(_list_of_mappings(frontmatter.get("short_quotes")), start=1):
        quote_text = str(quote.get("quote") or quote.get("text") or "")
        missing = [label for label, value in {"page": quote.get("page"), "quote": quote_text}.items() if _is_blank(value)]
        refs.append(
            {
                "claim_id": f"QT{index:03d}",
                "claim_text_zh": quote_text,
                "source_type": "short_quote",
                "source_path": note_display_path,
                "paper_id": paper_id,
                "page": quote.get("page"),
                "section": quote.get("section"),
                "source_chunk_id": quote.get("source_chunk_id"),
                "quote_id": str(quote.get("quote_id") or f"Q{index:03d}"),
                "visual_candidate_id": quote.get("visual_candidate_id"),
                "region_bbox": quote.get("region_bbox"),
                "evidence_level": quote.get("evidence_level") or "short_quote",
                "status": "needs_review" if missing else "linked",
                "warning_zh": "短引用缺少定位字段: " + ", ".join(missing) if missing else None,
                "repair_hint_zh": "补充短引用文本和页码。" if missing else None,
                "future": {
                    "doi": None,
                    "paragraph_id": None,
                    "sentence_id": None,
                    "figure_id": quote.get("figure_id"),
                    "table_id": quote.get("table_id"),
                    "confidence": quote.get("confidence"),
                    "llm_claim_review": {"status": "not_run"},
                },
            }
        )
    for index, ref in enumerate(refs, start=1):
        ref.setdefault("claim_order", offset + index)
    return refs


def _metadata_request_checks(
    config: ProjectConfig,
    campaign_id: str,
    request_data: dict[str, Any],
    request_path: Path,
) -> list[dict[str, Any]]:
    if not request_path.exists():
        return [
            _check(
                "metadata_intake_requests_safe",
                "needs_review",
                "尚未发现 metadata intake request 文件。",
                "queued 候选进入后续流程前应生成 C###_metadata_requests.yaml。",
                [request_path],
            )
        ]
    errors: list[str] = []
    requests = _list_of_mappings(request_data.get("requests"))
    for index, request in enumerate(requests, start=1):
        prefix = f"request {index}"
        if _is_blank(request.get("request_id")):
            errors.append(f"{prefix} 缺少 request_id")
        if request.get("source_campaign_id") != campaign_id:
            errors.append(f"{prefix} source_campaign_id 必须是 {campaign_id}")
        if request.get("status") not in METADATA_REQUEST_STATUSES:
            errors.append(f"{prefix} status 不支持: {request.get('status')}")
        if request.get("formal_write_allowed") is not False:
            errors.append(f"{prefix} formal_write_allowed 必须是 false")
        if not isinstance(request.get("candidate_metadata"), dict):
            errors.append(f"{prefix} candidate_metadata 必须是 mapping")
    p002_created = (config.metadata_root / "P002.yaml").exists()
    if requests and p002_created:
        errors.append("检测到 P002.yaml 已存在，需人工确认它不是 metadata intake 自动创建的正式记录")
    return [
        _check(
            "metadata_intake_requests_safe",
            "blocked" if errors else "passed",
            "metadata intake request 不会直接写 formal metadata。" if not errors else "metadata intake request 存在安全边界问题。",
            None if not errors else "修复 metadata request 字段，确保 formal_write_allowed: false 且不自动创建 P###.yaml。",
            [request_path],
            errors,
        )
    ]


def _formal_request_checks(
    request_data: dict[str, Any], request_path: Path
) -> list[dict[str, Any]]:
    if not request_path.exists():
        return [
            _check(
                "formal_request_non_execution",
                "needs_review",
                "尚未发现 formal write request 文件，无法确认 formal request 非自动执行。",
                "当 metadata request 被 accepted 后，应生成 pending_human_approval 的 formal_write_request。",
                [request_path],
            )
        ]
    errors: list[str] = []
    requests = _list_of_mappings(request_data.get("requests"))
    formal_requests = _list_of_mappings(request_data.get("formal_write_requests"))
    accepted_ids = {
        str(request.get("request_id"))
        for request in requests
        if request.get("status") == "accepted" and request.get("request_id")
    }
    formal_sources = {
        str(request.get("source_metadata_request_id"))
        for request in formal_requests
        if request.get("source_metadata_request_id")
    }
    for request_id in sorted(accepted_ids - formal_sources):
        errors.append(f"accepted metadata request {request_id} 尚未生成 formal_write_request")
    for index, request in enumerate(formal_requests, start=1):
        prefix = f"formal_write_request {index}"
        if request.get("status") not in FORMAL_WRITE_REQUEST_STATUSES:
            errors.append(f"{prefix} status 不支持: {request.get('status')}")
        if request.get("status") == "pending_human_approval":
            if request.get("human_confirmed") is not False:
                errors.append(f"{prefix} pending_human_approval 必须 human_confirmed: false")
            if request.get("formal_write_allowed") is not False:
                errors.append(f"{prefix} pending_human_approval 必须 formal_write_allowed: false")
    return [
        _check(
            "formal_request_non_execution",
            "needs_review" if errors else "passed",
            "formal write request 保持待人工确认，不会自动执行。" if not errors else "formal write request 需要人工复核。",
            None if not errors else "生成或修复 formal_write_requests，保持 pending_human_approval 不可自动写入。",
            [request_path],
            errors,
        )
    ]


def _review_queue_order_check(path: Path, queue_items: list[dict[str, Any]]) -> dict[str, Any]:
    order = []
    errors: list[str] = []
    for item in queue_items:
        group = str(item.get("queue_group") or "skipped")
        try:
            order.append(REVIEW_QUEUE_GROUPS.index(group))
        except ValueError:
            errors.append(f"未知 queue_group: {group}")
    if order != sorted(order):
        errors.append("review queue group 顺序不符合 urgency-first 排序")
    return _check(
        "review_queue_ordering",
        "needs_review" if errors else "passed",
        "review queue 顺序符合 Phase 11 urgency-first 规则。" if not errors else "review queue 排序可能回归。",
        None if not errors else "重新生成 review queue，检查 REVIEW_QUEUE_GROUPS 排序。",
        [path],
        errors,
    )


def _blocked_partial_aggregation_check(
    run_data: dict[str, Any], queue_items: list[dict[str, Any]], run_path: Path, queue_path: Path
) -> dict[str, Any]:
    run_items = _list_of_mappings(run_data.get("items"))
    blocked = sum(1 for item in run_items if item.get("status") == "blocked")
    partial = sum(1 for item in run_items if item.get("status") == "partial")
    queue_blocked = sum(1 for item in queue_items if item.get("queue_group") == "blocked")
    queue_partial = sum(1 for item in queue_items if item.get("queue_group") == "partial")
    errors: list[str] = []
    if blocked and not queue_blocked:
        errors.append("run ledger 中有 blocked 项，但 review queue 未聚合 blocked 项")
    if partial and not queue_partial:
        errors.append("run ledger 中有 partial 项，但 review queue 未聚合 partial 项")
    return _check(
        "blocked_partial_aggregation",
        "needs_review" if errors else "passed",
        "blocked/partial 项已进入监管队列或当前无此类项。" if not errors else "blocked/partial 聚合需要修复。",
        None if not errors else "重新生成 review queue 并检查 run ledger 到 queue 的映射。",
        [run_path, queue_path],
        errors,
    )


def _priority_confidence_queue_check(queue_items: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    errors: list[str] = []
    for item in queue_items:
        flags = set(item.get("risk_flags") or [])
        group = item.get("queue_group")
        if "low_confidence" in flags and group not in {"low_confidence", "blocked", "partial", "needs_review"}:
            errors.append(f"{item.get('queue_item_id')} low_confidence 未进入监管优先组")
        if "high_priority" in flags and group not in {"high_priority", "blocked", "partial", "needs_review", "low_confidence"}:
            errors.append(f"{item.get('queue_item_id')} high_priority 未进入监管优先组")
    return _check(
        "priority_confidence_queue_admission",
        "needs_review" if errors else "passed",
        "低置信度和高优先级项已按监管规则进入队列。" if not errors else "低置信度或高优先级队列准入异常。",
        None if not errors else "检查 scoring 信号和 review queue 分组逻辑。",
        [path],
        errors,
    )


def _completed_item_non_rerun_check(run_data: dict[str, Any], path: Path) -> dict[str, Any]:
    items = _list_of_mappings(run_data.get("items"))
    skipped_completed = [item for item in items if item.get("status") == "skipped_completed"]
    if skipped_completed:
        message = "检测到 completed-item non-rerun 证据：已完成项在 resume 中被跳过。"
    elif items:
        message = "当前 run ledger 未显示重复运行已完成项。"
    else:
        message = "缺少 run items，无法确认 completed-item non-rerun。"
    return _check(
        "completed_item_non_rerun",
        "needs_review" if not items else "passed",
        message,
        "运行一次包含已完成项的 resume 可进一步验证该语义。" if not items else None,
        [path],
    )


def _campaign_policy_check(run_data: dict[str, Any], path: Path) -> dict[str, Any]:
    errors: list[str] = []
    if run_data:
        pipeline = run_data.get("pipeline") or {}
        if not isinstance(pipeline, dict) or pipeline.get("strategy") != "stage_queue_limited_sync":
            errors.append("pipeline.strategy 需要保持 stage_queue_limited_sync")
        if "automation_policy_zh" not in run_data:
            errors.append("缺少 automation_policy_zh")
        if run_data.get("run_status") == "paused" and not run_data.get("pause_reason_zh"):
            errors.append("paused run 必须记录 pause_reason_zh")
    return _check(
        "campaign_error_policy_semantics",
        "needs_review" if errors else "passed",
        "campaign run 保留自动化边界、限流策略和暂停原因语义。" if not errors else "campaign error-policy 语义需要复核。",
        None if not errors else "修复 run ledger 中的 pipeline、automation_policy_zh 或 pause_reason_zh。",
        [path],
        errors,
    )


def _overall_status(checks: list[dict[str, Any]], claim_refs: list[dict[str, Any]]) -> str:
    if any(check.get("status") == "blocked" for check in checks):
        return "blocked"
    if any(check.get("status") == "needs_review" for check in checks):
        return "needs_review"
    if any(ref.get("status") == "needs_review" for ref in claim_refs):
        return "needs_review"
    return "passed"


def _check(
    check_id: str,
    status: str,
    message_zh: str,
    repair_hint_zh: str | None,
    evidence_paths: list[Path] | None = None,
    details: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": status,
        "message_zh": message_zh,
        "repair_hint_zh": repair_hint_zh,
        "details_zh": details or [],
        "evidence_links": [str(path) for path in evidence_paths or []],
    }


def _warnings(checks: list[dict[str, Any]], claim_refs: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for check in checks:
        if check.get("status") in {"needs_review", "blocked"}:
            warnings.append(str(check.get("message_zh") or check.get("check_id")))
        warnings.extend(str(item) for item in check.get("details_zh") or [])
    for ref in claim_refs:
        if ref.get("warning_zh"):
            warnings.append(str(ref["warning_zh"]))
    return _unique(warnings)


def _repair_hints(checks: list[dict[str, Any]], claim_refs: list[dict[str, Any]]) -> list[str]:
    hints = [str(check.get("repair_hint_zh")) for check in checks if check.get("repair_hint_zh")]
    hints.extend(str(ref.get("repair_hint_zh")) for ref in claim_refs if ref.get("repair_hint_zh"))
    return _unique(hints)


def _future_interfaces() -> dict[str, Any]:
    return {
        "llm_claim_review": {
            "status": "not_run",
            "note_zh": "预留给后续 LLM 辅助判断 claim 与证据是否匹配；当前不做自动真伪裁决。",
        },
        "citation_graph": {
            "status": "not_run",
            "note_zh": "预留 claim -> source -> page/region -> formal write request 的图结构接口。",
        },
        "advanced_figure_claim_binding": {
            "status": "not_run",
            "note_zh": "预留高级图表智能与 claim 绑定接口，当前不还原曲线或自动生成图表结论。",
        },
    }


def _render_paper_report(record: dict[str, Any], path: Path) -> str:
    lines = [
        f"# Phase 13 写作安全检查: {record['paper_id']}",
        "",
        f"- safety_status: `{record['safety_status']}`",
        f"- 含义: {record['status_meaning_zh']}",
        f"- safety YAML: `{path}`",
        f"- claim_refs: {len(record.get('claim_refs') or [])}",
        "",
        "## 检查结果",
        "",
    ]
    for check in record.get("checks") or []:
        lines.append(f"- `{check.get('check_id')}`: `{check.get('status')}` - {check.get('message_zh')}")
        if check.get("repair_hint_zh"):
            lines.append(f"  - 修复建议: {check.get('repair_hint_zh')}")
    lines.extend(["", "## Claim 引用链", ""])
    for ref in record.get("claim_refs") or []:
        warning = f"；警告: {ref.get('warning_zh')}" if ref.get("warning_zh") else ""
        lines.append(
            f"- `{ref.get('claim_id')}` `{ref.get('status')}` page={ref.get('page')} "
            f"section={ref.get('section')} chunk={ref.get('source_chunk_id')}{warning}"
        )
    lines.extend(["", "## Formal 边界", "", record["formal_record_policy_zh"], ""])
    return "\n".join(lines)


def _render_campaign_report(record: dict[str, Any], path: Path) -> str:
    lines = [
        f"# Phase 13 Campaign 安全检查: {record['campaign_id']}",
        "",
        f"- safety_status: `{record['safety_status']}`",
        f"- 含义: {record['status_meaning_zh']}",
        f"- safety YAML: `{path}`",
        "",
        "## 监测场景",
        "",
    ]
    for item in record.get("monitored_failure_scenarios") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", "## 检查结果", ""])
    for check in record.get("checks") or []:
        lines.append(f"- `{check.get('check_id')}`: `{check.get('status')}` - {check.get('message_zh')}")
        if check.get("repair_hint_zh"):
            lines.append(f"  - 修复建议: {check.get('repair_hint_zh')}")
    lines.extend(["", "## Formal 边界", "", record["formal_record_policy_zh"], ""])
    return "\n".join(lines)


def _status_meaning(status: str) -> str:
    return {
        "passed": "当前安全检查未发现确定性风险，但不等于 formal approval。",
        "needs_review": "存在需要用户监管或补证据的项目。",
        "blocked": "缺少必要输入或结构无效，不能继续作为可靠写作依据。",
        "missing": "尚未生成安全检查记录。",
    }.get(status, "未知状态。")


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise SafetyError(f"无法读取 YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise SafetyError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SafetyError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _require_paper_id(paper_id: str) -> None:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise SafetyError(f"paper_id 必须匹配 P###: {paper_id}")


def _require_campaign_id(campaign_id: str) -> None:
    if not re.match(r"^C\d{3}$", str(campaign_id)):
        raise SafetyError(f"campaign_id 必须匹配 C###: {campaign_id}")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
