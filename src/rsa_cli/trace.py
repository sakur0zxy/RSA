from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .rounds import load_round_summary, resolve_round_path


class TraceError(ValueError):
    """Raised when a round trace summary cannot be generated."""


@dataclass(frozen=True)
class TraceSummary:
    round_id: str
    path: Path
    tools_used: list[str]
    decisions_made: list[str]
    rejected_items: list[str]
    uncertain_items: list[str]
    human_approvals: list[str]
    formal_write_request_count: int


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _split_row(line: str) -> list[str]:
    return [cell.strip().replace("\\|", "|") for cell in line.strip().strip("|").split("|")]


def _parse_markdown_table(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"无法读取 {path.name}: {exc}"]
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if index + 1 >= len(lines) or "---" not in lines[index + 1]:
            continue
        headers = _split_row(line)
        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.strip().startswith("|"):
                break
            values = _split_row(row_line)
            values.extend([""] * (len(headers) - len(values)))
            row = dict(zip(headers, values[: len(headers)]))
            if any(value.strip() for value in row.values()):
                rows.append(row)
        return rows, []
    return [], []


def _tools_from_readme(round_path: Path) -> list[str]:
    readme = round_path / "README.md"
    if not readme.exists():
        return []
    for line in readme.read_text(encoding="utf-8").splitlines():
        if "allowed_tools:" not in line:
            continue
        value = line.split("allowed_tools:", 1)[1].strip().strip("`")
        if value in {"", "none"}:
            return []
        return [tool.strip() for tool in value.split(",") if tool.strip()]
    return []


def _candidate_trace(round_path: Path) -> tuple[list[str], list[str], list[str]]:
    review = round_path / "verification_review.md"
    if not review.exists():
        return [], [], []
    rows, _errors = _parse_markdown_table(review)
    decisions: list[str] = []
    rejected: list[str] = []
    uncertain: list[str] = []
    for row in rows:
        title = row.get("candidate_title", "").strip() or "(untitled)"
        decision = row.get("decision", "").strip()
        reason = row.get("reason", "").strip()
        item = f"{title} -> {decision}" + (f": {reason}" if reason else "")
        if decision:
            decisions.append(item)
        if decision == "rejected":
            rejected.append(item)
        if decision == "uncertain":
            uncertain.append(item)
    return decisions, rejected, uncertain


def build_trace_summary(config: ProjectConfig, round_id: str) -> TraceSummary:
    round_path = resolve_round_path(config, round_id)
    if not round_path.is_dir():
        raise TraceError(f"round archive 不存在: {round_path}")
    summary = load_round_summary(round_path)
    frontmatter = summary.frontmatter
    decisions, rejected, uncertain = _candidate_trace(round_path)
    requests = frontmatter.get("formal_write_requests") or []
    human_approvals: list[str] = []
    if frontmatter.get("human_confirmed") is True:
        confirmed_by = frontmatter.get("confirmed_by") or "(unknown)"
        confirmed_at = frontmatter.get("confirmed_at") or "(unknown)"
        human_approvals.append(f"round confirmed by {confirmed_by} at {confirmed_at}")
    if isinstance(requests, list) and requests:
        human_approvals.append(f"formal_write_requests pending/reviewed: {len(requests)}")
    return TraceSummary(
        round_id=round_id,
        path=round_path / "trace_summary.md",
        tools_used=_tools_from_readme(round_path),
        decisions_made=decisions,
        rejected_items=rejected,
        uncertain_items=uncertain,
        human_approvals=human_approvals,
        formal_write_request_count=len(requests) if isinstance(requests, list) else 0,
    )


def _yaml_ready(items: list[str]) -> list[str]:
    return list(items)


def render_trace_summary(trace: TraceSummary) -> str:
    frontmatter = {
        "round_id": trace.round_id,
        "generated_at": datetime.now(timezone.utc).date().isoformat(),
        "tools_used": _yaml_ready(trace.tools_used),
        "decisions_made": _yaml_ready(trace.decisions_made),
        "rejected_items": _yaml_ready(trace.rejected_items),
        "uncertain_items": _yaml_ready(trace.uncertain_items),
        "human_approvals": _yaml_ready(trace.human_approvals),
        "formal_write_request_count": trace.formal_write_request_count,
    }
    lines = [
        "---",
        yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        f"# Trace Summary / 追踪摘要: {trace.round_id}",
        "",
        "本文件用于快速审计研究轮次，不是正式文献事实源，也不会自动写入 metadata、map、reading note 或论文正文。",
        "",
        "## Tools Used / 使用工具",
    ]
    lines.extend([f"- `{tool}`" for tool in trace.tools_used] or ["- none"])
    lines.extend(["", "## Decisions Made / 决策记录"])
    lines.extend([f"- {item}" for item in trace.decisions_made] or ["- none"])
    lines.extend(["", "## Rejected Items / 拒绝项"])
    lines.extend([f"- {item}" for item in trace.rejected_items] or ["- none"])
    lines.extend(["", "## Uncertain Items / 不确定项"])
    lines.extend([f"- {item}" for item in trace.uncertain_items] or ["- none"])
    lines.extend(["", "## Human Approvals / 人工确认"])
    lines.extend([f"- {item}" for item in trace.human_approvals] or ["- none"])
    lines.extend(
        [
            "",
            "## Formal Write Requests / 正式写入请求",
            f"- count: {trace.formal_write_request_count}",
            "",
        ]
    )
    return "\n".join(lines)


def write_trace_summary(config: ProjectConfig, round_id: str) -> TraceSummary:
    trace = build_trace_summary(config, round_id)
    trace.path.write_text(render_trace_summary(trace), encoding="utf-8")
    return trace
