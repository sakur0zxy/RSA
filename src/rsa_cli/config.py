from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "literature_root": "01_literature",
    "templates_root": "templates",
    "source_discovery": {
        "automation_mode": "monitored_auto",
        "default_auto_download": True,
        "custom_providers": [],
    },
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
    "reading_draft": {
        "llm": {
            "provider": None,
            "model": None,
            "api_key_env": None,
            "base_url": None,
            "timeout_seconds": 60,
            "max_chunks": 8,
            "max_input_tokens": 12000,
            "temperature": 0,
            "language": "zh",
            "prompt_profile": "default",
        },
        "review": {
            "ready_score_threshold": 6,
        },
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
    def metadata_root(self) -> Path:
        return self.literature_root / "metadata"

    @property
    def paper_index_path(self) -> Path:
        return self.literature_root / "paper_index.md"

    @property
    def literature_map_path(self) -> Path:
        return self.literature_root / "literature_map.md"

    @property
    def agent_research_notes_path(self) -> Path:
        return self.literature_root / "agent_research_notes.md"

    @property
    def pdf_acquisition_report_path(self) -> Path:
        return self.literature_root / "pdf_acquisition_report.md"

    @property
    def sources_root(self) -> Path:
        return self.literature_root / "sources"

    @property
    def notes_root(self) -> Path:
        return self.literature_root / "notes"

    @property
    def synthesis_root(self) -> Path:
        return self.literature_root / "synthesis"

    @property
    def eval_report_path(self) -> Path:
        return self.synthesis_root / "eval_report.md"

    @property
    def eval_baseline_path(self) -> Path:
        return self.synthesis_root / "eval_baseline.yaml"

    @property
    def eval_regression_report_path(self) -> Path:
        return self.synthesis_root / "eval_regression_report.md"

    @property
    def assets_root(self) -> Path:
        return self.literature_root / "assets"

    @property
    def source_candidates_root(self) -> Path:
        return self.literature_root / "source_candidates"

    @property
    def campaigns_root(self) -> Path:
        return self.literature_root / "campaigns"

    @property
    def pdfs_root(self) -> Path:
        return self.literature_root / "pdfs"

    @property
    def extracted_root(self) -> Path:
        return self.literature_root / "extracted"

    @property
    def sessions_root(self) -> Path:
        return self.root / ".rsa" / "sessions"

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
    def source_discovery(self) -> dict[str, Any]:
        return dict(self.data.get("source_discovery", {}))

    @property
    def reading_draft(self) -> dict[str, Any]:
        return dict(self.data.get("reading_draft", {}))

    @property
    def reading_draft_llm(self) -> dict[str, Any]:
        return dict(self.reading_draft.get("llm", {}))

    @property
    def reading_draft_review(self) -> dict[str, Any]:
        return dict(self.reading_draft.get("review", {}))

    @property
    def reading_draft_ready_score_threshold(self) -> int:
        return int(self.reading_draft_review.get("ready_score_threshold", 6))

    @property
    def custom_source_providers(self) -> list[dict[str, Any]]:
        providers = self.source_discovery.get("custom_providers", [])
        return list(providers or [])

    @property
    def source_discovery_automation_mode(self) -> str:
        return str(self.source_discovery.get("automation_mode", "monitored_auto"))

    @property
    def source_discovery_default_auto_download(self) -> bool:
        return bool(self.source_discovery.get("default_auto_download", True))

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
        raise ConfigError(f"{path} 必须是 YAML mapping")
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
        raise ConfigError("rounds.allowed_tools 必须是 list")
    if not isinstance(config.source_discovery.get("custom_providers", []), list):
        raise ConfigError("source_discovery.custom_providers 必须是 list")
    if not isinstance(config.reading_draft.get("llm", {}), dict):
        raise ConfigError("reading_draft.llm 必须是 mapping")
    if not isinstance(config.reading_draft.get("review", {}), dict):
        raise ConfigError("reading_draft.review 必须是 mapping")
    if not config.output_policy:
        raise ConfigError("rounds.output_policy 不能为空")
    if not config.approval_mode:
        raise ConfigError("rounds.approval_mode 不能为空")
    if default_max <= 0:
        raise ConfigError("rounds.default_max_candidates 必须为正数")
    if hard_max <= 0:
        raise ConfigError("rounds.hard_max_candidates 必须为正数")
    if default_max > hard_max:
        raise ConfigError(
            "rounds.default_max_candidates 不能超过 rounds.hard_max_candidates"
        )
    threshold = config.reading_draft_ready_score_threshold
    if threshold < 0 or threshold > 10:
        raise ConfigError("reading_draft.review.ready_score_threshold 必须在 0 到 10 之间")


def load_project_config(root: Path | str = ".") -> ProjectConfig:
    project_root = Path(root).resolve()
    project_config = load_yaml_file(project_root / "rsa.yaml")
    local_config = load_yaml_file(project_root / ".rsa" / "local.yaml")
    data = deep_merge(DEFAULT_CONFIG, project_config)
    data = deep_merge(data, local_config)
    config = ProjectConfig(root=project_root, data=data)
    validate_config(config)
    return config
