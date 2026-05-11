from pathlib import Path

import yaml

from rsa_cli.config import load_project_config
from rsa_cli.metadata import (
    FIELD_DESCRIPTIONS_ZH,
    METADATA_FIELDS,
    MetadataError,
    next_paper_id,
    validate_metadata_record,
    write_metadata_record,
)
from rsa_cli.skeleton import create_literature_skeleton


def valid_record(paper_id: str = "P001") -> dict:
    return {
        "paper_id": paper_id,
        "title": "A Verified Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/test",
        "official_url": None,
        "source_reliability": "publisher",
        "verification_status": "verified",
        "decision": "include",
        "decision_reason": "直接支撑优先问题。",
        "last_checked": "2026-05-11",
        "pdf_status": "not_acquired",
        "local_pdf": None,
        "assets": [],
        "topic_profile": "topic_profiles/demo.yaml",
        "priority_questions": ["Q1"],
        "used_for": ["背景"],
        "research_roles": ["baseline"],
        "notes": "人工备注",
        "human_confirmed": True,
        "confirmed_by": "zxy",
        "confirmed_at": "2026-05-11",
    }


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_metadata_fields_have_chinese_descriptions():
    assert METADATA_FIELDS == [
        "paper_id",
        "title",
        "authors",
        "year",
        "venue",
        "doi",
        "official_url",
        "source_reliability",
        "verification_status",
        "decision",
        "decision_reason",
        "last_checked",
        "pdf_status",
        "local_pdf",
        "assets",
        "topic_profile",
        "priority_questions",
        "used_for",
        "research_roles",
        "notes",
        "human_confirmed",
        "confirmed_by",
        "confirmed_at",
    ]
    assert set(FIELD_DESCRIPTIONS_ZH) == set(METADATA_FIELDS)
    assert all(FIELD_DESCRIPTIONS_ZH[field] for field in METADATA_FIELDS)


def test_valid_metadata_record_returns_no_errors(tmp_path):
    path = tmp_path / "P001.yaml"
    write_yaml(path, valid_record())

    assert validate_metadata_record(path) == []


def test_metadata_rejects_unconfirmed_record(tmp_path):
    record = valid_record()
    record["human_confirmed"] = False
    path = tmp_path / "P001.yaml"
    write_yaml(path, record)

    errors = validate_metadata_record(path)

    assert any("human_confirmed" in error for error in errors)


def test_metadata_requires_doi_or_official_url(tmp_path):
    record = valid_record()
    record["doi"] = None
    record["official_url"] = None
    path = tmp_path / "P001.yaml"
    write_yaml(path, record)

    errors = validate_metadata_record(path)

    assert any("doi" in error and "official_url" in error for error in errors)


def test_metadata_filename_must_match_paper_id(tmp_path):
    path = tmp_path / "P002.yaml"
    write_yaml(path, valid_record("P001"))

    errors = validate_metadata_record(path)

    assert any("paper_id" in error for error in errors)


def test_next_paper_id_ignores_non_formal_files(tmp_path):
    metadata_root = tmp_path / "metadata"
    metadata_root.mkdir()
    (metadata_root / ".gitkeep").write_text("", encoding="utf-8")
    (metadata_root / "verification_review.md").write_text("candidate", encoding="utf-8")

    assert next_paper_id(metadata_root) == "P001"

    write_yaml(metadata_root / "P001.yaml", valid_record())

    assert next_paper_id(metadata_root) == "P002"


def test_write_metadata_record_requires_human_confirmation_before_file(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)

    try:
        write_metadata_record(
            config=config,
            values=valid_record(),
            human_confirmed=False,
            confirmed_by="zxy",
        )
    except MetadataError as exc:
        assert "human_confirmed" in str(exc)
    else:
        raise AssertionError("expected MetadataError")

    assert list(config.metadata_root.glob("P*.yaml")) == []


def test_write_metadata_record_allocates_id_and_assets_only_on_success(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)

    first = write_metadata_record(
        config=config,
        values=valid_record(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    second = write_metadata_record(
        config=config,
        values=valid_record(),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    assert first.name == "P001.yaml"
    assert second.name == "P002.yaml"
    assert (config.assets_root / "P001" / ".gitkeep").exists()
    assert validate_metadata_record(first) == []
