from pathlib import Path

from rsa_cli.config import load_project_config
from rsa_cli.skeleton import create_literature_skeleton


REQUIRED_DIRECTORIES = {
    "metadata",
    "topic_profiles",
    "agent_outputs",
    "notes",
    "synthesis",
    "sources",
    "source_candidates",
    "campaigns",
    "scores",
    "workflows",
    "review_workspace",
    "safety",
    "workers",
    "discovery",
    "dynamic_workflows",
    "pdfs",
    "assets",
    "extracted",
}

REQUIRED_FILES = {
    "paper_index.md",
    "literature_map.md",
    "research_tables.md",
    "agent_research_notes.md",
}

REQUIRED_TEMPLATES = {
    "topic_profile.yaml",
    "paper_metadata.yaml",
    "paper_note.md",
    "round_readme.md",
    "final_round_summary.md",
    "search_candidates.md",
    "verification_review.md",
    "map_integration.md",
    "pdf_acquisition_report.md",
    "reading_batch_report.md",
    "source_record.yaml",
    "source_candidates.yaml",
    "browser_session_provider.yaml",
    "asset_manifest.yaml",
    "dynamic_workflow_policy.yaml",
}


def test_create_literature_skeleton_creates_required_foundation(tmp_path):
    config = load_project_config(tmp_path)

    create_literature_skeleton(config)

    for directory in REQUIRED_DIRECTORIES:
        assert (tmp_path / "01_literature" / directory).is_dir()
        assert (tmp_path / "01_literature" / directory / ".gitkeep").exists()
    for file_name in REQUIRED_FILES:
        assert (tmp_path / "01_literature" / file_name).exists()
    for template_name in REQUIRED_TEMPLATES:
        assert (tmp_path / "templates" / template_name).exists()
    assert (
        tmp_path
        / "01_literature"
        / "topic_profiles"
        / "sar_noncontinuous_aperture.yaml"
    ).exists()


def test_create_literature_skeleton_is_idempotent(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    paper_index = tmp_path / "01_literature" / "paper_index.md"
    paper_index.write_text("human edited\n", encoding="utf-8")

    create_literature_skeleton(config)

    assert paper_index.read_text(encoding="utf-8") == "human edited\n"


def test_gitignore_protects_local_settings_pdfs_and_assets():
    repo_root = Path(__file__).resolve().parents[1]
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

    assert ".rsa/local.yaml" in gitignore
    assert ".rsa/sessions/**" in gitignore
    assert "01_literature/pdfs/**" in gitignore
    assert "!01_literature/pdfs/.gitkeep" in gitignore
    assert "01_literature/assets/**" in gitignore
    assert "!01_literature/assets/.gitkeep" in gitignore
    assert "!01_literature/assets/*/manifest.yaml" in gitignore
    assert "01_literature/extracted/**" in gitignore
    assert "!01_literature/extracted/.gitkeep" in gitignore


def test_templates_and_starter_profile_are_substantive():
    repo_root = Path(__file__).resolve().parents[1]
    topic_template = (repo_root / "templates" / "topic_profile.yaml").read_text(
        encoding="utf-8"
    )
    starter = (
        repo_root
        / "01_literature"
        / "topic_profiles"
        / "sar_noncontinuous_aperture.yaml"
    ).read_text(encoding="utf-8")

    for field in [
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
        assert field in topic_template

    for term in [
        "noncontinuous aperture",
        "wide-angle",
        "multi-aspect",
        "distributed SAR",
        "cross-channel coherence",
        "phase-history recovery",
        "ghost artifact",
        "failure boundary",
        "physics-constrained learning",
    ]:
        assert term in starter


def test_python_source_does_not_hard_code_sar_profile_details():
    repo_root = Path(__file__).resolve().parents[1]
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (repo_root / "src" / "rsa_cli").rglob("*.py")
    )

    assert "sar_noncontinuous_aperture" not in source_text
    assert "noncontinuous aperture SAR" not in source_text
    assert "distributed SAR" not in source_text
