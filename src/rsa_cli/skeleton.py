from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from .config import ProjectConfig
from .templates import FORMAL_RECORD_FILES, TEMPLATE_FILES


LITERATURE_DIRECTORIES = [
    "metadata",
    "topic_profiles",
    "agent_outputs",
    "notes",
    "synthesis",
    "sources",
    "source_candidates",
    "pdfs",
    "assets",
    "extracted",
]


@dataclass(frozen=True)
class SkeletonResult:
    created: list[Path]
    existing: list[Path]

    @property
    def created_count(self) -> int:
        return len(self.created)

    @property
    def existing_count(self) -> int:
        return len(self.existing)


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def touch_if_missing(path: Path) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return True


def iter_builtin_topic_profiles() -> list[tuple[str, str]]:
    profile_root = files("rsa_cli.data").joinpath("topic_profiles")
    return [
        (profile.name, profile.read_text(encoding="utf-8"))
        for profile in profile_root.iterdir()
        if profile.name.endswith(".yaml")
    ]


def create_literature_skeleton(config: ProjectConfig) -> SkeletonResult:
    created: list[Path] = []
    existing: list[Path] = []

    for directory in LITERATURE_DIRECTORIES:
        dir_path = config.literature_root / directory
        if dir_path.exists():
            existing.append(dir_path)
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
        gitkeep = dir_path / ".gitkeep"
        (created if touch_if_missing(gitkeep) else existing).append(gitkeep)

    for name, content in FORMAL_RECORD_FILES.items():
        path = config.literature_root / name
        (created if write_if_missing(path, content) else existing).append(path)

    for name, content in TEMPLATE_FILES.items():
        path = config.templates_root / name
        (created if write_if_missing(path, content) else existing).append(path)

    for profile_name, content in iter_builtin_topic_profiles():
        profile_path = config.topic_profiles_root / profile_name
        if write_if_missing(profile_path, content):
            created.append(profile_path)
        else:
            existing.append(profile_path)

    return SkeletonResult(created=created, existing=existing)
