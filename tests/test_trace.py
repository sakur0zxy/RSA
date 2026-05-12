from pathlib import Path

import yaml

from rsa_cli.config import load_project_config
from rsa_cli.rounds import create_research_round, load_round_summary
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.trace import TraceError, write_trace_summary


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    return config


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    yaml_text = text.split("---", 2)[1]
    loaded = yaml.safe_load(yaml_text)
    assert isinstance(loaded, dict)
    return loaded


def test_write_trace_summary_extracts_tools_decisions_and_approvals(tmp_path):
    config = prepare_project(tmp_path)
    profile = config.topic_profiles_root / "sar_noncontinuous_aperture.yaml"
    round_result = create_research_round(
        config,
        profile,
        "Trace fixture",
        "trace fixture",
        allowed_tools=["web_search", "local_pdf"],
    )
    (round_result.path / "verification_review.md").write_text(
        "| candidate_title | source | doi_or_url | decision | reason | last_checked |\n"
        "|-----------------|--------|------------|----------|--------|--------------|\n"
        "| Useful Paper | publisher | 10.1/useful | verified | supports Q1 | 2026-05-13 |\n"
        "| Rejected Paper | blog | https://example.test | rejected | weak source | 2026-05-13 |\n"
        "| Maybe Paper | arxiv | 10.1/maybe | uncertain | needs review | 2026-05-13 |\n",
        encoding="utf-8",
    )
    summary = load_round_summary(round_result.path)
    fm = dict(summary.frontmatter)
    fm.update(
        {
            "status": "completed",
            "included_files": ["verification_review.md"],
            "formal_write_requests": [
                {
                    "request_type": "add_map_row",
                    "paper_id": "P001",
                    "target_file": "literature_map.md",
                    "topic_profile": "sar_noncontinuous_aperture",
                    "priority_question": "Q1",
                    "thesis_section": "chapter 2",
                    "planned_output": "background",
                    "research_role": "theory",
                    "reason": "supports Q1",
                }
            ],
            "human_confirmed": True,
            "confirmed_by": "zxy",
            "confirmed_at": "2026-05-13",
        }
    )
    summary.path.write_text(
        "---\n"
        + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
        + "---\n"
        + summary.body,
        encoding="utf-8",
    )
    map_before = config.literature_map_path.read_text(encoding="utf-8")

    result = write_trace_summary(config, round_result.round_id)
    fm = frontmatter(result.path)

    assert result.path == round_result.path / "trace_summary.md"
    assert fm["tools_used"] == ["web_search", "local_pdf"]
    assert any("Useful Paper" in item for item in fm["decisions_made"])
    assert any("Rejected Paper" in item for item in fm["rejected_items"])
    assert any("Maybe Paper" in item for item in fm["uncertain_items"])
    assert any("zxy" in item for item in fm["human_approvals"])
    assert fm["formal_write_request_count"] == 1
    assert config.literature_map_path.read_text(encoding="utf-8") == map_before


def test_write_trace_summary_reports_missing_round(tmp_path):
    config = prepare_project(tmp_path)

    try:
        write_trace_summary(config, "R999_missing")
    except TraceError as exc:
        assert "R999_missing" in str(exc)
    else:
        raise AssertionError("expected TraceError")
