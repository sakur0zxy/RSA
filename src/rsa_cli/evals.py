from __future__ import annotations

from dataclasses import dataclass
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Callable, Any

import yaml

from .config import ProjectConfig, load_project_config
from .formal import FormalWriteError, apply_map_requests, apply_note_requests
from .map import validate_literature_map
from .metadata import MetadataError, write_metadata_record
from .notes import NoteError, create_reading_note, load_reading_note
from .rounds import create_research_round, load_round_summary
from .skeleton import create_literature_skeleton
from .templates import TEMPLATE_FILES


class EvalError(ValueError):
    """Raised when eval baseline or comparison cannot proceed."""


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    title: str
    passed: bool
    detail: str
    remediation: str


@dataclass(frozen=True)
class EvalRunResult:
    cases: list[EvalCaseResult]

    @property
    def passed(self) -> bool:
        return all(case.passed for case in self.cases)

    @property
    def passed_count(self) -> int:
        return sum(1 for case in self.cases if case.passed)

    @property
    def failed_count(self) -> int:
        return len(self.cases) - self.passed_count


@dataclass(frozen=True)
class EvalCompareResult:
    current: EvalRunResult
    regressions: list[str]
    path: Path

    @property
    def passed(self) -> bool:
        return not self.regressions and self.current.passed


@dataclass(frozen=True)
class EvalTopic:
    path: Path
    topic_id: str
    priority_question: str


def _eval_topic(config: ProjectConfig) -> EvalTopic:
    profiles = sorted(config.topic_profiles_root.glob("*.yaml"))
    if not profiles:
        raise AssertionError("no topic profile is available for eval fixtures")
    path = profiles[0]
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise AssertionError(f"topic profile must be a YAML mapping: {path}")
    questions = loaded.get("priority_questions")
    priority_question = (
        str(questions[0])
        if isinstance(questions, list) and questions
        else "eval_priority_question"
    )
    return EvalTopic(
        path=path,
        topic_id=str(loaded.get("topic_id") or path.stem),
        priority_question=priority_question,
    )


def _metadata_values(
    title: str = "Eval Paper",
    *,
    pdf_status: str = "not_acquired",
    topic_profile: str = "eval_topic",
    priority_question: str = "eval_priority_question",
) -> dict[str, Any]:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Evals",
        "doi": "10.1234/eval",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于 eval fixture。",
        "last_checked": "2026-05-13",
        "pdf_status": pdf_status,
        "local_pdf": None,
        "assets": [],
        "topic_profile": topic_profile,
        "priority_questions": [priority_question],
        "used_for": ["eval"],
        "research_roles": ["theory"],
        "notes": "eval",
    }


def _with_project(fn: Callable[[ProjectConfig], None]) -> None:
    with TemporaryDirectory() as tmp:
        config = load_project_config(Path(tmp))
        create_literature_skeleton(config)
        fn(config)


def _completed_round_with_map_request(config: ProjectConfig) -> str:
    topic = _eval_topic(config)
    result = create_research_round(config, topic.path, "Eval formal conflict", "eval formal")
    summary = load_round_summary(result.path)
    frontmatter = {
        "status": "completed",
        "included_files": [],
        "formal_write_requests": [
            {
                "request_type": "add_map_row",
                "paper_id": "P001",
                "target_file": "literature_map.md",
                "topic_profile": topic.topic_id,
                "priority_question": topic.priority_question,
                "thesis_section": "第2章",
                "planned_output": "eval",
                "research_role": "theory",
                "reason": "eval conflict check",
            }
        ],
        "human_confirmed": True,
        "confirmed_by": "eval",
        "confirmed_at": "2026-05-13",
    }
    summary.path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n"
        + summary.body,
        encoding="utf-8",
    )
    return result.round_id


def _case_metadata_hallucination() -> EvalCaseResult:
    try:
        def scenario(config: ProjectConfig) -> None:
            try:
                write_metadata_record(
                    config,
                    _metadata_values("Unconfirmed Eval Paper"),
                    human_confirmed=False,
                    confirmed_by=None,
                )
            except MetadataError:
                pass
            else:
                raise AssertionError("unconfirmed metadata write was allowed")
            if list(config.metadata_root.glob("P*.yaml")):
                raise AssertionError("metadata file was created without confirmation")

        _with_project(scenario)
    except Exception as exc:
        return EvalCaseResult(
            "metadata_hallucination",
            "Metadata hallucination gate",
            False,
            f"未确认 metadata 写入未被正确阻止: {exc}",
            "检查 `write_metadata_record` 是否仍强制 `--human-confirmed` 和 `confirmed_by`。",
        )
    return EvalCaseResult(
        "metadata_hallucination",
        "Metadata hallucination gate",
        True,
        "未确认 metadata 写入被阻止，未创建 `metadata/P###.yaml`。",
        "保持 metadata gate，不要让候选或模型判断直接分配 `paper_id`。",
    )


def _case_unauthorized_pdf() -> EvalCaseResult:
    try:
        def scenario(config: ProjectConfig) -> None:
            write_metadata_record(
                config,
                _metadata_values("Unauthorized PDF Eval", pdf_status="not_acquired"),
                human_confirmed=True,
                confirmed_by="eval",
            )
            try:
                create_reading_note(
                    config,
                    "P001",
                    source_file=str(config.pdfs_root / "missing.pdf"),
                    authorization="provided",
                )
            except NoteError:
                pass
            else:
                raise AssertionError("missing source created reading note")
            if (config.notes_root / "P001_reading_note.md").exists():
                raise AssertionError("fake reading note was created")
            report = config.pdf_acquisition_report_path.read_text(encoding="utf-8")
            if "blocked" not in report or "P001" not in report:
                raise AssertionError("blocked PDF status was not recorded")

        _with_project(scenario)
    except Exception as exc:
        return EvalCaseResult(
            "unauthorized_pdf_behavior",
            "Unauthorized PDF behavior",
            False,
            f"缺失或未授权全文处理失败: {exc}",
            "检查 `note create` 是否在 source_file 缺失时只写状态记录，不创建 reading note。",
        )
    return EvalCaseResult(
        "unauthorized_pdf_behavior",
        "Unauthorized PDF behavior",
        True,
        "缺失全文只记录 blocked 状态，没有生成伪 reading note。",
        "继续保持本地/提供/授权全文门禁。",
    )


def _case_formal_conflict() -> EvalCaseResult:
    try:
        def scenario(config: ProjectConfig) -> None:
            write_metadata_record(
                config,
                _metadata_values("Conflict Eval", pdf_status="local"),
                human_confirmed=True,
                confirmed_by="eval",
            )
            round_id = _completed_round_with_map_request(config)
            apply_map_requests(config, round_id, human_confirmed=True, confirmed_by="eval")
            before = config.literature_map_path.read_text(encoding="utf-8")
            try:
                apply_map_requests(config, round_id, human_confirmed=True, confirmed_by="eval")
            except FormalWriteError:
                pass
            else:
                raise AssertionError("duplicate formal map write was allowed")
            if config.literature_map_path.read_text(encoding="utf-8") != before:
                raise AssertionError("formal map changed after conflict")

        _with_project(scenario)
    except Exception as exc:
        return EvalCaseResult(
            "formal_record_conflict",
            "Formal record conflict blocking",
            False,
            f"正式记录冲突未被正确阻止: {exc}",
            "检查 formal writer 是否先完整 preflight，再执行 all-or-nothing 写入。",
        )
    return EvalCaseResult(
        "formal_record_conflict",
        "Formal record conflict blocking",
        True,
        "重复 formal map 写入被阻止，正式记录未被覆盖。",
        "保持冲突失败策略，不添加 force overwrite。",
    )


def _case_output_format_drift() -> EvalCaseResult:
    try:
        def scenario(config: ProjectConfig) -> None:
            errors = validate_literature_map(config)
            if errors:
                raise AssertionError("; ".join(errors))
            required_template_bits = {
                "final_round_summary.md": ["formal_write_requests", "human_confirmed"],
                "paper_note.md": ["source_grounded_claims", "note_integration_requests"],
                "trace_summary.md": ["tools_used", "human_approvals"],
            }
            for name, needles in required_template_bits.items():
                text = TEMPLATE_FILES[name]
                for needle in needles:
                    if needle not in text:
                        raise AssertionError(f"{name} missing {needle}")

        _with_project(scenario)
    except Exception as exc:
        return EvalCaseResult(
            "output_format_drift",
            "Output format drift",
            False,
            f"模板或正式表格格式漂移: {exc}",
            "恢复稳定 English 字段名和 Markdown/YAML schema，然后补充模板测试。",
        )
    return EvalCaseResult(
        "output_format_drift",
        "Output format drift",
        True,
        "核心模板和正式 map 表格仍保留机器可读字段。",
        "变更模板时同步更新 parser、renderer 和 tests。",
    )


def _case_scope_creep() -> EvalCaseResult:
    try:
        def scenario(config: ProjectConfig) -> None:
            source = config.pdfs_root / "P001.pdf"
            source.write_text("authorized source", encoding="utf-8")
            values = _metadata_values("Scope Creep Eval", pdf_status="local")
            values["local_pdf"] = str(source)
            write_metadata_record(config, values, human_confirmed=True, confirmed_by="eval")
            create_reading_note(config, "P001", source_file=str(source), authorization="local")
            note = load_reading_note(config, "P001")
            fm = dict(note.frontmatter)
            fm["note_status"] = "ready_for_review"
            fm["note_integration_requests"] = [
                {
                    "request_type": "add_research_note",
                    "target_file": "agent_research_notes.md",
                    "note_id": "scope-creep",
                    "summary": "should not apply",
                }
            ]
            note.path.write_text(
                "---\n"
                + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
                + "---\n"
                + note.body,
                encoding="utf-8",
            )
            before = config.agent_research_notes_path.read_text(encoding="utf-8")
            try:
                apply_note_requests(config, "P001", human_confirmed=True, confirmed_by="eval")
            except FormalWriteError:
                pass
            else:
                raise AssertionError("unapproved note affected formal research notes")
            if config.agent_research_notes_path.read_text(encoding="utf-8") != before:
                raise AssertionError("formal research notes changed from unapproved note")

        _with_project(scenario)
    except Exception as exc:
        return EvalCaseResult(
            "scope_creep",
            "Scope creep guardrail",
            False,
            f"未批准 reading note 影响了正式记录: {exc}",
            "检查 `formal apply-note` 是否仍要求 approved note 和人工确认字段。",
        )
    return EvalCaseResult(
        "scope_creep",
        "Scope creep guardrail",
        True,
        "未批准 reading note 无法影响正式研究记录。",
        "保持 formal writer 作为唯一正式写入路径。",
    )


def run_eval_fixtures() -> EvalRunResult:
    return EvalRunResult(
        [
            _case_metadata_hallucination(),
            _case_unauthorized_pdf(),
            _case_formal_conflict(),
            _case_output_format_drift(),
            _case_scope_creep(),
        ]
    )


def render_eval_report(result: EvalRunResult) -> str:
    lines = [
        "# Harness 评估报告 / Harness Eval Report",
        "",
        "本报告由本地 deterministic fixtures 生成，用于发现 harness 回归；它不是学术结论。",
        "",
        f"- passed: {result.passed_count}",
        f"- failed: {result.failed_count}",
        f"- total: {len(result.cases)}",
        "",
        "| case_id | status | detail | remediation |",
        "|---------|--------|--------|-------------|",
    ]
    for case in result.cases:
        status = "passed" if case.passed else "failed"
        lines.append(
            "| "
            + " | ".join(
                [
                    case.case_id,
                    status,
                    _escape_cell(case.detail),
                    _escape_cell(case.remediation),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _escape_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_eval_report(config: ProjectConfig, result: EvalRunResult) -> Path:
    config.synthesis_root.mkdir(parents=True, exist_ok=True)
    config.eval_report_path.write_text(render_eval_report(result), encoding="utf-8")
    return config.eval_report_path


def baseline_payload(result: EvalRunResult) -> dict[str, Any]:
    return {
        "cases": [
            {
                "case_id": case.case_id,
                "passed": case.passed,
                "detail": case.detail,
            }
            for case in result.cases
        ]
    }


def write_eval_baseline(config: ProjectConfig, result: EvalRunResult) -> Path:
    config.synthesis_root.mkdir(parents=True, exist_ok=True)
    config.eval_baseline_path.write_text(
        yaml.safe_dump(baseline_payload(result), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return config.eval_baseline_path


def compare_eval_baseline(config: ProjectConfig) -> EvalCompareResult:
    if not config.eval_baseline_path.exists():
        raise EvalError(f"eval baseline 不存在，请先运行 rsa eval baseline: {config.eval_baseline_path}")
    loaded = yaml.safe_load(config.eval_baseline_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict) or not isinstance(loaded.get("cases"), list):
        raise EvalError("eval_baseline.yaml 必须包含 cases list")
    baseline = {
        str(case.get("case_id")): bool(case.get("passed"))
        for case in loaded["cases"]
        if isinstance(case, dict) and case.get("case_id")
    }
    current = run_eval_fixtures()
    regressions: list[str] = []
    for case in current.cases:
        if baseline.get(case.case_id) is True and not case.passed:
            regressions.append(case.case_id)
    path = write_eval_regression_report(config, current, regressions)
    return EvalCompareResult(current=current, regressions=regressions, path=path)


def write_eval_regression_report(
    config: ProjectConfig, current: EvalRunResult, regressions: list[str]
) -> Path:
    lines = [
        "# 评估回归报告 / Eval Regression Report",
        "",
        "本报告比较当前 fixture 结果与本地 baseline，用于发现 prompt、模板、工具或规则变更造成的退化。",
        "",
        f"- regressions: {len(regressions)}",
        f"- current_passed: {current.passed_count}",
        f"- current_failed: {current.failed_count}",
        "",
    ]
    if regressions:
        lines.append("## Regressions / 回归项")
        lines.extend([f"- `{case_id}`" for case_id in regressions])
    else:
        lines.append("没有发现 baseline passing case 退化。")
    lines.append("")
    config.synthesis_root.mkdir(parents=True, exist_ok=True)
    config.eval_regression_report_path.write_text("\n".join(lines), encoding="utf-8")
    return config.eval_regression_report_path
