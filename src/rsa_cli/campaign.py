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
METADATA_REQUEST_STATUSES = {
    "auto_triaged",
    "needs_review",
    "accepted",
    "rejected",
    "merged",
}
FORMAL_WRITE_REQUEST_STATUSES = {
    "pending_human_approval",
    "approved_for_write",
    "rejected",
    "applied",
}
REVIEW_DECISIONS = {
    "accepted",
    "deferred",
    "rejected",
    "needs_followup",
}
CAMPAIGN_RUN_STATUSES = {
    "planned",
    "running",
    "paused",
    "completed",
    "partial",
    "blocked",
    "failed",
    "dry_run",
}
CAMPAIGN_ITEM_RUN_STATUSES = {
    "pending",
    "running",
    "completed",
    "partial",
    "failed",
    "blocked",
    "skipped",
    "skipped_completed",
    "skipped_by_filter",
    "metadata_intake_created",
    "formal_request_pending",
}
REVIEW_QUEUE_GROUPS = [
    "blocked",
    "partial",
    "needs_review",
    "auto_triaged",
    "low_confidence",
    "high_priority",
    "completed_staging",
    "skipped",
]
DEFAULT_CONCURRENCY = {
    "acquisition": 2,
    "reading_draft": 2,
    "visual_extraction": 1,
    "scoring": 2,
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


@dataclass(frozen=True)
class CampaignRunResult:
    campaign_id: str
    path: Path
    review_queue_path: Path
    batch_report_path: Path
    metadata_requests_path: Path
    processed_count: int
    queued_count: int
    linked_count: int
    blocked_count: int
    formal_request_count: int
    dry_run: bool
    campaign_status: str


@dataclass(frozen=True)
class CampaignReviewQueueResult:
    campaign_id: str
    path: Path
    total_count: int
    blocked_count: int
    partial_count: int
    needs_review_count: int
    auto_triaged_count: int
    high_priority_count: int
    low_confidence_count: int


@dataclass(frozen=True)
class CampaignReviewDecisionResult:
    campaign_id: str
    path: Path
    item_id: str
    decision: str
    history_count: int


def campaign_path(config: ProjectConfig, campaign_id: str) -> Path:
    if not CAMPAIGN_ID_PATTERN.match(campaign_id):
        raise CampaignError(f"campaign_id 必须匹配 C###: {campaign_id}")
    return config.campaigns_root / f"{campaign_id}.yaml"


def campaign_run_path(config: ProjectConfig, campaign_id: str) -> Path:
    if not CAMPAIGN_ID_PATTERN.match(campaign_id):
        raise CampaignError(f"campaign_id 必须匹配 C###: {campaign_id}")
    return config.campaigns_root / f"{campaign_id}_run.yaml"


def campaign_metadata_requests_path(config: ProjectConfig, campaign_id: str) -> Path:
    if not CAMPAIGN_ID_PATTERN.match(campaign_id):
        raise CampaignError(f"campaign_id 必须匹配 C###: {campaign_id}")
    return config.campaigns_root / f"{campaign_id}_metadata_requests.yaml"


def campaign_review_queue_path(config: ProjectConfig, campaign_id: str) -> Path:
    if not CAMPAIGN_ID_PATTERN.match(campaign_id):
        raise CampaignError(f"campaign_id 必须匹配 C###: {campaign_id}")
    return config.campaigns_root / f"{campaign_id}_review_queue.yaml"


def campaign_batch_report_path(config: ProjectConfig, campaign_id: str) -> Path:
    if not CAMPAIGN_ID_PATTERN.match(campaign_id):
        raise CampaignError(f"campaign_id 必须匹配 C###: {campaign_id}")
    return config.campaigns_root / f"{campaign_id}_batch_report.md"


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


def resolve_campaign_concurrency(
    config: ProjectConfig,
    *,
    max_acquisition: int | None = None,
    max_reading_draft: int | None = None,
    max_visual: int | None = None,
    max_scoring: int | None = None,
) -> dict[str, int]:
    configured = {**DEFAULT_CONCURRENCY, **config.campaign_concurrency}
    overrides = {
        "acquisition": max_acquisition,
        "reading_draft": max_reading_draft,
        "visual_extraction": max_visual,
        "scoring": max_scoring,
    }
    for key, value in overrides.items():
        if value is None:
            continue
        if value <= 0:
            raise CampaignError(f"{key} 并发数必须为正整数。")
        configured[key] = int(value)
    return configured


def ensure_metadata_intake_requests(
    config: ProjectConfig,
    campaign_id: str,
    *,
    item_ids: list[str] | None = None,
) -> dict[str, Any]:
    campaign = load_campaign(config, campaign_id)
    selected_ids = set(item_ids or [])
    data = _load_or_create_metadata_requests(config, campaign_id)
    requests = data.setdefault("requests", [])
    if not isinstance(requests, list):
        raise CampaignError("metadata requests 的 requests 必须是 list。")
    existing = {
        str(request.get("queued_item_id")): request
        for request in requests
        if isinstance(request, dict) and request.get("queued_item_id")
    }

    for item in _campaign_items(campaign):
        item_id = str(item.get("item_id") or "")
        if selected_ids and item_id not in selected_ids:
            continue
        if item.get("status") != "queued":
            continue
        if item_id in existing:
            continue
        request = _metadata_request_from_item(
            campaign_id,
            item,
            request_id=_next_prefixed_id(requests, "MR"),
        )
        requests.append(request)
        existing[item_id] = request

    data["updated_at"] = _now()
    _write_yaml(campaign_metadata_requests_path(config, campaign_id), data)
    return data


def generate_formal_write_requests(config: ProjectConfig, campaign_id: str) -> dict[str, Any]:
    data = _load_or_create_metadata_requests(config, campaign_id)
    requests = data.setdefault("requests", [])
    formal_requests = data.setdefault("formal_write_requests", [])
    if not isinstance(requests, list) or not isinstance(formal_requests, list):
        raise CampaignError("metadata request 文件中的 requests/formal_write_requests 必须是 list。")
    existing_sources = {
        str(request.get("source_metadata_request_id"))
        for request in formal_requests
        if isinstance(request, dict)
    }
    for request in requests:
        if not isinstance(request, dict):
            continue
        if request.get("status") != "accepted":
            continue
        request_id = str(request.get("request_id") or "")
        if request_id in existing_sources:
            continue
        formal_requests.append(
            {
                "formal_write_request_id": _next_prefixed_id(formal_requests, "FWR"),
                "request_type": "create_metadata",
                "status": "pending_human_approval",
                "source_campaign_id": campaign_id,
                "source_metadata_request_id": request_id,
                "queued_item_id": request.get("queued_item_id"),
                "candidate_metadata": request.get("candidate_metadata") or {},
                "formal_write_allowed": False,
                "human_confirmed": False,
                "reason_zh": (
                    "用户已在 review queue 中接受该候选，但正式 metadata 写入仍需要人工确认命令。"
                ),
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
    data["updated_at"] = _now()
    _write_yaml(campaign_metadata_requests_path(config, campaign_id), data)
    return data


def validate_campaign_run(config: ProjectConfig, campaign_id: str) -> list[str]:
    errors = validate_campaign(config, campaign_id)
    run_path = campaign_run_path(config, campaign_id)
    if not run_path.exists():
        return errors + [f"campaign run 文件不存在: {run_path}"]
    try:
        run_data = _read_yaml_mapping(run_path)
    except CampaignError as exc:
        return errors + [str(exc)]
    if run_data.get("campaign_id") != campaign_id:
        errors.append("run 文件中的 campaign_id 必须与文件名一致。")
    if run_data.get("run_status") not in CAMPAIGN_RUN_STATUSES:
        errors.append(f"run_status 不支持: {run_data.get('run_status')}")
    items = run_data.get("items")
    if not isinstance(items, list):
        errors.append("run.items 必须是 list。")
    else:
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"run.items 第 {index} 项必须是 mapping。")
                continue
            if item.get("status") not in CAMPAIGN_ITEM_RUN_STATUSES:
                errors.append(f"run.items 第 {index} 项 status 不支持: {item.get('status')}")
            if _is_blank(item.get("message_zh")):
                errors.append(f"run.items 第 {index} 项必须有 message_zh。")
    request_path = campaign_metadata_requests_path(config, campaign_id)
    if request_path.exists():
        request_data = _read_yaml_mapping(request_path)
        for request in request_data.get("requests", []) or []:
            if not isinstance(request, dict):
                errors.append("metadata request 必须是 mapping。")
                continue
            if request.get("status") not in METADATA_REQUEST_STATUSES:
                errors.append(f"metadata request status 不支持: {request.get('status')}")
            if request.get("formal_write_allowed") is not False:
                errors.append("metadata request 不允许直接写 formal metadata。")
        for request in request_data.get("formal_write_requests", []) or []:
            if not isinstance(request, dict):
                errors.append("formal_write_request 必须是 mapping。")
                continue
            if request.get("status") not in FORMAL_WRITE_REQUEST_STATUSES:
                errors.append(f"formal_write_request status 不支持: {request.get('status')}")
            if request.get("status") in {"pending_human_approval", "approved_for_write"} and request.get(
                "human_confirmed"
            ) is True:
                continue
            if request.get("status") == "pending_human_approval" and request.get("formal_write_allowed"):
                errors.append("pending_human_approval 不允许 formal_write_allowed=true。")
    return errors


def run_campaign(
    config: ProjectConfig,
    campaign_id: str,
    *,
    dry_run: bool = False,
    item_ids: list[str] | None = None,
    status_filter: list[str] | None = None,
    max_acquisition: int | None = None,
    max_reading_draft: int | None = None,
    max_visual: int | None = None,
    max_scoring: int | None = None,
) -> CampaignRunResult:
    campaign = load_campaign(config, campaign_id)
    concurrency = resolve_campaign_concurrency(
        config,
        max_acquisition=max_acquisition,
        max_reading_draft=max_reading_draft,
        max_visual=max_visual,
        max_scoring=max_scoring,
    )
    run_path = campaign_run_path(config, campaign_id)
    previous = _read_yaml_mapping(run_path) if run_path.exists() else {}
    existing_ledgers = {
        str(item.get("source_campaign_item_id")): item
        for item in previous.get("items", []) or []
        if isinstance(item, dict) and item.get("source_campaign_item_id")
    }
    selected_ids = set(item_ids or [])
    selected_statuses = set(status_filter or [])
    run_items: list[dict[str, Any]] = []
    processed = 0
    linked = 0
    queued = 0
    blocked = 0

    run_data: dict[str, Any] = {
        "campaign_id": campaign_id,
        "run_status": "dry_run" if dry_run else "running",
        "dry_run": dry_run,
        "started_at": previous.get("started_at") or _now(),
        "updated_at": _now(),
        "user_language": "zh",
        "automation_policy_zh": (
            "Campaign 会自动推进 acquisition -> reading draft -> visual extraction -> scoring -> review packet。"
            "正式记录写入必须经过 formal write gate 和人工确认。"
        ),
        "pipeline": {
            "strategy": "stage_queue_limited_sync",
            "strategy_zh": "阶段队列限流；多篇可进入同一流水线，单篇内部按依赖顺序执行。",
            "stage_order": [
                "acquisition",
                "reading_draft",
                "visual_extraction",
                "scoring",
                "review_packet",
            ],
            "worker_limits": concurrency,
            "future_background_worker_phase": "Phase 14",
        },
        "filters": {
            "item_ids": sorted(selected_ids),
            "status_filter": sorted(selected_statuses),
        },
        "items": run_items,
    }

    for item in _campaign_items(campaign):
        item_id = str(item.get("item_id") or "")
        item_status = str(item.get("status") or "")
        if selected_ids and item_id not in selected_ids:
            run_items.append(_run_item_ledger(item, "skipped_by_filter", "该候选不在本次 item 过滤范围内。"))
            continue
        if selected_statuses and item_status not in selected_statuses:
            run_items.append(_run_item_ledger(item, "skipped_by_filter", "该候选不在本次 status 过滤范围内。"))
            continue
        previous_ledger = existing_ledgers.get(item_id)
        if _is_completed_run_item(previous_ledger) and not dry_run:
            ledger = dict(previous_ledger)
            ledger["status"] = "skipped_completed"
            ledger["message_zh"] = "该候选已有完成态 run ledger，本次 resume 不重复执行。"
            ledger["updated_at"] = _now()
            run_items.append(ledger)
            continue

        if item_status == "linked" and item.get("paper_id"):
            linked += 1
            if dry_run:
                run_items.append(_run_item_ledger(item, "pending", "dry-run：将执行单篇 workflow，但本次未实际运行。"))
            else:
                run_items.append(_run_linked_campaign_item(config, campaign_id, item))
            processed += 1
            continue

        if item_status == "queued":
            queued += 1
            if not dry_run:
                ensure_metadata_intake_requests(config, campaign_id, item_ids=[item_id])
            run_items.append(
                _run_item_ledger(
                    item,
                    "metadata_intake_created" if not dry_run else "pending",
                    "候选尚未进入正式 metadata；已生成或计划生成 metadata intake request。",
                )
            )
            processed += 1
            continue

        if item_status == "blocked":
            blocked += 1
            run_items.append(_run_item_ledger(item, "blocked", item.get("reason_zh") or "该候选处于 blocked 状态。"))
            continue

        run_items.append(
            _run_item_ledger(
                item,
                "skipped",
                f"该候选状态为 {item_status}，本次 campaign run 不自动处理。",
            )
        )

    if dry_run:
        request_data = _load_or_create_metadata_requests(config, campaign_id)
        _write_yaml(campaign_metadata_requests_path(config, campaign_id), request_data)
    else:
        request_data = generate_formal_write_requests(config, campaign_id)
    formal_request_count = sum(
        1
        for request in request_data.get("formal_write_requests", []) or []
        if isinstance(request, dict) and request.get("status") == "pending_human_approval"
    )
    if dry_run:
        run_status = "dry_run"
    elif formal_request_count:
        run_status = "paused"
        run_data["pause_reason_zh"] = "存在待人工确认的 formal_write_request，自动流程在正式写入前暂停。"
    elif any(item.get("status") in {"failed", "partial", "blocked"} for item in run_items):
        run_status = "partial"
    else:
        run_status = "completed"
    run_data["run_status"] = run_status
    run_data["completed_at"] = _now()
    run_data["summary"] = {
        "processed_count": processed,
        "queued_count": queued,
        "linked_count": linked,
        "blocked_count": blocked,
        "formal_request_count": formal_request_count,
    }
    _write_yaml(run_path, run_data)
    _update_campaign_run_index(config, campaign_id, run_data)
    queue = generate_review_queue(config, campaign_id)
    report_path = write_batch_report(config, campaign_id)
    return CampaignRunResult(
        campaign_id=campaign_id,
        path=run_path,
        review_queue_path=queue.path,
        batch_report_path=report_path,
        metadata_requests_path=campaign_metadata_requests_path(config, campaign_id),
        processed_count=processed,
        queued_count=queued,
        linked_count=linked,
        blocked_count=blocked,
        formal_request_count=formal_request_count,
        dry_run=dry_run,
        campaign_status=run_status,
    )


def pause_campaign_run(
    config: ProjectConfig,
    campaign_id: str,
    *,
    reason_zh: str | None = None,
) -> CampaignRunResult:
    run_path = campaign_run_path(config, campaign_id)
    if not run_path.exists():
        raise CampaignError(f"campaign run 文件不存在，无法暂停: {run_path}")
    run_data = _read_yaml_mapping(run_path)
    run_data["run_status"] = "paused"
    run_data["paused_at"] = _now()
    run_data["pause_reason_zh"] = reason_zh or "用户手动暂停 campaign run。"
    run_data["updated_at"] = _now()
    _write_yaml(run_path, run_data)
    queue = generate_review_queue(config, campaign_id)
    report_path = write_batch_report(config, campaign_id)
    summary = run_data.get("summary", {}) if isinstance(run_data.get("summary"), dict) else {}
    return CampaignRunResult(
        campaign_id=campaign_id,
        path=run_path,
        review_queue_path=queue.path,
        batch_report_path=report_path,
        metadata_requests_path=campaign_metadata_requests_path(config, campaign_id),
        processed_count=int(summary.get("processed_count") or 0),
        queued_count=int(summary.get("queued_count") or 0),
        linked_count=int(summary.get("linked_count") or 0),
        blocked_count=int(summary.get("blocked_count") or 0),
        formal_request_count=int(summary.get("formal_request_count") or 0),
        dry_run=bool(run_data.get("dry_run")),
        campaign_status="paused",
    )


def resume_campaign_run(
    config: ProjectConfig,
    campaign_id: str,
    *,
    item_ids: list[str] | None = None,
    status_filter: list[str] | None = None,
) -> CampaignRunResult:
    return run_campaign(
        config,
        campaign_id,
        dry_run=False,
        item_ids=item_ids,
        status_filter=status_filter,
    )


def generate_review_queue(config: ProjectConfig, campaign_id: str) -> CampaignReviewQueueResult:
    campaign = load_campaign(config, campaign_id)
    run_path = campaign_run_path(config, campaign_id)
    run_data = _read_yaml_mapping(run_path) if run_path.exists() else {}
    request_data = _load_or_create_metadata_requests(config, campaign_id)
    queue_items: list[dict[str, Any]] = []

    for ledger in run_data.get("items", []) or []:
        if not isinstance(ledger, dict):
            continue
        if ledger.get("status") == "metadata_intake_created":
            continue
        queue_items.append(_review_item_from_run_ledger(config, campaign_id, campaign, ledger))

    for request in request_data.get("requests", []) or []:
        if not isinstance(request, dict):
            continue
        if request.get("status") not in {"auto_triaged", "needs_review"}:
            continue
        queue_items.append(_review_item_from_metadata_request(config, campaign_id, request))

    for request in request_data.get("formal_write_requests", []) or []:
        if not isinstance(request, dict):
            continue
        if request.get("status") != "pending_human_approval":
            continue
        queue_items.append(_review_item_from_formal_request(config, campaign_id, request))

    queue_items.sort(key=_review_queue_sort_key)
    for index, item in enumerate(queue_items, start=1):
        item["queue_item_id"] = f"QI{index:03d}"

    data = {
        "campaign_id": campaign_id,
        "generated_at": _now(),
        "user_language": "zh",
        "review_decision_enum": sorted(REVIEW_DECISIONS),
        "review_decision_extension_zh": (
            "后续可以新增枚举，但必须保留中文解释，并避免与 formal approval 混淆。"
        ),
        "formal_write_policy_zh": "该队列只用于监管和初审；正式写入必须走 formal write gate。",
        "queue_items": queue_items,
    }
    path = campaign_review_queue_path(config, campaign_id)
    _write_yaml(path, data)
    return CampaignReviewQueueResult(
        campaign_id=campaign_id,
        path=path,
        total_count=len(queue_items),
        blocked_count=sum(1 for item in queue_items if item.get("queue_group") == "blocked"),
        partial_count=sum(1 for item in queue_items if item.get("queue_group") == "partial"),
        needs_review_count=sum(1 for item in queue_items if item.get("queue_group") == "needs_review"),
        auto_triaged_count=sum(1 for item in queue_items if item.get("queue_group") == "auto_triaged"),
        high_priority_count=sum(1 for item in queue_items if "high_priority" in (item.get("risk_flags") or [])),
        low_confidence_count=sum(1 for item in queue_items if "low_confidence" in (item.get("risk_flags") or [])),
    )


def review_campaign_queue_item(
    config: ProjectConfig,
    campaign_id: str,
    *,
    queue_item_id: str,
    decision: str,
    reviewer: str,
    reason_zh: str | None = None,
) -> CampaignReviewDecisionResult:
    if decision not in REVIEW_DECISIONS:
        raise CampaignError(f"review decision 不支持: {decision}")
    if _is_blank(reviewer):
        raise CampaignError("reviewer 不能为空。")
    path = campaign_review_queue_path(config, campaign_id)
    if not path.exists():
        generate_review_queue(config, campaign_id)
    data = _read_yaml_mapping(path)
    items = data.get("queue_items")
    if not isinstance(items, list):
        raise CampaignError("review queue 的 queue_items 必须是 list。")
    target: dict[str, Any] | None = None
    for item in items:
        if isinstance(item, dict) and item.get("queue_item_id") == queue_item_id:
            target = item
            break
    if target is None:
        raise CampaignError(f"review queue item 不存在: {queue_item_id}")
    history = target.setdefault("review_history", [])
    if not isinstance(history, list):
        raise CampaignError("review_history 必须是 list。")
    history.append(
        {
            "decision": decision,
            "reviewer": reviewer,
            "reason_zh": reason_zh,
            "reviewed_at": _now(),
        }
    )
    target["review_decision"] = decision
    target["reviewer"] = reviewer
    target["review_reason_zh"] = reason_zh
    target["reviewed_at"] = _now()
    data["updated_at"] = _now()
    _write_yaml(path, data)
    return CampaignReviewDecisionResult(
        campaign_id=campaign_id,
        path=path,
        item_id=queue_item_id,
        decision=decision,
        history_count=len(history),
    )


def write_batch_report(config: ProjectConfig, campaign_id: str) -> Path:
    run_path = campaign_run_path(config, campaign_id)
    run_data = _read_yaml_mapping(run_path) if run_path.exists() else {}
    queue_path = campaign_review_queue_path(config, campaign_id)
    queue_data = _read_yaml_mapping(queue_path) if queue_path.exists() else {"queue_items": []}
    queue_items = queue_data.get("queue_items") if isinstance(queue_data.get("queue_items"), list) else []
    summary = run_data.get("summary", {}) if isinstance(run_data.get("summary"), dict) else {}
    lines = [
        f"# Campaign {campaign_id} 批量报告",
        "",
        "## 自动化状态",
        "",
        f"- run_status: `{run_data.get('run_status', 'not_run')}`",
        f"- processed_count: {summary.get('processed_count', 0)}",
        f"- linked_count: {summary.get('linked_count', 0)}",
        f"- queued_count: {summary.get('queued_count', 0)}",
        f"- blocked_count: {summary.get('blocked_count', 0)}",
        f"- formal_request_count: {summary.get('formal_request_count', 0)}",
        "",
        "## 监管队列",
        "",
        f"- 队列文件: `{queue_path}`",
        f"- 队列项总数: {len(queue_items)}",
    ]
    for group in REVIEW_QUEUE_GROUPS:
        count = sum(1 for item in queue_items if isinstance(item, dict) and item.get("queue_group") == group)
        if count:
            lines.append(f"- {group}: {count}")
    lines.extend(
        [
            "",
            "## 人工审批边界",
            "",
            "- 文献获取、阅读草稿、视觉证据候选、AI 评分和 review packet 可以自动生成。",
            "- 写入 formal metadata、literature_map 或正式研究记录前必须人工确认。",
            "- `accepted` 只表示用户处理或认可该队列项进入后续流程，不等于正式批准写入。",
            "",
            "## 关键文件",
            "",
            f"- campaign: `{campaign_path(config, campaign_id)}`",
            f"- run ledger: `{run_path}`",
            f"- metadata requests: `{campaign_metadata_requests_path(config, campaign_id)}`",
            f"- review queue: `{queue_path}`",
        ]
    )
    path = campaign_batch_report_path(config, campaign_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


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


def _campaign_items(campaign: dict[str, Any]) -> list[dict[str, Any]]:
    items = campaign.get("items") or []
    if not isinstance(items, list):
        raise CampaignError("items 必须是 YAML list。")
    return [item for item in items if isinstance(item, dict)]


def _load_or_create_metadata_requests(config: ProjectConfig, campaign_id: str) -> dict[str, Any]:
    path = campaign_metadata_requests_path(config, campaign_id)
    if path.exists():
        data = _read_yaml_mapping(path)
    else:
        data = {
            "campaign_id": campaign_id,
            "schema_version": "phase11-metadata-intake-v1",
            "user_language": "zh",
            "storage_note_zh": (
                "v2 当前把 metadata request 暂存在 campaign 文件旁；每条 request 都是独立对象，"
                "后续可平滑迁移到 metadata_requests/*.yaml。"
            ),
            "requests": [],
            "formal_write_requests": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
    data.setdefault("requests", [])
    data.setdefault("formal_write_requests", [])
    return data


def _next_prefixed_id(items: list[Any], prefix: str) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}(?P<number>\d{{3}})$")
    highest = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in ("request_id", "formal_write_request_id", "queue_item_id"):
            match = pattern.match(str(item.get(key) or ""))
            if match:
                highest = max(highest, int(match.group("number")))
    return f"{prefix}{highest + 1:03d}"


def _metadata_request_from_item(
    campaign_id: str,
    item: dict[str, Any],
    *,
    request_id: str,
) -> dict[str, Any]:
    item_id = str(item.get("item_id") or "")
    return {
        "request_id": request_id,
        "source_campaign_id": campaign_id,
        "queued_item_id": item_id,
        "status": "auto_triaged",
        "triage_confidence": _metadata_triage_confidence(item),
        "recommended_action": _metadata_recommended_action(item),
        "triage_reason_zh": _metadata_triage_reason(item),
        "formal_write_allowed": False,
        "candidate_metadata": _candidate_metadata_from_item(item),
        "field_explanations_zh": {
            "request_id": "metadata intake request 的稳定编号。",
            "status": "机器初审状态；auto_triaged 不等于人工批准。",
            "candidate_metadata": "由 campaign 候选整理出的候选元数据，不是正式 metadata。",
            "formal_write_allowed": "是否允许直接正式写入；v2 默认必须为 false。",
        },
        "source_trace": {
            "campaign_id": campaign_id,
            "campaign_item_id": item_id,
            "source_candidate_id": item.get("source_candidate_id"),
            "candidate_key": item.get("candidate_key"),
        },
        "created_at": _now(),
        "updated_at": _now(),
    }


def _candidate_metadata_from_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title"),
        "doi": item.get("doi"),
        "official_url": item.get("official_url"),
        "year": item.get("year"),
        "first_author": item.get("first_author"),
        "topic_profile": item.get("topic_profile"),
        "priority_question": item.get("priority_question"),
        "note_zh": item.get("reason_zh"),
    }


def _metadata_triage_confidence(item: dict[str, Any]) -> str:
    if item.get("doi") and item.get("title") and item.get("year"):
        return "high"
    if item.get("doi") or (item.get("title") and item.get("year")):
        return "medium"
    return "low"


def _metadata_recommended_action(item: dict[str, Any]) -> str:
    confidence = _metadata_triage_confidence(item)
    if confidence == "low":
        return "insufficient_metadata"
    if item.get("doi"):
        return "create_new_metadata"
    return "possible_duplicate"


def _metadata_triage_reason(item: dict[str, Any]) -> str:
    confidence = _metadata_triage_confidence(item)
    if confidence == "high":
        return "标题、DOI 和年份较完整，机器已完成初步分诊，建议进入人工监管队列。"
    if confidence == "medium":
        return "候选身份信息部分完整，机器已完成初步分诊，但建议人工核对重复项和来源。"
    return "候选缺少稳定身份信息，建议补充标题、DOI、年份或来源后再处理。"


def _run_item_ledger(
    item: dict[str, Any],
    status: str,
    message_zh: str,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ledger = {
        "source_campaign_item_id": item.get("item_id"),
        "paper_id": item.get("paper_id"),
        "title": item.get("title"),
        "campaign_item_status": item.get("status"),
        "status": status,
        "message_zh": message_zh,
        "updated_at": _now(),
    }
    if extra:
        ledger.update(extra)
    return ledger


def _run_linked_campaign_item(
    config: ProjectConfig,
    campaign_id: str,
    item: dict[str, Any],
) -> dict[str, Any]:
    paper_id = str(item.get("paper_id") or "")
    try:
        from .workflow import run_workflow

        result = run_workflow(
            config,
            paper_id,
            campaign_id=campaign_id,
            campaign_item_id=str(item.get("item_id") or ""),
        )
    except Exception as exc:  # campaign 必须 continue_on_error，不能让单篇失败拖垮整批。
        return _run_item_ledger(
            item,
            "failed",
            f"单篇 workflow 运行失败，已记录并继续处理其他候选: {exc}",
            extra={"error_zh": str(exc), "continue_on_error": True},
        )
    if result.workflow_status in {"completed", "needs_review"}:
        status = "completed"
    elif result.workflow_status == "partial":
        status = "partial"
    elif result.workflow_status == "blocked":
        status = "blocked"
    else:
        status = "failed"
    return _run_item_ledger(
        item,
        status,
        f"单篇 workflow 已运行，状态为 {result.workflow_status}。",
        extra={
            "workflow_run_id": result.run_id,
            "workflow_status": result.workflow_status,
            "workflow_current_step": result.current_step,
            "workflow_run_path": str(result.run_path),
            "workflow_report_path": str(result.report_path),
        },
    )


def _is_completed_run_item(item: dict[str, Any] | None) -> bool:
    return bool(item and item.get("status") in {"completed", "metadata_intake_created", "formal_request_pending"})


def _update_campaign_run_index(
    config: ProjectConfig,
    campaign_id: str,
    run_data: dict[str, Any],
) -> None:
    data = load_campaign(config, campaign_id)
    data["last_run_status"] = run_data.get("run_status")
    data["last_run_at"] = run_data.get("completed_at") or run_data.get("updated_at")
    data["last_run_file"] = str(campaign_run_path(config, campaign_id))
    data["last_review_queue_file"] = str(campaign_review_queue_path(config, campaign_id))
    data["last_batch_report_file"] = str(campaign_batch_report_path(config, campaign_id))
    if run_data.get("run_status") == "paused":
        data["status"] = "paused"
    elif run_data.get("run_status") == "completed":
        data["status"] = "completed"
    data["updated_at"] = _now()
    _write_yaml(campaign_path(config, campaign_id), data)


def _review_item_from_run_ledger(
    config: ProjectConfig,
    campaign_id: str,
    campaign: dict[str, Any],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    paper_id = ledger.get("paper_id")
    score = _score_signal(config, str(paper_id)) if paper_id else {}
    queue_group, risk_flags = _queue_group_from_run_status(str(ledger.get("status") or ""), score)
    return {
        "queue_group": queue_group,
        "source_type": "campaign_run_item",
        "source_campaign_id": campaign_id,
        "source_campaign_item_id": ledger.get("source_campaign_item_id"),
        "paper_id": paper_id,
        "title": ledger.get("title") or _campaign_item_title(campaign, str(ledger.get("source_campaign_item_id") or "")),
        "status": ledger.get("status"),
        "message_zh": ledger.get("message_zh"),
        "risk_flags": risk_flags,
        "ai_read_priority_score_10": score.get("ai_read_priority_score_10"),
        "score_confidence": score.get("score_confidence"),
        "ai_review_decision": score.get("ai_review_decision"),
        "artifact_links": _artifact_links(
            {
                "campaign": campaign_path(config, campaign_id),
                "run_ledger": campaign_run_path(config, campaign_id),
                "workflow_report": ledger.get("workflow_report_path"),
                "scoring_record": score.get("path"),
                "review_packet": score.get("review_packet_path"),
            }
        ),
        "review_decision": None,
        "decision_meaning_zh": "accepted/deferred/rejected/needs_followup 只是监管队列决策，不等于 formal approval。",
    }


def _review_item_from_metadata_request(
    config: ProjectConfig,
    campaign_id: str,
    request: dict[str, Any],
) -> dict[str, Any]:
    status = str(request.get("status") or "")
    return {
        "queue_group": "needs_review" if status == "needs_review" else "auto_triaged",
        "source_type": "metadata_request",
        "source_campaign_id": campaign_id,
        "source_campaign_item_id": request.get("queued_item_id"),
        "metadata_request_id": request.get("request_id"),
        "title": (request.get("candidate_metadata") or {}).get("title"),
        "status": status,
        "recommended_action": request.get("recommended_action"),
        "triage_confidence": request.get("triage_confidence"),
        "message_zh": request.get("triage_reason_zh"),
        "risk_flags": ["metadata_intake", "formal_write_blocked"],
        "artifact_links": _artifact_links(
            {
                "campaign": campaign_path(config, campaign_id),
                "metadata_requests": campaign_metadata_requests_path(config, campaign_id),
            }
        ),
        "review_decision": None,
        "decision_meaning_zh": "accepted 只表示候选进入后续 formal request 流程，不会直接创建 P###.yaml。",
    }


def _review_item_from_formal_request(
    config: ProjectConfig,
    campaign_id: str,
    request: dict[str, Any],
) -> dict[str, Any]:
    return {
        "queue_group": "needs_review",
        "source_type": "formal_write_request",
        "source_campaign_id": campaign_id,
        "source_campaign_item_id": request.get("queued_item_id"),
        "formal_write_request_id": request.get("formal_write_request_id"),
        "metadata_request_id": request.get("source_metadata_request_id"),
        "title": (request.get("candidate_metadata") or {}).get("title"),
        "status": request.get("status"),
        "message_zh": request.get("reason_zh"),
        "risk_flags": ["formal_write_pending", "human_confirmation_required"],
        "artifact_links": _artifact_links(
            {
                "metadata_requests": campaign_metadata_requests_path(config, campaign_id),
                "batch_report": campaign_batch_report_path(config, campaign_id),
            }
        ),
        "review_decision": None,
        "decision_meaning_zh": "该项涉及正式写入，必须再走 formal write gate 和人工确认命令。",
    }


def _score_signal(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    try:
        from .scoring import score_status

        status = score_status(config, paper_id)
    except Exception:
        return {}
    if not status.exists:
        return {}
    return {
        "ai_read_priority_score_10": status.ai_read_priority_score_10,
        "score_confidence": status.score_confidence,
        "ai_review_decision": status.ai_review_decision,
        "path": str(status.path),
        "review_packet_path": str(status.review_packet_path),
    }


def _queue_group_from_run_status(status: str, score: dict[str, Any]) -> tuple[str, list[str]]:
    risk_flags: list[str] = []
    if status in {"failed", "blocked"}:
        return "blocked", ["blocked"]
    if status == "partial":
        return "partial", ["partial"]
    if status == "metadata_intake_created":
        return "auto_triaged", ["metadata_intake"]
    if status in {"pending", "skipped", "skipped_completed", "skipped_by_filter"}:
        return "skipped", [status]
    priority = score.get("ai_read_priority_score_10")
    confidence = score.get("score_confidence")
    if isinstance(priority, int) and priority >= 8:
        risk_flags.append("high_priority")
    if confidence in {"low", "unknown"}:
        risk_flags.append("low_confidence")
    if "high_priority" in risk_flags:
        return "high_priority", risk_flags
    if "low_confidence" in risk_flags:
        return "low_confidence", risk_flags
    return "completed_staging", risk_flags


def _review_queue_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    group = str(item.get("queue_group") or "skipped")
    try:
        group_index = REVIEW_QUEUE_GROUPS.index(group)
    except ValueError:
        group_index = len(REVIEW_QUEUE_GROUPS)
    priority = item.get("ai_read_priority_score_10")
    priority_sort = -int(priority) if isinstance(priority, int) else 0
    return group_index, priority_sort, str(item.get("title") or "")


def _artifact_links(paths: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for label, value in paths.items():
        if not value:
            continue
        links.append({"label": str(label), "path": str(value)})
    return links


def _campaign_item_title(campaign: dict[str, Any], item_id: str) -> str | None:
    for item in _campaign_items(campaign):
        if item.get("item_id") == item_id:
            return item.get("title")
    return None


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
