from pathlib import Path

import pytest
import yaml

from rsa_cli.campaign import create_campaign
from rsa_cli.config import load_project_config
from rsa_cli.dynamic_workflow import (
    DynamicWorkflowError,
    evaluate_dynamic_workflow,
    override_dynamic_decision,
    validate_dynamic_decisions,
    validate_dynamic_policy,
)
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton


def prepare_project(root: Path):
    config = load_project_config(root)
    create_literature_skeleton(config)
    return config


def add_metadata(config):
    return write_metadata_record(
        config,
        {
            "title": "Dynamic Workflow Paper",
            "authors": ["Ada Lovelace"],
            "year": "2026",
            "venue": "Journal of Tests",
            "doi": "10.1234/dynamic",
            "official_url": None,
            "source_reliability": "publisher",
            "decision": "include",
            "decision_reason": "用于测试动态工作流。",
            "last_checked": "2026-06-01",
            "pdf_status": "not_acquired",
            "local_pdf": None,
            "assets": [],
            "topic_profile": "test_profile",
            "priority_questions": ["Q1"],
            "used_for": ["workflow"],
            "research_roles": ["method"],
            "notes": "人工备注",
        },
        human_confirmed=True,
        confirmed_by="zxy",
    )


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_dynamic_workflow_runs_paper_when_metadata_exists(tmp_path):
    config = prepare_project(tmp_path)
    add_metadata(config)

    result = evaluate_dynamic_workflow(config, "P001")

    data = read_yaml(result.decision_path)
    assert result.selected_action == "run_workflow"
    assert result.status == "proposed"
    assert data["formal_write_allowed"] is False
    assert data["inputs"]["artifacts"]["metadata"] is True
    assert data["next_actions"][0]["command"] == "rsa workflow run P001"
    assert result.report_path.exists()
    assert validate_dynamic_decisions(config, "DW001") == []


def test_dynamic_workflow_blocks_missing_metadata_without_fake_run(tmp_path):
    config = prepare_project(tmp_path)

    result = evaluate_dynamic_workflow(config, "P001")

    data = read_yaml(result.decision_path)
    assert result.selected_action == "block"
    assert result.status == "blocked"
    assert data["blocked_reason_zh"]
    assert data["inputs"]["artifacts"]["metadata"] is False
    assert data["formal_write_allowed"] is False


def test_dynamic_workflow_stops_before_formal_write(tmp_path):
    config = prepare_project(tmp_path)

    result = evaluate_dynamic_workflow(
        config,
        "formal_write",
        target_type="formal_write",
        trigger="formal_write_request",
    )

    data = read_yaml(result.decision_path)
    assert result.selected_action == "stop_before_formal_write"
    assert result.status == "needs_review"
    assert data["formal_write_allowed"] is False
    assert data["next_actions"][0]["requires_human_confirmation"] is True
    assert "rsa formal" in data["next_actions"][0]["command"]


def test_dynamic_workflow_runs_campaign_when_record_exists(tmp_path):
    config = prepare_project(tmp_path)
    create_campaign(
        config,
        name_zh="动态工作流 campaign",
        objective_zh="验证 Phase 17 campaign 分支。",
        created_by="zxy",
    )

    result = evaluate_dynamic_workflow(config, "C001")

    data = read_yaml(result.decision_path)
    assert result.selected_action == "run_campaign"
    assert data["inputs"]["artifacts"]["campaign"] is True
    assert data["next_actions"][0]["command"] == "rsa campaign run C001"


def test_dynamic_workflow_rejects_invalid_policy_before_writing(tmp_path):
    config = prepare_project(tmp_path)
    add_metadata(config)
    policy = tmp_path / "bad_policy.yaml"
    policy.write_text(
        yaml.safe_dump(
            {
                "schema_version": "phase17-dynamic-policy-v1",
                "policy_id": "bad",
                "rules": [
                    {
                        "rule_id": "bad_rule",
                        "unknown_if": {"target_type": "paper"},
                        "selected_action": "run_workflow",
                        "confidence": "medium",
                        "reason_zh": "错误策略。",
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(DynamicWorkflowError, match="policy 校验失败"):
        evaluate_dynamic_workflow(config, "P001", policy_file=policy)
    assert list(config.dynamic_workflows_root.glob("DW*.yaml")) == []


def test_dynamic_workflow_human_override_is_audited(tmp_path):
    config = prepare_project(tmp_path)
    add_metadata(config)
    evaluate_dynamic_workflow(config, "P001")

    result = override_dynamic_decision(
        config,
        "DW001",
        decision="accepted",
        reviewer="zxy",
        reason_zh="已确认可以继续执行建议动作。",
    )

    data = read_yaml(result.path)
    assert result.status == "accepted"
    assert data["status"] == "accepted"
    assert data["human_override"]["reviewer"] == "zxy"
    assert data["formal_write_allowed"] is False
    assert validate_dynamic_decisions(config, "DW001") == []


def test_default_dynamic_policy_schema_is_valid(tmp_path):
    config = prepare_project(tmp_path)

    policy = read_yaml(config.dynamic_workflow_default_policy)

    assert validate_dynamic_policy(policy) == []
    assert policy["future_interfaces"]["llm_suggestion_adapter"] == "reserved"
