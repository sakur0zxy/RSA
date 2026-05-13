from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, load_metadata_record, validate_metadata_record
from .templates import FORMAL_RECORD_FILES


NOTE_STATUSES = {"draft", "ready_for_review", "approved", "blocked"}
AUTHORIZATIONS = {"provided", "local", "authorized"}
NOTE_REQUEST_FIELDS: dict[str, set[str]] = {
    "add_map_row": {
        "paper_id",
        "target_file",
        "topic_profile",
        "priority_question",
        "research_role",
        "reason",
    },
    "add_research_note": {"target_file", "note_id", "summary"},
}


class NoteError(ValueError):
    """Raised when reading note operations cannot safely proceed."""


@dataclass(frozen=True)
class ReadingNote:
    path: Path
    frontmatter: dict[str, Any]
    body: str


@dataclass(frozen=True)
class CreateNoteResult:
    path: Path
    paper_id: str


def note_path(config: ProjectConfig, paper_id: str) -> Path:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise NoteError(f"paper_id 必须匹配 P###: {paper_id}")
    return config.notes_root / f"{paper_id}_reading_note.md"


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _resolve_project_path(config: ProjectConfig, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.root / path


def _escape_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


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


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


def _validate_paper_id_and_metadata(config: ProjectConfig, paper_id: str) -> list[str]:
    errors: list[str] = []
    if not PAPER_ID_PATTERN.match(paper_id):
        return [f"paper_id 必须匹配 P###: {paper_id}"]
    metadata_errors = validate_metadata_record(_metadata_path(config, paper_id))
    if metadata_errors:
        errors.append(f"{paper_id} metadata 无效: " + "; ".join(metadata_errors))
    return errors


def _ensure_pdf_report(config: ProjectConfig) -> None:
    if config.pdf_acquisition_report_path.exists():
        return
    config.pdf_acquisition_report_path.parent.mkdir(parents=True, exist_ok=True)
    config.pdf_acquisition_report_path.write_text(
        FORMAL_RECORD_FILES["pdf_acquisition_report.md"],
        encoding="utf-8",
    )


def record_pdf_status(
    config: ProjectConfig,
    *,
    paper_id: str,
    pdf_status: str,
    local_path: str,
    source_or_authorization: str,
    notes: str,
) -> Path:
    _ensure_pdf_report(config)
    path = config.pdf_acquisition_report_path
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    row = (
        f"| {_escape_cell(paper_id)} | {_escape_cell(pdf_status)} | "
        f"{_escape_cell(local_path)} | {_escape_cell(source_or_authorization)} | "
        f"{_escape_cell(notes)} |\n"
    )
    path.write_text(text + row, encoding="utf-8")
    return path


def render_reading_note(
    *,
    paper_id: str,
    metadata_path: str,
    source_file: str,
    authorization: str,
    created_at: str,
) -> str:
    frontmatter = {
        "paper_id": paper_id,
        "metadata": metadata_path,
        "note_status": "draft",
        "source_file": source_file,
        "authorization": authorization,
        "created_at": created_at,
        "source_grounded_claims": [],
        "short_quotes": [],
        "agent_summary": None,
        "human_decision": None,
        "human_confirmed": False,
        "confirmed_by": None,
        "confirmed_at": None,
        "note_integration_requests": [],
    }
    body = f"""# 文献阅读笔记: {paper_id}

## 字段说明

- `paper_id`: 正式文献编号，必须已经存在于 `metadata/P###.yaml`。
- `metadata`: 对应正式元数据文件路径。
- `note_status`: 阅读笔记状态，只能使用 `draft`、`ready_for_review`、`approved` 或 `blocked`。
- `source_file`: 本地、用户提供或已授权全文文件路径。
- `authorization`: 全文授权来源，只能使用 `provided`、`local` 或 `authorized`。
- `source_grounded_claims`: 可追溯到全文来源的事实或方法判断列表。
- `short_quotes`: 短引用摘录列表，只能保留必要短句，不能复制长段原文。
- `agent_summary`: agent 辅助摘要，不是正式学术结论。
- `human_decision`: 人工阅读判断或后续动作。
- `note_integration_requests`: 建议写入正式 map 或研究笔记的请求；必须通过 `rsa formal apply-note` 人工确认后才会生效。

## 来源与授权

- metadata 记录: `{metadata_path}`
- source_file: `{source_file}`
- authorization: `{authorization}`
- 授权状态: 仅允许使用本地、用户提供或已授权内容；不得根据未授权来源生成全文阅读结论。

## 来源支撑判断 / Source-Grounded Claims

## 短引用 / Short Quotes

## Agent 摘要 / Agent Summary

## 人工决策 / Human Decision

- 是否可进入正式研究记录:
- 需要补充核验:
"""
    return (
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + body
    )


def create_reading_note(
    config: ProjectConfig,
    paper_id: str,
    *,
    source_file: str,
    authorization: str,
) -> CreateNoteResult:
    metadata_errors = _validate_paper_id_and_metadata(config, paper_id)
    if metadata_errors:
        raise NoteError("; ".join(metadata_errors))
    if authorization not in AUTHORIZATIONS:
        record_pdf_status(
            config,
            paper_id=paper_id,
            pdf_status="blocked",
            local_path=source_file,
            source_or_authorization=authorization,
            notes="authorization 不在允许值 provided/local/authorized 中，未创建阅读笔记。",
        )
        raise NoteError("authorization 必须是 provided/local/authorized")

    source_path = _resolve_project_path(config, source_file)
    source_display = _display_path(config, source_path)
    if not source_path.is_file():
        record_pdf_status(
            config,
            paper_id=paper_id,
            pdf_status="blocked",
            local_path=source_display,
            source_or_authorization=authorization,
            notes="source_file 不存在或不是文件，未创建阅读笔记。",
        )
        raise NoteError("source_file 不存在或不是文件；已记录 PDF 获取状态，未创建阅读笔记")

    path = note_path(config, paper_id)
    if path.exists():
        raise NoteError(f"阅读笔记已存在，不会覆盖: {path}")

    metadata_display = _display_path(config, _metadata_path(config, paper_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_reading_note(
            paper_id=paper_id,
            metadata_path=metadata_display,
            source_file=source_display,
            authorization=authorization,
            created_at=datetime.now(timezone.utc).date().isoformat(),
        ),
        encoding="utf-8",
    )
    return CreateNoteResult(path=path, paper_id=paper_id)


def load_reading_note(config: ProjectConfig, paper_id: str) -> ReadingNote:
    path = note_path(config, paper_id)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NoteError(f"无法读取 reading note: {path}: {exc}") from exc
    frontmatter, body, errors = _split_frontmatter(text, path)
    if errors or frontmatter is None:
        raise NoteError("; ".join(errors))
    return ReadingNote(path=path, frontmatter=frontmatter, body=body)


def _validate_note_requests(requests: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(requests, list):
        return ["note_integration_requests 必须是 YAML list"]
    for index, request in enumerate(requests, start=1):
        if not isinstance(request, dict):
            errors.append(f"note_integration_requests 第 {index} 项必须是 mapping")
            continue
        request_type = request.get("request_type")
        if _is_blank(request_type):
            errors.append(f"note_integration_requests 第 {index} 项缺少 request_type")
            continue
        if request_type not in NOTE_REQUEST_FIELDS:
            errors.append(
                f"note_integration_requests 第 {index} 项 request_type 不支持: {request_type}"
            )
            continue
        for field in sorted(NOTE_REQUEST_FIELDS[str(request_type)]):
            if _is_blank(request.get(field)):
                errors.append(f"note_integration_requests 第 {index} 项缺少 {field}")
        if request_type == "add_map_row" and request.get("target_file") != "literature_map.md":
            errors.append("add_map_row 的 target_file 必须是 literature_map.md")
        if (
            request_type == "add_research_note"
            and request.get("target_file") != "agent_research_notes.md"
        ):
            errors.append("add_research_note 的 target_file 必须是 agent_research_notes.md")
    return errors


def _quote_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("text", "") or "")
    return str(value or "")


def validate_reading_note(config: ProjectConfig, paper_id: str) -> list[str]:
    if not PAPER_ID_PATTERN.match(paper_id):
        return [f"paper_id 必须匹配 P###: {paper_id}"]
    path = note_path(config, paper_id)
    if not path.exists():
        return [f"reading note 不存在: {path}"]
    try:
        note = load_reading_note(config, paper_id)
    except NoteError as exc:
        return [str(exc)]

    fm = note.frontmatter
    errors = _validate_paper_id_and_metadata(config, paper_id)
    if fm.get("paper_id") != paper_id:
        errors.append(f"paper_id 必须与文件名一致: expected {paper_id}, got {fm.get('paper_id')}")

    note_status = fm.get("note_status")
    if note_status not in NOTE_STATUSES:
        errors.append("note_status 必须是 draft/ready_for_review/approved/blocked")
    authorization = fm.get("authorization")
    if authorization not in AUTHORIZATIONS:
        errors.append("authorization 必须是 provided/local/authorized")

    for field in ["metadata", "source_file"]:
        if _is_blank(fm.get(field)):
            errors.append(f"缺少必填字段: {field}")

    source_file = fm.get("source_file")
    if not _is_blank(source_file):
        source_path = _resolve_project_path(config, str(source_file))
        if note_status != "blocked" and not source_path.is_file():
            errors.append(f"source_file 不存在或不是文件: {source_file}")

    for field in ["source_grounded_claims", "short_quotes", "note_integration_requests"]:
        if not isinstance(fm.get(field), list):
            errors.append(f"{field} 必须是 YAML list")

    short_quotes = fm.get("short_quotes")
    if isinstance(short_quotes, list):
        for index, quote in enumerate(short_quotes, start=1):
            if len(_quote_text(quote).split()) > 25:
                errors.append(f"short_quotes 第 {index} 项超过 25 个词，不能保留长段原文")

    errors.extend(_validate_note_requests(fm.get("note_integration_requests")))

    if note_status == "approved":
        if fm.get("human_confirmed") is not True:
            errors.append("note_status: approved 需要 human_confirmed: true")
        for field in ["confirmed_by", "confirmed_at"]:
            if _is_blank(fm.get(field)):
                errors.append(f"note_status: approved 需要填写 {field}")

    return errors


def note_status(config: ProjectConfig, paper_id: str) -> str:
    if not PAPER_ID_PATTERN.match(paper_id):
        return f"invalid_paper_id: {paper_id}"
    path = note_path(config, paper_id)
    if path.exists():
        try:
            note = load_reading_note(config, paper_id)
        except NoteError as exc:
            return f"invalid: {exc}"
        return str(note.frontmatter.get("note_status", "unknown"))
    metadata_errors = _validate_paper_id_and_metadata(config, paper_id)
    if metadata_errors:
        return "missing_metadata"
    record = load_metadata_record(_metadata_path(config, paper_id))
    return f"no_note; pdf_status={record.get('pdf_status', 'unknown')}"
