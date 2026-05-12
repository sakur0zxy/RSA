from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, load_metadata_record, validate_metadata_record
from .profiles import load_profile
from .rounds import load_round_summary, resolve_round_path, validate_round_archive


MAP_COLUMNS = [
    "paper_id",
    "topic_profile",
    "priority_question",
    "thesis_section",
    "planned_output",
    "research_role",
    "evidence_note",
    "map_status",
]
RESEARCH_ROLES = {
    "baseline",
    "theory",
    "method",
    "evaluation",
    "comparison",
    "background",
    "risk_or_limitation",
}
MAP_STATUSES = {"proposed", "approved", "needs_review", "deprecated"}
COVERING_ROLES = {"baseline", "theory", "method", "evaluation", "comparison"}
WEAK_REASONS = {
    "only_background_evidence",
    "only_risk_or_limitation",
    "missing_thesis_section",
    "missing_planned_output",
    "insufficient_method_or_evaluation_support",
}


class MapError(ValueError):
    """Raised when literature map operations cannot safely proceed."""


@dataclass(frozen=True)
class MapRow:
    paper_id: str
    topic_profile: str
    priority_question: str
    thesis_section: str
    planned_output: str
    research_role: str
    evidence_note: str
    map_status: str

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "MapRow":
        return cls(
            paper_id=str(values.get("paper_id", "") or "").strip(),
            topic_profile=str(values.get("topic_profile", "") or "").strip(),
            priority_question=str(values.get("priority_question", "") or "").strip(),
            thesis_section=str(values.get("thesis_section", "") or "").strip(),
            planned_output=str(values.get("planned_output", "") or "").strip(),
            research_role=str(values.get("research_role", "") or "").strip(),
            evidence_note=str(values.get("evidence_note", "") or "").strip(),
            map_status=str(values.get("map_status", "") or "").strip(),
        )

    def as_dict(self) -> dict[str, str]:
        return {column: getattr(self, column) for column in MAP_COLUMNS}

    def key(self) -> tuple[str, str, str, str]:
        return (self.paper_id, self.topic_profile, self.priority_question, self.research_role)


@dataclass(frozen=True)
class GapRow:
    priority_question: str
    status: str
    paper_ids: list[str]
    research_roles: list[str]
    weak_reason: list[str]
    next_action: str


def _escape_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _split_row(line: str) -> list[str]:
    return [cell.strip().replace("\\|", "|") for cell in line.strip().strip("|").split("|")]


def parse_literature_map_text(text: str) -> tuple[list[MapRow], list[str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        headers = _split_row(line)
        if set(MAP_COLUMNS).issubset(headers):
            rows: list[MapRow] = []
            for row_line in lines[index + 2 :]:
                if not row_line.strip().startswith("|"):
                    break
                values = _split_row(row_line)
                values.extend([""] * (len(headers) - len(values)))
                row = dict(zip(headers, values[: len(headers)]))
                if any(row.get(column, "").strip() for column in MAP_COLUMNS):
                    rows.append(MapRow.from_mapping(row))
            missing = [column for column in MAP_COLUMNS if column not in headers]
            return rows, [f"literature_map.md 缺少字段: {', '.join(missing)}"] if missing else []
    return [], ["literature_map.md 缺少 D-09 文献映射表格"]


def parse_literature_map(path: Path) -> tuple[list[MapRow], list[str]]:
    if not path.exists():
        return [], [f"literature_map.md 不存在: {path}"]
    return parse_literature_map_text(path.read_text(encoding="utf-8"))


def render_literature_map(rows: list[MapRow]) -> str:
    lines = [
        "# 文献映射",
        "",
        "用于人工维护 verified 文献与课题、优先问题、论文章节、计划产出和研究角色之间的关系。正式更新必须通过 `rsa formal apply-map --human-confirmed`。",
        "",
        "| paper_id | topic_profile | priority_question | thesis_section | planned_output | research_role | evidence_note | map_status |",
        "|----------|---------------|-------------------|----------------|----------------|---------------|---------------|------------|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_escape_cell(row.as_dict()[column]) for column in MAP_COLUMNS) + " |")
    lines.extend(
        [
            "",
            "## 字段说明",
            "",
            "- `paper_id`: 已通过 metadata gate 的正式文献编号，必须存在于 `metadata/P###.yaml`。",
            "- `topic_profile`: 课题 profile 的 `topic_id`。",
            "- `priority_question`: 该文献支持的优先问题。",
            "- `thesis_section`: 计划服务的论文或博士论文章节。",
            "- `planned_output`: 计划形成的综述、实验、表格或论文输出。",
            "- `research_role`: 研究角色，只能使用 `baseline`、`theory`、`method`、`evaluation`、`comparison`、`background`、`risk_or_limitation`。",
            "- `evidence_note`: 人工可读的证据摘要。",
            "- `map_status`: 映射状态，只能使用 `proposed`、`approved`、`needs_review`、`deprecated`；只有 `approved` 计入 gap coverage。",
            "",
            "## research_role 取值说明",
            "",
            "- `baseline`: 基线方法或对照。",
            "- `theory`: 理论依据。",
            "- `method`: 方法设计。",
            "- `evaluation`: 评价指标、数据或实验评价。",
            "- `comparison`: 对比分析。",
            "- `background`: 背景材料。",
            "- `risk_or_limitation`: 风险、局限或失败边界。",
            "",
            "## map_status 取值说明",
            "",
            "- `proposed`: 建议映射，尚未正式批准。",
            "- `approved`: 已批准映射，可用于 gap coverage。",
            "- `needs_review`: 需要复核。",
            "- `deprecated`: 已弃用，不计入当前覆盖。",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_duplicate_rows(rows: list[MapRow]) -> list[str]:
    errors: list[str] = []
    seen: dict[tuple[str, str, str, str], MapRow] = {}
    for row in rows:
        key = row.key()
        existing = seen.get(key)
        if existing is None:
            seen[key] = row
            continue
        if existing == row:
            errors.append(f"literature_map.md 存在重复映射行: {key}")
        else:
            errors.append(
                f"literature_map.md 存在冲突映射行: {key}; existing={existing.as_dict()}; requested={row.as_dict()}"
            )
    return errors


def validate_map_rows(config: ProjectConfig, rows: list[MapRow]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in ["paper_id", "topic_profile", "priority_question", "research_role", "map_status"]:
            if not row.as_dict()[field]:
                errors.append(f"literature_map.md 第 {index} 行缺少 {field}")
        if row.paper_id and not PAPER_ID_PATTERN.match(row.paper_id):
            errors.append(f"literature_map.md 第 {index} 行 paper_id 必须匹配 P###: {row.paper_id}")
        if row.research_role and row.research_role not in RESEARCH_ROLES:
            errors.append(
                f"literature_map.md 第 {index} 行 research_role 无效: {row.research_role}; "
                f"允许值: {', '.join(sorted(RESEARCH_ROLES))}"
            )
        if row.map_status and row.map_status not in MAP_STATUSES:
            errors.append(
                f"literature_map.md 第 {index} 行 map_status 无效: {row.map_status}; "
                f"允许值: {', '.join(sorted(MAP_STATUSES))}"
            )
        if PAPER_ID_PATTERN.match(row.paper_id):
            metadata_path = config.metadata_root / f"{row.paper_id}.yaml"
            metadata_errors = validate_metadata_record(metadata_path)
            if metadata_errors:
                errors.append(
                    f"literature_map.md 第 {index} 行引用的 {row.paper_id} metadata 无效: "
                    + "; ".join(metadata_errors)
                )
    errors.extend(_validate_duplicate_rows(rows))
    return errors


def validate_literature_map(config: ProjectConfig) -> list[str]:
    rows, parse_errors = parse_literature_map(config.literature_map_path)
    if parse_errors:
        return parse_errors
    return validate_map_rows(config, rows)


def _proposal_rows_from_requests(requests: Any) -> list[MapRow]:
    rows: list[MapRow] = []
    if not isinstance(requests, list):
        return rows
    for request in requests:
        if not isinstance(request, dict) or request.get("request_type") != "add_map_row":
            continue
        rows.append(
            MapRow(
                paper_id=str(request.get("paper_id", "") or ""),
                topic_profile=str(request.get("topic_profile", "") or ""),
                priority_question=str(request.get("priority_question", "") or ""),
                thesis_section=str(request.get("thesis_section", "") or ""),
                planned_output=str(request.get("planned_output", "") or ""),
                research_role=str(request.get("research_role", "") or ""),
                evidence_note=str(request.get("reason", "") or ""),
                map_status=str(request.get("map_status", "") or "proposed"),
            )
        )
    return rows


def render_map_proposal(round_id: str, rows: list[MapRow]) -> str:
    lines = [
        f"# 文献映射建议: {round_id}",
        "",
        "本文件由 `formal_write_requests` 生成，只是建议，不会修改正式 `literature_map.md`。",
        "正式写入必须运行 `rsa formal apply-map --source-round "
        f"{round_id} --human-confirmed --confirmed-by \"name\"`。",
        "",
        render_literature_map(rows),
    ]
    return "\n".join(lines)


def write_map_proposal(config: ProjectConfig, round_id: str) -> Path:
    validation = validate_round_archive(config, round_id)
    if validation.errors:
        raise MapError("; ".join(validation.errors))
    round_path = resolve_round_path(config, round_id)
    summary = load_round_summary(round_path)
    rows = _proposal_rows_from_requests(summary.frontmatter.get("formal_write_requests"))
    output_path = round_path / "map_proposal.md"
    output_path.write_text(render_map_proposal(round_id, rows), encoding="utf-8")
    return output_path


def _topic_profile_path(config: ProjectConfig, topic: str) -> Path:
    candidate = Path(topic)
    if candidate.exists():
        return candidate
    return config.topic_profiles_root / f"{topic}.yaml"


def _load_topic_profile(config: ProjectConfig, topic: str) -> dict[str, Any]:
    path = _topic_profile_path(config, topic)
    profile, errors = load_profile(path)
    if errors or profile is None:
        raise MapError("; ".join(errors))
    return profile


def classify_gap_rows(topic_id: str, questions: list[str], rows: list[MapRow]) -> list[GapRow]:
    approved = [
        row
        for row in rows
        if row.topic_profile == topic_id and row.map_status == "approved"
    ]
    gap_rows: list[GapRow] = []
    for question in questions:
        supporting = [row for row in approved if row.priority_question == question]
        if not supporting:
            gap_rows.append(
                GapRow(question, "missing", [], [], [], "补充检索或映射正式文献。")
            )
            continue
        roles = sorted({row.research_role for row in supporting})
        weak_reasons: list[str] = []
        if all(row.research_role == "background" for row in supporting):
            weak_reasons.append("only_background_evidence")
        if all(row.research_role == "risk_or_limitation" for row in supporting):
            weak_reasons.append("only_risk_or_limitation")
        if all(not row.thesis_section for row in supporting):
            weak_reasons.append("missing_thesis_section")
        if all(not row.planned_output for row in supporting):
            weak_reasons.append("missing_planned_output")
        if not any(row.research_role in COVERING_ROLES for row in supporting):
            weak_reasons.append("insufficient_method_or_evaluation_support")
        status = "weak" if weak_reasons else "covered"
        next_action = "保持覆盖并在写作时复核证据。" if status == "covered" else "补充方法、评价或章节/产出映射。"
        gap_rows.append(
            GapRow(
                priority_question=question,
                status=status,
                paper_ids=sorted({row.paper_id for row in supporting}),
                research_roles=roles,
                weak_reason=weak_reasons,
                next_action=next_action,
            )
        )
    return gap_rows


def render_gap_report(topic_id: str, rows: list[GapRow]) -> str:
    lines = [
        f"# 研究空白报告: {topic_id}",
        "",
        "本报告由 `literature_map.md` 和 topic profile 生成，用于规划后续阅读和检索，不是最终学术结论。",
        "",
        "| priority_question | status | paper_id | research_role | weak_reason | next_action |",
        "|-------------------|--------|----------|---------------|-------------|-------------|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(row.priority_question),
                    row.status,
                    ", ".join(row.paper_ids),
                    ", ".join(row.research_roles),
                    ", ".join(row.weak_reason),
                    _escape_cell(row.next_action),
                ]
            )
            + " |"
        )
    lines.extend(["", "## status 说明", "", "- `covered`: 已有 approved 且非纯背景/风险的映射支撑。", "- `weak`: 有证据但覆盖不完整，见 `weak_reason`。", "- `missing`: 没有 approved 映射。", ""])
    return "\n".join(lines)


def generate_gap_report(config: ProjectConfig, topic: str) -> tuple[Path, str]:
    profile = _load_topic_profile(config, topic)
    topic_id = str(profile["topic_id"])
    questions = list(profile.get("priority_questions", []))
    map_rows, parse_errors = parse_literature_map(config.literature_map_path)
    if parse_errors:
        raise MapError("; ".join(parse_errors))
    gap_rows = classify_gap_rows(topic_id, questions, map_rows)
    report = render_gap_report(topic_id, gap_rows)
    config.synthesis_root.mkdir(parents=True, exist_ok=True)
    path = config.synthesis_root / f"{topic_id}_gap_report.md"
    path.write_text(report, encoding="utf-8")
    return path, report


def validate_gap_report(config: ProjectConfig, topic: str) -> list[str]:
    profile = _load_topic_profile(config, topic)
    topic_id = str(profile["topic_id"])
    questions = list(profile.get("priority_questions", []))
    map_rows, parse_errors = parse_literature_map(config.literature_map_path)
    if parse_errors:
        return parse_errors
    expected = render_gap_report(topic_id, classify_gap_rows(topic_id, questions, map_rows))
    path = config.synthesis_root / f"{topic_id}_gap_report.md"
    if not path.exists():
        return [f"gap report 不存在，请运行 rsa gap generate --topic {topic_id}"]
    if path.read_text(encoding="utf-8") != expected:
        return [f"gap report 与当前 literature_map.md/topic profile 不一致，请重新运行 rsa gap generate --topic {topic_id}"]
    return []
