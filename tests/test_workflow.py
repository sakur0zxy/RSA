from pathlib import Path

import yaml

from rsa_cli.config import load_project_config
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.workflow import (
    STEP_IDS,
    build_workflow_run_skeleton,
    next_workflow_run_id,
    validate_workflow_run,
    workflow_paper_dir,
    workflow_report_path,
    workflow_run_path,
    write_workflow_run,
)


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    return config


def test_workflow_schema_paths_and_skeleton(tmp_path):
    config = prepare_project(tmp_path)
    data = build_workflow_run_skeleton(
        "P001",
        run_id="RUN-001",
        campaign_id="C001",
        campaign_item_id="CI001",
    )
    path = write_workflow_run(config, "P001", "RUN-001", data)

    assert config.workflows_root == tmp_path / "01_literature" / "workflows"
    assert workflow_paper_dir(config, "P001") == config.workflows_root / "P001"
    assert path == workflow_run_path(config, "P001", "RUN-001")
    assert workflow_report_path(config, "P001", "RUN-001").name == "RUN-001_report.md"
    assert validate_workflow_run(config, "P001", "RUN-001") == []
    assert [step["step_id"] for step in data["steps"]] == STEP_IDS
    assert data["campaign_id"] == "C001"
    assert data["campaign_item_id"] == "CI001"


def test_next_workflow_run_id_increments(tmp_path):
    config = prepare_project(tmp_path)
    write_workflow_run(
        config,
        "P001",
        "RUN-001",
        build_workflow_run_skeleton("P001", run_id="RUN-001"),
    )

    assert next_workflow_run_id(config, "P001") == "RUN-002"


def test_workflow_validation_requires_reason_fields(tmp_path):
    config = prepare_project(tmp_path)
    data = build_workflow_run_skeleton("P001", run_id="RUN-001")
    data["steps"][0]["status"] = "skipped"
    data["steps"][0]["skipped_reason_zh"] = None
    path = write_workflow_run(config, "P001", "RUN-001", data)

    errors = validate_workflow_run(config, "P001", "RUN-001")

    assert path.exists()
    assert any("skipped_reason_zh" in error for error in errors)


def test_workflow_validation_preserves_future_interfaces(tmp_path):
    config = prepare_project(tmp_path)
    data = build_workflow_run_skeleton("P001", run_id="RUN-001")
    data["future_interfaces"]["llm_visual_analysis"]["status"] = "completed"
    write_workflow_run(config, "P001", "RUN-001", data)

    errors = validate_workflow_run(config, "P001", "RUN-001")

    assert any("llm_visual_analysis.status" in error for error in errors)


def test_workflow_yaml_is_utf8_and_readable(tmp_path):
    config = prepare_project(tmp_path)
    write_workflow_run(
        config,
        "P001",
        "RUN-001",
        build_workflow_run_skeleton("P001", run_id="RUN-001"),
    )

    data = yaml.safe_load(
        workflow_run_path(config, "P001", "RUN-001").read_text(encoding="utf-8")
    )

    assert "人工确认" in data["formal_record_policy_zh"]
    assert data["future_interfaces"]["advanced_analysis"]["curve_extraction"]["status"] == "not_run"
