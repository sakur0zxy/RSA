from pathlib import Path

import pytest
import yaml

from rsa_cli.assets import add_source_record
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.workflow import (
    STEP_IDS,
    build_workflow_run_skeleton,
    next_workflow_run_id,
    resume_workflow,
    run_workflow,
    stop_workflow,
    validate_workflow_run,
    workflow_status,
    workflow_paper_dir,
    workflow_report_path,
    workflow_run_path,
    write_workflow_run,
)


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    return config


def metadata_values(local_pdf=None, pdf_status="authorized") -> dict:
    return {
        "title": "Workflow Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/workflow",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试 Phase 10 workflow。",
        "last_checked": "2026-05-21",
        "pdf_status": pdf_status,
        "local_pdf": local_pdf,
        "assets": [],
        "topic_profile": "demo_topic",
        "priority_questions": ["Q1"],
        "used_for": ["workflow"],
        "research_roles": ["method"],
        "notes": "人工备注",
    }


def prepare_workflow_project(tmp_path: Path):
    config = prepare_project(tmp_path)
    local = tmp_path / ".rsa" / "local.yaml"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(
        """
reading_draft:
  llm:
    provider: mock
    model: mock-reading-draft
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    source = tmp_path / "workflow-source.pdf"
    source.write_text(
        (
            "This paper studies gapped aperture SAR reconstruction. "
            "The method includes experiment result comparison and reports metrics. "
        )
        * 8,
        encoding="utf-8",
    )
    write_metadata_record(
        config,
        metadata_values(local_pdf=str(source)),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="authorized",
        source_type="pdf",
        license_note="用户已授权本地科研阅读。",
        added_by="zxy",
    )
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


def test_run_workflow_generates_review_packet_with_skipped_visual(tmp_path):
    config = prepare_workflow_project(tmp_path)

    result = run_workflow(
        config,
        "P001",
        campaign_id="C001",
        campaign_item_id="CI001",
        skip_steps=["acquisition", "visual_extraction"],
    )
    data = yaml.safe_load(result.run_path.read_text(encoding="utf-8"))

    assert result.workflow_status == "needs_review"
    assert result.report_path.exists()
    assert data["campaign_id"] == "C001"
    assert data["campaign_item_id"] == "CI001"
    assert data["steps"][0]["status"] == "skipped"
    assert data["steps"][1]["status"] == "needs_review"
    assert data["steps"][2]["status"] == "skipped"
    assert data["steps"][3]["status"] == "completed"
    assert data["steps"][4]["artifacts"]["workflow_report"].endswith("RUN-001_report.md")
    assert "formal record" in result.report_path.read_text(encoding="utf-8")


def test_workflow_blocks_when_reading_source_missing(tmp_path):
    config = prepare_project(tmp_path)
    local = tmp_path / ".rsa" / "local.yaml"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(
        """
reading_draft:
  llm:
    provider: mock
    model: mock-reading-draft
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    write_metadata_record(
        config,
        metadata_values(pdf_status="not_acquired"),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    result = run_workflow(config, "P001", skip_steps=["acquisition"])
    data = yaml.safe_load(result.run_path.read_text(encoding="utf-8"))

    assert result.workflow_status == "blocked"
    assert data["steps"][1]["status"] == "blocked"
    assert data["steps"][1]["blocked_reason_zh"]
    assert result.report_path.exists()


def test_resume_reruns_completed_step_when_artifact_missing(tmp_path):
    config = prepare_workflow_project(tmp_path)
    result = run_workflow(
        config,
        "P001",
        skip_steps=["acquisition", "visual_extraction"],
    )
    scoring_path = config.scores_root / "P001_scoring.yaml"
    scoring_path.unlink()

    resumed = resume_workflow(config, "P001")

    assert resumed.workflow_status == "needs_review"
    assert scoring_path.exists()
    assert validate_workflow_run(config, "P001", result.run_id) == []


def test_stop_prevents_automatic_resume_without_explicit_step(tmp_path):
    config = prepare_workflow_project(tmp_path)
    run_workflow(config, "P001", skip_steps=["acquisition", "visual_extraction"])

    stopped = stop_workflow(config, "P001", reason_zh="用户检查中，暂停自动推进。")
    status = workflow_status(config, "P001")

    assert stopped.workflow_status == "stopped"
    assert status.workflow_status == "stopped"
    with pytest.raises(Exception) as exc:
        resume_workflow(config, "P001")
    assert "stop" in str(exc.value)
