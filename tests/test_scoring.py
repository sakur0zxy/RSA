from __future__ import annotations

import time
from pathlib import Path

import yaml

from rsa_cli.campaign import create_campaign, import_campaign_items
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.scoring import (
    ScoringError,
    build_scoring_skeleton,
    campaign_scoring_summary_path,
    review_score,
    score_campaign,
    score_paper,
    score_status,
    scoring_path,
    validate_campaign_scoring_summary,
    validate_scoring_record,
    write_scoring_record,
)
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.visual import default_advanced_analysis, write_visual_candidates


def metadata_values(title: str = "Scoring Paper") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/scoring",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试 Phase 9 scoring。",
        "last_checked": "2026-05-21",
        "pdf_status": "local",
        "local_pdf": "01_literature/pdfs/P001/source.pdf",
        "assets": [],
        "topic_profile": "demo_topic",
        "priority_questions": ["Q1"],
        "used_for": ["评分测试"],
        "research_roles": ["method", "comparison"],
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


def write_reading_note(config) -> None:
    note = config.notes_root / "P001_reading_note.md"
    frontmatter = {
        "paper_id": "P001",
        "metadata": "01_literature/metadata/P001.yaml",
        "note_status": "ready_for_review",
        "source_file": "01_literature/pdfs/P001/source.pdf",
        "authorization": "local",
        "source_grounded_claims": [
            {
                "claim_zh": "论文提出一种 gapped aperture SAR reconstruction method，并包含 experiment result。",
                "evidence_page": 2,
                "evidence_section": "Method",
                "source_chunk_id": "CH001",
                "evidence_snippet": "method and experiment result",
                "needs_human_check": True,
            }
        ],
        "short_quotes": [
            {
                "quote": "method and experiment result",
                "page": 2,
                "section": "Method",
                "reason_zh": "用于定位原文。",
            }
        ],
        "uncertain_points_zh": [],
        "asset_suggestions": [
            {
                "page": 3,
                "figure_or_table": "Figure 1",
                "reason_zh": "正文提到结果图。",
                "confidence": "medium",
            }
        ],
        "note_integration_requests": [],
        "human_confirmed": False,
    }
    note.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "## Agent 摘要\n\n方法、实验、指标和结果均需要人工复核。\n",
        encoding="utf-8",
    )


def visual_candidate(confidence="high", status="ocr_success", warning_zh=None) -> dict:
    return {
        "candidate_id": "V001",
        "paper_id": "P001",
        "asset_id": "A001",
        "visual_type": "figure",
        "page": 3,
        "region_bbox": [10, 20, 120, 160],
        "source_rects": [[10, 20, 120, 160]],
        "source_text": "Figure 1. Experiment result and comparison.",
        "caption_zh": "Figure 1. Experiment result and comparison.",
        "ocr_summary_zh": "已提取嵌入文本。",
        "confidence": confidence,
        "evidence_level": "caption_visual_text",
        "status": status,
        "warning_zh": warning_zh,
        "repair_hint_zh": "请人工查看 PDF。",
        "source_links": {
            "metadata": "01_literature/metadata/P001.yaml",
            "source_ledger": "01_literature/sources/P001.yaml",
            "asset_manifest": "01_literature/assets/P001/manifest.yaml",
        },
        "advanced_analysis": default_advanced_analysis(),
        "llm_visual_analysis": {"status": "not_run"},
    }


def test_scoring_schema_validation_and_scores_root(tmp_path):
    config = prepare_project(tmp_path)
    record = build_scoring_skeleton("P001")
    record["scores"] = {
        "ai_relevance_score_10": 6,
        "ai_quality_score_10": 5,
        "ai_read_priority_score_10": 6,
    }
    path = write_scoring_record(config, "P001", record)

    assert config.scores_root == tmp_path / "01_literature" / "scores"
    assert path == scoring_path(config, "P001")
    assert validate_scoring_record(config, "P001") == []

    broken = yaml.safe_load(path.read_text(encoding="utf-8"))
    broken["scores"].pop("ai_quality_score_10")
    path.write_text(yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")

    errors = validate_scoring_record(config, "P001")
    assert any("ai_quality_score_10" in error for error in errors)


def test_score_paper_generates_scores_packet_and_visual_limitation(tmp_path):
    config = prepare_project(tmp_path)

    result = score_paper(config, "P001")
    data = yaml.safe_load(result.scoring_path.read_text(encoding="utf-8"))

    assert result.ai_relevance_score_10 >= 6
    assert "ai_quality_score_10" in data["scores"]
    assert "ai_read_priority_score_10" in data["scores"]
    assert data["evidence_signals"]["text_signals"]["method_signal"]
    assert any("缺少视觉证据候选" in item for item in data["limitations_zh"])
    assert result.review_packet_path.exists()
    assert "不是 formal approval" in result.review_packet_path.read_text(encoding="utf-8")


def test_visual_conflict_sets_needs_review_and_low_confidence_degrades(tmp_path):
    config = prepare_project(tmp_path)
    candidate = visual_candidate(
        confidence="low",
        status="needs_review",
        warning_zh="视觉结果与正文描述存在冲突。",
    )
    write_visual_candidates(
        config, "P001", {"paper_id": "P001", "candidates": [candidate]}
    )

    result = score_paper(config, "P001")
    data = yaml.safe_load(result.scoring_path.read_text(encoding="utf-8"))

    assert result.ai_review_decision == "needs_review"
    assert data["score_confidence"] in {"low", "medium"}
    assert "text_visual_conflict" in data["evidence_signals"]["uncertainty_signals"]
    visual_item = data["evidence_signals"]["visual_signals"]["candidates"][0]
    assert "弱信号" in visual_item["degraded_reason_zh"]


def test_missing_metadata_or_note_fails_closed(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)

    try:
        score_paper(config, "P001")
    except ScoringError as exc:
        assert "正式 metadata" in str(exc)
    else:
        raise AssertionError("missing metadata should fail closed")

    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    try:
        score_paper(config, "P001")
    except ScoringError as exc:
        assert "reading note" in str(exc)
    else:
        raise AssertionError("missing reading note should fail closed")


def test_validate_status_are_read_only(tmp_path):
    config = prepare_project(tmp_path)
    result = score_paper(config, "P001")
    before = result.scoring_path.read_text(encoding="utf-8")
    before_mtime = result.scoring_path.stat().st_mtime_ns
    time.sleep(0.01)

    assert validate_scoring_record(config, "P001") == []
    status = score_status(config, "P001")

    assert status.exists is True
    assert status.ai_review_decision == result.ai_review_decision
    assert result.scoring_path.read_text(encoding="utf-8") == before
    assert result.scoring_path.stat().st_mtime_ns == before_mtime


def test_review_score_appends_history_without_formal_writes(tmp_path):
    config = prepare_project(tmp_path)
    result = score_paper(config, "P001")
    metadata_path = tmp_path / "01_literature" / "metadata" / "P001.yaml"
    metadata_before = metadata_path.read_text(encoding="utf-8")

    review = review_score(
        config,
        "P001",
        final_decision="approved",
        reviewer="zxy",
        reason="人工复核后认为该评分可作为当前阶段排序参考。",
    )
    data = yaml.safe_load(result.scoring_path.read_text(encoding="utf-8"))

    assert review.history_count == 1
    assert data["human_review"]["reviewed"] is True
    assert data["review_history"][0]["previous_decision"] == result.ai_review_decision
    assert metadata_path.read_text(encoding="utf-8") == metadata_before
    assert not (tmp_path / "01_literature" / "literature_map.md").read_text(
        encoding="utf-8"
    ).startswith("P001")


def test_campaign_scoring_summary_reuses_single_paper_and_skips_unlinked(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_campaign(
        config,
        name_zh="评分批量队列",
        objective_zh="验证 Phase 9 campaign scoring summary。",
        created_by="zxy",
    )
    csv_path = tmp_path / "campaign.csv"
    csv_path.write_text(
        "title,doi,year,first_author\n"
        "Scoring Paper,10.1234/scoring,2024,Ada\n"
        "Unlinked Paper,10.1234/unlinked,2025,Bob\n",
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(csv_path))
    campaign_before = campaign.path.read_text(encoding="utf-8")

    result = score_campaign(config, campaign.campaign_id)
    summary = yaml.safe_load(result.path.read_text(encoding="utf-8"))

    assert result.scored_count == 1
    assert result.skipped_count == 1
    assert summary["rows"][0]["paper_id"] == "P001"
    assert summary["rows"][0]["review_packet"]
    assert validate_campaign_scoring_summary(config, campaign.campaign_id) == []
    assert campaign_scoring_summary_path(config, campaign.campaign_id).exists()
    assert campaign.path.read_text(encoding="utf-8") == campaign_before

