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
    assert config.default_max_candidates == 5
    assert config.hard_max_candidates == 20


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
