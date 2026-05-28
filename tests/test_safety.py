from __future__ import annotations

from pathlib import Path

import yaml

from rsa_cli.campaign import (
    create_campaign,
    ensure_metadata_intake_requests,
    generate_formal_write_requests,
    generate_review_queue,
    import_campaign_items,
)
from rsa_cli.cli import main
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.safety import (
    campaign_safety_record_path,
    check_campaign_safety,
    check_paper_safety,
    safety_record_path,
    safety_status,
    validate_safety_record,
)
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(title: str = "Safety Paper") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/safety",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试 Phase 13 写作安全检查。",
        "last_checked": "2026-05-28",
        "pdf_status": "local",
        "local_pdf": "01_literature/pdfs/P001/source.pdf",
        "assets": [],
        "topic_profile": "demo_topic",
        "priority_questions": ["Q1"],
        "used_for": ["写作安全测试"],
        "research_roles": ["method"],
        "notes": "人工备注",
    }


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    source = tmp_path / "01_literature" / "pdfs" / "P001" / "source.pdf"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("authorized source", encoding="utf-8")
    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    write_reading_note(config)
    return config


def write_reading_note(config, *, weak_claim: bool = False) -> None:
    claim = {
        "claim_zh": "论文提出一种可用于间断孔径 SAR 的重建方法，并给出实验结果。",
        "evidence_page": 2,
        "evidence_section": "Method",
        "evidence_snippet": "method and experiment result",
        "needs_human_check": True,
    }
    if not weak_claim:
        claim["source_chunk_id"] = "CH001"
    frontmatter = {
        "paper_id": "P001",
        "metadata": "01_literature/metadata/P001.yaml",
        "note_status": "ready_for_review",
        "source_file": "01_literature/pdfs/P001/source.pdf",
        "authorization": "local",
        "source_grounded_claims": [claim],
        "short_quotes": [
            {
                "quote": "method and experiment result",
                "page": 2,
                "section": "Method",
                "reason_zh": "用于定位原文。",
            }
        ],
        "uncertain_points_zh": [],
        "asset_suggestions": [],
        "note_integration_requests": [],
        "human_confirmed": False,
    }
    note = config.notes_root / "P001_reading_note.md"
    note.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "## Agent 摘要\n\n该草稿只进入 staging/review。\n",
        encoding="utf-8",
    )


def test_paper_safety_check_writes_claim_refs_and_report(tmp_path):
    config = prepare_project(tmp_path)

    result = check_paper_safety(config, "P001")
    data = yaml.safe_load(result.path.read_text(encoding="utf-8"))

    assert config.safety_root == tmp_path / "01_literature" / "safety"
    assert result.safety_status == "passed"
    assert result.claim_count == 2
    assert data["schema_version"] == "phase13-safety-v1"
    assert data["citation_review_version"] == "claim-ref-v1"
    assert data["claim_refs"][0]["source_chunk_id"] == "CH001"
    assert data["future_interfaces"]["llm_claim_review"]["status"] == "not_run"
    assert "不是 formal approval" in result.report_path.read_text(encoding="utf-8")
    assert validate_safety_record(config, "P001") == []


def test_weak_claim_trace_becomes_needs_review_not_fake_success(tmp_path):
    config = prepare_project(tmp_path)
    write_reading_note(config, weak_claim=True)

    result = check_paper_safety(config, "P001")
    data = yaml.safe_load(result.path.read_text(encoding="utf-8"))

    assert result.safety_status == "needs_review"
    assert any("source_chunk_id" in warning for warning in data["warnings_zh"])
    assert data["claim_refs"][0]["status"] == "needs_review"
    assert validate_safety_record(config, "P001") == []


def test_safety_validate_and_status_are_read_only(tmp_path):
    config = prepare_project(tmp_path)
    check_paper_safety(config, "P001")
    path = safety_record_path(config, "P001")
    before = path.read_bytes()

    assert validate_safety_record(config, "P001") == []
    status = safety_status(config, "P001")

    assert status.exists is True
    assert status.safety_status == "passed"
    assert path.read_bytes() == before


def test_missing_reading_note_blocks_safety_check(tmp_path):
    config = prepare_project(tmp_path)
    (config.notes_root / "P001_reading_note.md").unlink()

    result = check_paper_safety(config, "P001")
    data = yaml.safe_load(result.path.read_text(encoding="utf-8"))

    assert result.safety_status == "blocked"
    assert any(check["check_id"] == "reading_note_valid" for check in data["checks"])
    assert any("reading note" in warning for warning in data["warnings_zh"])


def test_campaign_safety_monitors_formal_request_boundary(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="安全监测 campaign",
        objective_zh="确认 metadata intake 不直接写正式记录。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump(
            {"items": [{"title": "Accepted Candidate", "doi": "10.1234/accepted"}]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    data = ensure_metadata_intake_requests(config, campaign.campaign_id)
    data["requests"][0]["status"] = "accepted"
    request_path = tmp_path / "01_literature" / "campaigns" / "C001_metadata_requests.yaml"
    request_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    generate_formal_write_requests(config, campaign.campaign_id)
    generate_review_queue(config, campaign.campaign_id)

    result = check_campaign_safety(config, campaign.campaign_id)
    safety = yaml.safe_load(result.path.read_text(encoding="utf-8"))

    assert result.safety_status == "needs_review"
    assert not (config.metadata_root / "P002.yaml").exists()
    check_statuses = {check["check_id"]: check["status"] for check in safety["checks"]}
    assert check_statuses["metadata_intake_requests_safe"] == "passed"
    assert check_statuses["formal_request_non_execution"] == "passed"
    assert "formal_request_non_execution" in safety["monitored_failure_scenarios"]


def test_campaign_safety_blocks_unsafe_metadata_request(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="不安全 request",
        objective_zh="确认 formal_write_allowed 不能打开。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump({"items": [{"title": "Unsafe Candidate", "doi": "10.1234/unsafe"}]}, allow_unicode=True),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    data = ensure_metadata_intake_requests(config, campaign.campaign_id)
    data["requests"][0]["formal_write_allowed"] = True
    request_path = tmp_path / "01_literature" / "campaigns" / "C001_metadata_requests.yaml"
    request_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    result = check_campaign_safety(config, campaign.campaign_id)
    data = yaml.safe_load(campaign_safety_record_path(config, "C001").read_text(encoding="utf-8"))

    assert result.safety_status == "blocked"
    assert any("formal_write_allowed" in warning for warning in data["warnings_zh"])


def test_cli_safety_commands(tmp_path, capsys):
    prepare_project(tmp_path)

    exit_code = main(["--root", str(tmp_path), "safety", "check", "P001"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "写作安全检查完成" in captured.out
    assert safety_record_path(load_project_config(tmp_path), "P001").exists()

    exit_code = main(["--root", str(tmp_path), "safety", "validate", "P001"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "safety 记录有效" in captured.out

    exit_code = main(["--root", str(tmp_path), "safety", "status", "P001"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "safety 状态" in captured.out
