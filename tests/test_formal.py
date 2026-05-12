from pathlib import Path

import yaml

from rsa_cli.cli import main
from rsa_cli.config import load_project_config
from rsa_cli.formal import FormalWriteError, apply_map_requests, validate_apply_map_requests
from rsa_cli.map import parse_literature_map
from rsa_cli.metadata import write_metadata_record
from rsa_cli.rounds import create_research_round, load_round_summary
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(title: str = "Formal Map Paper") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/formal",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "支持优先问题。",
        "last_checked": "2026-05-12",
        "pdf_status": "not_acquired",
        "local_pdf": None,
        "assets": [],
        "topic_profile": "sar_noncontinuous_aperture",
        "priority_questions": ["Q1"],
        "used_for": ["背景"],
        "research_roles": ["theory"],
        "notes": "人工备注",
    }


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    return config


def create_completed_round(config, *, request_overrides=None, status="completed"):
    profile = config.topic_profiles_root / "sar_noncontinuous_aperture.yaml"
    result = create_research_round(config, profile, "Formal apply", "formal apply")
    request = {
        "request_type": "add_map_row",
        "paper_id": "P001",
        "target_file": "literature_map.md",
        "topic_profile": "sar_noncontinuous_aperture",
        "priority_question": "Q1",
        "thesis_section": "第2章",
        "planned_output": "综述背景",
        "research_role": "theory",
        "reason": "解释孔径缺失影响。",
    }
    if request_overrides:
        request.update(request_overrides)
    summary = load_round_summary(result.path)
    frontmatter = {
        "status": status,
        "included_files": [],
        "formal_write_requests": [request],
        "human_confirmed": True,
        "confirmed_by": "zxy",
        "confirmed_at": "2026-05-12",
    }
    summary.path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n"
        + summary.body,
        encoding="utf-8",
    )
    return result.round_id


def test_apply_map_requires_cli_confirmation(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(config, metadata_values(), human_confirmed=True, confirmed_by="zxy")
    round_id = create_completed_round(config)
    before = config.literature_map_path.read_text(encoding="utf-8")

    try:
        apply_map_requests(config, round_id, human_confirmed=False, confirmed_by="zxy")
    except FormalWriteError as exc:
        assert "human_confirmed" in str(exc) or "--human-confirmed" in str(exc)
    else:
        raise AssertionError("expected FormalWriteError")

    assert config.literature_map_path.read_text(encoding="utf-8") == before


def test_apply_map_requires_completed_source_round(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(config, metadata_values(), human_confirmed=True, confirmed_by="zxy")
    round_id = create_completed_round(config, status="ready_for_review")

    try:
        validate_apply_map_requests(config, round_id)
    except FormalWriteError as exc:
        assert "ready_for_review" in str(exc)
    else:
        raise AssertionError("expected FormalWriteError")


def test_apply_map_appends_approved_row_and_skips_metadata_requests(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(config, metadata_values(), human_confirmed=True, confirmed_by="zxy")
    round_id = create_completed_round(config)
    summary = load_round_summary(config.agent_outputs_root / round_id)
    frontmatter = dict(summary.frontmatter)
    frontmatter["formal_write_requests"].append(
        {
            "request_type": "add_metadata",
            "source_file": "verification_review.md",
            "source_row": 1,
            "candidate_title": "Candidate",
            "doi_or_url": "10.1/candidate",
            "reason": "已核验，后续走 metadata gate。",
        }
    )
    summary.path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n"
        + summary.body,
        encoding="utf-8",
    )

    result = apply_map_requests(
        config,
        round_id,
        human_confirmed=True,
        confirmed_by="zxy",
    )
    rows, errors = parse_literature_map(config.literature_map_path)

    assert result.applied_count == 1
    assert result.skipped_metadata_count == 1
    assert errors == []
    assert rows[0].paper_id == "P001"
    assert rows[0].map_status == "approved"
    assert rows[0].evidence_note == "解释孔径缺失影响。"
    assert list(config.metadata_root.glob("P*.yaml")) == [config.metadata_root / "P001.yaml"]


def test_apply_map_blocks_missing_metadata_invalid_role_and_duplicates(tmp_path):
    config = prepare_project(tmp_path)
    round_id = create_completed_round(config, request_overrides={"research_role": "unknown"})
    before = config.literature_map_path.read_text(encoding="utf-8")

    try:
        apply_map_requests(config, round_id, human_confirmed=True, confirmed_by="zxy")
    except FormalWriteError as exc:
        assert "P001" in str(exc)
        assert "research_role" in str(exc)
    else:
        raise AssertionError("expected FormalWriteError")
    assert config.literature_map_path.read_text(encoding="utf-8") == before

    write_metadata_record(config, metadata_values(), human_confirmed=True, confirmed_by="zxy")
    round_id = create_completed_round(config)
    apply_map_requests(config, round_id, human_confirmed=True, confirmed_by="zxy")
    before_duplicate = config.literature_map_path.read_text(encoding="utf-8")

    try:
        apply_map_requests(config, round_id, human_confirmed=True, confirmed_by="zxy")
    except FormalWriteError as exc:
        assert "重复" in str(exc) or "冲突" in str(exc)
    else:
        raise AssertionError("expected duplicate FormalWriteError")
    assert config.literature_map_path.read_text(encoding="utf-8") == before_duplicate


def test_cli_formal_apply_map_positive_and_negative(tmp_path, capsys):
    config = prepare_project(tmp_path)
    write_metadata_record(config, metadata_values(), human_confirmed=True, confirmed_by="zxy")
    round_id = create_completed_round(config)

    missing = main(["--root", str(tmp_path), "formal", "apply-map", "--source-round", round_id])
    missing_out = capsys.readouterr()
    ok = main(
        [
            "--root",
            str(tmp_path),
            "formal",
            "apply-map",
            "--source-round",
            round_id,
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    ok_out = capsys.readouterr()

    assert missing == 1
    assert "--human-confirmed" in missing_out.err or "human_confirmed" in missing_out.err
    assert "Traceback" not in missing_out.err
    assert ok == 0
    assert "正式映射写入完成" in ok_out.out
