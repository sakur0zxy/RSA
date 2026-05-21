from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN


SCHEMA_VERSION = "phase10-workflow-v1"
STEP_IDS = [
    "acquisition",
    "reading_draft",
    "visual_extraction",
    "scoring",
    "review_packet",
]
WORKFLOW_STATUSES = {
    "pending",
    "running",
    "completed",
    "partial",
    "needs_review",
    "blocked",
    "skipped",
    "stopped",
    "failed",
    "not_run",
}
STEP_STATUSES = WORKFLOW_STATUSES
RUN_ID_PATTERN = re.compile(r"^RUN-\d{3}$")


class WorkflowError(ValueError):
    """Raised when workflow orchestration cannot safely continue."""


@dataclass(frozen=True)
class WorkflowRunResult:
    paper_id: str
    run_id: str
    run_path: Path
    report_path: Path
    workflow_status: str
    current_step: str | None


@dataclass(frozen=True)
class WorkflowStatus:
    path: Path
    paper_id: str
    run_id: str | None
    exists: bool
    workflow_status: str | None
    current_step: str | None
    report_path: Path | None


def workflow_paper_dir(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.workflows_root / paper_id


def workflow_run_path(config: ProjectConfig, paper_id: str, run_id: str) -> Path:
    _require_paper_id(paper_id)
    _require_run_id(run_id)
    return workflow_paper_dir(config, paper_id) / f"{run_id}.yaml"


def workflow_report_path(config: ProjectConfig, paper_id: str, run_id: str) -> Path:
    _require_paper_id(paper_id)
    _require_run_id(run_id)
    return workflow_paper_dir(config, paper_id) / f"{run_id}_report.md"


def next_workflow_run_id(config: ProjectConfig, paper_id: str) -> str:
    _require_paper_id(paper_id)
    highest = 0
    paper_dir = workflow_paper_dir(config, paper_id)
    if paper_dir.exists():
        for path in paper_dir.glob("RUN-*.yaml"):
            match = RUN_ID_PATTERN.match(path.stem)
            if match:
                highest = max(highest, int(path.stem.split("-")[1]))
    return f"RUN-{highest + 1:03d}"


def build_workflow_run_skeleton(
    paper_id: str,
    *,
    run_id: str = "RUN-001",
    campaign_id: str | None = None,
    campaign_item_id: str | None = None,
    skip_steps: list[str] | None = None,
) -> dict[str, Any]:
    _require_paper_id(paper_id)
    _require_run_id(run_id)
    skip_set = set(skip_steps or [])
    unknown = skip_set.difference(STEP_IDS)
    if unknown:
        raise WorkflowError(f"未知 workflow step: {', '.join(sorted(unknown))}")

    now = _now()
    steps = []
    for step_id in STEP_IDS:
        skipped = step_id in skip_set
        steps.append(
            {
                "step_id": step_id,
                "command": _default_command(step_id, paper_id),
                "status": "skipped" if skipped else "pending",
                "started_at": None,
                "finished_at": None,
                "input_summary": {
                    "paper_id": paper_id,
                    "campaign_id": campaign_id,
                    "campaign_item_id": campaign_item_id,
                },
                "artifacts": {},
                "error_zh": None,
                "repair_hint_zh": None,
                "retryable": False,
                "needs_user_action": False,
                "partial_reason_zh": None,
                "blocked_reason_zh": None,
                "skipped_reason_zh": "用户配置或命令参数要求跳过该步骤。"
                if skipped
                else None,
            }
        )

    first_pending = next(
        (step["step_id"] for step in steps if step["status"] == "pending"),
        None,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "paper_id": paper_id,
        "campaign_id": campaign_id,
        "campaign_item_id": campaign_item_id,
        "workflow_status": "pending",
        "created_at": now,
        "updated_at": now,
        "current_step": first_pending,
        "steps": steps,
        "artifacts": {},
        "retry_policy": {
            "max_attempts": 1,
            "retryable_statuses": ["failed"],
            "note_zh": "Phase 10 只做单篇顺序工作流；批量重试和队列限流属于 Phase 11。",
        },
        "future_interfaces": {
            "llm_visual_analysis": {
                "status": "not_run",
                "note_zh": "Phase 10 默认不运行 LLM 图像理解，只保留后续高级图表智能接口。",
            },
            "advanced_analysis": {
                "curve_extraction": {
                    "status": "not_run",
                    "note_zh": "曲线数据自动还原属于后续高级图表智能，不在 Phase 10 执行。",
                },
                "table_structure": {
                    "status": "not_run",
                    "note_zh": "高级表格结构重建属于后续扩展，不在 Phase 10 执行。",
                },
                "multimodal_interpretation": {
                    "status": "not_run",
                    "note_zh": "多模态图像结论生成不会写入正式科研记录。",
                },
            },
        },
        "formal_record_policy_zh": (
            "Workflow run 只是 staging/review 编排记录，不是 formal record；"
            "metadata、literature_map、agent_research_notes 等正式写入仍必须通过 "
            "rsa formal 命令和人工确认。"
        ),
    }


def load_workflow_run(config: ProjectConfig, paper_id: str, run_id: str) -> dict[str, Any]:
    path = workflow_run_path(config, paper_id, run_id)
    if not path.exists():
        raise WorkflowError(f"workflow run 文件不存在: {path}")
    return _read_yaml_mapping(path)


def write_workflow_run(
    config: ProjectConfig, paper_id: str, run_id: str, data: dict[str, Any]
) -> Path:
    _require_paper_id(paper_id)
    _require_run_id(run_id)
    if not isinstance(data, dict):
        raise WorkflowError("workflow run 必须是 YAML mapping。")
    if data.get("paper_id") not in (None, paper_id):
        raise WorkflowError(
            f"workflow run paper_id 必须与文件名一致: expected {paper_id}, got {data.get('paper_id')}"
        )
    if data.get("run_id") not in (None, run_id):
        raise WorkflowError(
            f"workflow run run_id 必须与文件名一致: expected {run_id}, got {data.get('run_id')}"
        )
    data["paper_id"] = paper_id
    data["run_id"] = run_id
    data["updated_at"] = _now()
    path = workflow_run_path(config, paper_id, run_id)
    _write_yaml(path, data)
    return path


def validate_workflow_run(config: ProjectConfig, paper_id: str, run_id: str) -> list[str]:
    try:
        path = workflow_run_path(config, paper_id, run_id)
    except WorkflowError as exc:
        return [str(exc)]
    if not path.exists():
        return [f"workflow run 文件不存在: {path}"]
    try:
        data = _read_yaml_mapping(path)
    except WorkflowError as exc:
        return [str(exc)]
    return validate_workflow_mapping(
        data, expected_paper_id=paper_id, expected_run_id=run_id
    )


def validate_workflow_mapping(
    data: dict[str, Any],
    *,
    expected_paper_id: str | None = None,
    expected_run_id: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["workflow run 必须是 YAML mapping。"]
    for field in [
        "schema_version",
        "run_id",
        "paper_id",
        "workflow_status",
        "created_at",
        "updated_at",
        "steps",
        "artifacts",
        "retry_policy",
        "future_interfaces",
        "formal_record_policy_zh",
    ]:
        if field not in data:
            errors.append(f"workflow run 缺少字段: {field}")
    paper_id = str(data.get("paper_id") or "")
    run_id = str(data.get("run_id") or "")
    if expected_paper_id and paper_id != expected_paper_id:
        errors.append(f"paper_id 必须与文件名一致: expected {expected_paper_id}, got {paper_id}")
    if expected_run_id and run_id != expected_run_id:
        errors.append(f"run_id 必须与文件名一致: expected {expected_run_id}, got {run_id}")
    if not PAPER_ID_PATTERN.match(paper_id):
        errors.append(f"paper_id 必须匹配 P###: {paper_id}")
    if not RUN_ID_PATTERN.match(run_id):
        errors.append(f"run_id 必须匹配 RUN-###: {run_id}")
    if data.get("workflow_status") not in WORKFLOW_STATUSES:
        errors.append(f"workflow_status 不支持: {data.get('workflow_status')}")

    steps = data.get("steps")
    if not isinstance(steps, list):
        errors.append("steps 必须是 list。")
        return errors
    seen: set[str] = set()
    for index, step in enumerate(steps, start=1):
        prefix = f"steps 第 {index} 项"
        if not isinstance(step, dict):
            errors.append(f"{prefix} 必须是 mapping。")
            continue
        for field in [
            "step_id",
            "command",
            "status",
            "started_at",
            "finished_at",
            "input_summary",
            "artifacts",
            "error_zh",
            "repair_hint_zh",
            "retryable",
            "needs_user_action",
            "partial_reason_zh",
            "blocked_reason_zh",
            "skipped_reason_zh",
        ]:
            if field not in step:
                errors.append(f"{prefix} 缺少字段: {field}")
        step_id = str(step.get("step_id") or "")
        status = step.get("status")
        if step_id not in STEP_IDS:
            errors.append(f"{prefix} step_id 不支持: {step_id}")
        elif step_id in seen:
            errors.append(f"{prefix} step_id 重复: {step_id}")
        else:
            seen.add(step_id)
        if status not in STEP_STATUSES:
            errors.append(f"{prefix} status 不支持: {status}")
        if status == "skipped" and not step.get("skipped_reason_zh"):
            errors.append(f"{prefix} skipped 状态必须填写 skipped_reason_zh")
        if status == "blocked" and not step.get("blocked_reason_zh"):
            errors.append(f"{prefix} blocked 状态必须填写 blocked_reason_zh")
        if status == "partial" and not step.get("partial_reason_zh"):
            errors.append(f"{prefix} partial 状态必须填写 partial_reason_zh")
        if not isinstance(step.get("input_summary"), dict):
            errors.append(f"{prefix} input_summary 必须是 mapping。")
        if not isinstance(step.get("artifacts"), dict):
            errors.append(f"{prefix} artifacts 必须是 mapping。")
        if not isinstance(step.get("retryable"), bool):
            errors.append(f"{prefix} retryable 必须是 bool。")
        if not isinstance(step.get("needs_user_action"), bool):
            errors.append(f"{prefix} needs_user_action 必须是 bool。")
    missing = [step_id for step_id in STEP_IDS if step_id not in seen]
    if missing:
        errors.append(f"steps 缺少 canonical step: {', '.join(missing)}")

    future = data.get("future_interfaces")
    if not isinstance(future, dict):
        errors.append("future_interfaces 必须是 mapping。")
    else:
        llm = future.get("llm_visual_analysis")
        advanced = future.get("advanced_analysis")
        if not isinstance(llm, dict) or llm.get("status") != "not_run":
            errors.append("future_interfaces.llm_visual_analysis.status 必须是 not_run。")
        if not isinstance(advanced, dict):
            errors.append("future_interfaces.advanced_analysis 必须是 mapping。")
        else:
            for field in [
                "curve_extraction",
                "table_structure",
                "multimodal_interpretation",
            ]:
                value = advanced.get(field)
                if not isinstance(value, dict) or value.get("status") != "not_run":
                    errors.append(
                        f"future_interfaces.advanced_analysis.{field}.status 必须是 not_run。"
                    )
    policy = str(data.get("formal_record_policy_zh") or "")
    if "formal" not in policy or "人工确认" not in policy:
        errors.append("formal_record_policy_zh 必须说明 formal write gate 和人工确认。")
    return errors


def run_workflow(
    config: ProjectConfig,
    paper_id: str,
    *,
    campaign_id: str | None = None,
    campaign_item_id: str | None = None,
    skip_steps: list[str] | None = None,
    from_step: str | None = None,
    run_id: str | None = None,
) -> WorkflowRunResult:
    _require_paper_id(paper_id)
    run_id = run_id or next_workflow_run_id(config, paper_id)
    _require_run_id(run_id)
    combined_skips = _combined_skip_steps(config, skip_steps)
    if from_step:
        _require_step_id(from_step)
        for step_id in STEP_IDS[: STEP_IDS.index(from_step)]:
            if step_id not in combined_skips:
                combined_skips.append(step_id)
    data = build_workflow_run_skeleton(
        paper_id,
        run_id=run_id,
        campaign_id=campaign_id,
        campaign_item_id=campaign_item_id,
        skip_steps=combined_skips,
    )
    for step in data["steps"]:
        if step["status"] == "skipped" and from_step and STEP_IDS.index(step["step_id"]) < STEP_IDS.index(from_step):
            step["skipped_reason_zh"] = (
                f"用户指定从 {from_step} 开始，本步骤不会在本次 run 中重新执行。"
            )
    return _execute_run(config, data, start_step=from_step)


def resume_workflow(
    config: ProjectConfig, paper_id: str, *, from_step: str | None = None
) -> WorkflowRunResult:
    run_id = _latest_run_id(config, paper_id)
    data = load_workflow_run(config, paper_id, run_id)
    if data.get("workflow_status") == "stopped" and not from_step:
        raise WorkflowError(
            "workflow 已被用户 stop；请显式使用 --from-step 指定恢复位置，避免自动继续用户暂停的 run。"
        )
    start_step = from_step or _default_resume_step(data)
    if start_step:
        _require_step_id(start_step)
    return _execute_run(config, data, start_step=start_step)


def rerun_workflow(config: ProjectConfig, paper_id: str, *, from_step: str) -> WorkflowRunResult:
    _require_step_id(from_step)
    run_id = _latest_run_id(config, paper_id)
    data = load_workflow_run(config, paper_id, run_id)
    _reset_from_step(
        data,
        from_step,
        reason_zh=f"用户要求从 {from_step} 重新计算；该步骤及其后续步骤会重新生成或刷新 artifact。",
    )
    return _execute_run(config, data, start_step=from_step)


def stop_workflow(
    config: ProjectConfig, paper_id: str, *, reason_zh: str | None = None
) -> WorkflowRunResult:
    run_id = _latest_run_id(config, paper_id)
    data = load_workflow_run(config, paper_id, run_id)
    data["workflow_status"] = "stopped"
    data["current_step"] = data.get("current_step")
    data["stop_reason_zh"] = reason_zh or "用户手动暂停 workflow。"
    data["updated_at"] = _now()
    run_path = write_workflow_run(config, paper_id, run_id, data)
    report = _write_workflow_report(config, data, status="stopped")
    return WorkflowRunResult(
        paper_id=paper_id,
        run_id=run_id,
        run_path=run_path,
        report_path=report,
        workflow_status="stopped",
        current_step=str(data.get("current_step") or "") or None,
    )


def workflow_status(config: ProjectConfig, paper_id: str) -> WorkflowStatus:
    try:
        run_id = _latest_run_id(config, paper_id)
    except WorkflowError:
        return WorkflowStatus(
            path=workflow_paper_dir(config, paper_id),
            paper_id=paper_id,
            run_id=None,
            exists=False,
            workflow_status=None,
            current_step=None,
            report_path=None,
        )
    data = load_workflow_run(config, paper_id, run_id)
    return WorkflowStatus(
        path=workflow_run_path(config, paper_id, run_id),
        paper_id=paper_id,
        run_id=run_id,
        exists=True,
        workflow_status=str(data.get("workflow_status") or ""),
        current_step=str(data.get("current_step") or "") or None,
        report_path=workflow_report_path(config, paper_id, run_id),
    )


def _execute_run(
    config: ProjectConfig, data: dict[str, Any], *, start_step: str | None = None
) -> WorkflowRunResult:
    paper_id = str(data["paper_id"])
    run_id = str(data["run_id"])
    if start_step:
        _reset_from_step(
            data,
            start_step,
            reason_zh=f"从 {start_step} 恢复或重新执行；已完成步骤会先做 artifact 校验。",
        )
    data["workflow_status"] = "running"
    data["current_step"] = start_step or _default_resume_step(data)
    write_workflow_run(config, paper_id, run_id, data)

    for step in data["steps"]:
        step_id = str(step["step_id"])
        if step["status"] == "skipped":
            continue
        if step["status"] in {"completed", "partial", "needs_review"}:
            validation_errors = _validate_step_artifacts(config, paper_id, step)
            if not validation_errors:
                continue
            step["status"] = "pending"
            step["error_zh"] = "已完成步骤的 artifact 校验失败，需要从该步骤重新执行。"
            step["repair_hint_zh"] = "请保留或重新生成缺失 artifact；workflow 将尝试从该步骤恢复。"
            step["partial_reason_zh"] = "; ".join(validation_errors)
        if step["status"] not in {"pending", "failed", "running"}:
            continue

        _mark_step_started(data, step)
        write_workflow_run(config, paper_id, run_id, data)
        result = _run_step(config, data, step_id)
        _apply_step_result(data, step, result)
        write_workflow_run(config, paper_id, run_id, data)

        if result["status"] in {"blocked", "failed"}:
            final_status = "blocked" if result["status"] == "blocked" else "failed"
            data["workflow_status"] = final_status
            data["current_step"] = step_id
            data["updated_at"] = _now()
            write_workflow_run(config, paper_id, run_id, data)
            report = _write_workflow_report(config, data, status=final_status)
            return WorkflowRunResult(
                paper_id=paper_id,
                run_id=run_id,
                run_path=workflow_run_path(config, paper_id, run_id),
                report_path=report,
                workflow_status=final_status,
                current_step=step_id,
            )

    final_status = _aggregate_status(data)
    data["workflow_status"] = final_status
    data["current_step"] = None if final_status in {"completed", "partial", "needs_review"} else data.get("current_step")
    data["updated_at"] = _now()
    write_workflow_run(config, paper_id, run_id, data)
    report = _write_workflow_report(config, data, status=final_status)
    return WorkflowRunResult(
        paper_id=paper_id,
        run_id=run_id,
        run_path=workflow_run_path(config, paper_id, run_id),
        report_path=report,
        workflow_status=final_status,
        current_step=str(data.get("current_step") or "") or None,
    )


def _run_step(config: ProjectConfig, data: dict[str, Any], step_id: str) -> dict[str, Any]:
    try:
        if step_id == "acquisition":
            return _run_acquisition_step(config, data)
        if step_id == "reading_draft":
            return _run_reading_draft_step(config, data)
        if step_id == "visual_extraction":
            return _run_visual_step(config, data)
        if step_id == "scoring":
            return _run_scoring_step(config, data)
        if step_id == "review_packet":
            return _run_review_packet_step(config, data)
    except WorkflowError:
        raise
    except Exception as exc:
        return {
            "status": "blocked",
            "artifacts": {},
            "error_zh": str(exc),
            "repair_hint_zh": "请先修复该步骤依赖的输入或配置，再运行 rsa workflow resume。",
            "retryable": True,
            "needs_user_action": True,
            "blocked_reason_zh": str(exc),
        }
    raise WorkflowError(f"未知 workflow step: {step_id}")


def _run_acquisition_step(config: ProjectConfig, data: dict[str, Any]) -> dict[str, Any]:
    from .acquisition import find_sources
    from .assets import source_status

    paper_id = str(data["paper_id"])
    result = find_sources(config, paper_id)
    status = source_status(config, paper_id)
    artifacts = {
        "candidate_record": _display_path(config, result.path),
        "source_ledger": _display_path(config, status.path),
    }
    if status.available_count > 0 or result.downloaded_count > 0:
        return {
            "status": "completed",
            "artifacts": artifacts,
            "summary_zh": f"已发现来源并确认可用 PDF 数量 {status.available_count}。",
        }
    return {
        "status": "partial",
        "artifacts": artifacts,
        "partial_reason_zh": "尚未获得可用 PDF；后续 reading_draft 可能会被阻断。",
        "repair_hint_zh": "可通过 rsa source add 或配置授权 provider 后重新运行 acquisition。",
        "summary_zh": f"候选 {result.candidates_found} 项，尚无可用 PDF。",
    }


def _run_reading_draft_step(config: ProjectConfig, data: dict[str, Any]) -> dict[str, Any]:
    from .notes import note_path, validate_reading_note
    from .reading_draft import DraftError, draft_reading_note

    paper_id = str(data["paper_id"])
    note_file = note_path(config, paper_id)
    if note_file.exists():
        errors = validate_reading_note(config, paper_id)
        if errors:
            return {
                "status": "blocked",
                "artifacts": {"reading_note": _display_path(config, note_file)},
                "blocked_reason_zh": "已有 reading note 但 schema 校验失败: " + "; ".join(errors),
                "repair_hint_zh": "请修复 reading note 或删除草稿后重新生成。",
                "retryable": False,
                "needs_user_action": True,
            }
        return {
            "status": "needs_review",
            "artifacts": {"reading_note": _display_path(config, note_file)},
            "summary_zh": "复用已有 reading note；仍需要人工监管。",
            "partial_reason_zh": None,
        }
    try:
        result = draft_reading_note(config, paper_id)
    except DraftError as exc:
        return {
            "status": "blocked",
            "artifacts": {
                "prompt_packet": _display_path(config, config.extracted_root / paper_id / "prompt_packet.yaml")
            },
            "blocked_reason_zh": str(exc),
            "error_zh": str(exc),
            "repair_hint_zh": "请补充授权全文、配置 reading_draft.llm，或修复模型输出 schema 后再 resume。",
            "retryable": True,
            "needs_user_action": True,
        }
    status = "needs_review" if result.note_status == "ready_for_review" else "completed"
    return {
        "status": status,
        "artifacts": {
            "reading_note": _display_path(config, result.note_path),
            "reading_review_packet": _display_path(config, result.review_packet_path),
            "extraction_cache": _display_path(config, result.extraction_cache_path),
            "prompt_packet": _display_path(config, result.prompt_packet_path),
        },
        "summary_zh": f"reading draft 已生成，note_status={result.note_status}。",
        "needs_user_action": status == "needs_review",
    }


def _run_visual_step(config: ProjectConfig, data: dict[str, Any]) -> dict[str, Any]:
    from .visual import VisualError, extract_visual_evidence, validate_visual_candidate_file, visual_status

    paper_id = str(data["paper_id"])
    errors = validate_visual_candidate_file(config, paper_id)
    if not errors:
        status = visual_status(config, paper_id)
        step_status = "needs_review" if status.needs_review_count or status.blocked_count else "completed"
        return {
            "status": step_status,
            "artifacts": {
                "visual_candidates": _display_path(config, status.path),
            },
            "summary_zh": f"复用已有视觉证据候选，total={status.total_count}。",
            "needs_user_action": step_status == "needs_review",
        }
    try:
        result = extract_visual_evidence(config, paper_id)
    except VisualError as exc:
        return {
            "status": "partial",
            "artifacts": {},
            "partial_reason_zh": str(exc),
            "repair_hint_zh": "视觉证据提取失败不会阻断正文评分；需要图表证据时请修复 PDF/PyMuPDF 后 rerun visual_extraction。",
            "summary_zh": "视觉证据提取失败，workflow 将降级继续。",
            "retryable": True,
            "needs_user_action": True,
        }
    status = visual_status(config, paper_id)
    step_status = "needs_review" if status.needs_review_count or status.blocked_count else "completed"
    return {
        "status": step_status,
        "artifacts": {
            "visual_candidates": _display_path(config, result.candidate_path),
            "asset_manifest": _display_path(config, result.manifest_path),
            "crops_written": result.crops_written,
            "context_packets_written": result.context_packets_written,
        },
        "summary_zh": f"视觉证据候选新增 {result.candidates_created} 项。",
        "needs_user_action": step_status == "needs_review",
    }


def _run_scoring_step(config: ProjectConfig, data: dict[str, Any]) -> dict[str, Any]:
    from .scoring import ScoringError, score_paper, scoring_path, validate_scoring_record

    paper_id = str(data["paper_id"])
    existing = scoring_path(config, paper_id)
    if existing.exists():
        errors = validate_scoring_record(config, paper_id)
        if not errors:
            return {
                "status": "completed",
                "artifacts": {"scoring": _display_path(config, existing)},
                "summary_zh": "复用已有 scoring YAML。",
            }
    try:
        result = score_paper(config, paper_id, campaign_item=_campaign_item(config, data))
    except ScoringError as exc:
        return {
            "status": "blocked",
            "artifacts": {},
            "blocked_reason_zh": str(exc),
            "error_zh": str(exc),
            "repair_hint_zh": "请先补齐有效 reading note 和必要证据，再运行 rsa workflow resume。",
            "retryable": True,
            "needs_user_action": True,
        }
    step_status = "needs_review" if result.ai_review_decision == "needs_review" else "completed"
    return {
        "status": step_status,
        "artifacts": {
            "scoring": _display_path(config, result.scoring_path),
            "scoring_review_packet": _display_path(config, result.review_packet_path),
        },
        "summary_zh": (
            f"评分完成：relevance={result.ai_relevance_score_10}/10, "
            f"quality={result.ai_quality_score_10}/10, priority={result.ai_read_priority_score_10}/10。"
        ),
        "needs_user_action": step_status == "needs_review",
    }


def _run_review_packet_step(config: ProjectConfig, data: dict[str, Any]) -> dict[str, Any]:
    status = _aggregate_status(data, include_review_step=False)
    report = _write_workflow_report(config, data, status=status)
    return {
        "status": status if status in {"partial", "needs_review"} else "completed",
        "artifacts": {"workflow_report": _display_path(config, report)},
        "summary_zh": f"workflow review packet 已生成，workflow_status={status}。",
        "needs_user_action": status in {"partial", "needs_review"},
    }


def _write_workflow_report(
    config: ProjectConfig, data: dict[str, Any], *, status: str | None = None
) -> Path:
    paper_id = str(data["paper_id"])
    run_id = str(data["run_id"])
    status = status or _aggregate_status(data)
    path = workflow_report_path(config, paper_id, run_id)
    rows = []
    for step in data.get("steps", []):
        artifacts = step.get("artifacts") if isinstance(step.get("artifacts"), dict) else {}
        artifact_text = ", ".join(f"`{key}`={value}" for key, value in artifacts.items()) or "-"
        reason = (
            step.get("blocked_reason_zh")
            or step.get("partial_reason_zh")
            or step.get("skipped_reason_zh")
            or step.get("error_zh")
            or step.get("summary_zh")
            or "-"
        )
        rows.append(
            f"| `{step.get('step_id')}` | `{step.get('status')}` | {artifact_text} | {reason} |"
        )
    report = f"""# Workflow Review Packet: {paper_id} / {run_id}

## 概览

- `paper_id`: `{paper_id}`
- `run_id`: `{run_id}`
- `workflow_status`: `{status}`
- `campaign_id`: `{data.get("campaign_id")}`
- `campaign_item_id`: `{data.get("campaign_item_id")}`

本报告是自动工作流的 staging/review packet，不是 formal record。metadata、literature_map、agent_research_notes 等正式写入必须继续通过 `rsa formal ... --human-confirmed`。

## 步骤记录

| step_id | status | artifacts | 中文原因/说明 |
|---|---|---|---|
{chr(10).join(rows)}

## 监管提示

{_next_action_text(status)}

## 高级图表智能接口

- `llm_visual_analysis`: `{data.get("future_interfaces", {}).get("llm_visual_analysis", {}).get("status", "not_run")}`
- `advanced_analysis.curve_extraction`: `{data.get("future_interfaces", {}).get("advanced_analysis", {}).get("curve_extraction", {}).get("status", "not_run")}`
- `advanced_analysis.table_structure`: `{data.get("future_interfaces", {}).get("advanced_analysis", {}).get("table_structure", {}).get("status", "not_run")}`
- `advanced_analysis.multimodal_interpretation`: `{data.get("future_interfaces", {}).get("advanced_analysis", {}).get("multimodal_interpretation", {}).get("status", "not_run")}`

这些接口目前只保留状态和链接位置，不代表 Phase 10 已执行 LLM 图像理解或高级图表智能。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    data.setdefault("artifacts", {})["workflow_report"] = _display_path(config, path)
    return path


def _mark_step_started(data: dict[str, Any], step: dict[str, Any]) -> None:
    step["status"] = "running"
    step["started_at"] = step.get("started_at") or _now()
    step["finished_at"] = None
    data["current_step"] = step["step_id"]
    data["updated_at"] = _now()


def _apply_step_result(data: dict[str, Any], step: dict[str, Any], result: dict[str, Any]) -> None:
    status = result.get("status", "failed")
    step["status"] = status
    step["finished_at"] = _now()
    step["artifacts"] = result.get("artifacts") or {}
    step["error_zh"] = result.get("error_zh")
    step["repair_hint_zh"] = result.get("repair_hint_zh")
    step["retryable"] = bool(result.get("retryable", status == "failed"))
    step["needs_user_action"] = bool(result.get("needs_user_action", False))
    step["partial_reason_zh"] = result.get("partial_reason_zh")
    step["blocked_reason_zh"] = result.get("blocked_reason_zh")
    step["summary_zh"] = result.get("summary_zh")
    data.setdefault("artifacts", {})[step["step_id"]] = step["artifacts"]
    data["updated_at"] = _now()


def _aggregate_status(data: dict[str, Any], *, include_review_step: bool = True) -> str:
    steps = data.get("steps", [])
    if not include_review_step:
        steps = [step for step in steps if step.get("step_id") != "review_packet"]
    statuses = [step.get("status") for step in steps if isinstance(step, dict)]
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "running" for status in statuses):
        return "running"
    if any(status == "needs_review" for status in statuses):
        return "needs_review"
    if any(status == "partial" for status in statuses):
        return "partial"
    if all(status in {"completed", "skipped"} for status in statuses):
        return "completed"
    return "pending"


def _default_resume_step(data: dict[str, Any]) -> str | None:
    for step in data.get("steps", []):
        if not isinstance(step, dict):
            continue
        if step.get("status") in {"pending", "running", "failed"} or step.get("retryable") is True:
            return str(step.get("step_id"))
    return None


def _reset_from_step(data: dict[str, Any], step_id: str, *, reason_zh: str) -> None:
    _require_step_id(step_id)
    reset = False
    for step in data.get("steps", []):
        if not isinstance(step, dict):
            continue
        if step.get("step_id") == step_id:
            reset = True
        if reset and step.get("status") != "skipped":
            step["status"] = "pending"
            step["started_at"] = None
            step["finished_at"] = None
            step["repair_hint_zh"] = reason_zh
            step["retryable"] = False
            step["needs_user_action"] = False
    data["current_step"] = step_id


def _validate_step_artifacts(config: ProjectConfig, paper_id: str, step: dict[str, Any]) -> list[str]:
    step_id = step.get("step_id")
    artifacts = step.get("artifacts") if isinstance(step.get("artifacts"), dict) else {}
    errors: list[str] = []
    if step_id == "reading_draft":
        from .notes import validate_reading_note

        errors.extend(validate_reading_note(config, paper_id))
    if step_id == "visual_extraction" and artifacts.get("visual_candidates"):
        from .visual import validate_visual_candidate_file

        errors.extend(validate_visual_candidate_file(config, paper_id))
    if step_id == "scoring":
        from .scoring import validate_scoring_record

        errors.extend(validate_scoring_record(config, paper_id))
    for key, value in artifacts.items():
        if not isinstance(value, str) or not value or key.endswith("_written"):
            continue
        resolved = _resolve_artifact_path(config, value)
        if not resolved.exists():
            errors.append(f"{step_id}.{key} artifact 不存在: {value}")
    return errors


def _campaign_item(config: ProjectConfig, data: dict[str, Any]) -> dict[str, Any] | None:
    campaign_id = data.get("campaign_id")
    item_id = data.get("campaign_item_id")
    if not campaign_id:
        return None
    try:
        from .campaign import load_campaign

        campaign = load_campaign(config, str(campaign_id))
    except Exception:
        return None
    items = campaign.get("items")
    if not isinstance(items, list):
        return None
    for item in items:
        if not isinstance(item, dict):
            continue
        if item_id and item.get("item_id") == item_id:
            return item
        if item.get("paper_id") == data.get("paper_id"):
            return item
    return None


def _latest_run_id(config: ProjectConfig, paper_id: str) -> str:
    _require_paper_id(paper_id)
    paper_dir = workflow_paper_dir(config, paper_id)
    ids = sorted(path.stem for path in paper_dir.glob("RUN-*.yaml") if RUN_ID_PATTERN.match(path.stem))
    if not ids:
        raise WorkflowError(f"{paper_id} 没有可恢复的 workflow run。")
    return ids[-1]


def _combined_skip_steps(config: ProjectConfig, explicit: list[str] | None) -> list[str]:
    skip_steps = []
    for value in [*config.workflow_skip_steps, *(explicit or [])]:
        step_id = str(value)
        _require_step_id(step_id)
        if step_id not in skip_steps:
            skip_steps.append(step_id)
    return skip_steps


def _next_action_text(status: str) -> str:
    if status == "completed":
        return "自动链路已跑到 review packet。涉及 formal 写入时仍需人工确认。"
    if status == "needs_review":
        return "workflow 已生成 review packet，但存在需要人工监管的项目；请查看上表中的 needs_review 步骤。"
    if status == "partial":
        return "workflow 以降级模式完成；请优先检查 partial_reason_zh，再决定是否 rerun 对应步骤。"
    if status == "blocked":
        return "workflow 已 fail closed；请按 repair_hint_zh 修复后运行 rsa workflow resume。"
    if status == "stopped":
        return "workflow 已被用户暂停；自动 resume 不会继续，需显式指定 --from-step。"
    return "workflow 尚未完成，请查看 current_step 和 step ledger。"


def _resolve_artifact_path(config: ProjectConfig, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.root / path


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _default_command(step_id: str, paper_id: str) -> str:
    commands = {
        "acquisition": f"rsa source find {paper_id}",
        "reading_draft": f"rsa note draft {paper_id}",
        "visual_extraction": f"rsa visual extract {paper_id}",
        "scoring": f"rsa score {paper_id}",
        "review_packet": f"rsa workflow report {paper_id}",
    }
    return commands[step_id]


def _require_paper_id(paper_id: str) -> None:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise WorkflowError(f"paper_id 必须匹配 P###: {paper_id}")


def _require_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.match(run_id):
        raise WorkflowError(f"run_id 必须匹配 RUN-###: {run_id}")


def _require_step_id(step_id: str) -> None:
    if step_id not in STEP_IDS:
        raise WorkflowError(f"step_id 必须是以下之一: {', '.join(STEP_IDS)}")


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise WorkflowError(f"无法读取 workflow YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise WorkflowError(f"workflow YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise WorkflowError(f"workflow YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
