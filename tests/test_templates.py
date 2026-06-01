import tomllib
from pathlib import Path

from rsa_cli.config import load_project_config
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.templates import FORMAL_RECORD_FILES, TEMPLATE_FILES


REPO_ROOT = Path(__file__).resolve().parents[1]


def root_template(name: str) -> str:
    return (REPO_ROOT / "templates" / name).read_text(encoding="utf-8")


def assert_in_root_and_fallback(name: str, *needles: str) -> None:
    root_text = root_template(name)
    fallback = TEMPLATE_FILES[name]
    for needle in needles:
        assert needle in root_text
        assert needle in fallback


def test_paper_metadata_template_has_full_chinese_field_guide():
    text = root_template("paper_metadata.yaml")
    fallback = TEMPLATE_FILES["paper_metadata.yaml"]
    for needle in ["字段说明", "paper_id", "human_confirmed", "confirmed_at"]:
        assert needle in text
        assert needle in fallback
    for field in [
        "title",
        "authors",
        "year",
        "venue",
        "doi",
        "official_url",
        "source_reliability",
        "verification_status",
        "decision",
        "decision_reason",
        "last_checked",
        "pdf_status",
        "local_pdf",
        "assets",
        "topic_profile",
        "priority_questions",
        "used_for",
        "research_roles",
        "notes",
    ]:
        assert field in text


def test_candidate_review_template_preserves_locked_fields_and_statuses():
    assert_in_root_and_fallback(
        "verification_review.md",
        "# 候选文献核验记录",
        "candidate_title",
        "source",
        "doi_or_url",
        "decision",
        "reason",
        "last_checked",
        "字段说明",
        "verified",
        "rejected",
        "uncertain",
        "human_confirmed",
    )


def test_search_candidates_template_stays_in_staging_boundary():
    text = root_template("search_candidates.md")
    fallback = TEMPLATE_FILES["search_candidates.md"]
    for needle in [
        "候选文献",
        "candidate_title",
        "source",
        "doi_or_url",
        "why_relevant",
        "next_review_action",
        "verification_review.md",
        "metadata/P###.yaml",
    ]:
        assert needle in text
        assert needle in fallback
    assert "C001.yaml" not in text
    assert "C001.yaml" not in fallback


def test_topic_profile_keeps_english_keys_with_chinese_explanations():
    text = root_template("topic_profile.yaml")
    fallback = TEMPLATE_FILES["topic_profile.yaml"]
    for key in [
        "topic_id",
        "topic_name",
        "core_keywords",
        "priority_questions",
        "important_metrics",
        "preferred_sources",
        "exclude_scope",
        "grade_rules",
        "required_outputs",
    ]:
        assert key in text
        assert key in fallback
    assert "字段说明" in text
    assert "字段说明" in fallback


def test_round_templates_preserve_placeholders_and_chinese_sections():
    round_text = root_template("round_readme.md")
    fallback = TEMPLATE_FILES["round_readme.md"]
    for placeholder in [
        "{round_id}",
        "{objective}",
        "{topic_profile}",
        "{max_candidates}",
        "{allowed_tools}",
        "{output_policy}",
        "{approval_mode}",
        "{campaign_id}",
    ]:
        assert placeholder in round_text
        assert placeholder in fallback

    final_text = root_template("final_round_summary.md")
    assert final_text.startswith("---\n")
    for needle in [
        "status: draft",
        "included_files",
        "formal_write_requests",
        "human_confirmed",
        "ready_for_review",
        "completed",
        "metadata/P###.yaml",
        "literature_map.md",
        "状态",
        "关键发现",
        "候选决策",
        "请求写入正式记录",
        "人工确认",
    ]:
        assert needle in final_text
        assert needle in TEMPLATE_FILES["final_round_summary.md"]


def test_later_phase_seed_templates_are_safe_and_localized():
    assert_in_root_and_fallback(
        "paper_note.md",
        "授权",
        "人工决策",
        "source_grounded_claims",
        "short_quotes",
        "asset_suggestions",
        "agent_review_score_10",
        "recommended_human_action_zh",
        "prompt_packet",
        "note_integration_requests",
    )
    assert_in_root_and_fallback(
        "map_integration.md",
        "文献映射建议",
        "literature_map.md",
        "topic_profile",
        "planned_output",
        "research_role",
        "map_status",
    )
    assert_in_root_and_fallback("pdf_acquisition_report.md", "不得下载未授权 PDF")
    assert_in_root_and_fallback("reading_batch_report.md", "人工确认")
    assert_in_root_and_fallback(
        "source_record.yaml",
        "字段说明",
        "authorization",
        "license_note",
        "local_path",
        "provided",
    )
    assert_in_root_and_fallback(
        "source_candidates.yaml",
        "字段说明",
        "candidate_id",
        "provider_id",
        "authorization_mode",
        "usage_restriction_zh",
        "monitored_auto",
        "字段名保持英文稳定",
    )
    assert_in_root_and_fallback(
        "browser_session_provider.yaml",
        "browser_session provider 模板",
        "provider_type",
        "login_url",
        "session_storage",
        ".rsa/sessions",
        "不保存账号密码",
        "仅供个人科研阅读",
    )
    assert_in_root_and_fallback(
        "asset_manifest.yaml",
        "字段说明",
        "asset_id",
        "description_zh",
        "local_path",
        "screenshot",
    )
    assert_in_root_and_fallback(
        "trace_summary.md",
        "Trace Summary",
        "tools_used",
        "decisions_made",
        "human_approvals",
        "formal_write_request_count",
    )

    assert "不得下载未授权 PDF" in root_template("pdf_acquisition_report.md")
    assert "不会因为填写本模板而自动写入正式记录" in root_template("map_integration.md")


def test_formal_record_seeds_are_chinese_readable():
    for name, needle in {
        "paper_index.md": "文献索引",
        "literature_map.md": "文献映射",
        "research_tables.md": "研究表格",
        "agent_research_notes.md": "辅助材料",
    }.items():
        text = (REPO_ROOT / "01_literature" / name).read_text(encoding="utf-8")
        assert needle in text
        assert needle in FORMAL_RECORD_FILES[name]


def test_readme_documents_visual_evidence_workflow():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "rsa visual extract P001" in text
    assert "--all-detected" in text
    assert "视觉候选只是 staging/review 材料，不是 formal record" in text
    assert "PyMuPDF" in text


def test_readme_documents_phase9_scoring_workflow():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . score P001",
        "rsa --root . score campaign C001",
        "ai_relevance_score_10",
        "ai_quality_score_10",
        "ai_read_priority_score_10",
        "`recommend_pass` 只是 staging/review 层建议",
        "不是 formal approval",
    ]:
        assert needle in text


def test_readme_documents_phase10_workflow_orchestrator():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . workflow run P001",
        "rsa --root . workflow status P001",
        "rsa --root . workflow report P001",
        "01_literature/workflows/P###/RUN-###.yaml",
        "campaign 批量调度属于 Phase 11",
        "llm_visual_analysis",
        "formal write gate",
        "fail closed",
    ]:
        assert needle in text


def test_readme_documents_phase12_local_review_workspace():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . review build --campaign C001",
        "rsa --root . review build --paper P001",
        "rsa --root . review status",
        "rsa --root . review clean --generated-only",
        "review_workspace_manifest.yaml",
        "index.html",
        "groups/*.html",
        "objects/*.html",
        "formal_write_request",
        "只展示命令，不自动执行",
        "不会直接写入 `metadata/`",
    ]:
        assert needle in text


def test_readme_documents_phase13_writing_safety():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . safety check P001",
        "rsa --root . safety validate P001",
        "rsa --root . safety status P001",
        "rsa --root . safety campaign C001",
        "01_literature/safety/P###_safety.yaml",
        "01_literature/safety/C###_campaign_safety.yaml",
        "claim_refs",
        "safety_status",
        "llm_claim_review",
        "citation_graph",
        "advanced_figure_claim_binding",
        "不是 formal approval",
        "不直接写 formal metadata",
        "只写 `01_literature/safety/` 审计记录",
    ]:
        assert needle in text


def test_readme_documents_phase14_worker_automation():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . worker enqueue campaign-run C001",
        "rsa --root . worker run --max-tasks 1",
        "rsa --root . worker run --include-due --max-tasks 5",
        "rsa --root . worker status",
        "rsa --root . worker logs",
        "rsa --root . worker schedule add campaign-run C001 --interval-hours 24",
        "01_literature/workers/queue.yaml",
        "01_literature/workers/schedules.yaml",
        "01_literature/workers/worker_log.md",
        "不执行 formal write",
        "正式记录仍需人工确认",
    ]:
        assert needle in text


def test_readme_documents_phase15_codex_oauth_provider():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . llm codex status",
        "rsa --root . llm codex import",
        "rsa --root . doctor",
        "codex_oauth",
        ".rsa/auth/codex_oauth.yaml",
        "不会输出 token",
        "不自动网页登录",
        "不抓取浏览器 cookies",
        "不能绕过 formal write gate",
    ]:
        assert needle in text


def test_readme_documents_phase16_research_plan_discovery():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for needle in [
        "rsa --root . discovery run --plan-file research_plan.md --provider openalex",
        "rsa --root . discovery validate DR001",
        "Research Plan Discovery Workflow",
        "DR###_profile.yaml",
        "DR###_queries.yaml",
        "DR###_results.yaml",
        "DR###_campaign_import.yaml",
        "不创建正式 `paper_id`",
        "不写 `paper_index.md`",
        "formal write gate",
        "iterative_query_refinement",
        "web_review_ui",
    ]:
        assert needle in text


def test_init_writes_localized_templates_and_formal_records(tmp_path):
    config = load_project_config(tmp_path)

    create_literature_skeleton(config)

    assert "candidate_title" in (
        tmp_path / "templates" / "verification_review.md"
    ).read_text(encoding="utf-8")
    assert "候选文献" in (tmp_path / "templates" / "search_candidates.md").read_text(
        encoding="utf-8"
    )
    assert "文献映射" in (
        tmp_path / "01_literature" / "literature_map.md"
    ).read_text(encoding="utf-8")
    assert "研究表格" in (
        tmp_path / "01_literature" / "research_tables.md"
    ).read_text(encoding="utf-8")
    assert "辅助材料" in (
        tmp_path / "01_literature" / "agent_research_notes.md"
    ).read_text(encoding="utf-8")
    assert "PDF 获取状态记录" in (
        tmp_path / "01_literature" / "pdf_acquisition_report.md"
    ).read_text(encoding="utf-8")
    assert "license_note" in (tmp_path / "templates" / "source_record.yaml").read_text(
        encoding="utf-8"
    )
    assert "description_zh" in (
        tmp_path / "templates" / "asset_manifest.yaml"
    ).read_text(encoding="utf-8")
    assert "tools_used" in (tmp_path / "templates" / "trace_summary.md").read_text(
        encoding="utf-8"
    )


def test_language_policy_is_documented_for_chinese_users():
    policy = (REPO_ROOT / ".planning" / "LANGUAGE-POLICY.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    requirements = (REPO_ROOT / ".planning" / "REQUIREMENTS.md").read_text(
        encoding="utf-8"
    )

    for text in [policy, readme, requirements]:
        assert "中文优先" in text
    for needle in ["YAML key", "CLI flag", "状态枚举", "代码标识"]:
        assert needle in policy


def test_dependency_policy_matches_base_runtime_and_doctor_contract():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = "\n".join(pyproject["project"]["dependencies"])
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    policy = (REPO_ROOT / ".planning" / "DEPENDENCY-POLICY.md").read_text(encoding="utf-8")

    for package in ["PyYAML", "pypdf", "PyMuPDF", "playwright"]:
        assert package in dependencies
        assert package in policy
    for needle in [
        "功能-依赖矩阵",
        "基础安装",
        "一次性环境初始化",
        "OK",
        "WARN",
        "BLOCKED",
        "rsa --root . doctor",
    ]:
        assert needle in readme
    assert "rsa doctor --strict" in policy


def test_second_init_does_not_overwrite_human_edited_formal_records(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    edited = tmp_path / "01_literature" / "literature_map.md"
    edited.write_text("human edited\n", encoding="utf-8")

    create_literature_skeleton(config)

    assert edited.read_text(encoding="utf-8") == "human edited\n"
