from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig


QUEUE_SCHEMA_VERSION = "phase14-worker-queue-v1"
SCHEDULE_SCHEMA_VERSION = "phase14-worker-schedule-v1"
TASK_ID_PATTERN = re.compile(r"^WT(?P<number>\d{3})$")
SCHEDULE_ID_PATTERN = re.compile(r"^WS(?P<number>\d{3})$")
CAMPAIGN_ID_PATTERN = re.compile(r"^C\d{3}$")
TASK_TYPES = {
    "campaign_run",
    "campaign_resume",
    "campaign_queue",
    "campaign_report",
    "campaign_safety",
    "review_workspace",
}
TASK_STATUSES = {
    "queued",
    "running",
    "completed",
    "failed",
    "blocked",
    "cancelled",
    "skipped",
}


class WorkerError(ValueError):
    """Raised when local worker automation cannot safely continue."""


@dataclass(frozen=True)
class WorkerEnqueueResult:
    task_id: str
    task_type: str
    target_id: str
    path: Path


@dataclass(frozen=True)
class WorkerRunResult:
    path: Path
    processed_count: int
    completed_count: int
    failed_count: int
    queued_remaining_count: int
    due_enqueued_count: int


@dataclass(frozen=True)
class WorkerStatus:
    path: Path
    schedule_path: Path
    log_path: Path
    total_count: int
    queued_count: int
    running_count: int
    completed_count: int
    failed_count: int
    cancelled_count: int
    schedule_count: int
    enabled_schedule_count: int
    last_task_id: str | None
    last_message_zh: str | None


@dataclass(frozen=True)
class WorkerTaskMutationResult:
    task_id: str
    status: str
    path: Path


@dataclass(frozen=True)
class WorkerScheduleResult:
    schedule_id: str
    task_type: str
    target_id: str
    path: Path
    next_run_at: str


@dataclass(frozen=True)
class WorkerDueResult:
    path: Path
    enqueued_count: int
    due_schedule_ids: list[str]


def worker_queue_path(config: ProjectConfig) -> Path:
    return config.workers_root / "queue.yaml"


def worker_schedule_path(config: ProjectConfig) -> Path:
    return config.workers_root / "schedules.yaml"


def worker_log_path(config: ProjectConfig) -> Path:
    return config.workers_root / "worker_log.md"


def enqueue_worker_task(
    config: ProjectConfig,
    task_type: str,
    target_id: str,
    *,
    source: str = "manual",
    schedule_id: str | None = None,
) -> WorkerEnqueueResult:
    normalized = _normalize_task_type(task_type)
    _require_campaign_target(normalized, target_id)
    data = _load_or_create_queue(config)
    tasks = _tasks(data)
    task_id = _next_prefixed_id(tasks, "WT", "task_id")
    now = _now()
    tasks.append(
        {
            "task_id": task_id,
            "task_type": normalized,
            "target_id": target_id,
            "status": "queued",
            "source": source,
            "schedule_id": schedule_id,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "finished_at": None,
            "attempts": 0,
            "max_attempts": 1,
            "message_zh": "任务已进入本地 worker 队列，等待执行。",
            "error_zh": None,
            "repair_hint_zh": None,
            "result_status": None,
            "artifacts": {},
            "formal_write_allowed": False,
            "next_action_zh": "运行 rsa worker run 处理队列；正式写入仍需人工确认。",
        }
    )
    data["updated_at"] = now
    _write_yaml(worker_queue_path(config), data)
    _append_log(config, f"已入队 {task_id}: {normalized} {target_id}")
    return WorkerEnqueueResult(task_id, normalized, target_id, worker_queue_path(config))


def run_worker(
    config: ProjectConfig,
    *,
    max_tasks: int | None = None,
    include_due: bool = False,
) -> WorkerRunResult:
    if max_tasks is not None and max_tasks <= 0:
        raise WorkerError("--max-tasks 必须是正整数。")
    due_count = 0
    if include_due:
        due_count = enqueue_due_schedules(config).enqueued_count
    data = _load_or_create_queue(config)
    tasks = _tasks(data)
    selected = [task for task in tasks if task.get("status") == "queued"]
    if max_tasks is not None:
        selected = selected[:max_tasks]

    processed = 0
    completed = 0
    failed = 0
    for task in selected:
        processed += 1
        _mark_running(config, data, task)
        try:
            result = _execute_task(config, task)
        except Exception as exc:  # worker 必须 continue_on_error，避免单个任务拖死整条队列。
            failed += 1
            task["status"] = "failed"
            task["error_zh"] = str(exc)
            task["repair_hint_zh"] = "查看 worker_log.md 和对应 campaign/review/safety 文件，修复后运行 rsa worker recover。"
            task["message_zh"] = "任务执行失败，已记录错误并继续处理后续任务。"
            task["finished_at"] = _now()
            task["updated_at"] = task["finished_at"]
            task["next_action_zh"] = "修复输入或依赖后运行 rsa worker recover WT###。"
            _append_log(config, f"失败 {task.get('task_id')}: {task.get('task_type')} {task.get('target_id')} - {exc}")
        else:
            completed += 1
            task["status"] = "completed"
            task["result_status"] = result.get("result_status")
            task["artifacts"] = result.get("artifacts") or {}
            task["message_zh"] = result.get("message_zh")
            task["repair_hint_zh"] = result.get("repair_hint_zh")
            task["finished_at"] = _now()
            task["updated_at"] = task["finished_at"]
            task["next_action_zh"] = result.get("next_action_zh")
            _append_log(
                config,
                f"完成 {task.get('task_id')}: {task.get('task_type')} {task.get('target_id')} -> {task.get('result_status')}",
            )
        _write_yaml(worker_queue_path(config), data)

    queued_remaining = sum(1 for task in tasks if task.get("status") == "queued")
    data["last_run_at"] = _now()
    data["last_run_summary"] = {
        "processed_count": processed,
        "completed_count": completed,
        "failed_count": failed,
        "queued_remaining_count": queued_remaining,
        "due_enqueued_count": due_count,
    }
    data["updated_at"] = _now()
    _write_yaml(worker_queue_path(config), data)
    return WorkerRunResult(
        path=worker_queue_path(config),
        processed_count=processed,
        completed_count=completed,
        failed_count=failed,
        queued_remaining_count=queued_remaining,
        due_enqueued_count=due_count,
    )


def worker_status(config: ProjectConfig) -> WorkerStatus:
    data = _load_or_create_queue(config)
    schedule_data = _load_or_create_schedules(config)
    tasks = _tasks(data)
    schedules = _schedules(schedule_data)
    last = tasks[-1] if tasks else {}
    return WorkerStatus(
        path=worker_queue_path(config),
        schedule_path=worker_schedule_path(config),
        log_path=worker_log_path(config),
        total_count=len(tasks),
        queued_count=sum(1 for task in tasks if task.get("status") == "queued"),
        running_count=sum(1 for task in tasks if task.get("status") == "running"),
        completed_count=sum(1 for task in tasks if task.get("status") == "completed"),
        failed_count=sum(1 for task in tasks if task.get("status") == "failed"),
        cancelled_count=sum(1 for task in tasks if task.get("status") == "cancelled"),
        schedule_count=len(schedules),
        enabled_schedule_count=sum(1 for item in schedules if item.get("enabled") is True),
        last_task_id=last.get("task_id"),
        last_message_zh=last.get("message_zh"),
    )


def cancel_worker_task(
    config: ProjectConfig, task_id: str, *, reason_zh: str | None = None
) -> WorkerTaskMutationResult:
    data, task = _find_task(config, task_id)
    if task.get("status") in {"completed", "cancelled"}:
        raise WorkerError(f"{task_id} 已是 {task.get('status')}，不能取消。")
    task["status"] = "cancelled"
    task["updated_at"] = _now()
    task["finished_at"] = task.get("finished_at") or task["updated_at"]
    task["message_zh"] = reason_zh or "用户取消 worker 任务。"
    task["next_action_zh"] = "如需重新执行，请重新 enqueue 一个任务。"
    _write_yaml(worker_queue_path(config), data)
    _append_log(config, f"取消 {task_id}: {task['message_zh']}")
    return WorkerTaskMutationResult(task_id, "cancelled", worker_queue_path(config))


def recover_worker_task(
    config: ProjectConfig, task_id: str, *, reason_zh: str | None = None
) -> WorkerTaskMutationResult:
    data, task = _find_task(config, task_id)
    if task.get("status") not in {"running", "failed", "blocked"}:
        raise WorkerError(f"{task_id} 当前状态为 {task.get('status')}，不需要 recover。")
    task["status"] = "queued"
    task["updated_at"] = _now()
    task["started_at"] = None
    task["finished_at"] = None
    task["error_zh"] = None
    task["repair_hint_zh"] = None
    task["message_zh"] = reason_zh or "任务已由用户显式恢复到 queued。"
    task["next_action_zh"] = "运行 rsa worker run 重新处理该任务。"
    _write_yaml(worker_queue_path(config), data)
    _append_log(config, f"恢复 {task_id}: {task['message_zh']}")
    return WorkerTaskMutationResult(task_id, "queued", worker_queue_path(config))


def add_worker_schedule(
    config: ProjectConfig,
    task_type: str,
    target_id: str,
    *,
    interval_hours: int,
    start_at: str | None = None,
) -> WorkerScheduleResult:
    if interval_hours <= 0:
        raise WorkerError("--interval-hours 必须是正整数。")
    normalized = _normalize_task_type(task_type)
    _require_campaign_target(normalized, target_id)
    data = _load_or_create_schedules(config)
    schedules = _schedules(data)
    schedule_id = _next_prefixed_id(schedules, "WS", "schedule_id")
    next_run = _parse_time(start_at) if start_at else datetime.now(timezone.utc)
    schedules.append(
        {
            "schedule_id": schedule_id,
            "task_type": normalized,
            "target_id": target_id,
            "interval_hours": interval_hours,
            "next_run_at": next_run.isoformat(),
            "enabled": True,
            "created_at": _now(),
            "updated_at": _now(),
            "last_enqueued_at": None,
            "message_zh": "该计划只负责按时间入队，不会直接执行任务。",
            "formal_write_allowed": False,
            "future_interfaces": {
                "external_scheduler": {"status": "not_enabled"},
                "daemon_mode": {"status": "not_enabled"},
            },
        }
    )
    data["updated_at"] = _now()
    _write_yaml(worker_schedule_path(config), data)
    _append_log(config, f"新增计划 {schedule_id}: {normalized} {target_id}")
    return WorkerScheduleResult(
        schedule_id=schedule_id,
        task_type=normalized,
        target_id=target_id,
        path=worker_schedule_path(config),
        next_run_at=next_run.isoformat(),
    )


def list_worker_schedules(config: ProjectConfig) -> list[dict[str, Any]]:
    return list(_schedules(_load_or_create_schedules(config)))


def enqueue_due_schedules(config: ProjectConfig) -> WorkerDueResult:
    data = _load_or_create_schedules(config)
    schedules = _schedules(data)
    now = datetime.now(timezone.utc)
    due_ids: list[str] = []
    for schedule in schedules:
        if schedule.get("enabled") is not True:
            continue
        next_run = _parse_time(schedule.get("next_run_at"))
        if next_run > now:
            continue
        result = enqueue_worker_task(
            config,
            str(schedule.get("task_type")),
            str(schedule.get("target_id")),
            source="schedule",
            schedule_id=str(schedule.get("schedule_id")),
        )
        due_ids.append(str(schedule.get("schedule_id")))
        schedule["last_enqueued_at"] = _now()
        schedule["updated_at"] = schedule["last_enqueued_at"]
        interval = int(schedule.get("interval_hours") or 1)
        while next_run <= now:
            next_run = next_run + timedelta(hours=interval)
        schedule["next_run_at"] = next_run.isoformat()
    data["updated_at"] = _now()
    _write_yaml(worker_schedule_path(config), data)
    if due_ids:
        _append_log(config, f"已从定时计划入队 {len(due_ids)} 个任务，来源 schedule: {', '.join(due_ids)}")
    return WorkerDueResult(
        path=worker_schedule_path(config),
        enqueued_count=len(due_ids),
        due_schedule_ids=due_ids,
    )


def read_worker_logs(config: ProjectConfig, *, max_lines: int = 20) -> list[str]:
    path = worker_log_path(config)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[-max_lines:]


def _execute_task(config: ProjectConfig, task: dict[str, Any]) -> dict[str, Any]:
    task_type = str(task.get("task_type"))
    target_id = str(task.get("target_id"))
    if task_type == "campaign_run":
        from .campaign import run_campaign

        result = run_campaign(config, target_id)
        return {
            "result_status": result.campaign_status,
            "message_zh": f"campaign run 已执行，状态为 {result.campaign_status}。",
            "next_action_zh": _campaign_next_action(result.campaign_status),
            "artifacts": {
                "run": str(result.path),
                "review_queue": str(result.review_queue_path),
                "batch_report": str(result.batch_report_path),
                "metadata_requests": str(result.metadata_requests_path),
            },
        }
    if task_type == "campaign_resume":
        from .campaign import resume_campaign_run

        result = resume_campaign_run(config, target_id)
        return {
            "result_status": result.campaign_status,
            "message_zh": f"campaign resume 已执行，状态为 {result.campaign_status}。",
            "next_action_zh": _campaign_next_action(result.campaign_status),
            "artifacts": {
                "run": str(result.path),
                "review_queue": str(result.review_queue_path),
                "batch_report": str(result.batch_report_path),
                "metadata_requests": str(result.metadata_requests_path),
            },
        }
    if task_type == "campaign_queue":
        from .campaign import generate_review_queue

        result = generate_review_queue(config, target_id)
        return {
            "result_status": "review_queue_generated",
            "message_zh": f"review queue 已生成，共 {result.total_count} 项。",
            "next_action_zh": "查看 review queue 或生成 review workspace。",
            "artifacts": {"review_queue": str(result.path)},
        }
    if task_type == "campaign_report":
        from .campaign import write_batch_report

        path = write_batch_report(config, target_id)
        return {
            "result_status": "batch_report_generated",
            "message_zh": "campaign 批量报告已生成。",
            "next_action_zh": "查看中文批量报告和 review queue。",
            "artifacts": {"batch_report": str(path)},
        }
    if task_type == "campaign_safety":
        from .safety import check_campaign_safety

        result = check_campaign_safety(config, target_id)
        return {
            "result_status": result.safety_status,
            "message_zh": f"campaign safety 已执行，状态为 {result.safety_status}。",
            "next_action_zh": "查看 safety report；正式写入仍需人工确认。",
            "artifacts": {"safety": str(result.path), "safety_report": str(result.report_path)},
        }
    if task_type == "review_workspace":
        from .review_workspace import build_review_workspace

        result = build_review_workspace(config, campaign_id=target_id)
        return {
            "result_status": "review_workspace_generated",
            "message_zh": f"本地监管台已生成，objects={result.object_count}。",
            "next_action_zh": "打开 review workspace 进行人工监管。",
            "artifacts": {"index": str(result.index_path), "manifest": str(result.manifest_path)},
        }
    raise WorkerError(f"未知 worker task_type: {task_type}")


def _mark_running(config: ProjectConfig, data: dict[str, Any], task: dict[str, Any]) -> None:
    now = _now()
    task["status"] = "running"
    task["started_at"] = now
    task["updated_at"] = now
    task["attempts"] = int(task.get("attempts") or 0) + 1
    task["message_zh"] = "worker 正在执行该任务。"
    _write_yaml(worker_queue_path(config), data)


def _campaign_next_action(status: str) -> str:
    if status == "paused":
        return "campaign 已在 formal gate 前暂停；请在 review workspace 中人工处理 formal request。"
    if status == "partial":
        return "查看 batch report 和 safety report，处理 blocked/partial 项。"
    if status == "completed":
        return "查看 review queue、review workspace 或 safety report。"
    return "查看 campaign 状态和 batch report。"


def _load_or_create_queue(config: ProjectConfig) -> dict[str, Any]:
    path = worker_queue_path(config)
    if path.exists():
        return _read_yaml_mapping(path)
    now = _now()
    return {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "user_language": "zh",
        "created_at": now,
        "updated_at": now,
        "formal_record_policy_zh": (
            "worker queue 只调度 staging/review 自动化，不执行 formal write；正式记录仍需人工确认。"
        ),
        "future_interfaces": _future_interfaces(),
        "tasks": [],
    }


def _load_or_create_schedules(config: ProjectConfig) -> dict[str, Any]:
    path = worker_schedule_path(config)
    if path.exists():
        return _read_yaml_mapping(path)
    now = _now()
    return {
        "schema_version": SCHEDULE_SCHEMA_VERSION,
        "user_language": "zh",
        "created_at": now,
        "updated_at": now,
        "schedule_policy_zh": "schedule 只负责把到期任务放入 worker queue，不直接执行任务。",
        "future_interfaces": _future_interfaces(),
        "schedules": [],
    }


def _future_interfaces() -> dict[str, Any]:
    return {
        "daemon_mode": {"status": "not_enabled"},
        "external_scheduler": {"status": "not_enabled"},
        "task_lock": {"status": "not_enabled"},
        "heartbeat": {"status": "not_enabled"},
        "worker_id": None,
        "max_runtime_seconds": None,
        "failure_detector_plugins": {"status": "not_run"},
    }


def _tasks(data: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = data.setdefault("tasks", [])
    if not isinstance(tasks, list):
        raise WorkerError("worker queue 的 tasks 必须是 YAML list。")
    return tasks


def _schedules(data: dict[str, Any]) -> list[dict[str, Any]]:
    schedules = data.setdefault("schedules", [])
    if not isinstance(schedules, list):
        raise WorkerError("worker schedules 的 schedules 必须是 YAML list。")
    return schedules


def _find_task(config: ProjectConfig, task_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not TASK_ID_PATTERN.match(task_id):
        raise WorkerError(f"task_id 必须匹配 WT###: {task_id}")
    data = _load_or_create_queue(config)
    for task in _tasks(data):
        if isinstance(task, dict) and task.get("task_id") == task_id:
            return data, task
    raise WorkerError(f"worker task 不存在: {task_id}")


def _next_prefixed_id(items: list[Any], prefix: str, key: str) -> str:
    pattern = TASK_ID_PATTERN if prefix == "WT" else SCHEDULE_ID_PATTERN
    highest = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        match = pattern.match(str(item.get(key) or ""))
        if match:
            highest = max(highest, int(match.group("number")))
    return f"{prefix}{highest + 1:03d}"


def _normalize_task_type(value: str) -> str:
    task_type = str(value or "").strip().replace("-", "_")
    if task_type not in TASK_TYPES:
        raise WorkerError(f"task_type 不支持: {value}")
    return task_type


def _require_campaign_target(task_type: str, target_id: str) -> None:
    if task_type in TASK_TYPES and not CAMPAIGN_ID_PATTERN.match(str(target_id)):
        raise WorkerError(f"{task_type} 当前只支持 campaign 编号 C###: {target_id}")


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise WorkerError(f"无法读取 YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise WorkerError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise WorkerError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _append_log(config: ProjectConfig, message_zh: str) -> None:
    path = worker_log_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Worker Log\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {_now()} {message_zh}\n")


def _parse_time(value: Any) -> datetime:
    if value is None:
        raise WorkerError("时间字段不能为空。")
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise WorkerError(f"时间格式无效，应使用 ISO 8601: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
