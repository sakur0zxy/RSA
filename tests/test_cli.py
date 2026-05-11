import pytest

from rsa_cli.cli import main
from rsa_cli.config import load_project_config
from rsa_cli.skeleton import create_literature_skeleton


def prepare_project(root):
    config = load_project_config(root)
    create_literature_skeleton(config)
    return root / "01_literature" / "topic_profiles" / "sar_noncontinuous_aperture.yaml"


def round_payloads(root):
    agent_outputs = root / "01_literature" / "agent_outputs"
    return [path for path in agent_outputs.iterdir() if path.name != ".gitkeep"]


def test_help_lists_expected_subcommands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    captured = capsys.readouterr()

    assert exc.value.code == 0
    assert "init" in captured.out
    assert "validate-profile" in captured.out
    assert "new-round" in captured.out


def test_cli_init_and_validate_profile(tmp_path, capsys):
    exit_code = main(["--root", str(tmp_path), "init"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Initialized literature foundation" in captured.out

    profile = tmp_path / "01_literature" / "topic_profiles" / "sar_noncontinuous_aperture.yaml"
    exit_code = main(["validate-profile", str(profile)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Profile valid" in captured.out


def test_cli_new_round_success(tmp_path, capsys):
    profile = prepare_project(tmp_path)

    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "new-round",
            "--topic",
            str(profile),
            "--objective",
            "Smoke test",
            "--name",
            "short topic name",
            "--max-candidates",
            "5",
            "--allowed-tool",
            "web_search",
            "--campaign-id",
            "C001",
        ]
    )
    captured = capsys.readouterr()

    round_dir = tmp_path / "01_literature" / "agent_outputs" / "R001_short_topic_name"
    assert exit_code == 0
    assert "Created round R001_short_topic_name" in captured.out
    assert (round_dir / "README.md").exists()
    assert (round_dir / "final_round_summary.md").exists()


def test_cli_new_round_validates_profile_before_writing(tmp_path, capsys):
    prepare_project(tmp_path)
    bad_profile = tmp_path / "bad.yaml"
    bad_profile.write_text("topic_id: bad\ntopic_name: Bad\n", encoding="utf-8")

    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "new-round",
            "--topic",
            str(bad_profile),
            "--objective",
            "Bad profile",
            "--name",
            "bad profile",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "topic profile invalid" in captured.err
    assert round_payloads(tmp_path) == []


def test_cli_new_round_expected_errors_have_no_traceback(tmp_path, capsys):
    profile = prepare_project(tmp_path)

    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "new-round",
            "--topic",
            str(profile),
            "--objective",
            "Too many",
            "--name",
            "too many",
            "--max-candidates",
            "21",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "hard cap" in captured.err
    assert "Traceback" not in captured.err


def test_agents_guidance_mentions_cli_and_asset_policy():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")

    assert "rsa init" in agents
    assert "rsa validate-profile" in agents
    assert "rsa new-round" in agents
    assert "PDFs are local-only" in agents
    assert "screenshots and result assets are local-only" in agents
    assert "human confirmation before writes" in agents
