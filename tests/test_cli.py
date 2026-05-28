import pytest
import yaml

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


def add_paper_args(title="CLI Paper", *, official_url=None, doi="10.1234/cli"):
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
        doi,
        *(["--official-url", official_url] if official_url else []),
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
    assert "map" in captured.out
    assert "gap" in captured.out
    assert "note" in captured.out
    assert "source" in captured.out
    assert "asset" in captured.out
    assert "visual" in captured.out
    assert "campaign" in captured.out
    assert "score" in captured.out
    assert "workflow" in captured.out
    assert "review" in captured.out
    assert "safety" in captured.out
    assert "worker" in captured.out
    assert "eval" in captured.out
    assert "formal" in captured.out


def test_cli_init_and_validate_profile(tmp_path, capsys):
    exit_code = main(["--root", str(tmp_path), "init"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "已初始化文献基础" in captured.out

    profile = tmp_path / "01_literature" / "topic_profiles" / "sar_noncontinuous_aperture.yaml"
    exit_code = main(["validate-profile", str(profile)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "profile 有效" in captured.out


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
    assert "已创建调研轮次 R001_short_topic_name" in captured.out
    assert (round_dir / "README.md").exists()
    assert (round_dir / "final_round_summary.md").exists()
    assert (round_dir / "trace_summary.md").exists()


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
    assert "topic profile 无效" in captured.err
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
    assert "硬上限" in captured.err
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
    trace = main(["--root", str(tmp_path), "round", "trace", "R001_phase_three"])
    trace_out = capsys.readouterr()
    complete = main(
        ["--root", str(tmp_path), "round", "complete-check", "R001_phase_three"]
    )
    complete_out = capsys.readouterr()

    assert ok == 0
    assert "archive" in ok_out.out
    assert trace == 0
    assert "trace" in trace_out.out
    assert (
        tmp_path
        / "01_literature"
        / "agent_outputs"
        / "R001_phase_three"
        / "trace_summary.md"
    ).exists()
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


def test_cli_map_validate_and_gap_generate(tmp_path, capsys):
    prepare_project(tmp_path)

    map_ok = main(["--root", str(tmp_path), "map", "validate"])
    map_out = capsys.readouterr()
    gap_ok = main(
        [
            "--root",
            str(tmp_path),
            "gap",
            "generate",
            "--topic",
            "sar_noncontinuous_aperture",
        ]
    )
    gap_out = capsys.readouterr()
    gap_validate = main(
        [
            "--root",
            str(tmp_path),
            "gap",
            "validate",
            "--topic",
            "sar_noncontinuous_aperture",
        ]
    )
    gap_validate_out = capsys.readouterr()

    assert map_ok == 0
    assert "文献映射有效" in map_out.out
    assert gap_ok == 0
    assert "研究空白报告" in gap_out.out
    assert gap_validate == 0
    assert "研究空白报告一致" in gap_validate_out.out


def test_cli_note_create_validate_and_status(tmp_path, capsys):
    profile = prepare_project(tmp_path)
    source = tmp_path / "01_literature" / "pdfs" / "P001.pdf"
    source.write_text("authorized local source", encoding="utf-8")
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Reading Note CLI Paper"),
            "--pdf-status",
            "local",
            "--local-pdf",
            str(source),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()

    created = main(
        [
            "--root",
            str(tmp_path),
            "note",
            "create",
            "P001",
            "--source-file",
            str(source),
            "--authorization",
            "local",
        ]
    )
    created_out = capsys.readouterr()
    valid = main(["--root", str(tmp_path), "note", "validate", "P001"])
    valid_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "note", "status", "P001"])
    status_out = capsys.readouterr()

    assert profile.exists()
    assert created == 0
    assert "已创建阅读笔记" in created_out.out
    assert valid == 0
    assert "阅读笔记有效" in valid_out.out
    assert status == 0
    assert "draft" in status_out.out


def test_cli_note_draft_generates_ready_review_packet(tmp_path, capsys):
    prepare_project(tmp_path)
    local_yaml = tmp_path / ".rsa" / "local.yaml"
    local_yaml.parent.mkdir(parents=True, exist_ok=True)
    local_yaml.write_text(
        """
reading_draft:
  llm:
    provider: mock
    model: mock-reading-draft
""",
        encoding="utf-8",
    )
    source = tmp_path / "authorized-full-text.pdf"
    source.write_text(
        (
            "This paper studies gapped aperture SAR imaging with reconstruction experiments. "
            "Figure 3 reports results and Table 1 lists metrics. "
        )
        * 8,
        encoding="utf-8",
    )
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Draft CLI Paper"),
            "--pdf-status",
            "local",
            "--local-pdf",
            str(source),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()

    drafted = main(
        [
            "--root",
            str(tmp_path),
            "note",
            "draft",
            "P001",
            "--source-file",
            str(source),
        ]
    )
    drafted_out = capsys.readouterr()
    valid = main(["--root", str(tmp_path), "note", "validate", "P001"])
    valid_out = capsys.readouterr()

    assert drafted == 0
    assert "已生成自动阅读草稿" in drafted_out.out
    assert "ready_for_review" in drafted_out.out
    assert "score=" in drafted_out.out
    assert valid == 0
    assert "阅读笔记有效" in valid_out.out
    assert (tmp_path / "01_literature" / "notes" / "P001_review_packet.md").exists()


def test_cli_source_and_asset_add_validate_status(tmp_path, capsys):
    prepare_project(tmp_path)
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Source Asset CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()
    source = tmp_path / "source.pdf"
    source.write_text("authorized source", encoding="utf-8")
    asset = tmp_path / "figure.png"
    asset.write_text("asset", encoding="utf-8")

    source_add = main(
        [
            "--root",
            str(tmp_path),
            "source",
            "add",
            "P001",
            "--source-file",
            str(source),
            "--authorization",
            "provided",
            "--license-note",
            "用户提供 PDF，仅用于本地科研阅读。",
            "--added-by",
            "zxy",
        ]
    )
    source_add_out = capsys.readouterr()
    source_validate = main(["--root", str(tmp_path), "source", "validate", "P001"])
    source_validate_out = capsys.readouterr()
    source_status_code = main(["--root", str(tmp_path), "source", "status", "P001"])
    source_status_out = capsys.readouterr()

    asset_add = main(
        [
            "--root",
            str(tmp_path),
            "asset",
            "add",
            "P001",
            "--file",
            str(asset),
            "--kind",
            "figure",
            "--label",
            "Fig. 1",
            "--description-zh",
            "关键结果图。",
            "--added-by",
            "zxy",
        ]
    )
    asset_add_out = capsys.readouterr()
    asset_validate = main(["--root", str(tmp_path), "asset", "validate", "P001"])
    asset_validate_out = capsys.readouterr()
    asset_status_code = main(["--root", str(tmp_path), "asset", "status", "P001"])
    asset_status_out = capsys.readouterr()

    assert source_add == 0
    assert "已登记来源 S001" in source_add_out.out
    assert source_validate == 0
    assert "来源记录有效" in source_validate_out.out
    assert source_status_code == 0
    assert "总数=1" in source_status_out.out
    assert asset_add == 0
    assert "已登记资产 A001" in asset_add_out.out
    assert asset_validate == 0
    assert "资产记录有效" in asset_validate_out.out
    assert asset_status_code == 0
    assert "总数=1" in asset_status_out.out


def test_cli_source_add_expected_error_has_no_traceback(tmp_path, capsys):
    prepare_project(tmp_path)
    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "source",
            "add",
            "P001",
            "--source-file",
            str(tmp_path / "missing.pdf"),
            "--authorization",
            "provided",
            "--license-note",
            "用户提供。",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "来源操作失败" in captured.err
    assert "Traceback" not in captured.err


def test_cli_visual_help_validate_status_and_expected_error(tmp_path, capsys):
    from rsa_cli.config import load_project_config
    from rsa_cli.visual import default_advanced_analysis, write_visual_candidates

    prepare_project(tmp_path)
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Visual CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()
    config = load_project_config(tmp_path)
    write_visual_candidates(
        config,
        "P001",
        {
            "paper_id": "P001",
            "candidates": [
                {
                    "candidate_id": "V001",
                    "paper_id": "P001",
                    "asset_id": None,
                    "visual_type": "figure",
                    "page": 1,
                    "region_bbox": [10, 20, 120, 160],
                    "source_rects": [[10, 20, 120, 160]],
                    "source_text": "Figure 1. Reconstruction result.",
                    "caption_zh": "Figure 1. Reconstruction result.",
                    "ocr_summary_zh": "已提取嵌入文本。",
                    "confidence": "medium",
                    "evidence_level": "caption_visual_text",
                    "status": "cropped",
                    "source_links": {
                        "metadata": "01_literature/metadata/P001.yaml",
                        "source_ledger": "01_literature/sources/P001.yaml",
                        "asset_manifest": "01_literature/assets/P001/manifest.yaml",
                    },
                    "advanced_analysis": default_advanced_analysis(),
                    "llm_visual_analysis": {"status": "not_run"},
                }
            ],
        },
    )
    candidate_path = tmp_path / "01_literature" / "assets" / "P001" / "visual_evidence_candidates.yaml"
    before = candidate_path.read_text(encoding="utf-8")

    with pytest.raises(SystemExit) as help_exc:
        main(["visual", "extract", "--help"])
    help_out = capsys.readouterr()
    valid = main(["--root", str(tmp_path), "visual", "validate", "P001"])
    valid_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "visual", "status", "P001"])
    status_out = capsys.readouterr()
    missing_source = main(["--root", str(tmp_path), "visual", "extract", "P001"])
    missing_out = capsys.readouterr()

    assert help_exc.value.code == 0
    assert "--all-detected" in help_out.out
    assert "--pages" in help_out.out
    assert "--asset-suggestions-only" in help_out.out
    assert valid == 0
    assert "视觉证据候选有效" in valid_out.out
    assert status == 0
    assert "视觉证据候选状态" in status_out.out
    assert "总数=1" in status_out.out
    assert candidate_path.read_text(encoding="utf-8") == before
    assert missing_source == 1
    assert "视觉证据操作失败" in missing_out.err
    assert "Traceback" not in missing_out.err


def test_cli_campaign_create_import_validate_status(tmp_path, capsys):
    prepare_project(tmp_path)
    csv_path = tmp_path / "campaign.csv"
    csv_path.write_text(
        "title,doi,year,first_author\n"
        "Campaign CLI Paper,10.1234/campaign-cli,2025,Ada\n"
        "Campaign CLI Paper Duplicate,10.1234/campaign-cli,2025,Ada\n",
        encoding="utf-8",
    )

    created = main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "create",
            "--name-zh",
            "CLI 批量队列",
            "--objective-zh",
            "导入 CLI 候选并做去重。",
            "--created-by",
            "zxy",
        ]
    )
    created_out = capsys.readouterr()
    imported = main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "import",
            "C001",
            "--file",
            str(csv_path),
        ]
    )
    imported_out = capsys.readouterr()
    candidate_path = tmp_path / "01_literature" / "campaigns" / "C001.yaml"
    before = candidate_path.read_text(encoding="utf-8")
    valid = main(["--root", str(tmp_path), "campaign", "validate", "C001"])
    valid_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "campaign", "status", "C001"])
    status_out = capsys.readouterr()

    assert created == 0
    assert "已创建批量队列 C001" in created_out.out
    assert imported == 0
    assert "导入=2" in imported_out.out
    assert "重复=1" in imported_out.out
    assert valid == 0
    assert "批量队列有效" in valid_out.out
    assert status == 0
    assert "批量队列状态" in status_out.out
    assert "duplicate=1" in status_out.out
    assert candidate_path.read_text(encoding="utf-8") == before


def test_cli_campaign_run_queue_report_and_review(tmp_path, capsys):
    prepare_project(tmp_path)
    csv_path = tmp_path / "campaign_run.csv"
    csv_path.write_text(
        "title,doi,year,first_author\n"
        "Campaign Run Paper,10.1234/campaign-run,2026,Ada\n",
        encoding="utf-8",
    )
    created = main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "create",
            "--name-zh",
            "CLI campaign run",
            "--objective-zh",
            "验证 Phase 11 campaign run。",
        ]
    )
    capsys.readouterr()
    imported = main(["--root", str(tmp_path), "campaign", "import", "C001", "--file", str(csv_path)])
    capsys.readouterr()

    run = main(["--root", str(tmp_path), "campaign", "run", "C001", "--dry-run"])
    run_out = capsys.readouterr()
    queue = main(["--root", str(tmp_path), "campaign", "queue", "C001"])
    queue_out = capsys.readouterr()
    report = main(["--root", str(tmp_path), "campaign", "report", "C001"])
    report_out = capsys.readouterr()

    queue_path = tmp_path / "01_literature" / "campaigns" / "C001_review_queue.yaml"
    queue_data = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue_item_id = queue_data["queue_items"][0]["queue_item_id"]
    reviewed = main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "queue",
            "review",
            "C001",
            "--item",
            queue_item_id,
            "--decision",
            "accepted",
            "--reviewer",
            "zxy",
            "--reason",
            "进入后续流程",
        ]
    )
    reviewed_out = capsys.readouterr()

    assert created == 0
    assert imported == 0
    assert run == 0
    assert "campaign 运行完成" in run_out.out
    assert queue == 0
    assert "review queue 已生成" in queue_out.out
    assert report == 0
    assert "campaign 批量报告已生成" in report_out.out
    assert reviewed == 0
    assert "review queue 已记录监管决策" in reviewed_out.out
    assert (tmp_path / "01_literature" / "campaigns" / "C001_run.yaml").exists()
    assert (tmp_path / "01_literature" / "campaigns" / "C001_batch_report.md").exists()


def test_cli_review_build_status_and_clean_are_chinese(tmp_path, capsys):
    prepare_project(tmp_path)
    csv_path = tmp_path / "review_workspace.csv"
    csv_path.write_text(
        "title,doi,year,first_author\n"
        "Review Workspace CLI Paper,10.1234/review-workspace-cli,2026,Ada\n",
        encoding="utf-8",
    )
    main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "create",
            "--name-zh",
            "监管台 CLI",
            "--objective-zh",
            "验证 review workspace CLI。",
        ]
    )
    capsys.readouterr()
    main(["--root", str(tmp_path), "campaign", "import", "C001", "--file", str(csv_path)])
    capsys.readouterr()
    main(["--root", str(tmp_path), "campaign", "run", "C001", "--dry-run"])
    capsys.readouterr()

    build = main(["--root", str(tmp_path), "review", "build", "--campaign", "C001"])
    build_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "review", "status"])
    status_out = capsys.readouterr()
    clean_missing_flag = main(["--root", str(tmp_path), "review", "clean"])
    clean_missing_flag_out = capsys.readouterr()
    clean = main(["--root", str(tmp_path), "review", "clean", "--generated-only"])
    clean_out = capsys.readouterr()

    assert build == 0
    assert "本地监管台已生成" in build_out.out
    assert "manifest=" in build_out.out
    assert status == 0
    assert "本地监管台状态" in status_out.out
    assert "target=campaign:C001" in status_out.out
    assert clean_missing_flag == 2
    assert "需要 --generated-only" in clean_missing_flag_out.err
    assert clean == 0
    assert "生成文件已清理" in clean_out.out
    assert not (tmp_path / "01_literature" / "review_workspace" / "index.html").exists()


def write_cli_scoring_note(root):
    source = root / "01_literature" / "pdfs" / "P001" / "source.pdf"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("authorized source", encoding="utf-8")
    note = root / "01_literature" / "notes" / "P001_reading_note.md"
    frontmatter = {
        "paper_id": "P001",
        "metadata": "01_literature/metadata/P001.yaml",
        "note_status": "ready_for_review",
        "source_file": "01_literature/pdfs/P001/source.pdf",
        "authorization": "local",
        "source_grounded_claims": [
            {
                "claim_zh": "论文提出 method 并包含 experiment result。",
                "evidence_page": 1,
                "evidence_section": "Method",
                "source_chunk_id": "CH001",
                "evidence_snippet": "method experiment result",
                "needs_human_check": True,
            }
        ],
        "short_quotes": [
            {
                "quote": "method experiment result",
                "page": 1,
                "section": "Method",
                "reason_zh": "用于定位。",
            }
        ],
        "uncertain_points_zh": [],
        "asset_suggestions": [],
        "note_integration_requests": [],
        "human_confirmed": False,
    }
    note.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "## Agent 摘要\n\n用于 CLI scoring 测试。\n",
        encoding="utf-8",
    )


def prepare_cli_workflow_project(root):
    from rsa_cli.assets import add_source_record
    from rsa_cli.metadata import write_metadata_record

    prepare_project(root)
    local_yaml = root / ".rsa" / "local.yaml"
    local_yaml.parent.mkdir(parents=True, exist_ok=True)
    local_yaml.write_text(
        """
reading_draft:
  llm:
    provider: mock
    model: mock-reading-draft
""",
        encoding="utf-8",
    )
    config = load_project_config(root)
    source = root / "workflow-source.pdf"
    source.write_text(
        (
            "This paper studies gapped aperture SAR reconstruction. "
            "The method compares experiment results and reports metrics. "
        )
        * 8,
        encoding="utf-8",
    )
    write_metadata_record(
        config,
        {
            "title": "Workflow CLI Paper",
            "authors": ["Ada Lovelace"],
            "year": "2024",
            "venue": "Journal of Tests",
            "doi": "10.1234/workflow-cli",
            "official_url": None,
            "source_reliability": "publisher",
            "decision": "include",
            "decision_reason": "用于测试 workflow CLI。",
            "last_checked": "2026-05-21",
            "pdf_status": "authorized",
            "local_pdf": str(source),
            "assets": [],
            "topic_profile": "demo_topic",
            "priority_questions": ["Q1"],
            "used_for": ["workflow"],
            "research_roles": ["method"],
            "notes": "人工备注",
        },
        human_confirmed=True,
        confirmed_by="zxy",
    )
    add_source_record(
        config,
        "P001",
        source_file=str(source),
        authorization="authorized",
        source_type="pdf",
        license_note="用户已授权本地科研阅读。",
        added_by="zxy",
    )


def test_cli_score_single_validate_status_review_and_campaign(tmp_path, capsys):
    prepare_project(tmp_path)
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Score CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()
    write_cli_scoring_note(tmp_path)

    scored = main(["--root", str(tmp_path), "score", "P001"])
    scored_out = capsys.readouterr()
    valid = main(["--root", str(tmp_path), "score", "validate", "P001"])
    valid_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "score", "status", "P001"])
    status_out = capsys.readouterr()
    review_missing = main(
        [
            "--root",
            str(tmp_path),
            "score",
            "review",
            "P001",
            "--final-decision",
            "approved",
            "--reviewer",
            "zxy",
        ]
    )
    review_missing_out = capsys.readouterr()
    reviewed = main(
        [
            "--root",
            str(tmp_path),
            "score",
            "review",
            "P001",
            "--final-decision",
            "approved",
            "--reviewer",
            "zxy",
            "--reason",
            "人工复核后认为该评分可作为排序参考。",
        ]
    )
    reviewed_out = capsys.readouterr()

    assert scored == 0
    assert "评分完成" in scored_out.out
    assert "relevance=" in scored_out.out
    assert valid == 0
    assert "评分记录有效" in valid_out.out
    assert status == 0
    assert "评分状态" in status_out.out
    assert review_missing == 1
    assert "评分操作失败" in review_missing_out.err
    assert "Traceback" not in review_missing_out.err
    assert reviewed == 0
    assert "评分人工监管已记录" in reviewed_out.out

    csv_path = tmp_path / "score_campaign.csv"
    csv_path.write_text(
        "title,doi,year,first_author\n"
        "Score CLI Paper,10.1234/cli,2024,Ada\n",
        encoding="utf-8",
    )
    created = main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "create",
            "--name-zh",
            "评分队列",
            "--objective-zh",
            "测试 Phase 9 campaign scoring。",
        ]
    )
    capsys.readouterr()
    imported = main(
        [
            "--root",
            str(tmp_path),
            "campaign",
            "import",
            "C001",
            "--file",
            str(csv_path),
        ]
    )
    capsys.readouterr()
    campaign_scored = main(["--root", str(tmp_path), "score", "campaign", "C001"])
    campaign_out = capsys.readouterr()

    assert created == 0
    assert imported == 0
    assert campaign_scored == 0
    assert "批量评分完成" in campaign_out.out
    assert (tmp_path / "01_literature" / "campaigns" / "C001_scoring_summary.yaml").exists()


def test_cli_workflow_run_status_report_stop_and_resume_boundary(tmp_path, capsys):
    prepare_cli_workflow_project(tmp_path)

    with pytest.raises(SystemExit) as help_exc:
        main(["workflow", "run", "--help"])
    help_out = capsys.readouterr()
    run = main(
        [
            "--root",
            str(tmp_path),
            "workflow",
            "run",
            "P001",
            "--campaign-id",
            "C001",
            "--campaign-item-id",
            "CI001",
            "--skip-acquisition",
            "--skip-visual",
        ]
    )
    run_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "workflow", "status", "P001"])
    status_out = capsys.readouterr()
    report = main(["--root", str(tmp_path), "workflow", "report", "P001"])
    report_out = capsys.readouterr()
    stopped = main(
        [
            "--root",
            str(tmp_path),
            "workflow",
            "stop",
            "P001",
            "--reason",
            "用户检查中，暂停自动推进。",
        ]
    )
    stopped_out = capsys.readouterr()
    resume = main(["--root", str(tmp_path), "workflow", "resume", "P001"])
    resume_out = capsys.readouterr()

    assert help_exc.value.code == 0
    assert "--skip-acquisition" in help_out.out
    assert "--campaign-id" in help_out.out
    assert run == 0
    assert "workflow 运行完成" in run_out.out
    assert "needs_review" in run_out.out
    assert "next_action=" in run_out.out
    assert status == 0
    assert "workflow 状态" in status_out.out
    assert "next_action=" in status_out.out
    assert "C001" not in status_out.err
    assert report == 0
    assert "Workflow Review Packet" in report_out.out
    assert stopped == 0
    assert "workflow 已暂停" in stopped_out.out
    assert resume == 1
    assert "workflow 操作失败" in resume_out.err
    assert "stop" in resume_out.err


def test_cli_workflow_rejects_campaign_as_main_target(tmp_path, capsys):
    prepare_project(tmp_path)

    exit_code = main(["--root", str(tmp_path), "workflow", "run", "C001"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "campaign 批量调度属于 Phase 11" in captured.err


def test_cli_source_phase7_help_lists_monitored_acquisition_commands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["source", "--help"])

    captured = capsys.readouterr()

    assert exc.value.code == 0
    assert "find" in captured.out
    assert "candidates" in captured.out
    assert "download" in captured.out
    assert "login" in captured.out
    assert "session" in captured.out

    with pytest.raises(SystemExit) as download_exc:
        main(["source", "download", "--help"])
    download_help = capsys.readouterr()

    assert download_exc.value.code == 0
    for needle in [
        "--best",
        "--candidate",
        "--authorization-mode",
        "--usage-restriction-zh",
    ]:
        assert needle in download_help.out

    with pytest.raises(SystemExit) as login_exc:
        main(["source", "login", "--help"])
    login_help = capsys.readouterr()
    assert login_exc.value.code == 0
    assert "--wait-seconds" in login_help.out
    assert "browser_session" in login_help.out

    with pytest.raises(SystemExit) as session_exc:
        main(["source", "session", "--help"])
    session_help = capsys.readouterr()
    assert session_exc.value.code == 0
    assert "status" in session_help.out
    assert "clear" in session_help.out


def test_cli_source_find_no_download_and_candidates_are_read_only(tmp_path, capsys):
    prepare_project(tmp_path)
    pdf = tmp_path / "authorized.pdf"
    pdf.write_bytes(b"%PDF-1.4\ncli")
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Find No Download CLI Paper", official_url=pdf.as_uri()),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()

    found = main(["--root", str(tmp_path), "source", "find", "P001", "--no-download"])
    found_out = capsys.readouterr()
    candidates_path = tmp_path / "01_literature" / "source_candidates" / "P001.yaml"
    before = candidates_path.read_text(encoding="utf-8")
    shown = main(["--root", str(tmp_path), "source", "candidates", "P001"])
    shown_out = capsys.readouterr()

    assert found == 0
    assert "仅生成候选" in found_out.out
    assert "已下载=0" in found_out.out
    assert not (tmp_path / "01_literature" / "sources" / "P001.yaml").exists()
    assert shown == 0
    assert "候选来源" in shown_out.out
    assert candidates_path.read_text(encoding="utf-8") == before


def test_cli_source_find_default_downloads_approved_pdf(tmp_path, capsys):
    prepare_project(tmp_path)
    pdf = tmp_path / "authorized.pdf"
    pdf.write_bytes(b"%PDF-1.4\ncli")
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Find Download CLI Paper", official_url=pdf.as_uri()),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()

    found = main(["--root", str(tmp_path), "source", "find", "P001"])
    found_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "source", "status", "P001"])
    status_out = capsys.readouterr()

    assert found == 0
    assert "monitored_auto" in found_out.out
    assert "已下载=1" in found_out.out
    assert status == 0
    assert "候选=" in status_out.out
    assert "已下载=1" in status_out.out
    assert (tmp_path / "01_literature" / "sources" / "P001.yaml").exists()


def test_cli_source_download_url_requires_authorization_without_traceback(tmp_path, capsys):
    prepare_project(tmp_path)
    pdf = tmp_path / "manual.pdf"
    pdf.write_bytes(b"%PDF-1.4\ncli")
    main(
        [
            "--root",
            str(tmp_path),
            *add_paper_args("Manual URL CLI Paper"),
            "--human-confirmed",
            "--confirmed-by",
            "zxy",
        ]
    )
    capsys.readouterr()

    failed = main(["--root", str(tmp_path), "source", "download", "P001", "--url", pdf.as_uri()])
    failed_out = capsys.readouterr()
    ok = main(
        [
            "--root",
            str(tmp_path),
            "source",
            "download",
            "P001",
            "--url",
            pdf.as_uri(),
            "--authorization-mode",
            "direct_access",
            "--access-mode",
            "direct_access",
            "--usage-restriction-zh",
            "仅供个人科研阅读，不得公开分发 PDF。",
        ]
    )
    ok_out = capsys.readouterr()

    assert failed == 1
    assert "来源操作失败" in failed_out.err
    assert "Traceback" not in failed_out.err
    assert ok == 0
    assert "来源下载完成" in ok_out.out


def test_cli_source_session_status_and_clear_are_chinese(tmp_path, capsys):
    prepare_project(tmp_path)
    local_yaml = tmp_path / ".rsa" / "local.yaml"
    local_yaml.parent.mkdir(parents=True, exist_ok=True)
    local_yaml.write_text(
        """
source_discovery:
  custom_providers:
    - provider_id: library_browser
      enabled: true
      name_zh: 学校图书馆浏览器会话
      provider_type: browser_session
      base_url: https://library.example.edu
      login_url: https://library.example.edu/login
      session_storage: .rsa/sessions/library_browser.storage_state.json
      session_required: true
      query_mode: url_template
      query_template: https://library.example.edu/papers/{doi}.pdf
      allowed_domains:
        - library.example.edu
      allowed_result_types:
        - pdf
      access_mode: institutional_subscription
      requires_login: true
      user_access_confirmed: true
      authorization_policy: user_authorized_access
      usage_restriction_zh: 仅供个人科研阅读，不得公开分发 PDF。
      notes_zh: 用户通过学校账号自行登录；RSA 不保存账号密码。
""",
        encoding="utf-8",
    )

    status = main(["--root", str(tmp_path), "source", "session", "status", "library_browser"])
    status_out = capsys.readouterr()
    clear = main(["--root", str(tmp_path), "source", "session", "clear", "library_browser"])
    clear_out = capsys.readouterr()

    assert status == 0
    assert "浏览器会话状态" in status_out.out
    assert "未登录" in status_out.out
    assert clear == 0
    assert "无需清除" in clear_out.out


def test_cli_eval_run_baseline_and_compare(tmp_path, capsys):
    run = main(["--root", str(tmp_path), "eval", "run"])
    run_out = capsys.readouterr()
    baseline = main(["--root", str(tmp_path), "eval", "baseline"])
    baseline_out = capsys.readouterr()
    compare = main(["--root", str(tmp_path), "eval", "compare"])
    compare_out = capsys.readouterr()

    assert run == 0
    assert "Eval 完成" in run_out.out
    assert baseline == 0
    assert "baseline" in baseline_out.out
    assert compare == 0
    assert "回归数=0" in compare_out.out
    assert (tmp_path / "01_literature" / "synthesis" / "eval_report.md").exists()
    assert (tmp_path / "01_literature" / "synthesis" / "eval_baseline.yaml").exists()
    assert (
        tmp_path / "01_literature" / "synthesis" / "eval_regression_report.md"
    ).exists()
