from pathlib import Path

from rsa_cli.config import load_project_config
from rsa_cli.index import (
    generate_paper_index,
    regenerate_paper_index,
    render_paper_index,
    validate_paper_index,
)
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(title: str = "A Verified Paper") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/test",
        "official_url": None,
        "source_reliability": "publisher",
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
    }


def test_render_paper_index_is_sorted_and_chinese_explained():
    rendered = render_paper_index(
        [
            {
                "paper_id": "P002",
                "year": "2025",
                "title": "Second",
                "venue": "Venue",
                "decision": "include",
                "used_for": ["对比"],
                "pdf_status": "local",
            },
            {
                "paper_id": "P001",
                "year": "2024",
                "title": "First",
                "venue": "Venue",
                "decision": "include",
                "used_for": ["背景"],
                "pdf_status": "not_acquired",
            },
        ]
    )

    assert rendered.index("P001") < rendered.index("P002")
    assert "# 文献索引" in rendered
    assert "字段说明" in rendered
    assert "metadata/P###.yaml" in rendered
    for column in ["paper_id", "year", "title", "venue", "decision", "used_for", "pdf_status"]:
        assert column in rendered


def test_regenerate_and_validate_paper_index(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config=config,
        values=metadata_values("Index Paper"),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    path = regenerate_paper_index(config)

    text = path.read_text(encoding="utf-8")
    assert "P001" in text
    assert "Index Paper" in text
    assert validate_paper_index(config) == []


def test_validate_index_reports_stale_file_without_rewriting(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config=config,
        values=metadata_values("Stale Check"),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    config.paper_index_path.write_text("stale text\n", encoding="utf-8")

    errors = validate_paper_index(config)

    assert errors
    assert "rsa regenerate-index" in errors[0]
    assert config.paper_index_path.read_text(encoding="utf-8") == "stale text\n"


def test_empty_committed_index_matches_renderer():
    repo_root = Path(__file__).resolve().parents[1]
    index_text = (repo_root / "01_literature" / "paper_index.md").read_text(
        encoding="utf-8"
    )

    assert index_text == render_paper_index([])


def test_generate_paper_index_reads_metadata_records(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config=config,
        values=metadata_values("Generated Paper"),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    generated = generate_paper_index(config)

    assert "P001" in generated
    assert "Generated Paper" in generated
