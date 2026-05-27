from __future__ import annotations

from pathlib import Path

import yaml

from rsa_cli.campaign import (
    campaign_metadata_requests_path,
    create_campaign,
    ensure_metadata_intake_requests,
    generate_formal_write_requests,
    import_campaign_items,
    run_campaign,
)
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.review_workspace import (
    build_review_workspace,
    clean_review_workspace,
    review_workspace_status,
)
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(title: str = "Review Workspace Paper") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/review-workspace",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试本地监管台。",
        "last_checked": "2026-05-27",
        "pdf_status": "not_acquired",
        "local_pdf": None,
        "assets": [],
        "topic_profile": "demo",
        "priority_questions": ["Q1"],
        "used_for": ["监管台测试"],
        "research_roles": ["method"],
        "notes": "人工备注",
    }


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    return config


def test_build_campaign_review_workspace_generates_manifest_pages_and_actions(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="本地监管台 campaign",
        objective_zh="验证 review workspace 聚合批量队列。",
    )
    source = tmp_path / "items.csv"
    source.write_text(
        "title,doi,year,first_author\n"
        "New Workspace Candidate,10.1234/workspace-new,2026,Ada\n",
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    run_campaign(config, campaign.campaign_id, dry_run=True)
    ensure_metadata_intake_requests(config, campaign.campaign_id)
    requests_path = campaign_metadata_requests_path(config, campaign.campaign_id)
    request_data = yaml.safe_load(requests_path.read_text(encoding="utf-8"))
    request_data["requests"][0]["status"] = "accepted"
    requests_path.write_text(
        yaml.safe_dump(request_data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    generate_formal_write_requests(config, campaign.campaign_id)

    result = build_review_workspace(config, campaign_id=campaign.campaign_id)
    manifest = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))

    assert result.object_count >= 1
    assert result.action_count >= 1
    assert result.index_path.exists()
    assert (config.review_workspace_root / "groups" / "formal_write_request.html").exists()
    assert (config.review_workspace_root / "objects" / "RO001.html").exists()
    assert manifest["schema_version"] == "phase12-review-workspace-v1"
    assert manifest["target_type"] == "campaign"
    assert manifest["target_id"] == "C001"
    assert manifest["user_language"] == "zh"
    assert any(item["group"] == "formal_write_request" for item in manifest["review_objects"])
    assert any("人工确认门禁" in item["formal_gate_policy_zh"] for item in manifest["review_objects"])
    assert any(action["command"].startswith("rsa campaign queue review") for action in manifest["actions"])
    assert "不会直接修改文件" in result.index_path.read_text(encoding="utf-8")


def test_build_paper_review_workspace_marks_missing_and_existing_evidence(tmp_path):
    config = prepare_project(tmp_path)
    note = config.notes_root / "P001_reading_note.md"
    note.write_text(
        "---\n"
        + yaml.safe_dump(
            {
                "paper_id": "P001",
                "note_status": "ready_for_review",
                "agent_review_score_10": 7,
                "note_integration_requests": [],
            },
            allow_unicode=True,
            sort_keys=False,
        )
        + "---\n\n中文阅读草稿。\n",
        encoding="utf-8",
    )
    scoring = config.scores_root / "P001_scoring.yaml"
    scoring.write_text(
        yaml.safe_dump(
            {
                "paper_id": "P001",
                "scoring_status": "scored",
                "ai_review_decision": "recommend_pass",
                "score_confidence": "low",
                "scores": {
                    "ai_relevance_score_10": 8,
                    "ai_quality_score_10": 6,
                    "ai_read_priority_score_10": 8,
                },
                "human_review": {"final_decision": None},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    visual = config.assets_root / "P001" / "visual_evidence_candidates.yaml"
    visual.parent.mkdir(parents=True, exist_ok=True)
    visual.write_text(
        yaml.safe_dump(
            {
                "paper_id": "P001",
                "candidates": [
                    {
                        "candidate_id": "V001",
                        "status": "needs_review",
                        "visual_type": "figure",
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = build_review_workspace(config, paper_id="P001")
    manifest = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))

    assert result.object_count >= 5
    assert any(item["object_type"] == "reading_note" for item in manifest["review_objects"])
    assert any(item["object_type"] == "visual_evidence" and item["group"] == "needs_followup" for item in manifest["review_objects"])
    assert any(item["object_type"] == "ai_scoring" and item["group"] == "low_confidence" for item in manifest["review_objects"])
    assert manifest["missing_link_count"] >= 1
    assert any(link["missing_zh"] for link in manifest["missing_links"])
    assert "rsa score review P001" in result.action_checklist_path.read_text(encoding="utf-8")


def test_review_workspace_status_and_clean_preserve_user_records(tmp_path):
    config = prepare_project(tmp_path)
    build_review_workspace(config, paper_id="P001")
    user_record = config.review_workspace_root / "user_records" / "manual_note.md"
    user_record.parent.mkdir(parents=True, exist_ok=True)
    user_record.write_text("人工记录\n", encoding="utf-8")

    status = review_workspace_status(config)
    assert status.index_path.exists()
    clean = clean_review_workspace(config, generated_only=True)

    assert status.exists is True
    assert status.target_type == "paper"
    assert status.target_id == "P001"
    assert clean.removed_count >= 1
    assert user_record.exists()
    assert not status.index_path.exists()
    assert user_record in clean.preserved_paths or user_record.parent in clean.preserved_paths
