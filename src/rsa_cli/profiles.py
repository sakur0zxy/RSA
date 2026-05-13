from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REQUIRED_PROFILE_FIELDS: dict[str, type] = {
    "topic_id": str,
    "topic_name": str,
    "core_keywords": list,
    "priority_questions": list,
    "important_metrics": list,
    "preferred_sources": list,
    "exclude_scope": list,
    "grade_rules": dict,
    "required_outputs": list,
}


def load_profile(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"profile 文件不存在: {path}"]
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, [f"profile YAML 无效: {path}: {exc}"]
    if not isinstance(loaded, dict):
        return None, [f"profile 必须是 YAML mapping: {path}"]
    return loaded, []


def _validate_required_fields(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field, expected_type in REQUIRED_PROFILE_FIELDS.items():
        if field not in profile:
            errors.append(f"缺少必填字段: {field}")
            continue
        value = profile[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"{field} 必须是 {expected_type.__name__}，当前是 {type(value).__name__}"
            )
            continue
        if expected_type is str and not value.strip():
            errors.append(f"{field} 不能为空")
        if expected_type is list:
            if not value:
                errors.append(f"{field} 至少需要一项")
            elif any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{field} 的每一项都必须是非空字符串")
        if expected_type is dict and not value:
            errors.append(f"{field} 至少需要一条规则")
    return errors


def _validate_grade_rules(profile: dict[str, Any]) -> list[str]:
    grade_rules = profile.get("grade_rules")
    if not isinstance(grade_rules, dict):
        return []

    errors: list[str] = []
    for priority in ["A", "B", "C", "Reject"]:
        if priority not in grade_rules:
            errors.append(f"grade_rules 缺少候选优先级: {priority}")
            continue
        rule = grade_rules[priority]
        if not isinstance(rule, dict):
            errors.append(f"grade_rules.{priority} 必须是 mapping")
            continue
        criteria = rule.get("criteria", [])
        description = rule.get("description", "")
        if not description:
            errors.append(f"grade_rules.{priority}.description 不能为空")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"grade_rules.{priority}.criteria 必须是非空 list")
    return errors


def validate_topic_profile(path: Path | str) -> list[str]:
    profile_path = Path(path)
    profile, errors = load_profile(profile_path)
    if profile is None:
        return errors
    errors.extend(_validate_required_fields(profile))
    errors.extend(_validate_grade_rules(profile))
    return errors
