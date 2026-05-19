from __future__ import annotations

from pathlib import Path

import yaml

from rsa_cli.campaign import (
    campaign_status,
    create_campaign,
    import_campaign_items,
    validate_campaign,
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
