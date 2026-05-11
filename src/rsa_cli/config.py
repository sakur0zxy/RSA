from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "literature_root": "01_literature",
    "templates_root": "templates",
    "profiles": {
        "root": "topic_profiles",
    },
    "rounds": {
        "default_max_candidates": 5,
        "hard_max_candidates": 20,
        "allowed_tools": [],
        "output_policy": "agent_outputs_only",
        "approval_mode": "human_confirmed_formal_writes",
        "campaign_id": None,
    },
}


class ConfigError(ValueError):
    """Raised when project configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    data: dict[str, Any]

    @property
    def literature_root(self) -> Path:
        return self.resolve_path(str(self.data["literature_root"]))

    @property
    def templates_root(self) -> Path:
        return self.resolve_path(str(self.data["templates_root"]))

    @property
    def topic_profiles_root(self) -> Path:
        profiles_root = self.data.get("profiles", {}).get("root", "topic_profiles")
        return self.literature_root / str(profiles_root)

    @property
    def agent_outputs_root(self) -> Path:
        return self.literature_root / "agent_outputs"

    @property
    def rounds(self) -> dict[str, Any]:
        return dict(self.data.get("rounds", {}))

    @property
    def default_max_candidates(self) -> int:
        return int(self.rounds.get("default_max_candidates", 5))

    @property
    def hard_max_candidates(self) -> int:
        return int(self.rounds.get("hard_max_candidates", 20))

    @property
    def allowed_tools(self) -> list[str]:
        tools = self.rounds.get("allowed_tools", [])
        return list(tools or [])

    @property
    def output_policy(self) -> str:
        return str(self.rounds.get("output_policy", "agent_outputs_only"))

    @property
    def approval_mode(self) -> str:
        return str(self.rounds.get("approval_mode", "human_confirmed_formal_writes"))

    @property
    def campaign_id(self) -> str | None:
        value = self.rounds.get("campaign_id")
        return None if value in (None, "") else str(value)

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.root / path


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")
    return loaded


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def validate_config(config: ProjectConfig) -> None:
    default_max = config.default_max_candidates
    hard_max = config.hard_max_candidates
    if not isinstance(config.rounds.get("allowed_tools", []), list):
        raise ConfigError("rounds.allowed_tools must be a list")
    if not config.output_policy:
        raise ConfigError("rounds.output_policy must be non-empty")
    if not config.approval_mode:
        raise ConfigError("rounds.approval_mode must be non-empty")
    if default_max <= 0:
        raise ConfigError("rounds.default_max_candidates must be positive")
    if hard_max <= 0:
        raise ConfigError("rounds.hard_max_candidates must be positive")
    if default_max > hard_max:
        raise ConfigError(
            "rounds.default_max_candidates must not exceed rounds.hard_max_candidates"
        )


def load_project_config(root: Path | str = ".") -> ProjectConfig:
    project_root = Path(root).resolve()
    project_config = load_yaml_file(project_root / "rsa.yaml")
    local_config = load_yaml_file(project_root / ".rsa" / "local.yaml")
    data = deep_merge(DEFAULT_CONFIG, project_config)
    data = deep_merge(data, local_config)
    config = ProjectConfig(root=project_root, data=data)
    validate_config(config)
    return config
