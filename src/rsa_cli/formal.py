from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .map import MapRow, parse_literature_map, render_literature_map, validate_map_rows
from .notes import load_reading_note, validate_reading_note
from .rounds import (
    load_round_summary,
    resolve_round_path,
    validate_formal_write_requests,
    validate_round_archive,
)


class FormalWriteError(ValueError):
    """Raised when a formal write is blocked by guardrails."""


@dataclass(frozen=True)
class ApplyMapResult:
    destination: str
    applied_count: int
    skipped_metadata_count: int


@dataclass(frozen=True)
class ApplyNoteResult:
    map_destination: str
    research_notes_destination: str
    map_rows_applied: int
    research_notes_applied: int


@dataclass(frozen=True)
class ResearchNoteRow:
    note_id: str
    source: str
    summary: str
    human_status: str

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "ResearchNoteRow":
        return cls(
            note_id=str(values.get("note_id", "") or "").strip(),
            source=str(values.get("source", "") or "").strip(),
            summary=str(values.get("summary", "") or "").strip(),
            human_status=str(values.get("human_status", "") or "").strip(),
        )

    def key(self) -> str:
        return self.note_id


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _require_cli_confirmation(human_confirmed: bool, confirmed_by: str | None) -> None:
    if not human_confirmed:
        raise FormalWriteError("正式写入必须提供 --human-confirmed，并让 human_confirmed 为 true")
    if _is_blank(confirmed_by):
        raise FormalWriteError("正式写入必须提供 --confirmed-by 记录人工确认人")


def _load_completed_round_requests(config: ProjectConfig, source_round: str) -> list[dict[str, Any]]:
    validation = validate_round_archive(config, source_round, completion_check=True)
    if validation.errors:
        raise FormalWriteError("; ".join(validation.errors))
    round_path = resolve_round_path(config, source_round)
    summary = load_round_summary(round_path)
    requests = summary.frontmatter.get("formal_write_requests")
    schema_errors = validate_formal_write_requests(requests)
    if schema_errors:
        raise FormalWriteError("; ".join(schema_errors))
    return list(requests or [])


def _map_row_from_request(request: dict[str, Any]) -> MapRow:
    return MapRow(
        paper_id=str(request.get("paper_id", "") or "").strip(),
        topic_profile=str(request.get("topic_profile", "") or "").strip(),
        priority_question=str(request.get("priority_question", "") or "").strip(),
        thesis_section=str(request.get("thesis_section", "") or "").strip(),
        planned_output=str(request.get("planned_output", "") or "").strip(),
        research_role=str(request.get("research_role", "") or "").strip(),
        evidence_note=str(request.get("reason", "") or "").strip(),
        map_status="approved",
    )


def _map_row_from_note_request(request: dict[str, Any]) -> MapRow:
    return MapRow(
        paper_id=str(request.get("paper_id", "") or "").strip(),
        topic_profile=str(request.get("topic_profile", "") or "").strip(),
        priority_question=str(request.get("priority_question", "") or "").strip(),
        thesis_section=str(request.get("thesis_section", "") or "").strip(),
        planned_output=str(request.get("planned_output", "") or "").strip(),
        research_role=str(request.get("research_role", "") or "").strip(),
        evidence_note=str(request.get("reason", "") or "").strip(),
        map_status="approved",
    )


def validate_apply_map_requests(config: ProjectConfig, source_round: str) -> tuple[list[MapRow], int]:
    requests = _load_completed_round_requests(config, source_round)
    skipped_metadata = 0
    requested_rows: list[MapRow] = []
    for request in requests:
        request_type = request.get("request_type")
        if request_type == "add_metadata":
            skipped_metadata += 1
            continue
        if request_type == "add_map_row":
            if request.get("target_file") != "literature_map.md":
                raise FormalWriteError("add_map_row 的 target_file 必须是 literature_map.md")
            requested_rows.append(_map_row_from_request(request))

    existing_rows, parse_errors = parse_literature_map(config.literature_map_path)
    if parse_errors:
        raise FormalWriteError("; ".join(parse_errors))

    validation_errors = validate_map_rows(config, existing_rows + requested_rows)
    if validation_errors:
        raise FormalWriteError("; ".join(validation_errors))
    return requested_rows, skipped_metadata


RESEARCH_NOTE_COLUMNS = ["note_id", "source", "summary", "human_status"]


def _escape_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _split_row(line: str) -> list[str]:
    return [cell.strip().replace("\\|", "|") for cell in line.strip().strip("|").split("|")]


def parse_agent_research_notes(path: Path) -> tuple[list[ResearchNoteRow], list[str]]:
    if not path.exists():
        return [], [f"agent_research_notes.md 不存在: {path}"]
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        headers = _split_row(line)
        if set(RESEARCH_NOTE_COLUMNS).issubset(headers):
            rows: list[ResearchNoteRow] = []
            for row_line in lines[index + 2 :]:
                if not row_line.strip().startswith("|"):
                    break
                values = _split_row(row_line)
                values.extend([""] * (len(headers) - len(values)))
                row = dict(zip(headers, values[: len(headers)]))
                if any(row.get(column, "").strip() for column in RESEARCH_NOTE_COLUMNS):
                    rows.append(ResearchNoteRow.from_mapping(row))
            missing = [column for column in RESEARCH_NOTE_COLUMNS if column not in headers]
            return rows, [f"agent_research_notes.md 缺少字段: {', '.join(missing)}"] if missing else []
    return [], ["agent_research_notes.md 缺少研究笔记表格"]


def render_agent_research_notes(rows: list[ResearchNoteRow]) -> str:
    lines = [
        "# Agent 辅助材料",
        "",
        "Agent 生成的研究笔记只作为辅助材料；进入论文、正式 map 或研究表格前必须人工审核和确认。",
        "",
        "| note_id | source | summary | human_status |",
        "|---------|--------|---------|--------------|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(row.note_id),
                    _escape_cell(row.source),
                    _escape_cell(row.summary),
                    _escape_cell(row.human_status),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 字段说明",
            "",
            "- `note_id`: 正式辅助笔记编号，必须唯一。",
            "- `source`: 来源 reading note 或其他正式记录路径。",
            "- `summary`: 经过人工确认可以保留的辅助摘要。",
            "- `human_status`: 人工状态；由 `formal apply-note` 写入时使用 `approved`。",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_research_note_rows(rows: list[ResearchNoteRow]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, ResearchNoteRow] = {}
    for index, row in enumerate(rows, start=1):
        for field, value in [
            ("note_id", row.note_id),
            ("source", row.source),
            ("summary", row.summary),
            ("human_status", row.human_status),
        ]:
            if _is_blank(value):
                errors.append(f"agent_research_notes.md 第 {index} 行缺少 {field}")
        existing = seen.get(row.key())
        if existing is None:
            seen[row.key()] = row
            continue
        if existing == row:
            errors.append(f"agent_research_notes.md 存在重复 note_id: {row.note_id}")
        else:
            errors.append(f"agent_research_notes.md 存在冲突 note_id: {row.note_id}")
    return errors


def _research_note_row_from_request(request: dict[str, Any], source: str) -> ResearchNoteRow:
    return ResearchNoteRow(
        note_id=str(request.get("note_id", "") or "").strip(),
        source=str(request.get("source", "") or source).strip(),
        summary=str(request.get("summary", "") or "").strip(),
        human_status="approved",
    )


def validate_apply_note_requests(
    config: ProjectConfig, source_note: str
) -> tuple[list[MapRow], list[ResearchNoteRow]]:
    note_errors = validate_reading_note(config, source_note)
    if note_errors:
        raise FormalWriteError("; ".join(note_errors))
    note = load_reading_note(config, source_note)
    frontmatter = note.frontmatter
    if frontmatter.get("note_status") != "approved":
        raise FormalWriteError("reading note 必须是 note_status: approved 才能正式写入")
    if frontmatter.get("human_confirmed") is not True:
        raise FormalWriteError("approved reading note 需要 human_confirmed: true")

    map_rows: list[MapRow] = []
    research_rows: list[ResearchNoteRow] = []
    requests = frontmatter.get("note_integration_requests") or []
    for request in requests:
        request_type = request.get("request_type")
        if request_type == "add_map_row":
            map_rows.append(_map_row_from_note_request(request))
        if request_type == "add_research_note":
            research_rows.append(_research_note_row_from_request(request, str(note.path)))

    existing_map_rows, map_parse_errors = parse_literature_map(config.literature_map_path)
    if map_parse_errors:
        raise FormalWriteError("; ".join(map_parse_errors))
    map_validation_errors = validate_map_rows(config, existing_map_rows + map_rows)
    if map_validation_errors:
        raise FormalWriteError("; ".join(map_validation_errors))

    existing_research_rows, research_parse_errors = parse_agent_research_notes(
        config.agent_research_notes_path
    )
    if research_parse_errors:
        raise FormalWriteError("; ".join(research_parse_errors))
    research_validation_errors = _validate_research_note_rows(
        existing_research_rows + research_rows
    )
    if research_validation_errors:
        raise FormalWriteError("; ".join(research_validation_errors))
    return map_rows, research_rows


def apply_map_requests(
    config: ProjectConfig,
    source_round: str,
    *,
    human_confirmed: bool,
    confirmed_by: str | None,
    confirmed_at: str | None = None,
) -> ApplyMapResult:
    _require_cli_confirmation(human_confirmed, confirmed_by)
    requested_rows, skipped_metadata = validate_apply_map_requests(config, source_round)
    existing_rows, parse_errors = parse_literature_map(config.literature_map_path)
    if parse_errors:
        raise FormalWriteError("; ".join(parse_errors))
    if requested_rows:
        config.literature_map_path.write_text(
            render_literature_map(existing_rows + requested_rows),
            encoding="utf-8",
        )
    return ApplyMapResult(
        destination=str(config.literature_map_path),
        applied_count=len(requested_rows),
        skipped_metadata_count=skipped_metadata,
    )


def apply_note_requests(
    config: ProjectConfig,
    source_note: str,
    *,
    human_confirmed: bool,
    confirmed_by: str | None,
    confirmed_at: str | None = None,
) -> ApplyNoteResult:
    _require_cli_confirmation(human_confirmed, confirmed_by)
    map_rows, research_rows = validate_apply_note_requests(config, source_note)

    existing_map_rows, map_parse_errors = parse_literature_map(config.literature_map_path)
    if map_parse_errors:
        raise FormalWriteError("; ".join(map_parse_errors))
    existing_research_rows, research_parse_errors = parse_agent_research_notes(
        config.agent_research_notes_path
    )
    if research_parse_errors:
        raise FormalWriteError("; ".join(research_parse_errors))

    if map_rows:
        config.literature_map_path.write_text(
            render_literature_map(existing_map_rows + map_rows),
            encoding="utf-8",
        )
    if research_rows:
        config.agent_research_notes_path.write_text(
            render_agent_research_notes(existing_research_rows + research_rows),
            encoding="utf-8",
        )
    return ApplyNoteResult(
        map_destination=str(config.literature_map_path),
        research_notes_destination=str(config.agent_research_notes_path),
        map_rows_applied=len(map_rows),
        research_notes_applied=len(research_rows),
    )
