from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rsa_cli.assets import add_source_record
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.visual import (
    VisualError,
    build_initial_candidate_from_suggestion,
    default_advanced_analysis,
    extract_visual_evidence,
    load_asset_suggestions,
    select_visual_source,
    validate_visual_candidate_file,
    visual_candidate_path,
    visual_context_packet_dir,
    visual_status,
    write_visual_candidates,
)


def metadata_values(local_pdf=None, pdf_status="authorized") -> dict:
    return {
        "title": "Visual Evidence Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/visual",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试视觉证据候选流程。",
        "last_checked": "2026-05-19",
        "pdf_status": pdf_status,
        "local_pdf": local_pdf,
        "assets": [],
        "topic_profile": "demo",
        "priority_questions": ["Q1"],
        "used_for": ["视觉证据"],
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


def valid_candidate(paper_id="P001", candidate_id="V001", status="detected") -> dict:
    return {
        "candidate_id": candidate_id,
        "paper_id": paper_id,
        "asset_id": None,
        "visual_type": "figure",
        "page": 1,
        "region_bbox": [10, 20, 120, 160],
        "source_rects": [[10, 20, 120, 160]],
        "source_text": "Figure 1. Reconstruction result.",
        "caption_zh": "Figure 1. Reconstruction result.",
        "ocr_summary_zh": "已提取嵌入文本。",
        "confidence": "medium",
        "evidence_level": "caption_visual_text",
        "status": status,
        "source_links": {
            "metadata": "01_literature/metadata/P001.yaml",
            "source_ledger": "01_literature/sources/P001.yaml",
            "asset_manifest": "01_literature/assets/P001/manifest.yaml",
        },
        "advanced_analysis": default_advanced_analysis(),
        "llm_visual_analysis": {"status": "not_run"},
    }


def write_note_with_suggestions(config) -> None:
    note = config.notes_root / "P001_reading_note.md"
    frontmatter = {
        "paper_id": "P001",
        "note_status": "ready_for_review",
        "source_file": "01_literature/pdfs/P001/S001_paper.pdf",
        "authorization": "authorized",
        "asset_suggestions": [
            {
                "asset_request_type": "figure_or_table_candidate",
                "page": 1,
                "figure_or_table": "Figure 1",
                "reason_zh": "正文提到 Figure 1 展示重建结果，建议作为候选视觉证据。",
                "confidence": "medium",
            }
        ],
    }
    note.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "## 候选图表/表格建议\n\n"
        + "- page: 1; Figure 1; 正文提到重建结果。\n",
        encoding="utf-8",
    )


def add_dummy_source(config, tmp_path: Path) -> Path:
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"%PDF-1.4\n% visual placeholder")
    result = add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="authorized",
        source_type="pdf",
        license_note="用户已授权本地科研阅读。",
        added_by="zxy",
    )
    return result.local_path


def test_visual_registry_validation_and_default_analysis(tmp_path):
    config = prepare_project(tmp_path)
    data = {"paper_id": "P001", "candidates": [valid_candidate()]}

    path = write_visual_candidates(config, "P001", data)

    assert path == visual_candidate_path(config, "P001")
    assert validate_visual_candidate_file(config, "P001") == []
    assert default_advanced_analysis()["curve_extraction"]["status"] == "not_run"


def test_visual_validation_reports_duplicate_and_missing_warning(tmp_path):
    config = prepare_project(tmp_path)
    first = valid_candidate(candidate_id="V001")
    second = valid_candidate(candidate_id="V001", status="needs_review")
    second.pop("warning_zh", None)
    second.pop("repair_hint_zh", None)
    write_visual_candidates(config, "P001", {"paper_id": "P001", "candidates": [first, second]})

    errors = validate_visual_candidate_file(config, "P001")

    assert any("重复" in error for error in errors)
    assert any("warning_zh" in error for error in errors)
    assert any("repair_hint_zh" in error for error in errors)


def test_visual_validation_requires_source_links_and_llm_placeholder(tmp_path):
    config = prepare_project(tmp_path)
    candidate = valid_candidate()
    candidate.pop("source_links")
    candidate.pop("llm_visual_analysis")
    write_visual_candidates(config, "P001", {"paper_id": "P001", "candidates": [candidate]})

    errors = validate_visual_candidate_file(config, "P001")

    assert any("source_links" in error for error in errors)
    assert any("llm_visual_analysis" in error for error in errors)


def test_select_visual_source_and_asset_suggestions(tmp_path):
    config = prepare_project(tmp_path)
    add_dummy_source(config, tmp_path)
    write_note_with_suggestions(config)

    source = select_visual_source(config, "P001")
    suggestions = load_asset_suggestions(config, "P001")
    candidate = build_initial_candidate_from_suggestion(
        config, "P001", suggestions[0], "V001"
    )

    assert source.source_id == "S001"
    assert suggestions[0]["reason_zh"]
    assert candidate["advanced_analysis"]["curve_extraction"]["status"] == "not_run"
    assert candidate["llm_visual_analysis"]["status"] == "not_run"


def test_missing_visual_source_fails_closed(tmp_path):
    config = prepare_project(tmp_path)

    with pytest.raises(VisualError) as exc:
        select_visual_source(config, "P001")

    assert "缺少可用 PDF" in str(exc.value)


def test_extract_visual_evidence_reports_missing_pymupdf(tmp_path, monkeypatch):
    config = prepare_project(tmp_path)
    add_dummy_source(config, tmp_path)

    def missing_fitz():
        raise VisualError("缺少 PyMuPDF，无法执行视觉证据提取；请安装基础依赖后重试。")

    monkeypatch.setattr("rsa_cli.visual._load_fitz", missing_fitz)

    with pytest.raises(VisualError) as exc:
        extract_visual_evidence(config, "P001")

    assert "缺少 PyMuPDF" in str(exc.value)


def make_synthetic_pdf(path: Path) -> None:
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 24, 24), 0)
    pix.clear_with(180)
    image_stream = pix.tobytes("png")
    for page_index in range(2):
        page = doc.new_page()
        top = 90
        page.insert_text((50, 50), f"Page {page_index + 1} discusses SAR reconstruction.")
        page.insert_image(fitz.Rect(50, top, 190, top + 90), stream=image_stream)
        page.insert_text(
            (50, top + 110),
            f"Figure {page_index + 1}. Reconstruction comparison result.",
        )
    doc.save(path)
    doc.close()


def prepare_pdf_project(tmp_path: Path):
    config = prepare_project(tmp_path)
    pdf = tmp_path / "visual.pdf"
    make_synthetic_pdf(pdf)
    add_source_record(
        config,
        "P001",
        source_file=str(pdf),
        authorization="authorized",
        source_type="pdf",
        license_note="用户已授权本地科研阅读。",
        added_by="zxy",
    )
    return config


def test_extract_asset_suggestions_only_does_not_scan_pdf(tmp_path):
    pytest.importorskip("fitz")
    config = prepare_pdf_project(tmp_path)
    write_note_with_suggestions(config)

    result = extract_visual_evidence(config, "P001", asset_suggestions_only=True)
    data = yaml.safe_load(result.candidate_path.read_text(encoding="utf-8"))

    assert result.candidates_created == 1
    assert result.crops_written == 0
    assert len(data["candidates"]) == 1
    assert data["candidates"][0]["asset_id"] is None


def test_extract_all_detected_writes_crops_manifest_and_context_packet(tmp_path):
    pytest.importorskip("fitz")
    config = prepare_pdf_project(tmp_path)

    result = extract_visual_evidence(config, "P001", all_detected=True)
    data = yaml.safe_load(result.candidate_path.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))
    first = data["candidates"][0]
    packet = visual_context_packet_dir(config, "P001") / f"{first['candidate_id']}.yaml"
    packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))

    assert result.crops_written >= 2
    assert any(item["visual_type"] == "figure" for item in data["candidates"])
    assert (config.assets_root / "P001" / "crops" / "V001.png").exists()
    assert manifest["assets"][0]["generated_by"] == "rsa visual extract"
    assert manifest["assets"][0]["source_candidate_id"] == "V001"
    assert packet_data["llm_visual_analysis"]["status"] == "not_run"
    assert validate_visual_candidate_file(config, "P001") == []


def test_extract_pages_restricts_candidates(tmp_path):
    pytest.importorskip("fitz")
    config = prepare_pdf_project(tmp_path)

    result = extract_visual_evidence(config, "P001", all_detected=True, pages={2})
    data = yaml.safe_load(result.candidate_path.read_text(encoding="utf-8"))

    assert result.candidates_created >= 1
    assert {item["page"] for item in data["candidates"]} == {2}


def test_visual_status_counts_candidates(tmp_path):
    config = prepare_project(tmp_path)
    write_visual_candidates(
        config,
        "P001",
        {
            "paper_id": "P001",
            "candidates": [
                valid_candidate(candidate_id="V001", status="cropped"),
                valid_candidate(candidate_id="V002", status="needs_review")
                | {
                    "warning_zh": "需要人工复核。",
                    "repair_hint_zh": "请查看 PDF。",
                    "evidence_level": "visual_only",
                },
            ],
        },
    )

    status = visual_status(config, "P001")

    assert status.total_count == 2
    assert status.cropped_count == 1
    assert status.needs_review_count == 1
