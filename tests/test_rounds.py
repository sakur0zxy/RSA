from pathlib import Path

import pytest

from rsa_cli.config import load_project_config
from rsa_cli.rounds import RoundError, create_research_round
from rsa_cli.skeleton import create_literature_skeleton


def round_payloads(root: Path) -> list[Path]:
    agent_outputs = root / "01_literature" / "agent_outputs"
    return [path for path in agent_outputs.iterdir() if path.name != ".gitkeep"]


def prepare_project(root: Path):
    config = load_project_config(root)
    create_literature_skeleton(config)
    profile = root / "01_literature" / "topic_profiles" / "sar_noncontinuous_aperture.yaml"
    return config, profile


def test_create_first_round_writes_required_files_only_under_agent_outputs(tmp_path):
    config, profile = prepare_project(tmp_path)
    paper_index_before = (tmp_path / "01_literature" / "paper_index.md").read_text(
        encoding="utf-8"
    )
    map_before = (tmp_path / "01_literature" / "literature_map.md").read_text(
        encoding="utf-8"
    )

    result = create_research_round(
        config,
        profile,
        objective="Find starter evidence",
        name="short topic name",
    )

    round_dir = tmp_path / "01_literature" / "agent_outputs" / "R001_short_topic_name"
    assert result.round_id == "R001_short_topic_name"
    assert result.path == round_dir
    assert (round_dir / "README.md").exists()
    assert (round_dir / "final_round_summary.md").exists()
    assert (round_dir / "trace_summary.md").exists()
    assert (round_dir / "final_round_summary.md").read_text(encoding="utf-8").startswith(
        "---\n"
    )
    assert (round_dir / "trace_summary.md").read_text(encoding="utf-8").startswith(
        "---\n"
    )
    assert not (round_dir / "search_candidates.md").exists()
    assert sorted(p.name for p in (tmp_path / "01_literature" / "metadata").iterdir()) == [
        ".gitkeep"
    ]
    assert sorted(p.name for p in (tmp_path / "01_literature" / "notes").iterdir()) == [
        ".gitkeep"
    ]
    assert (tmp_path / "01_literature" / "paper_index.md").read_text(
        encoding="utf-8"
    ) == paper_index_before
    assert (tmp_path / "01_literature" / "literature_map.md").read_text(
        encoding="utf-8"
    ) == map_before


def test_round_number_increments(tmp_path):
    config, profile = prepare_project(tmp_path)

    first = create_research_round(config, profile, "First", "starter")
    second = create_research_round(config, profile, "Second", "starter")

    assert first.round_id == "R001_starter"
    assert second.round_id == "R002_starter"


def test_candidate_hard_cap_fails_before_directory_creation(tmp_path):
    config, profile = prepare_project(tmp_path)

    with pytest.raises(RoundError, match="硬上限"):
        create_research_round(
            config,
            profile,
            objective="Too large",
            name="too large",
            max_candidates=21,
        )

    assert round_payloads(tmp_path) == []


def test_unsafe_round_name_fails_before_directory_creation(tmp_path):
    config, profile = prepare_project(tmp_path)

    with pytest.raises(RoundError, match="路径分隔符"):
        create_research_round(
            config,
            profile,
            objective="Unsafe",
            name="../unsafe",
        )

    assert round_payloads(tmp_path) == []


def test_campaign_id_is_recorded_without_nested_campaign_directories(tmp_path):
    config, profile = prepare_project(tmp_path)

    result = create_research_round(
        config,
        profile,
        objective="Campaign smoke",
        name="campaign smoke",
        max_candidates=5,
        campaign_id="C001",
    )

    readme = (result.path / "README.md").read_text(encoding="utf-8")
    assert "Campaign ID: C001" in readme
    assert not (tmp_path / "01_literature" / "agent_outputs" / "C001").exists()
