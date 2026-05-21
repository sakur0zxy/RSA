from __future__ import annotations

import re
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
