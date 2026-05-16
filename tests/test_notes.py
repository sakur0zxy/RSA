from pathlib import Path

import pytest
import yaml

from rsa_cli.assets import add_source_record
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.notes import (
    NoteError,
    create_reading_note,
    load_reading_note,
    note_status,
    validate_reading_note,
)
from rsa_cli.reading_draft import DraftError, draft_reading_note
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(local_pdf=None, pdf_status="local") -> dict:
    return {
        "title": "Reading Note Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/note",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "支持阅读笔记流程。",
        "last_checked": "2026-05-12",
        "pdf_status": pdf_status,
        "local_pdf": local_pdf,
        "assets": [],
        "topic_profile": "sar_noncontinuous_aperture",
        "priority_questions": ["Q1"],
        "used_for": ["阅读笔记"],
        "research_roles": ["theory"],
        "notes": "人工备注",
    }


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    return config


def write_source(config, name="P001.pdf") -> Path:
    source = config.pdfs_root / name
    source.write_text("authorized local full text placeholder", encoding="utf-8")
    return source


def write_mock_llm_config(config) -> None:
    local = config.root / ".rsa" / "local.yaml"
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


def write_long_source(tmp_path: Path) -> Path:
    source = tmp_path / "authorized-full-text.pdf"
    source.write_text(
        (
            "This paper studies gapped aperture SAR imaging. "
            "The method compares reconstruction results with baseline methods. "
            "Figure 3 reports the reconstruction quality and Table 1 lists metrics. "
            "The experiment uses simulated sparse aperture observations and evaluates sidelobe artifacts. "
        )
        * 6,
        encoding="utf-8",
    )
    return source


def rewrite_note(note, frontmatter):
    note.path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n"
        + note.body,
        encoding="utf-8",
    )


def test_create_reading_note_from_authorized_local_source(tmp_path):
    config = prepare_project(tmp_path)
    source = write_source(config)
    write_metadata_record(
        config,
        metadata_values(local_pdf=str(source)),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    result = create_reading_note(
        config,
        "P001",
        source_file=str(source),
        authorization="local",
    )
    note = load_reading_note(config, "P001")

    assert result.path == config.notes_root / "P001_reading_note.md"
    assert note.frontmatter["paper_id"] == "P001"
    assert note.frontmatter["authorization"] == "local"
    assert note.frontmatter["source_grounded_claims"] == []
    assert validate_reading_note(config, "P001") == []


def test_missing_or_unauthorized_source_records_status_without_note(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(
        config,
        metadata_values(pdf_status="not_acquired"),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    with pytest.raises(NoteError) as exc:
        create_reading_note(
            config,
            "P001",
            source_file=str(config.pdfs_root / "missing.pdf"),
            authorization="provided",
        )

    assert "source_file" in str(exc.value)
    assert not (config.notes_root / "P001_reading_note.md").exists()
    report = config.pdf_acquisition_report_path.read_text(encoding="utf-8")
    assert "P001" in report
    assert "blocked" in report
    assert "未创建阅读笔记" in report


def test_validate_reading_note_is_read_only(tmp_path):
    config = prepare_project(tmp_path)
    source = write_source(config)
    write_metadata_record(
        config,
        metadata_values(local_pdf=str(source)),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    create_reading_note(config, "P001", source_file=str(source), authorization="provided")
    path = config.notes_root / "P001_reading_note.md"
    before = path.read_text(encoding="utf-8")

    assert validate_reading_note(config, "P001") == []

    assert path.read_text(encoding="utf-8") == before


def test_approved_reading_note_requires_human_confirmation(tmp_path):
    config = prepare_project(tmp_path)
    source = write_source(config)
    write_metadata_record(
        config,
        metadata_values(local_pdf=str(source)),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    create_reading_note(config, "P001", source_file=str(source), authorization="authorized")
    note = load_reading_note(config, "P001")
    frontmatter = dict(note.frontmatter)
    frontmatter["note_status"] = "approved"
    frontmatter["human_confirmed"] = False
    rewrite_note(note, frontmatter)

    errors = validate_reading_note(config, "P001")

    assert any("human_confirmed" in error for error in errors)
    assert any("confirmed_by" in error for error in errors)
    assert any("confirmed_at" in error for error in errors)


def test_note_status_reports_missing_note_with_metadata_pdf_status(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(
        config,
        metadata_values(pdf_status="not_acquired"),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    assert note_status(config, "P001") == "no_note; pdf_status=not_acquired"


def test_draft_reading_note_from_source_ledger_generates_review_packet(tmp_path):
    config = prepare_project(tmp_path)
    write_mock_llm_config(config)
    config = load_project_config(tmp_path)
    write_metadata_record(
        config,
        metadata_values(pdf_status="authorized"),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    source = write_long_source(tmp_path)
    add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="authorized",
        source_type="pdf",
        license_note="用户已授权本地科研阅读。",
        added_by="zxy",
    )

    result = draft_reading_note(config, "P001")
    note = load_reading_note(config, "P001")

    assert result.note_status == "ready_for_review"
    assert result.agent_review_score_10 >= 6
    assert result.review_packet_path.exists()
    assert result.prompt_packet_path.exists()
    assert result.extraction_cache_path.exists()
    assert note.frontmatter["human_confirmed"] is False
    assert note.frontmatter["note_status"] == "ready_for_review"
    assert note.frontmatter["agent_review_score_10"] >= 6
    assert "prompt_packet" in note.frontmatter
    assert "asset_suggestions" in note.frontmatter
    assert validate_reading_note(config, "P001") == []


def test_draft_reading_note_missing_llm_config_blocks_without_note(tmp_path):
    config = prepare_project(tmp_path)
    source = write_long_source(tmp_path)
    write_metadata_record(
        config,
        metadata_values(local_pdf=str(source), pdf_status="local"),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    with pytest.raises(DraftError) as exc:
        draft_reading_note(config, "P001", source_file=str(source))

    assert "reading_draft.llm.provider" in str(exc.value)
    assert not (config.notes_root / "P001_reading_note.md").exists()
    assert (config.extracted_root / "P001" / "prompt_packet.yaml").exists()


def test_draft_reading_note_does_not_overwrite_ready_note(tmp_path):
    config = prepare_project(tmp_path)
    write_mock_llm_config(config)
    config = load_project_config(tmp_path)
    source = write_long_source(tmp_path)
    write_metadata_record(
        config,
        metadata_values(local_pdf=str(source), pdf_status="local"),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    draft_reading_note(config, "P001", source_file=str(source))

    with pytest.raises(DraftError) as exc:
        draft_reading_note(
            config,
            "P001",
            source_file=str(source),
            overwrite_draft=True,
        )

    assert "note_status: draft" in str(exc.value)
