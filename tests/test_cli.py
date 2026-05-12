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


def add_paper_args(title="CLI Paper"):
    return [
        "add-paper",
        "--title",
        title,
        "--author",
        "Ada Lovelace",
        "--year",
        "2024",
        "--venue",
        "Journal of Tests",
        "--doi",
        "10.1234/cli",
        "--source-reliability",
        "publisher",
        "--decision",
        "include",
        "--decision-reason",
        "直接支撑优先问题。",
        "--last-checked",
        "2026-05-11",
        "--pdf-status",
        "not_acquired",
        "--used-for",
        "背景",
        "--research-role",
        "baseline",
    ]


def test_help_lists_expected_subcommands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    captured = capsys.readouterr()

    assert exc.value.code == 0
    assert "init" in captured.out
    assert "validate-profile" in captured.out
    assert "new-round" in captured.out
    assert "round" in captured.out
    assert "validate-metadata" in captured.out
    assert "add-paper" in captured.out
    assert "validate-index" in captured.out
    assert "regenerate-index" in captured.out


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


def test_cli_round_validate_and_complete_check(tmp_path, capsys):
    profile = prepare_project(tmp_path)
    main(
        [
            "--root",
            str(tmp_path),
            "new-round",
            "--topic",
            str(profile),
            "--objective",
            "Round validate",
            "--name",
            "phase three",
        ]
    )
    capsys.readouterr()

    ok = main(["--root", str(tmp_path), "round", "validate", "R001_phase_three"])
    ok_out = capsys.readouterr()
    complete = main(
        ["--root", str(tmp_path), "round", "complete-check", "R001_phase_three"]
    )
    complete_out = capsys.readouterr()

    assert ok == 0
    assert "archive" in ok_out.out
    assert complete == 1
    assert "ready_for_review" in complete_out.err
    assert "Traceback" not in complete_out.err


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


def test_cli_init_writes_updated_review_and_search_templates(tmp_path, capsys):
    exit_code = main(["--root", str(tmp_path), "init"])
    capsys.readouterr()

    assert exit_code == 0
    assert "candidate_title" in (
        tmp_path / "templates" / "verification_review.md"
    ).read_text(encoding="utf-8")
    assert "候选文献" in (tmp_path / "templates" / "search_candidates.md").read_text(
        encoding="utf-8"
    )


def test_cli_add_paper_without_human_confirmation_writes_nothing(tmp_path, capsys):
    prepare_project(tmp_path)

    exit_code = main(["--root", str(tmp_path), *add_paper_args()])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "human_confirmed" in captured.err
    assert "Traceback" not in captured.err
    assert list((tmp_path / "01_literature" / "metadata").glob("P*.yaml")) == []


def test_cli_add_paper_success_allocates_sequential_ids(tmp_path, capsys):
    prepare_project(tmp_path)

    first = main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("First CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    first_out = capsys.readouterr()
    second = main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Second CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    second_out = capsys.readouterr()

    metadata_root = tmp_path / "01_literature" / "metadata"
    assert first == 0
    assert second == 0
    assert "已写入正式文献 P001" in first_out.out
    assert "P002" in second_out.out
    assert (metadata_root / "P001.yaml").exists()
    assert (metadata_root / "P002.yaml").exists()
    assert (tmp_path / "01_literature" / "assets" / "P001" / ".gitkeep").exists()


def test_cli_validate_metadata_reports_success_and_errors_without_traceback(tmp_path, capsys):
    prepare_project(tmp_path)
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Validated CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()
    valid_path = tmp_path / "01_literature" / "metadata" / "P001.yaml"

    ok = main(["validate-metadata", str(valid_path)])
    ok_out = capsys.readouterr()
    bad = main(["validate-metadata", str(tmp_path / "missing.yaml")])
    bad_out = capsys.readouterr()

    assert ok == 0
    assert "元数据有效" in ok_out.out
    assert bad == 1
    assert "Traceback" not in bad_out.err


def test_cli_index_smoke_and_stale_validation_is_read_only(tmp_path, capsys):
    prepare_project(tmp_path)
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Indexed CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()

    regen = main(["--root", str(tmp_path), "regenerate-index"])
    regen_out = capsys.readouterr()
    validate = main(["--root", str(tmp_path), "validate-index"])
    validate_out = capsys.readouterr()

    index_path = tmp_path / "01_literature" / "paper_index.md"
    assert regen == 0
    assert "已重建文献索引" in regen_out.out
    assert validate == 0
    assert "索引一致" in validate_out.out
    assert "P001" in index_path.read_text(encoding="utf-8")

    index_path.write_text("stale text\n", encoding="utf-8")
    stale = main(["--root", str(tmp_path), "validate-index"])
    stale_out = capsys.readouterr()

    assert stale == 1
    assert "rsa regenerate-index" in stale_out.err
    assert index_path.read_text(encoding="utf-8") == "stale text\n"
    assert "Traceback" not in stale_out.err
