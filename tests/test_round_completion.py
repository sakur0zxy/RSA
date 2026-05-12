from pathlib import Path

import yaml

from rsa_cli.config import load_project_config
from rsa_cli.rounds import (
    load_round_summary,
    validate_formal_write_requests,
    validate_round_archive,
)
from rsa_cli.skeleton import create_literature_skeleton


def prepare_round(tmp_path: Path):
    from rsa_cli.rounds import create_research_round

    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    profile = tmp_path / "01_literature" / "topic_profiles" / "sar_noncontinuous_aperture.yaml"
    result = create_research_round(config, profile, objective="Round validation", name="phase three")
    return config, result.path, result.round_id


def update_summary_frontmatter(round_dir: Path, **updates) -> None:
    summary = load_round_summary(round_dir)
    frontmatter = dict(summary.frontmatter)
    frontmatter.update(updates)
    text = (
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n"
        + summary.body
    )
    summary.path.write_text(text, encoding="utf-8")


def test_new_round_summary_has_frontmatter_and_valid_draft_archive(tmp_path):
    config, round_dir, round_id = prepare_round(tmp_path)

    summary_text = (round_dir / "final_round_summary.md").read_text(encoding="utf-8")
    result = validate_round_archive(config, round_id)

    assert summary_text.startswith("---\n")
    assert result.errors == []
    assert result.status == "draft"


def test_missing_required_file_is_reported(tmp_path):
    config, round_dir, round_id = prepare_round(tmp_path)
    (round_dir / "README.md").unlink()

    result = validate_round_archive(config, round_id)

    assert any("README.md" in error for error in result.errors)


def test_declared_optional_file_must_exist(tmp_path):
    config, round_dir, round_id = prepare_round(tmp_path)
    update_summary_frontmatter(round_dir, included_files=["verification_review.md"])

    result = validate_round_archive(config, round_id)

    assert any("included_files" in error and "verification_review.md" in error for error in result.errors)


def test_completed_requires_human_confirmation_fields(tmp_path):
    config, round_dir, round_id = prepare_round(tmp_path)
    update_summary_frontmatter(
        round_dir,
        status="completed",
        human_confirmed=False,
        confirmed_by="",
        confirmed_at="",
    )

    result = validate_round_archive(config, round_id, completion_check=True)

    assert any("human_confirmed" in error for error in result.errors)
    assert any("confirmed_by" in error for error in result.errors)
    assert any("confirmed_at" in error for error in result.errors)


def test_ready_for_review_passes_archive_validation_but_not_completion_check(tmp_path):
    config, round_dir, round_id = prepare_round(tmp_path)
    update_summary_frontmatter(round_dir, status="ready_for_review")

    archive = validate_round_archive(config, round_id)
    complete = validate_round_archive(config, round_id, completion_check=True)

    assert archive.errors == []
    assert any("ready_for_review" in error for error in complete.errors)


def test_candidate_review_rows_must_be_resolved(tmp_path):
    config, round_dir, round_id = prepare_round(tmp_path)
    (round_dir / "verification_review.md").write_text(
        "\n".join(
            [
                "# 候选文献核验记录",
                "| candidate_title | source | doi_or_url | decision | reason | last_checked |",
                "|-----------------|--------|------------|----------|--------|--------------|",
                "| Paper A | web | 10.1/a | include |  |  |",
            ]
        ),
        encoding="utf-8",
    )
    update_summary_frontmatter(round_dir, included_files=["verification_review.md"])

    result = validate_round_archive(config, round_id)

    assert any("decision" in error and "verified/rejected/uncertain" in error for error in result.errors)
    assert any("reason" in error for error in result.errors)
    assert any("last_checked" in error for error in result.errors)


def test_formal_write_request_schema_accepts_supported_requests():
    errors = validate_formal_write_requests(
        [
            {
                "request_type": "add_metadata",
                "source_file": "verification_review.md",
                "source_row": 1,
                "candidate_title": "Paper",
                "doi_or_url": "10.1/example",
                "reason": "已核验",
            },
            {
                "request_type": "add_map_row",
                "paper_id": "P001",
                "target_file": "literature_map.md",
                "priority_question": "Q1",
                "research_role": "theory",
                "reason": "支持理论背景",
            },
        ]
    )

    assert errors == []


def test_add_map_row_requires_literature_map_target():
    errors = validate_formal_write_requests(
        [
            {
                "request_type": "add_map_row",
                "paper_id": "P001",
                "target_file": "paper_index.md",
                "priority_question": "Q1",
                "research_role": "theory",
                "reason": "支持理论背景",
            }
        ]
    )

    assert any("target_file" in error and "literature_map.md" in error for error in errors)
