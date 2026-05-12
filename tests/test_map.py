from pathlib import Path

from rsa_cli.config import load_project_config
from rsa_cli.map import (
    MAP_COLUMNS,
    MapRow,
    classify_gap_rows,
    generate_gap_report,
    parse_literature_map,
    render_literature_map,
    validate_gap_report,
    validate_literature_map,
    write_map_proposal,
)
from rsa_cli.metadata import write_metadata_record
from rsa_cli.rounds import create_research_round, load_round_summary
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(title: str = "Mapped Paper") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/map",
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


def test_literature_map_seed_uses_phase3_columns():
    repo_root = Path(__file__).resolve().parents[1]
    text = (repo_root / "01_literature" / "literature_map.md").read_text(
        encoding="utf-8"
    )

    for column in MAP_COLUMNS:
        assert column in text
    for role in [
        "baseline",
        "theory",
        "method",
        "evaluation",
        "comparison",
        "background",
        "risk_or_limitation",
    ]:
        assert role in text
    for status in ["proposed", "approved", "needs_review", "deprecated"]:
        assert status in text


def test_parse_and_render_literature_map_round_trip():
    row = MapRow(
        paper_id="P001",
        topic_profile="sar_noncontinuous_aperture",
        priority_question="Q1",
        thesis_section="第2章",
        planned_output="综述背景",
        research_role="theory",
        evidence_note="解释孔径缺失影响。",
        map_status="approved",
    )

    rendered = render_literature_map([row])
    path = Path("unused")
    rows, errors = parse_literature_map_text_for_test(rendered, path)

    assert errors == []
    assert rows == [row]


def parse_literature_map_text_for_test(text: str, path: Path):
    path.write_text(text, encoding="utf-8")
    try:
        return parse_literature_map(path)
    finally:
        path.unlink(missing_ok=True)


def test_validate_literature_map_rejects_missing_metadata_and_bad_vocab(tmp_path):
    config = prepare_project(tmp_path)
    config.literature_map_path.write_text(
        render_literature_map(
            [
                MapRow(
                    paper_id="P999",
                    topic_profile="sar_noncontinuous_aperture",
                    priority_question="Q1",
                    thesis_section="第2章",
                    planned_output="综述背景",
                    research_role="unknown",
                    evidence_note="证据",
                    map_status="approved",
                )
            ]
        ),
        encoding="utf-8",
    )

    errors = validate_literature_map(config)

    assert any("P999" in error for error in errors)
    assert any("research_role" in error and "unknown" in error for error in errors)


def test_validate_literature_map_accepts_verified_metadata(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(
        config=config,
        values=metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    config.literature_map_path.write_text(
        render_literature_map(
            [
                MapRow(
                    paper_id="P001",
                    topic_profile="sar_noncontinuous_aperture",
                    priority_question="Q1",
                    thesis_section="第2章",
                    planned_output="综述背景",
                    research_role="theory",
                    evidence_note="解释孔径缺失影响。",
                    map_status="approved",
                )
            ]
        ),
        encoding="utf-8",
    )

    assert validate_literature_map(config) == []


def test_validate_literature_map_detects_conflicts(tmp_path):
    config = prepare_project(tmp_path)
    write_metadata_record(
        config=config,
        values=metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    rows = [
        MapRow("P001", "sar_noncontinuous_aperture", "Q1", "第2章", "输出A", "theory", "A", "approved"),
        MapRow("P001", "sar_noncontinuous_aperture", "Q1", "第3章", "输出B", "theory", "B", "approved"),
    ]
    config.literature_map_path.write_text(render_literature_map(rows), encoding="utf-8")

    errors = validate_literature_map(config)

    assert any("冲突" in error for error in errors)


def test_map_proposal_writes_only_round_generated_file(tmp_path):
    config = prepare_project(tmp_path)
    profile = config.topic_profiles_root / "sar_noncontinuous_aperture.yaml"
    result = create_research_round(config, profile, "Proposal", "proposal")
    summary = load_round_summary(result.path)
    summary.path.write_text(
        "---\n"
        "status: ready_for_review\n"
        "included_files: []\n"
        "formal_write_requests:\n"
        "  - request_type: add_map_row\n"
        "    paper_id: P001\n"
        "    target_file: literature_map.md\n"
        "    topic_profile: sar_noncontinuous_aperture\n"
        "    priority_question: Q1\n"
        "    thesis_section: 第2章\n"
        "    planned_output: 综述背景\n"
        "    research_role: theory\n"
        "    reason: 解释孔径缺失影响。\n"
        "human_confirmed: false\n"
        "confirmed_by:\n"
        "confirmed_at:\n"
        "---\n"
        + summary.body,
        encoding="utf-8",
    )
    before = config.literature_map_path.read_text(encoding="utf-8")

    proposal = write_map_proposal(config, result.round_id)

    assert proposal.name == "map_proposal.md"
    assert "formal_write_requests" in proposal.read_text(encoding="utf-8")
    assert "rsa formal apply-map" in proposal.read_text(encoding="utf-8")
    assert config.literature_map_path.read_text(encoding="utf-8") == before


def test_gap_classification_covers_weak_and_missing():
    rows = [
        MapRow("P001", "topic", "Q1", "第2章", "综述", "theory", "note", "approved"),
        MapRow("P002", "topic", "Q2", "", "", "background", "note", "approved"),
    ]

    gaps = classify_gap_rows("topic", ["Q1", "Q2", "Q3"], rows)

    assert gaps[0].status == "covered"
    assert gaps[1].status == "weak"
    assert "only_background_evidence" in gaps[1].weak_reason
    assert "missing_thesis_section" in gaps[1].weak_reason
    assert gaps[2].status == "missing"


def test_gap_generate_and_validate_are_deterministic(tmp_path):
    config = prepare_project(tmp_path)
    config.literature_map_path.write_text(render_literature_map([]), encoding="utf-8")

    path, report = generate_gap_report(config, "sar_noncontinuous_aperture")
    errors = validate_gap_report(config, "sar_noncontinuous_aperture")
    path.write_text("stale\n", encoding="utf-8")
    stale = validate_gap_report(config, "sar_noncontinuous_aperture")

    assert path.name == "sar_noncontinuous_aperture_gap_report.md"
    assert "不是最终学术结论" in report
    assert errors == []
    assert stale
