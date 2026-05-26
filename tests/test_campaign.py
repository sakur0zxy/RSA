from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import yaml

from rsa_cli.campaign import (
    campaign_status,
    create_campaign,
    ensure_metadata_intake_requests,
    generate_formal_write_requests,
    generate_review_queue,
    import_campaign_items,
    pause_campaign_run,
    review_campaign_queue_item,
    run_campaign,
    validate_campaign,
    validate_campaign_run,
)
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values() -> dict:
    return {
        "title": "Known Campaign Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/campaign",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试 campaign 与正式 metadata 的轻量链接。",
        "last_checked": "2026-05-19",
        "pdf_status": "not_acquired",
        "local_pdf": None,
        "assets": [],
        "topic_profile": "demo",
        "priority_questions": ["Q1"],
        "used_for": ["批量队列"],
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


def test_create_campaign_and_import_csv_with_dedup_and_linking(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="SAR 批量候选",
        objective_zh="导入一组待处理 SAR 文献候选。",
        topic_profile="demo",
        created_by="zxy",
    )
    csv_path = tmp_path / "candidates.csv"
    csv_path.write_text(
        "title,doi,year,first_author,note_zh\n"
        "Known Campaign Paper,10.1234/campaign,2024,Ada,已有正式记录\n"
        "New Paper,10.1234/new,2025,Bob,新候选\n"
        "New Paper Duplicate,10.1234/new,2025,Bob,重复候选\n",
        encoding="utf-8",
    )

    result = import_campaign_items(config, campaign.campaign_id, source_file=str(csv_path))
    data = yaml.safe_load(campaign.path.read_text(encoding="utf-8"))
    status = campaign_status(config, campaign.campaign_id)

    assert result.imported_count == 3
    assert result.linked_count == 1
    assert result.duplicate_count == 1
    assert data["items"][0]["paper_id"] == "P001"
    assert data["items"][0]["status"] == "linked"
    assert data["items"][1]["status"] == "queued"
    assert data["items"][2]["status"] == "duplicate"
    assert data["items"][2]["duplicate_of"] == "CI002"
    assert status.total_count == 3
    assert status.queued_count == 1
    assert validate_campaign(config, campaign.campaign_id) == []


def test_import_yaml_blocks_identityless_candidate(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="缺失身份测试",
        objective_zh="验证缺少 title 和 doi 的候选会被阻塞。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump({"items": [{"note_zh": "没有标题也没有 DOI"}]}, allow_unicode=True),
        encoding="utf-8",
    )

    result = import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    data = yaml.safe_load(campaign.path.read_text(encoding="utf-8"))

    assert result.blocked_count == 1
    assert data["items"][0]["status"] == "blocked"
    assert data["items"][0]["reason_zh"]


def test_validate_campaign_detects_duplicate_key_not_marked(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="重复校验测试",
        objective_zh="验证未标记重复的 dedup_key 会被校验发现。",
    )
    data = yaml.safe_load(campaign.path.read_text(encoding="utf-8"))
    data["items"] = [
        {
            "item_id": "CI001",
            "title": "A",
            "doi": "10.1/a",
            "dedup_key": "doi:10.1/a",
            "status": "queued",
        },
        {
            "item_id": "CI002",
            "title": "A duplicate",
            "doi": "10.1/a",
            "dedup_key": "doi:10.1/a",
            "status": "queued",
        },
    ]
    campaign.path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    errors = validate_campaign(config, campaign.campaign_id)

    assert any("dedup_key" in error and "重复" in error for error in errors)


def test_metadata_intake_requests_are_independent_and_idempotent(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="metadata intake",
        objective_zh="生成独立 metadata request。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump(
            {"items": [{"title": "New Intake Paper", "doi": "10.1234/intake", "year": "2026"}]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))

    first = ensure_metadata_intake_requests(config, campaign.campaign_id)
    second = ensure_metadata_intake_requests(config, campaign.campaign_id)

    assert len(first["requests"]) == 1
    assert len(second["requests"]) == 1
    request = second["requests"][0]
    assert request["request_id"] == "MR001"
    assert request["status"] == "auto_triaged"
    assert request["formal_write_allowed"] is False
    assert request["candidate_metadata"]["title"] == "New Intake Paper"
    assert not (config.metadata_root / "P002.yaml").exists()


def test_accepted_metadata_request_creates_pending_formal_request_only(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="formal request",
        objective_zh="正式写入前只生成请求。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump({"items": [{"title": "Accepted Candidate", "doi": "10.1234/accepted"}]}, allow_unicode=True),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    data = ensure_metadata_intake_requests(config, campaign.campaign_id)
    data["requests"][0]["status"] = "accepted"
    request_path = tmp_path / "01_literature" / "campaigns" / "C001_metadata_requests.yaml"
    request_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    updated = generate_formal_write_requests(config, campaign.campaign_id)
    repeated = generate_formal_write_requests(config, campaign.campaign_id)

    assert len(updated["formal_write_requests"]) == 1
    assert len(repeated["formal_write_requests"]) == 1
    formal = repeated["formal_write_requests"][0]
    assert formal["status"] == "pending_human_approval"
    assert formal["human_confirmed"] is False
    assert formal["formal_write_allowed"] is False
    assert not (config.metadata_root / "P002.yaml").exists()


def test_run_campaign_dry_run_writes_plan_queue_and_report(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="dry run",
        objective_zh="验证 dry-run 不执行 workflow。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump({"items": [{"title": "Dry Candidate", "doi": "10.1234/dry"}]}, allow_unicode=True),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))

    result = run_campaign(config, campaign.campaign_id, dry_run=True, max_visual=1)
    run_data = yaml.safe_load(result.path.read_text(encoding="utf-8"))
    report_text = result.batch_report_path.read_text(encoding="utf-8")

    assert result.campaign_status == "dry_run"
    assert run_data["pipeline"]["worker_limits"]["visual_extraction"] == 1
    assert result.review_queue_path.exists()
    assert "人工审批边界" in report_text


def test_run_campaign_processes_linked_items_and_continues_queued_items(tmp_path, monkeypatch):
    import rsa_cli.workflow as workflow

    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="pipeline run",
        objective_zh="验证 linked workflow 与 queued intake。",
    )
    source = tmp_path / "items.csv"
    source.write_text(
        "title,doi,year,first_author\n"
        "Known Campaign Paper,10.1234/campaign,2024,Ada\n"
        "Queued Candidate,10.1234/queued,2026,Bob\n",
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))

    def fake_run_workflow(config, paper_id, campaign_id=None, campaign_item_id=None):
        run_path = config.workflows_root / paper_id / "campaign-run.yaml"
        report_path = config.workflows_root / paper_id / "campaign-report.md"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        run_path.write_text("run", encoding="utf-8")
        report_path.write_text("report", encoding="utf-8")
        return SimpleNamespace(
            paper_id=paper_id,
            run_id="WR001",
            run_path=run_path,
            report_path=report_path,
            workflow_status="completed",
            current_step="review_packet",
        )

    monkeypatch.setattr(workflow, "run_workflow", fake_run_workflow)

    result = run_campaign(config, campaign.campaign_id)
    errors = validate_campaign_run(config, campaign.campaign_id)
    run_data = yaml.safe_load(result.path.read_text(encoding="utf-8"))
    request_data = yaml.safe_load(result.metadata_requests_path.read_text(encoding="utf-8"))
    queue = generate_review_queue(config, campaign.campaign_id)

    assert errors == []
    assert result.campaign_status == "completed"
    assert {item["status"] for item in run_data["items"]} >= {"completed", "metadata_intake_created"}
    assert request_data["requests"][0]["status"] == "auto_triaged"
    assert queue.total_count >= 2


def test_pause_and_review_queue_decision_do_not_formal_write(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="review queue",
        objective_zh="验证监管决策不等于正式写入。",
    )
    source = tmp_path / "items.yaml"
    source.write_text(
        yaml.safe_dump({"items": [{"title": "Review Candidate", "doi": "10.1234/review"}]}, allow_unicode=True),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    run_campaign(config, campaign.campaign_id, dry_run=True)
    paused = pause_campaign_run(config, campaign.campaign_id, reason_zh="测试暂停")
    queue = generate_review_queue(config, campaign.campaign_id)
    queue_data = yaml.safe_load(queue.path.read_text(encoding="utf-8"))
    item_id = queue_data["queue_items"][0]["queue_item_id"]

    decision = review_campaign_queue_item(
        config,
        campaign.campaign_id,
        queue_item_id=item_id,
        decision="accepted",
        reviewer="zxy",
        reason_zh="进入后续流程",
    )

    updated_queue = yaml.safe_load(queue.path.read_text(encoding="utf-8"))
    assert paused.campaign_status == "paused"
    assert decision.decision == "accepted"
    assert updated_queue["queue_items"][0]["review_decision"] == "accepted"
    assert not (config.metadata_root / "P002.yaml").exists()
