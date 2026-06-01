from pathlib import Path

import pytest

from rsa_cli.config import ConfigError, load_project_config


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_project_config_defaults_when_local_file_missing(tmp_path):
    write(
        tmp_path / "rsa.yaml",
        """
literature_root: custom_literature
templates_root: custom_templates
""",
    )

    config = load_project_config(tmp_path)

    assert config.literature_root == tmp_path / "custom_literature"
    assert config.templates_root == tmp_path / "custom_templates"
    assert config.metadata_root == tmp_path / "custom_literature" / "metadata"
    assert config.paper_index_path == tmp_path / "custom_literature" / "paper_index.md"
    assert config.assets_root == tmp_path / "custom_literature" / "assets"
    assert config.source_candidates_root == tmp_path / "custom_literature" / "source_candidates"
    assert config.pdfs_root == tmp_path / "custom_literature" / "pdfs"
    assert config.extracted_root == tmp_path / "custom_literature" / "extracted"
    assert config.discovery_root == tmp_path / "custom_literature" / "discovery"
    assert config.dynamic_workflows_root == tmp_path / "custom_literature" / "dynamic_workflows"
    assert config.sessions_root == tmp_path / ".rsa" / "sessions"
    assert config.auth_root == tmp_path / ".rsa" / "auth"
    assert config.topic_profiles_root == tmp_path / "custom_literature" / "topic_profiles"
    assert config.default_max_candidates == 5
    assert config.hard_max_candidates == 20
    assert config.allowed_tools == []
    assert config.output_policy == "agent_outputs_only"
    assert config.approval_mode == "human_confirmed_formal_writes"
    assert config.campaign_id is None
    assert config.source_discovery_automation_mode == "monitored_auto"
    assert config.source_discovery_default_auto_download is True
    assert config.custom_source_providers == []
    assert config.reading_draft_llm["provider"] is None
    assert config.reading_draft_llm_codex_oauth["auth_store"] == ".rsa/auth/codex_oauth.yaml"
    assert config.reading_draft_llm_codex_oauth["token_source"] == "rsa_store"
    assert config.reading_draft_ready_score_threshold == 6
    assert config.discovery_default_provider == "openalex"
    assert config.discovery_default_max_queries == 3
    assert config.discovery_default_max_results == 5
    assert config.discovery_allowed_providers == ["openalex", "crossref", "offline"]
    assert config.discovery_automation_mode == "monitored_auto"
    assert config.dynamic_workflow_default_policy == tmp_path / "templates" / "dynamic_workflow_policy.yaml"
    assert config.dynamic_workflow_automation_mode == "monitored_auto"
    assert config.dynamic_workflow_min_confidence_to_run == "medium"
    assert config.dynamic_workflow_allow_llm_suggestions is False


def test_local_overrides_win_over_project_defaults(tmp_path):
    write(
        tmp_path / "rsa.yaml",
        """
literature_root: project_literature
rounds:
  default_max_candidates: 5
  hard_max_candidates: 20
""",
    )
    write(
        tmp_path / ".rsa" / "local.yaml",
        """
literature_root: local_literature
rounds:
  default_max_candidates: 7
""",
    )

    config = load_project_config(tmp_path)

    assert config.literature_root == tmp_path / "local_literature"
    assert config.default_max_candidates == 7
    assert config.hard_max_candidates == 20


def test_round_accessors_expose_policy_and_campaign(tmp_path):
    write(
        tmp_path / "rsa.yaml",
        """
rounds:
  default_max_candidates: 4
  hard_max_candidates: 12
  allowed_tools:
    - web_search
  output_policy: staging_only
  approval_mode: confirm_before_formal_write
  campaign_id: C001
""",
    )

    config = load_project_config(tmp_path)

    assert config.default_max_candidates == 4
    assert config.hard_max_candidates == 12
    assert config.allowed_tools == ["web_search"]
    assert config.output_policy == "staging_only"
    assert config.approval_mode == "confirm_before_formal_write"
    assert config.campaign_id == "C001"


def test_invalid_round_limits_raise_actionable_error(tmp_path):
    write(
        tmp_path / "rsa.yaml",
        """
rounds:
  default_max_candidates: 21
  hard_max_candidates: 20
""",
    )

    with pytest.raises(ConfigError, match="default_max_candidates"):
        load_project_config(tmp_path)


def test_source_discovery_local_overrides_are_merged(tmp_path):
    write(
        tmp_path / "rsa.yaml",
        """
source_discovery:
  default_auto_download: false
  custom_providers:
    - provider_id: project_source
""",
    )
    write(
        tmp_path / ".rsa" / "local.yaml",
        """
source_discovery:
  automation_mode: monitored_auto
  custom_providers:
    - provider_id: local_source
""",
    )

    config = load_project_config(tmp_path)

    assert config.source_discovery_default_auto_download is False
    assert config.source_discovery_automation_mode == "monitored_auto"
    assert config.custom_source_providers == [{"provider_id": "local_source"}]


def test_reading_draft_local_llm_overrides_are_merged(tmp_path):
    write(
        tmp_path / "rsa.yaml",
        """
reading_draft:
  llm:
    provider: openai_compatible
    model: project-model
    language: zh
  review:
    ready_score_threshold: 7
""",
    )
    write(
        tmp_path / ".rsa" / "local.yaml",
        """
reading_draft:
  llm:
    provider: mock
    model: local-mock
""",
    )

    config = load_project_config(tmp_path)

    assert config.reading_draft_llm["provider"] == "mock"
    assert config.reading_draft_llm["model"] == "local-mock"
    assert config.reading_draft_llm["language"] == "zh"
    assert config.reading_draft_ready_score_threshold == 7
