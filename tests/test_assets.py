from pathlib import Path

import yaml

from rsa_cli.assets import (
    AssetError,
    add_asset_record,
    add_source_record,
    asset_status,
    source_status,
    validate_asset_manifest,
    validate_source_record,
)
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values() -> dict:
    return {
        "title": "Asset Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/asset",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试来源与资产登记。",
        "last_checked": "2026-05-13",
        "pdf_status": "not_acquired",
        "local_pdf": None,
        "assets": [],
        "topic_profile": "demo",
        "priority_questions": ["Q1"],
        "used_for": ["资产管理"],
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


def test_add_source_record_copies_file_and_writes_ledger(tmp_path):
    config = prepare_project(tmp_path)
    source = tmp_path / "paper.pdf"
    source.write_text("authorized pdf", encoding="utf-8")

    result = add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="provided",
        source_type="pdf",
        license_note="用户提供 PDF，仅用于本地科研阅读。",
        added_by="zxy",
    )

    assert result.source_id == "S001"
    assert result.local_path.is_file()
    assert result.local_path.parent == config.pdfs_root / "P001"
    assert validate_source_record(config, "P001") == []
    status = source_status(config, "P001")
    assert status.total_count == 1
    assert status.available_count == 1
    report = config.pdf_acquisition_report_path.read_text(encoding="utf-8")
    assert "P001" in report
    assert "available" in report


def test_source_record_requires_formal_metadata_and_license_note(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    source = tmp_path / "paper.pdf"
    source.write_text("authorized pdf", encoding="utf-8")

    try:
        add_source_record(
            config,
            "P001",
            source_file=str(source),
            authorization="provided",
            source_type="pdf",
            license_note="用户提供。",
        )
    except AssetError as exc:
        assert "metadata" in str(exc)
    else:
        raise AssertionError("expected AssetError")

    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    try:
        add_source_record(
            config,
            "P001",
            source_file=str(source),
            authorization="provided",
            source_type="pdf",
            license_note=None,
        )
    except AssetError as exc:
        assert "license-note" in str(exc)
    else:
        raise AssertionError("expected AssetError")


def test_validate_source_record_is_read_only(tmp_path):
    config = prepare_project(tmp_path)
    source = tmp_path / "paper.pdf"
    source.write_text("authorized pdf", encoding="utf-8")
    result = add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="local",
        source_type="pdf",
        license_note="本地已有合法副本。",
    )
    before = result.record_path.read_text(encoding="utf-8")

    assert validate_source_record(config, "P001") == []

    assert result.record_path.read_text(encoding="utf-8") == before


def test_validate_source_record_detects_missing_local_file(tmp_path):
    config = prepare_project(tmp_path)
    source = tmp_path / "paper.pdf"
    source.write_text("authorized pdf", encoding="utf-8")
    result = add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="authorized",
        source_type="pdf",
        license_note="已授权。",
    )
    result.local_path.unlink()

    errors = validate_source_record(config, "P001")

    assert any("local_path" in error and "不存在" in error for error in errors)


def test_add_asset_record_copies_file_and_writes_manifest(tmp_path):
    config = prepare_project(tmp_path)
    asset = tmp_path / "figure.png"
    asset.write_text("image placeholder", encoding="utf-8")

    result = add_asset_record(
        config,
        "P001",
        asset_file=str(asset),
        kind="figure",
        label="Fig. 1",
        description_zh="展示关键实验结果。",
        page="3",
        figure="1",
        added_by="zxy",
    )

    assert result.asset_id == "A001"
    assert result.local_path.is_file()
    assert result.manifest_path == config.assets_root / "P001" / "manifest.yaml"
    assert validate_asset_manifest(config, "P001") == []
    status = asset_status(config, "P001")
    assert status.total_count == 1
    assert status.available_count == 1


def test_validate_asset_manifest_detects_bad_kind(tmp_path):
    config = prepare_project(tmp_path)
    asset = tmp_path / "figure.png"
    asset.write_text("image placeholder", encoding="utf-8")
    result = add_asset_record(
        config,
        "P001",
        asset_file=str(asset),
        kind="screenshot",
    )
    data = yaml.safe_load(result.manifest_path.read_text(encoding="utf-8"))
    data["assets"][0]["kind"] = "unsupported"
    result.manifest_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    errors = validate_asset_manifest(config, "P001")

    assert any("kind" in error and "不支持" in error for error in errors)
