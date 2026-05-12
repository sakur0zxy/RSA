from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

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


@dataclass(frozen=True)
class RoundSummary:
    path: Path
    frontmatter: dict[str, Any]
    body: str


@dataclass(frozen=True)
class RoundValidationResult:
    round_id: str
    path: Path
    errors: list[str]
    status: str | None

    @property
    def valid(self) -> bool:
        return not self.errors


ROUND_STATUSES = {"draft", "ready_for_review", "completed", "blocked"}
CANDIDATE_DECISIONS = {"verified", "rejected", "uncertain"}
FORMAL_REQUEST_FIELDS: dict[str, set[str]] = {
    "add_metadata": {"source_file", "source_row", "candidate_title", "doi_or_url", "reason"},
    "add_map_row": {"paper_id", "target_file", "priority_question", "research_role", "reason"},
}


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


def resolve_round_path(config: ProjectConfig, round_id: str) -> Path:
    if "/" in round_id or "\\" in round_id or ".." in round_id:
        raise RoundError("round_id 不能包含路径分隔符或 '..'")
    if not ROUND_DIR_PATTERN.match(round_id):
        raise RoundError("round_id 必须匹配 R###_name 格式")
    return config.agent_outputs_root / round_id


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _split_frontmatter(text: str, path: Path) -> tuple[dict[str, Any] | None, str, list[str]]:
    if not text.startswith("---\n"):
        return None, text, [f"{path.name} 缺少 YAML frontmatter 起始 `---`"]
    lines = text.splitlines()
    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return None, text, [f"{path.name} 缺少 YAML frontmatter 结束 `---`"]
    yaml_text = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :])
    try:
        loaded = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as exc:
        return None, body, [f"{path.name} YAML frontmatter 无效: {exc}"]
    if not isinstance(loaded, dict):
        return None, body, [f"{path.name} YAML frontmatter 必须是 mapping"]
    return loaded, body, []


def load_round_summary(round_path: Path) -> RoundSummary:
    summary_path = round_path / "final_round_summary.md"
    try:
        text = summary_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoundError(f"无法读取 final_round_summary.md: {exc}") from exc
    frontmatter, body, errors = _split_frontmatter(text, summary_path)
    if errors or frontmatter is None:
        raise RoundError("; ".join(errors))
    return RoundSummary(path=summary_path, frontmatter=frontmatter, body=body)


def _safe_declared_file(round_path: Path, value: Any, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append("included_files 中的文件名必须是非空字符串")
        return None
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        errors.append(f"included_files 包含不安全路径: {value}")
        return None
    return round_path / rel


def _parse_markdown_table(path: Path) -> tuple[list[str], list[dict[str, str]], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [], [f"无法读取 {path.name}: {exc}"]

    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if index + 1 >= len(lines) or "---" not in lines[index + 1]:
            continue
        headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.strip().startswith("|"):
                break
            values = [cell.strip() for cell in row_line.strip().strip("|").split("|")]
            values.extend([""] * (len(headers) - len(values)))
            row = dict(zip(headers, values[: len(headers)]))
            if any(value.strip() for value in row.values()):
                rows.append(row)
        return headers, rows, []
    return [], [], [f"{path.name} 缺少 Markdown 表格"]


def validate_candidate_review(path: Path) -> list[str]:
    required = ["candidate_title", "source", "doi_or_url", "decision", "reason", "last_checked"]
    headers, rows, errors = _parse_markdown_table(path)
    if errors:
        return errors
    missing = [field for field in required if field not in headers]
    if missing:
        return [f"verification_review.md 缺少字段: {', '.join(missing)}"]
    for row_number, row in enumerate(rows, start=1):
        decision = row.get("decision", "").strip()
        if decision not in CANDIDATE_DECISIONS:
            errors.append(
                f"verification_review.md 第 {row_number} 行 decision 必须是 "
                "verified/rejected/uncertain"
            )
        for field in ["reason", "last_checked"]:
            if _is_blank(row.get(field)):
                errors.append(f"verification_review.md 第 {row_number} 行缺少 {field}")
    return errors


def validate_formal_write_requests(requests: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(requests, list):
        return ["formal_write_requests 必须是 YAML list"]
    for index, request in enumerate(requests, start=1):
        if not isinstance(request, dict):
            errors.append(f"formal_write_requests 第 {index} 项必须是 mapping")
            continue
        request_type = request.get("request_type")
        if _is_blank(request_type):
            errors.append(f"formal_write_requests 第 {index} 项缺少 request_type")
            continue
        if request_type not in FORMAL_REQUEST_FIELDS:
            errors.append(
                f"formal_write_requests 第 {index} 项 request_type 不支持: {request_type}"
            )
            continue
        for field in sorted(FORMAL_REQUEST_FIELDS[str(request_type)]):
            if _is_blank(request.get(field)):
                errors.append(f"formal_write_requests 第 {index} 项缺少 {field}")
        if request_type == "add_map_row" and request.get("target_file") != "literature_map.md":
            errors.append("add_map_row 的 target_file 必须是 literature_map.md")
    return errors


def validate_round_archive(
    config: ProjectConfig, round_id: str, *, completion_check: bool = False
) -> RoundValidationResult:
    errors: list[str] = []
    try:
        round_path = resolve_round_path(config, round_id)
    except RoundError as exc:
        return RoundValidationResult(
            round_id=round_id,
            path=config.agent_outputs_root / round_id,
            errors=[str(exc)],
            status=None,
        )

    if not round_path.is_dir():
        return RoundValidationResult(
            round_id=round_id,
            path=round_path,
            errors=[f"round archive 不存在: {round_path}"],
            status=None,
        )

    for required in ["README.md", "final_round_summary.md"]:
        if not (round_path / required).exists():
            errors.append(f"缺少必需文件: {required}")
    if errors and not (round_path / "final_round_summary.md").exists():
        return RoundValidationResult(round_id=round_id, path=round_path, errors=errors, status=None)

    try:
        summary = load_round_summary(round_path)
    except RoundError as exc:
        errors.append(str(exc))
        return RoundValidationResult(round_id=round_id, path=round_path, errors=errors, status=None)

    frontmatter = summary.frontmatter
    status = frontmatter.get("status")
    if status not in ROUND_STATUSES:
        errors.append("status 必须是 draft/ready_for_review/completed/blocked")

    included_files = frontmatter.get("included_files")
    if not isinstance(included_files, list):
        errors.append("included_files 必须是 YAML list")
        included_files = []
    declared: set[str] = set()
    for value in included_files:
        declared_path = _safe_declared_file(round_path, value, errors)
        if declared_path is None:
            continue
        declared.add(str(value))
        if not declared_path.exists():
            errors.append(f"included_files 声明的文件不存在: {value}")

    errors.extend(validate_formal_write_requests(frontmatter.get("formal_write_requests")))

    if status == "completed":
        if frontmatter.get("human_confirmed") is not True:
            errors.append("status: completed 需要 human_confirmed: true")
        for field in ["confirmed_by", "confirmed_at"]:
            if _is_blank(frontmatter.get(field)):
                errors.append(f"status: completed 需要填写 {field}")
    elif completion_check:
        errors.append("当前轮次最多只能到 ready_for_review；completed 需要人工确认字段")

    review_path = round_path / "verification_review.md"
    if review_path.exists() or "verification_review.md" in declared:
        if review_path.exists():
            errors.extend(validate_candidate_review(review_path))

    return RoundValidationResult(
        round_id=round_id,
        path=round_path,
        errors=errors,
        status=str(status) if isinstance(status, str) else None,
    )


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
