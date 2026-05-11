from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import ProjectConfig
from .profiles import validate_topic_profile
from .templates import TEMPLATE_FILES


ROUND_DIR_PATTERN = re.compile(r"^R(?P<number>\d{3})_")


class RoundError(ValueError):
    """Raised when a research round cannot be created safely."""


@dataclass(frozen=True)
class RoundResult:
    round_id: str
    path: Path
    max_candidates: int


def slugify_round_name(name: str) -> str:
    if "/" in name or "\\" in name or ".." in name:
        raise RoundError("round name must not contain path separators or '..'")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise RoundError("round name must contain at least one letter or number")
    return slug


def next_round_number(agent_outputs_root: Path) -> int:
    if not agent_outputs_root.exists():
        return 1
    highest = 0
    for child in agent_outputs_root.iterdir():
        if not child.is_dir():
            continue
        match = ROUND_DIR_PATTERN.match(child.name)
        if match:
            highest = max(highest, int(match.group("number")))
    return highest + 1


def enforce_candidate_limit(config: ProjectConfig, max_candidates: int | None) -> int:
    resolved = config.default_max_candidates if max_candidates is None else max_candidates
    if resolved <= 0:
        raise RoundError("max candidates must be positive")
    if resolved > config.hard_max_candidates:
        raise RoundError(
            f"max candidates {resolved} exceeds hard cap {config.hard_max_candidates}"
        )
    return resolved


def render_template(config: ProjectConfig, template_name: str, values: dict[str, str]) -> str:
    template_path = config.templates_root / template_name
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = TEMPLATE_FILES[template_name]
    return template.format(**values)


def create_research_round(
    config: ProjectConfig,
    topic_profile_path: Path | str,
    objective: str,
    name: str,
    max_candidates: int | None = None,
    allowed_tools: list[str] | None = None,
    output_policy: str | None = None,
    approval_mode: str | None = None,
    campaign_id: str | None = None,
) -> RoundResult:
    profile_path = Path(topic_profile_path)
    profile_errors = validate_topic_profile(profile_path)
    if profile_errors:
        joined = "; ".join(profile_errors)
        raise RoundError(f"topic profile invalid: {joined}")

    resolved_max = enforce_candidate_limit(config, max_candidates)
    slug = slugify_round_name(name)

    tools = allowed_tools if allowed_tools is not None else config.allowed_tools
    policy = output_policy or config.output_policy
    approval = approval_mode or config.approval_mode
    campaign = campaign_id or config.campaign_id or "none"

    round_number = next_round_number(config.agent_outputs_root)
    round_id = f"R{round_number:03d}_{slug}"
    round_path = config.agent_outputs_root / round_id
    if round_path.exists():
        raise RoundError(f"round directory already exists: {round_path}")

    round_path.mkdir(parents=True, exist_ok=False)
    values = {
        "round_id": round_id,
        "objective": objective,
        "topic_profile": str(profile_path),
        "max_candidates": str(resolved_max),
        "allowed_tools": ", ".join(tools) if tools else "none",
        "output_policy": policy,
        "approval_mode": approval,
        "campaign_id": campaign,
    }
    (round_path / "README.md").write_text(
        render_template(config, "round_readme.md", values), encoding="utf-8"
    )
    (round_path / "final_round_summary.md").write_text(
        render_template(config, "final_round_summary.md", values), encoding="utf-8"
    )
    return RoundResult(round_id=round_id, path=round_path, max_candidates=resolved_max)
