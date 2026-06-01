from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .assets import asset_manifest_path, source_record_path
from .campaign import (
    campaign_metadata_requests_path,
    campaign_path,
    campaign_review_queue_path,
    campaign_run_path,
)
from .config import ProjectConfig
from .notes import note_path
from .scoring import score_status, scoring_path
from .visual import visual_candidate_path
from .workflow import workflow_status


POLICY_SCHEMA_VERSION = "phase17-dynamic-policy-v1"
DECISION_SCHEMA_VERSION = "phase17-dynamic-decision-v1"
DECISION_ID_PATTERN = re.compile(r"^DW(?P<number>\d{3})$")
PAPER_ID_PATTERN = re.compile(r"^P\d{3}$")
CAMPAIGN_ID_PATTERN = re.compile(r"^C\d{3}$")

TARGET_TYPES = {"paper", "campaign", "formal_write"}
CONDITION_KEYS = {
    "run_if",
    "skip_if",
    "retry_if",
    "block_if",
    "route_to_review_if",
    "stop_before_formal_write",
}
CONDITION_FIELDS = {
    "always",
    "target_type",
    "target_id_prefix",
    "trigger",
    "trigger_in",
    "artifact_exists",
    "artifact_missing",
    "workflow_status_in",
    "campaign_status_in",
    "score_confidence_in",
    "min_priority_score",
}
SELECTED_ACTIONS = {
    "run_workflow",
    "run_campaign",
    "retry_workflow",
    "skip",
    "block",
    "route_to_review",
    "stop_before_formal_write",
}
DECISION_STATUSES = {
    "proposed",
    "blocked",
    "needs_review",
    "accepted",
    "deferred",
    "rejected",
    "needs_followup",
}
REVIEW_DECISIONS = {"accepted", "deferred", "rejected", "needs_followup"}
CONFIDENCE_LEVELS = {"low", "medium", "high", "unknown"}


class DynamicWorkflowError(ValueError):
    """Raised when dynamic workflow cannot safely choose the next action."""


@dataclass(frozen=True)
class DynamicWorkflowDecisionResult:
    decision_id: str
    target_type: str
    target_id: str
    selected_action: str
    status: str
    confidence: str
    reason_zh: str
    decision_path: Path
    report_path: Path
    next_actions: list[dict[str, Any]]


@dataclass(frozen=True)
class DynamicWorkflowStatus:
    decision_id: str | None
    path: Path | None
    exists: bool
    status: str | None
    selected_action: str | None
    target_type: str | None
    target_id: str | None
    counts: dict[str, int]


@dataclass(frozen=True)
class DynamicWorkflowOverrideResult:
    decision_id: str
    status: str
    path: Path
    reviewer: str
    reason_zh: str


def dynamic_decision_path(config: ProjectConfig, decision_id: str) -> Path:
    _require_decision_id(decision_id)
    return config.dynamic_workflows_root / f"{decision_id}.yaml"


def dynamic_report_path(config: ProjectConfig, decision_id: str) -> Path:
    _require_decision_id(decision_id)
    return config.dynamic_workflows_root / f"{decision_id}_report.md"


def next_dynamic_decision_id(config: ProjectConfig) -> str:
    highest = 0
    if config.dynamic_workflows_root.exists():
        for child in config.dynamic_workflows_root.glob("DW*.yaml"):
            match = DECISION_ID_PATTERN.match(child.stem)
            if match:
                highest = max(highest, int(match.group("number")))
    return f"DW{highest + 1:03d}"


def load_dynamic_policy(
    config: ProjectConfig, policy_file: str | Path | None = None
) -> tuple[dict[str, Any], str]:
    path = _policy_path(config, policy_file)
    if path.exists():
        policy = _read_yaml_mapping(path)
        source = _display_path(config, path)
    else:
        policy = default_dynamic_policy()
        source = "builtin_default"
    errors = validate_dynamic_policy(policy)
    if errors:
        raise DynamicWorkflowError("dynamic workflow policy 校验失败: " + "; ".join(errors))
    return policy, source


def default_dynamic_policy() -> dict[str, Any]:
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_id": "default_dynamic_workflow",
        "description_zh": "保守默认策略：自动建议下一步，但不绕过人工 formal 写入门禁。",
        "automation_mode": "monitored_auto",
        "rules": [
            {
                "rule_id": "formal_write_guard",
                "stop_before_formal_write": {"target_type": "formal_write"},
                "selected_action": "stop_before_formal_write",
                "confidence": "high",
                "reason_zh": "涉及正式写入，动态工作流只能停止并提示人工确认。",
            },
            {
                "rule_id": "paper_missing_metadata",
                "block_if": {"target_type": "paper", "artifact_missing": ["metadata"]},
                "selected_action": "block",
                "confidence": "high",
                "reason_zh": "未找到正式 metadata/P###.yaml，不能启动后续自动链路。",
                "repair_hint_zh": "先通过 metadata gate 创建并确认正式元数据。",
            },
            {
                "rule_id": "campaign_missing_record",
                "block_if": {"target_type": "campaign", "artifact_missing": ["campaign"]},
                "selected_action": "block",
                "confidence": "high",
                "reason_zh": "未找到 campaign 记录，不能启动批量调度。",
                "repair_hint_zh": "先创建 campaign YAML 或导入候选列表。",
            },
            {
                "rule_id": "paper_blocked_workflow_retry",
                "retry_if": {
                    "target_type": "paper",
                    "workflow_status_in": ["blocked", "failed"],
                },
                "selected_action": "retry_workflow",
                "confidence": "medium",
                "reason_zh": "单篇工作流处于失败或阻塞状态，建议按原状态恢复或重试。",
            },
            {
                "rule_id": "paper_needs_review",
                "route_to_review_if": {
                    "target_type": "paper",
                    "workflow_status_in": ["partial", "needs_review", "stopped"],
                },
                "selected_action": "route_to_review",
                "confidence": "medium",
                "reason_zh": "当前论文已有部分结果或需要审阅，建议进入监管队列。",
            },
            {
                "rule_id": "paper_ready_to_run",
                "run_if": {
                    "target_type": "paper",
                    "artifact_exists": ["metadata"],
                    "artifact_missing": ["workflow_run"],
                },
                "selected_action": "run_workflow",
                "confidence": "medium",
                "reason_zh": "已存在正式 metadata，但尚未发现 workflow run，可启动单篇自动链路。",
            },
            {
                "rule_id": "campaign_ready_to_run",
                "run_if": {
                    "target_type": "campaign",
                    "artifact_exists": ["campaign"],
                    "artifact_missing": ["campaign_run"],
                },
                "selected_action": "run_campaign",
                "confidence": "medium",
                "reason_zh": "已存在 campaign 记录，但尚未发现 campaign run，可启动批量受控流水线。",
            },
            {
                "rule_id": "fallback_review",
                "route_to_review_if": {"always": True},
                "selected_action": "route_to_review",
                "confidence": "low",
                "reason_zh": "未命中更明确的自动规则，保守进入人工监管队列。",
            },
        ],
        "future_interfaces": _default_future_interfaces(),
    }


def validate_dynamic_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        errors.append(f"schema_version 必须是 {POLICY_SCHEMA_VERSION}")
    if _is_blank(policy.get("policy_id")):
        errors.append("policy_id 不能为空。")
    rules = policy.get("rules")
    if not isinstance(rules, list) or not rules:
        return errors + ["rules 必须是非空 list。"]

    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules, start=1):
        prefix = f"rules 第 {index} 项"
        if not isinstance(rule, dict):
            errors.append(f"{prefix} 必须是 mapping。")
            continue
        rule_id = str(rule.get("rule_id") or "")
        if not rule_id:
            errors.append(f"{prefix} 缺少 rule_id。")
        elif rule_id in seen_rule_ids:
            errors.append(f"{prefix} rule_id 重复: {rule_id}")
        else:
            seen_rule_ids.add(rule_id)

        condition_keys = [key for key in CONDITION_KEYS if key in rule]
        if len(condition_keys) != 1:
            errors.append(f"{prefix} 必须且只能包含一个条件组: {sorted(CONDITION_KEYS)}")
        else:
            condition = rule.get(condition_keys[0])
            if not isinstance(condition, dict):
                errors.append(f"{prefix}.{condition_keys[0]} 必须是 mapping。")
            else:
                errors.extend(_validate_condition(condition, prefix=f"{prefix}.{condition_keys[0]}"))

        action = rule.get("selected_action")
        if action not in SELECTED_ACTIONS:
            errors.append(f"{prefix} selected_action 不支持: {action}")
        confidence = str(rule.get("confidence") or "unknown")
        if confidence not in CONFIDENCE_LEVELS:
            errors.append(f"{prefix} confidence 不支持: {confidence}")
        if _is_blank(rule.get("reason_zh")):
            errors.append(f"{prefix} 必须提供 reason_zh。")

    future = policy.get("future_interfaces", {})
    if future is not None and not isinstance(future, dict):
        errors.append("future_interfaces 必须是 mapping。")
    return errors


def evaluate_dynamic_workflow(
    config: ProjectConfig,
    target_id: str,
    *,
    target_type: str | None = None,
    trigger: str = "manual",
    policy_file: str | Path | None = None,
) -> DynamicWorkflowDecisionResult:
    resolved_type = infer_target_type(target_id, target_type=target_type)
    policy, policy_source = load_dynamic_policy(config, policy_file=policy_file)
    inputs = _build_inputs(config, resolved_type, target_id, trigger)
    rule, condition_key = _match_rule(policy, inputs)
    if rule is None:
        rule = {
            "rule_id": "no_matching_rule",
            "selected_action": "block",
            "confidence": "low",
            "reason_zh": "没有匹配到动态工作流规则，已按 fail-closed 停止。",
            "repair_hint_zh": "请检查 dynamic_workflow policy 或手动指定后续动作。",
        }
        condition_key = "none"

    decision_id = next_dynamic_decision_id(config)
    selected_action = str(rule["selected_action"])
    status = _status_for_action(selected_action)
    next_actions = _next_actions_for(selected_action, resolved_type, target_id)
    reason_zh = str(rule.get("reason_zh") or "")
    record = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "decision_id": decision_id,
        "created_at": _now(),
        "updated_at": _now(),
        "status": status,
        "trigger": trigger,
        "target": {
            "target_type": resolved_type,
            "target_id": target_id,
        },
        "policy": {
            "policy_id": policy.get("policy_id"),
            "policy_source": policy_source,
            "matched_rule_id": rule.get("rule_id"),
            "matched_condition_group": condition_key,
        },
        "inputs": inputs,
        "selected_action": selected_action,
        "reason_zh": reason_zh,
        "confidence": str(rule.get("confidence") or "unknown"),
        "evidence_level": _evidence_level(selected_action, inputs),
        "blocked_reason_zh": reason_zh if selected_action == "block" else None,
        "repair_hint_zh": rule.get("repair_hint_zh") or _repair_hint_for(selected_action),
        "next_actions": next_actions,
        "formal_write_allowed": False,
        "human_override": {
            "decision": None,
            "reviewer": None,
            "reviewed_at": None,
            "reason_zh": None,
        },
        "future_interfaces": policy.get("future_interfaces") or _default_future_interfaces(),
        "field_explanations_zh": _field_explanations(),
    }
    errors = _validate_decision_mapping(record)
    if errors:
        raise DynamicWorkflowError("dynamic workflow decision 内部校验失败: " + "; ".join(errors))

    path = dynamic_decision_path(config, decision_id)
    _write_yaml(path, record)
    report = _write_report(config, record)
    return DynamicWorkflowDecisionResult(
        decision_id=decision_id,
        target_type=resolved_type,
        target_id=target_id,
        selected_action=selected_action,
        status=status,
        confidence=str(record["confidence"]),
        reason_zh=reason_zh,
        decision_path=path,
        report_path=report,
        next_actions=next_actions,
    )


def validate_dynamic_decisions(config: ProjectConfig, decision_id: str | None = None) -> list[str]:
    paths = [dynamic_decision_path(config, decision_id)] if decision_id else list_dynamic_decisions(config)
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"dynamic workflow decision 不存在: {path}")
            continue
        data = _read_yaml_mapping(path)
        errors.extend(f"{path.name}: {error}" for error in _validate_decision_mapping(data))
    return errors


def dynamic_workflow_status(config: ProjectConfig, decision_id: str | None = None) -> DynamicWorkflowStatus:
    if decision_id:
        path = dynamic_decision_path(config, decision_id)
        if not path.exists():
            return DynamicWorkflowStatus(decision_id, path, False, None, None, None, None, {})
        data = _read_yaml_mapping(path)
        target = data.get("target") if isinstance(data.get("target"), dict) else {}
        return DynamicWorkflowStatus(
            decision_id=decision_id,
            path=path,
            exists=True,
            status=str(data.get("status") or ""),
            selected_action=str(data.get("selected_action") or ""),
            target_type=str(target.get("target_type") or ""),
            target_id=str(target.get("target_id") or ""),
            counts={str(data.get("status") or "unknown"): 1},
        )

    counts: dict[str, int] = {}
    latest: Path | None = None
    for path in list_dynamic_decisions(config):
        latest = path
        data = _read_yaml_mapping(path)
        status = str(data.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return DynamicWorkflowStatus(
        decision_id=latest.stem if latest else None,
        path=latest,
        exists=latest is not None,
        status=None,
        selected_action=None,
        target_type=None,
        target_id=None,
        counts=counts,
    )


def override_dynamic_decision(
    config: ProjectConfig,
    decision_id: str,
    *,
    decision: str,
    reviewer: str,
    reason_zh: str,
) -> DynamicWorkflowOverrideResult:
    if decision not in REVIEW_DECISIONS:
        raise DynamicWorkflowError(f"review decision 不支持: {decision}")
    if _is_blank(reviewer):
        raise DynamicWorkflowError("reviewer 不能为空。")
    if _is_blank(reason_zh):
        raise DynamicWorkflowError("reason_zh 不能为空。")
    path = dynamic_decision_path(config, decision_id)
    if not path.exists():
        raise DynamicWorkflowError(f"dynamic workflow decision 不存在: {decision_id}")
    data = _read_yaml_mapping(path)
    data["status"] = decision
    data["updated_at"] = _now()
    data["human_override"] = {
        "decision": decision,
        "reviewer": reviewer,
        "reviewed_at": _now(),
        "reason_zh": reason_zh,
    }
    data["formal_write_allowed"] = False
    errors = _validate_decision_mapping(data)
    if errors:
        raise DynamicWorkflowError("dynamic workflow decision 校验失败: " + "; ".join(errors))
    _write_yaml(path, data)
    _write_report(config, data)
    return DynamicWorkflowOverrideResult(
        decision_id=decision_id,
        status=decision,
        path=path,
        reviewer=reviewer,
        reason_zh=reason_zh,
    )


def list_dynamic_decisions(config: ProjectConfig) -> list[Path]:
    if not config.dynamic_workflows_root.exists():
        return []
    return sorted(
        path
        for path in config.dynamic_workflows_root.glob("DW*.yaml")
        if DECISION_ID_PATTERN.match(path.stem)
    )


def infer_target_type(target_id: str, *, target_type: str | None = None) -> str:
    if target_type:
        if target_type not in TARGET_TYPES:
            raise DynamicWorkflowError(f"target_type 不支持: {target_type}")
        return target_type
    if PAPER_ID_PATTERN.match(target_id):
        return "paper"
    if CAMPAIGN_ID_PATTERN.match(target_id):
        return "campaign"
    if target_id in {"formal", "formal_write", "formal-write"}:
        return "formal_write"
    raise DynamicWorkflowError("无法根据 target_id 推断 target_type，请使用 --target-type。")


def _build_inputs(config: ProjectConfig, target_type: str, target_id: str, trigger: str) -> dict[str, Any]:
    artifacts = _artifact_snapshot(config, target_type, target_id)
    workflow = workflow_status(config, target_id) if target_type == "paper" else None
    score = score_status(config, target_id) if target_type == "paper" else None
    campaign_status_value = None
    campaign_run_status = None
    if target_type == "campaign" and CAMPAIGN_ID_PATTERN.match(target_id):
        path = campaign_path(config, target_id)
        if path.exists():
            campaign_status_value = _read_yaml_mapping(path).get("status")
        run_path = campaign_run_path(config, target_id)
        if run_path.exists():
            campaign_run_status = _read_yaml_mapping(run_path).get("run_status")
    return {
        "target_type": target_type,
        "target_id": target_id,
        "trigger": trigger,
        "automation_mode": config.dynamic_workflow_automation_mode,
        "min_confidence_to_run": config.dynamic_workflow_min_confidence_to_run,
        "llm_suggestions_enabled": config.dynamic_workflow_allow_llm_suggestions,
        "artifacts": artifacts,
        "workflow_status": workflow.workflow_status if workflow else None,
        "workflow_run_id": workflow.run_id if workflow else None,
        "campaign_status": campaign_status_value,
        "campaign_run_status": campaign_run_status,
        "score_confidence": score.score_confidence if score else None,
        "ai_read_priority_score_10": score.ai_read_priority_score_10 if score else None,
    }


def _artifact_snapshot(config: ProjectConfig, target_type: str, target_id: str) -> dict[str, bool]:
    artifacts = {
        "metadata": False,
        "source_ledger": False,
        "reading_note": False,
        "visual_candidates": False,
        "asset_manifest": False,
        "scoring": False,
        "workflow_run": False,
        "workflow_report": False,
        "campaign": False,
        "campaign_run": False,
        "review_queue": False,
        "metadata_requests": False,
    }
    if target_type == "paper" and PAPER_ID_PATTERN.match(target_id):
        artifacts.update(
            {
                "metadata": (config.metadata_root / f"{target_id}.yaml").exists(),
                "source_ledger": source_record_path(config, target_id).exists(),
                "reading_note": note_path(config, target_id).exists(),
                "visual_candidates": visual_candidate_path(config, target_id).exists(),
                "asset_manifest": asset_manifest_path(config, target_id).exists(),
                "scoring": scoring_path(config, target_id).exists(),
            }
        )
        workflow = workflow_status(config, target_id)
        artifacts["workflow_run"] = workflow.exists
        artifacts["workflow_report"] = bool(workflow.report_path and workflow.report_path.exists())
    elif target_type == "campaign" and CAMPAIGN_ID_PATTERN.match(target_id):
        artifacts.update(
            {
                "campaign": campaign_path(config, target_id).exists(),
                "campaign_run": campaign_run_path(config, target_id).exists(),
                "review_queue": campaign_review_queue_path(config, target_id).exists(),
                "metadata_requests": campaign_metadata_requests_path(config, target_id).exists(),
            }
        )
    return artifacts


def _match_rule(policy: dict[str, Any], inputs: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    for rule in policy.get("rules", []) or []:
        if not isinstance(rule, dict):
            continue
        condition_key = next((key for key in CONDITION_KEYS if key in rule), None)
        if not condition_key:
            continue
        condition = rule.get(condition_key)
        if isinstance(condition, dict) and _condition_matches(condition, inputs):
            return rule, condition_key
    return None, None


def _condition_matches(condition: dict[str, Any], inputs: dict[str, Any]) -> bool:
    if condition.get("always") is True:
        return True
    if condition.get("target_type") and condition["target_type"] != inputs.get("target_type"):
        return False
    if condition.get("target_id_prefix") and not str(inputs.get("target_id") or "").startswith(
        str(condition["target_id_prefix"])
    ):
        return False
    if condition.get("trigger") and condition["trigger"] != inputs.get("trigger"):
        return False
    if condition.get("trigger_in") and inputs.get("trigger") not in condition["trigger_in"]:
        return False
    artifacts = inputs.get("artifacts") if isinstance(inputs.get("artifacts"), dict) else {}
    for key in _as_list(condition.get("artifact_exists")):
        if artifacts.get(str(key)) is not True:
            return False
    for key in _as_list(condition.get("artifact_missing")):
        if artifacts.get(str(key)) is True:
            return False
    workflow_values = _as_list(condition.get("workflow_status_in"))
    if workflow_values and inputs.get("workflow_status") not in workflow_values:
        return False
    campaign_values = _as_list(condition.get("campaign_status_in"))
    if campaign_values and inputs.get("campaign_run_status") not in campaign_values and inputs.get(
        "campaign_status"
    ) not in campaign_values:
        return False
    score_values = _as_list(condition.get("score_confidence_in"))
    if score_values and inputs.get("score_confidence") not in score_values:
        return False
    if condition.get("min_priority_score") is not None:
        score = inputs.get("ai_read_priority_score_10")
        if not isinstance(score, int) or score < int(condition["min_priority_score"]):
            return False
    return True


def _validate_condition(condition: dict[str, Any], *, prefix: str) -> list[str]:
    errors: list[str] = []
    for key in condition:
        if key not in CONDITION_FIELDS:
            errors.append(f"{prefix} 条件字段不支持: {key}")
    if "target_type" in condition and condition["target_type"] not in TARGET_TYPES:
        errors.append(f"{prefix}.target_type 不支持: {condition['target_type']}")
    for list_key in [
        "trigger_in",
        "artifact_exists",
        "artifact_missing",
        "workflow_status_in",
        "campaign_status_in",
        "score_confidence_in",
    ]:
        if list_key in condition and not isinstance(condition[list_key], list):
            errors.append(f"{prefix}.{list_key} 必须是 list。")
    if "min_priority_score" in condition:
        try:
            value = int(condition["min_priority_score"])
        except (TypeError, ValueError):
            errors.append(f"{prefix}.min_priority_score 必须是整数。")
        else:
            if value < 0 or value > 10:
                errors.append(f"{prefix}.min_priority_score 必须在 0 到 10 之间。")
    return errors


def _validate_decision_mapping(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"schema_version 必须是 {DECISION_SCHEMA_VERSION}")
    decision_id = str(data.get("decision_id") or "")
    if not DECISION_ID_PATTERN.match(decision_id):
        errors.append(f"decision_id 必须匹配 DW###: {decision_id}")
    if data.get("status") not in DECISION_STATUSES:
        errors.append(f"status 不支持: {data.get('status')}")
    target = data.get("target")
    if not isinstance(target, dict):
        errors.append("target 必须是 mapping。")
    else:
        if target.get("target_type") not in TARGET_TYPES:
            errors.append(f"target.target_type 不支持: {target.get('target_type')}")
        if _is_blank(target.get("target_id")):
            errors.append("target.target_id 不能为空。")
    if data.get("selected_action") not in SELECTED_ACTIONS:
        errors.append(f"selected_action 不支持: {data.get('selected_action')}")
    if _is_blank(data.get("reason_zh")):
        errors.append("reason_zh 不能为空。")
    if data.get("confidence") not in CONFIDENCE_LEVELS:
        errors.append(f"confidence 不支持: {data.get('confidence')}")
    if data.get("formal_write_allowed") is not False:
        errors.append("formal_write_allowed 必须为 false，不能绕过 formal write gate。")
    if not isinstance(data.get("inputs"), dict):
        errors.append("inputs 必须是 mapping。")
    if not isinstance(data.get("next_actions"), list):
        errors.append("next_actions 必须是 list。")
    if not isinstance(data.get("human_override"), dict):
        errors.append("human_override 必须是 mapping。")
    if not isinstance(data.get("future_interfaces"), dict):
        errors.append("future_interfaces 必须是 mapping。")
    if data.get("selected_action") == "block" and _is_blank(data.get("blocked_reason_zh")):
        errors.append("block 决策必须填写 blocked_reason_zh。")
    if data.get("selected_action") == "stop_before_formal_write":
        next_actions = data.get("next_actions") if isinstance(data.get("next_actions"), list) else []
        if not any(
            isinstance(action, dict) and action.get("requires_human_confirmation") is True
            for action in next_actions
        ):
            errors.append("stop_before_formal_write 必须给出人工确认 next action。")
    for index, action in enumerate(data.get("next_actions") or [], start=1):
        if not isinstance(action, dict):
            errors.append(f"next_actions 第 {index} 项必须是 mapping。")
            continue
        command = str(action.get("command") or "")
        if command.startswith("rsa formal") and action.get("requires_human_confirmation") is not True:
            errors.append(f"next_actions 第 {index} 项 formal 命令必须 requires_human_confirmation=true。")
    return errors


def _next_actions_for(action: str, target_type: str, target_id: str) -> list[dict[str, Any]]:
    if action == "run_workflow":
        return [
            {
                "action_type": "run_cli",
                "command": f"rsa workflow run {target_id}",
                "description_zh": "启动单篇论文自动链路，产出 review packet。",
                "requires_human_confirmation": False,
            }
        ]
    if action == "retry_workflow":
        return [
            {
                "action_type": "run_cli",
                "command": f"rsa workflow resume {target_id}",
                "description_zh": "从 workflow 当前状态恢复或重试。",
                "requires_human_confirmation": False,
            }
        ]
    if action == "run_campaign":
        return [
            {
                "action_type": "run_cli",
                "command": f"rsa campaign run {target_id}",
                "description_zh": "启动 campaign 级受控流水线。",
                "requires_human_confirmation": False,
            }
        ]
    if action == "route_to_review":
        if target_type == "campaign":
            command = f"rsa campaign review-queue {target_id}"
        elif target_type == "paper":
            command = f"rsa workflow report {target_id}"
        else:
            command = "rsa formal status"
        return [
            {
                "action_type": "review",
                "command": command,
                "description_zh": "进入人工监管视图或生成可审阅报告。",
                "requires_human_confirmation": False,
            }
        ]
    if action == "stop_before_formal_write":
        return [
            {
                "action_type": "formal_gate",
                "command": "rsa formal ... --human-confirmed --confirmed-by <name>",
                "description_zh": "涉及正式记录写入，必须由人工显式确认后执行。",
                "requires_human_confirmation": True,
                "enabled_for_auto_run": False,
            }
        ]
    if action == "skip":
        return [
            {
                "action_type": "skip",
                "description_zh": "当前目标无需自动推进，保留状态记录。",
                "requires_human_confirmation": False,
            }
        ]
    return []


def _write_report(config: ProjectConfig, data: dict[str, Any]) -> Path:
    decision_id = str(data["decision_id"])
    target = data.get("target") if isinstance(data.get("target"), dict) else {}
    inputs = data.get("inputs") if isinstance(data.get("inputs"), dict) else {}
    artifacts = inputs.get("artifacts") if isinstance(inputs.get("artifacts"), dict) else {}
    artifact_rows = [
        f"| `{name}` | `{value}` |"
        for name, value in sorted(artifacts.items())
    ] or ["| - | - |"]
    action_rows = []
    for action in data.get("next_actions", []) or []:
        if not isinstance(action, dict):
            continue
        action_rows.append(
            "| "
            + " | ".join(
                [
                    f"`{action.get('action_type', '-')}`",
                    f"`{action.get('command', '-')}`",
                    str(action.get("description_zh") or "-"),
                    f"`{action.get('requires_human_confirmation', False)}`",
                ]
            )
            + " |"
        )
    if not action_rows:
        action_rows.append("| - | - | - | - |")
    report = f"""# Dynamic Workflow Decision: {decision_id}

## 概览

- `decision_id`: `{decision_id}`
- `status`: `{data.get("status")}`
- `target_type`: `{target.get("target_type")}`
- `target_id`: `{target.get("target_id")}`
- `selected_action`: `{data.get("selected_action")}`
- `confidence`: `{data.get("confidence")}`
- `evidence_level`: `{data.get("evidence_level")}`
- `formal_write_allowed`: `{data.get("formal_write_allowed")}`

## 中文理由

{data.get("reason_zh") or "-"}

## 修复或监管提示

{data.get("repair_hint_zh") or "-"}

## 下一步动作

| action_type | command | 中文说明 | requires_human_confirmation |
|---|---|---|---|
{chr(10).join(action_rows)}

## 输入状态快照

| artifact | exists |
|---|---|
{chr(10).join(artifact_rows)}

## 写入边界

本决策只允许生成下一步建议和审计记录，不允许直接写入 `metadata/`、`literature_map.md` 或 `agent_research_notes.md`。
任何 formal 写入必须继续通过 `rsa formal ... --human-confirmed`。
"""
    path = dynamic_report_path(config, decision_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path


def _policy_path(config: ProjectConfig, policy_file: str | Path | None) -> Path:
    if policy_file is None:
        return config.dynamic_workflow_default_policy
    path = Path(policy_file)
    if path.is_absolute():
        return path
    return config.root / path


def _status_for_action(action: str) -> str:
    if action == "block":
        return "blocked"
    if action in {"route_to_review", "stop_before_formal_write"}:
        return "needs_review"
    return "proposed"


def _repair_hint_for(action: str) -> str:
    if action == "block":
        return "请补齐缺失输入或修复策略后重新 evaluate。"
    if action == "route_to_review":
        return "请在 review workspace 或对应 report 中监管该项。"
    if action == "stop_before_formal_write":
        return "请人工审阅后通过 formal 命令显式确认。"
    if action == "retry_workflow":
        return "请确认上一次失败原因已修复，再运行建议命令。"
    return "可按 next_actions 中的建议继续推进。"


def _evidence_level(action: str, inputs: dict[str, Any]) -> str:
    if action == "stop_before_formal_write":
        return "policy_guard"
    artifacts = inputs.get("artifacts") if isinstance(inputs.get("artifacts"), dict) else {}
    if any(artifacts.values()):
        return "state_snapshot"
    return "partial_state_snapshot"


def _default_future_interfaces() -> dict[str, str]:
    return {
        "llm_suggestion_adapter": "reserved",
        "learned_policy_adapter": "reserved",
        "web_review_adapter": "reserved",
        "advanced_signal_adapter": "reserved",
    }


def _field_explanations() -> dict[str, str]:
    return {
        "decision_id": "动态工作流决策记录的稳定编号。",
        "selected_action": "机器根据当前状态建议的下一步动作，不等于已执行。",
        "reason_zh": "中文决策理由，供用户监管。",
        "confidence": "规则匹配置信度，不是学术结论置信度。",
        "formal_write_allowed": "是否允许直接正式写入；Phase 17 必须为 false。",
        "human_override": "人工复核或覆盖记录，便于后续追溯。",
    }


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise DynamicWorkflowError(f"{path} 必须是 YAML mapping。")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _require_decision_id(decision_id: str) -> None:
    if not DECISION_ID_PATTERN.match(decision_id):
        raise DynamicWorkflowError(f"decision_id 必须匹配 DW###: {decision_id}")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
