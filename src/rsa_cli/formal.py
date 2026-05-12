from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import ProjectConfig
from .map import MapRow, parse_literature_map, render_literature_map, validate_map_rows
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
