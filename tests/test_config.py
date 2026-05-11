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
    assert config.pdfs_root == tmp_path / "custom_literature" / "pdfs"
    assert config.topic_profiles_root == tmp_path / "custom_literature" / "topic_profiles"
    assert config.default_max_candidates == 5
    assert config.hard_max_candidates == 20
    assert config.allowed_tools == []
    assert config.output_policy == "agent_outputs_only"
    assert config.approval_mode == "human_confirmed_formal_writes"
    assert config.campaign_id is None


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
