from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .campaign import CAMPAIGN_ID_PATTERN, campaign_path, load_campaign
from .config import ProjectConfig
from .metadata import (
    PAPER_ID_PATTERN,
    load_metadata_record,
    validate_metadata_record,
)
from .notes import NoteError, load_reading_note, note_path
from .visual import (
    CONFIDENCE_LEVELS as VISUAL_CONFIDENCE_LEVELS,
    load_visual_candidates,
    validate_visual_candidate_file,
    visual_candidate_path,
)


SCHEMA_VERSION = "phase9-scoring-v1"
SCORE_VERSION = "phase9-deterministic-v1"
SCORING_STATUSES = {"scored", "needs_review", "blocked"}
AI_REVIEW_DECISIONS = {
    "recommend_pass",
    "recommend_defer",
    "needs_review",
    "blocked",
}
FINAL_DECISIONS = {"approved", "rejected", "deferred"}
SCORE_CONFIDENCE_LEVELS = {"high", "medium", "low"}
SCORING_EVIDENCE_LEVELS = {
    "metadata_only",
    "text_only",
    "text_and_visual",
    "partial",
    "blocked",
}
SCORE_FIELDS = [
    "ai_relevance_score_10",
    "ai_quality_score_10",
    "ai_read_priority_score_10",
]
QUALITY_RUBRIC_FIELDS = [
    "method_clarity",
    "experiment_strength",
    "comparison_fairness",
    "reproducibility_signals",
    "limitation_awareness",
]
TEXT_SIGNAL_FIELDS = [
    "problem_signal",
    "method_signal",
    "experiment_signal",
    "dataset_signal",
    "metric_signal",
    "finding_signal",
    "limitation_signal",
]


class ScoringError(ValueError):
    """Raised when Phase 9 scoring cannot safely continue."""


@dataclass(frozen=True)
class ScorePaperResult:
    paper_id: str
    scoring_path: Path
    review_packet_path: Path
    ai_review_decision: str
    ai_relevance_score_10: int
    ai_quality_score_10: int
    ai_read_priority_score_10: int
    score_confidence: str


@dataclass(frozen=True)
class ScoreStatus:
    path: Path
    paper_id: str
    exists: bool
    scoring_status: str | None
    ai_review_decision: str | None
    ai_relevance_score_10: int | None
    ai_quality_score_10: int | None
    ai_read_priority_score_10: int | None
    score_confidence: str | None
    human_final_decision: str | None
    review_packet_path: Path


@dataclass(frozen=True)
class ReviewScoreResult:
    paper_id: str
    scoring_path: Path
    review_packet_path: Path
    final_decision: str
    history_count: int


@dataclass(frozen=True)
class CampaignScoringResult:
    campaign_id: str
    path: Path
    scored_count: int
    blocked_count: int
    skipped_count: int
    needs_review_count: int
    recommend_pass_count: int
    recommend_defer_count: int


def scoring_path(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.scores_root / f"{paper_id}_scoring.yaml"


def review_packet_path(config: ProjectConfig, paper_id: str) -> Path:
    _require_paper_id(paper_id)
    return config.scores_root / f"{paper_id}_review_packet.md"


def campaign_scoring_summary_path(config: ProjectConfig, campaign_id: str) -> Path:
    _require_campaign_id(campaign_id)
    return config.campaigns_root / f"{campaign_id}_scoring_summary.yaml"


def build_scoring_skeleton(paper_id: str) -> dict[str, Any]:
    _require_paper_id(paper_id)
    return {
        "paper_id": paper_id,
        "schema_version": SCHEMA_VERSION,
        "score_version": SCORE_VERSION,
        "generated_at": _now(),
        "scoring_status": "scored",
        "evidence_level": "text_only",
        "score_confidence": "medium",
        "ai_review_decision": "recommend_defer",
        "scores": {field: 0 for field in SCORE_FIELDS},
        "quality_rubric": {
            field: {
                "score_10": 0,
                "rationale_zh": "尚未生成该 rubric 子项的评分依据。",
            }
            for field in QUALITY_RUBRIC_FIELDS
        },
        "evidence_signals": {
            "text_signals": {field: [] for field in TEXT_SIGNAL_FIELDS},
            "visual_signals": {
                "visual_candidate_ids": [],
                "candidates": [],
                "degraded_reasons_zh": [],
            },
            "topic_signals": {
                "topic_profile": None,
                "priority_questions": [],
                "matches": [],
                "explanation_zh": "尚未生成 topic 匹配解释。",
            },
            "uncertainty_signals": [],
        },
        "scoring_basis": {
            "relevance_signals": [],
            "quality_signals_positive": [],
            "quality_signals_negative": [],
            "read_priority_factors": [],
            "threshold_semantics_zh": (
                "8-10 建议优先阅读或重点复核；6-7 表示 AI 初审建议进入监管队列；"
                "0-5 表示低优先级或暂缓。该建议不是 formal approval。"
            ),
        },
        "provenance": {
            "metadata": None,
            "reading_note": None,
            "source_chunks": [],
            "visual_candidates": None,
            "visual_context_packets": [],
            "campaign_item": None,
        },
        "limitations_zh": [],
        "human_review": default_human_review(),
        "review_history": [],
        "formal_record_policy_zh": (
            "Phase 9 scoring 是 AI 辅助的 staging/review 指导，不是正式学术结论；"
            "不是 formal approval；不得直接写入 metadata、literature_map、"
            "agent_research_notes 或论文正文。"
        ),
    }


def default_human_review() -> dict[str, Any]:
    return {
        "reviewed": False,
        "final_decision": None,
        "reviewer": None,
        "reviewed_at": None,
        "override_scores": {},
        "change_reason_zh": None,
        "policy_zh": (
            "这里记录 Phase 9 scoring 的人工监管或纠正结果；"
            "它不等同于 formal write approval。"
        ),
    }


def load_scoring_record(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    path = scoring_path(config, paper_id)
    if not path.exists():
        raise ScoringError(f"scoring 文件不存在: {path}")
    return _read_yaml_mapping(path)


def write_scoring_record(
    config: ProjectConfig, paper_id: str, data: dict[str, Any]
) -> Path:
    _require_paper_id(paper_id)
    if not isinstance(data, dict):
        raise ScoringError("scoring record 必须是 YAML mapping。")
    if data.get("paper_id") not in (None, paper_id):
        raise ScoringError(
            f"paper_id 必须与文件名一致: expected {paper_id}, got {data.get('paper_id')}"
        )
    data["paper_id"] = paper_id
    path = scoring_path(config, paper_id)
    _write_yaml(path, data)
    return path


def validate_scoring_record(config: ProjectConfig, paper_id: str) -> list[str]:
    if not PAPER_ID_PATTERN.match(paper_id):
        return [f"paper_id 必须匹配 P###: {paper_id}"]
    path = scoring_path(config, paper_id)
    if not path.exists():
        return [f"scoring 文件不存在: {path}"]
    try:
        data = _read_yaml_mapping(path)
    except ScoringError as exc:
        return [str(exc)]
    return _validate_scoring_mapping(data, expected_paper_id=paper_id)


def build_evidence_signals(
    config: ProjectConfig, paper_id: str, campaign_item: dict[str, Any] | None = None
) -> dict[str, Any]:
    _ensure_metadata(config, paper_id)
    metadata = load_metadata_record(_metadata_path(config, paper_id))
    try:
        note = load_reading_note(config, paper_id)
    except NoteError as exc:
        raise ScoringError(
            f"{paper_id} 缺少可读取的 Phase 8 reading note，无法生成可信评分: {exc}"
        ) from exc

    note_status = str(note.frontmatter.get("note_status") or "")
    if note_status == "blocked":
        raise ScoringError(f"{paper_id} reading note 状态为 blocked，不能生成正常评分。")

    claims = _list_of_mappings(note.frontmatter.get("source_grounded_claims"))
    short_quotes = _list_of_mappings(note.frontmatter.get("short_quotes"))
    uncertain = _list_values(note.frontmatter.get("uncertain_points_zh"))
    asset_suggestions = _list_of_mappings(note.frontmatter.get("asset_suggestions"))

    text_pool = _join_text([metadata, note.frontmatter, note.body])
    text_signals = {
        "problem_signal": _signal_items(claims, text_pool, ["problem", "challenge", "gap", "问题", "挑战", "缺口"]),
        "method_signal": _signal_items(claims, text_pool, ["method", "algorithm", "approach", "方法", "模型", "算法"]),
        "experiment_signal": _signal_items(claims, text_pool, ["experiment", "evaluation", "result", "实验", "评价", "结果"]),
        "dataset_signal": _signal_items(claims, text_pool, ["dataset", "data", "benchmark", "数据", "数据集"]),
        "metric_signal": _signal_items(claims, text_pool, ["metric", "accuracy", "rmse", "psnr", "指标", "精度"]),
        "finding_signal": _signal_items(claims, text_pool, ["finding", "show", "demonstrate", "发现", "表明", "说明"]),
        "limitation_signal": _signal_items(claims, text_pool, ["limitation", "future", "weak", "限制", "不足", "局限"]),
    }
    if claims and not any(text_signals.values()):
        text_signals["finding_signal"] = [_claim_summary(claims[0])]

    visual_signals, visual_limitations, visual_conflict = _build_visual_signals(
        config, paper_id
    )
    topic_profile = campaign_item.get("topic_profile") if campaign_item else None
    priority_question = campaign_item.get("priority_question") if campaign_item else None
    topic_profile = topic_profile or metadata.get("topic_profile")
    priority_questions = [
        item for item in _list_values(metadata.get("priority_questions")) if item
    ]
    if priority_question and priority_question not in priority_questions:
        priority_questions.append(str(priority_question))
    topic_signals = {
        "topic_profile": topic_profile,
        "priority_questions": priority_questions,
        "matches": [
            {
                "field": "topic_profile",
                "value": topic_profile,
                "explanation_zh": "来自正式 metadata 或 campaign 条目，用于判断论文与当前研究主题的相关性。",
            }
        ]
        if topic_profile
        else [],
        "explanation_zh": (
            "topic_profile 与 priority_questions 只用于 Phase 9 staging 评分，"
            "不代表正式学术结论。"
        ),
    }

    source_chunks = [
        {
            "source_chunk_id": claim.get("source_chunk_id"),
            "page": claim.get("evidence_page"),
            "section": claim.get("evidence_section"),
            "claim_zh": claim.get("claim_zh"),
        }
        for claim in claims
    ]
    uncertainty = []
    limitations = []
    if not claims:
        uncertainty.append("missing_source_grounded_claims")
        limitations.append("reading note 中缺少可定位的 source_grounded_claims，评分置信度会降低。")
    if str(note.frontmatter.get("extraction_status") or "") == "partial":
        uncertainty.append("partial_full_text")
        limitations.append("全文解析状态为 partial，评分只能作为初筛参考。")
    if not note.frontmatter.get("source_file"):
        uncertainty.append("missing_full_text_source")
        limitations.append("reading note 未记录 source_file，无法确认全文来源。")
    if visual_limitations:
        uncertainty.extend(visual_limitations)
        limitations.extend(_visual_limitation_text(item) for item in visual_limitations)
    if visual_conflict or _has_conflict([text_pool, uncertain, visual_signals]):
        uncertainty.append("text_visual_conflict")
        limitations.append("检测到正文/视觉证据可能存在冲突，需要人工复核。")
    if not short_quotes:
        limitations.append("reading note 中没有 short_quotes；回源定位仍可依赖 source chunks。")
    if asset_suggestions and not visual_signals["visual_candidate_ids"]:
        limitations.append("reading note 有 asset_suggestions，但尚未生成视觉证据候选。")

    return {
        "text_signals": text_signals,
        "visual_signals": visual_signals,
        "topic_signals": topic_signals,
        "uncertainty_signals": _unique(uncertainty),
        "provenance": {
            "metadata": _display_path(config, _metadata_path(config, paper_id)),
            "reading_note": _display_path(config, note.path),
            "source_chunks": source_chunks,
            "visual_candidates": _display_path(
                config, visual_candidate_path(config, paper_id)
            )
            if visual_candidate_path(config, paper_id).exists()
            else None,
            "visual_context_packets": [
                item.get("visual_context_packet")
                for item in visual_signals.get("candidates", [])
                if item.get("visual_context_packet")
            ],
            "campaign_item": campaign_item,
        },
        "limitations_zh": _unique(limitations),
    }


def score_paper(
    config: ProjectConfig,
    paper_id: str,
    campaign_item: dict[str, Any] | None = None,
    *,
    overwrite: bool = False,
) -> ScorePaperResult:
    _require_paper_id(paper_id)
    existing = _load_existing_or_empty(config, paper_id)
    signals = build_evidence_signals(config, paper_id, campaign_item=campaign_item)
    record = build_scoring_skeleton(paper_id)
    record["generated_at"] = _now()
    record["evidence_signals"] = {
        "text_signals": signals["text_signals"],
        "visual_signals": signals["visual_signals"],
        "topic_signals": signals["topic_signals"],
        "uncertainty_signals": signals["uncertainty_signals"],
    }
    record["provenance"] = signals["provenance"]
    record["limitations_zh"] = signals["limitations_zh"]

    scores, rubric, basis, confidence, evidence_level, decision, status = _compute_scores(
        signals
    )
    record["scores"] = scores
    record["quality_rubric"] = rubric
    record["scoring_basis"] = basis
    record["score_confidence"] = confidence
    record["evidence_level"] = evidence_level
    record["ai_review_decision"] = decision
    record["scoring_status"] = status

    if existing:
        record["human_review"] = existing.get("human_review") or default_human_review()
        record["review_history"] = existing.get("review_history") or []

    score_file = write_scoring_record(config, paper_id, record)
    packet_file = _write_review_packet(config, paper_id, record)
    return ScorePaperResult(
        paper_id=paper_id,
        scoring_path=score_file,
        review_packet_path=packet_file,
        ai_review_decision=str(record["ai_review_decision"]),
        ai_relevance_score_10=int(scores["ai_relevance_score_10"]),
        ai_quality_score_10=int(scores["ai_quality_score_10"]),
        ai_read_priority_score_10=int(scores["ai_read_priority_score_10"]),
        score_confidence=str(record["score_confidence"]),
    )


def score_status(config: ProjectConfig, paper_id: str) -> ScoreStatus:
    path = scoring_path(config, paper_id)
    packet = review_packet_path(config, paper_id)
    if not path.exists():
        return ScoreStatus(
            path=path,
            paper_id=paper_id,
            exists=False,
            scoring_status=None,
            ai_review_decision=None,
            ai_relevance_score_10=None,
            ai_quality_score_10=None,
            ai_read_priority_score_10=None,
            score_confidence=None,
            human_final_decision=None,
            review_packet_path=packet,
        )
    data = _read_yaml_mapping(path)
    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    human = data.get("human_review") if isinstance(data.get("human_review"), dict) else {}
    return ScoreStatus(
        path=path,
        paper_id=paper_id,
        exists=True,
        scoring_status=_clean(data.get("scoring_status")),
        ai_review_decision=_clean(data.get("ai_review_decision")),
        ai_relevance_score_10=_optional_int(scores.get("ai_relevance_score_10")),
        ai_quality_score_10=_optional_int(scores.get("ai_quality_score_10")),
        ai_read_priority_score_10=_optional_int(
            scores.get("ai_read_priority_score_10")
        ),
        score_confidence=_clean(data.get("score_confidence")),
        human_final_decision=_clean(human.get("final_decision")),
        review_packet_path=packet,
    )


def review_score(
    config: ProjectConfig,
    paper_id: str,
    *,
    final_decision: str,
    reviewer: str,
    reason: str,
    override_scores: dict[str, int] | None = None,
) -> ReviewScoreResult:
    if final_decision not in FINAL_DECISIONS:
        raise ScoringError("final_decision 必须是 approved/rejected/deferred。")
    if _is_blank(reviewer):
        raise ScoringError("必须提供 reviewer，记录谁完成了人工监管。")
    if _is_blank(reason) or not _contains_cjk(str(reason)):
        raise ScoringError("必须提供中文 reason，说明本次人工监管或纠正原因。")
    data = load_scoring_record(config, paper_id)
    errors = _validate_scoring_mapping(data, expected_paper_id=paper_id)
    if errors:
        raise ScoringError("scoring 文件无效，不能记录人工监管: " + "; ".join(errors))

    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    previous_human = (
        data.get("human_review") if isinstance(data.get("human_review"), dict) else {}
    )
    previous_decision = previous_human.get("final_decision") or data.get(
        "ai_review_decision"
    )
    changed_scores: dict[str, dict[str, int]] = {}
    if override_scores:
        for field, value in override_scores.items():
            if field not in SCORE_FIELDS:
                raise ScoringError(f"不支持覆盖的 score 字段: {field}")
            score = _coerce_score(value, f"override_scores.{field}")
            changed_scores[field] = {
                "previous": int(scores.get(field) or 0),
                "new": score,
            }
            scores[field] = score

    reviewed_at = _now()
    data["human_review"] = {
        "reviewed": True,
        "final_decision": final_decision,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "override_scores": override_scores or {},
        "change_reason_zh": reason,
        "policy_zh": (
            "这是 Phase 9 scoring 的人工监管结果，不是 formal write approval；"
            "如需写入正式记录，必须走 formal write gate。"
        ),
    }
    history = data.setdefault("review_history", [])
    if not isinstance(history, list):
        raise ScoringError("review_history 必须是 YAML list。")
    history.append(
        {
            "reviewed_at": reviewed_at,
            "reviewer": reviewer,
            "previous_decision": previous_decision,
            "new_decision": final_decision,
            "changed_scores": changed_scores,
            "change_reason_zh": reason,
        }
    )
    data["scores"] = scores
    score_file = write_scoring_record(config, paper_id, data)
    packet_file = _write_review_packet(config, paper_id, data)
    return ReviewScoreResult(
        paper_id=paper_id,
        scoring_path=score_file,
        review_packet_path=packet_file,
        final_decision=final_decision,
        history_count=len(history),
    )


def score_campaign(config: ProjectConfig, campaign_id: str) -> CampaignScoringResult:
    _require_campaign_id(campaign_id)
    source_path = campaign_path(config, campaign_id)
    campaign = load_campaign(config, campaign_id)
    items = campaign.get("items")
    if not isinstance(items, list):
        raise ScoringError("campaign items 必须是 YAML list。")
    rows: list[dict[str, Any]] = []
    counts = {
        "scored": 0,
        "blocked": 0,
        "skipped": 0,
        "needs_review": 0,
        "recommend_pass": 0,
        "recommend_defer": 0,
    }
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or "")
        paper_id = item.get("paper_id")
        if _is_blank(paper_id):
            counts["skipped"] += 1
            rows.append(
                {
                    "item_id": item_id,
                    "paper_id": None,
                    "status": "skipped",
                    "reason_zh": "该 campaign 条目尚未链接正式 metadata，Phase 9 不生成论文评分。",
                }
            )
            continue
        try:
            result = score_paper(config, str(paper_id), campaign_item=item)
        except ScoringError as exc:
            counts["blocked"] += 1
            rows.append(
                {
                    "item_id": item_id,
                    "paper_id": str(paper_id),
                    "status": "blocked",
                    "reason_zh": str(exc),
                }
            )
            continue
        counts["scored"] += 1
        decision = result.ai_review_decision
        if decision in counts:
            counts[decision] += 1
        row = {
            "item_id": item_id,
            "paper_id": result.paper_id,
            "status": "scored",
            "ai_review_decision": decision,
            "ai_relevance_score_10": result.ai_relevance_score_10,
            "ai_quality_score_10": result.ai_quality_score_10,
            "ai_read_priority_score_10": result.ai_read_priority_score_10,
            "score_confidence": result.score_confidence,
            "scoring_file": _display_path(config, result.scoring_path),
            "review_packet": _display_path(config, result.review_packet_path),
            "limitations_zh": load_scoring_record(config, result.paper_id).get(
                "limitations_zh", []
            ),
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            int(row.get("ai_read_priority_score_10") or -1),
            int(row.get("ai_relevance_score_10") or -1),
            int(row.get("ai_quality_score_10") or -1),
        ),
        reverse=True,
    )
    summary = {
        "campaign_id": campaign_id,
        "schema_version": SCHEMA_VERSION,
        "score_version": SCORE_VERSION,
        "generated_at": _now(),
        "source_campaign": _display_path(config, source_path),
        "policy_zh": (
            "该文件只是 Phase 9 批量 scoring summary，用于排序和监管；"
            "它不修改 campaign 队列，也不写入 formal records。"
        ),
        "counts": counts,
        "rows": rows,
    }
    path = campaign_scoring_summary_path(config, campaign_id)
    _write_yaml(path, summary)
    return CampaignScoringResult(
        campaign_id=campaign_id,
        path=path,
        scored_count=counts["scored"],
        blocked_count=counts["blocked"],
        skipped_count=counts["skipped"],
        needs_review_count=counts["needs_review"],
        recommend_pass_count=counts["recommend_pass"],
        recommend_defer_count=counts["recommend_defer"],
    )


def validate_campaign_scoring_summary(
    config: ProjectConfig, campaign_id: str
) -> list[str]:
    path = campaign_scoring_summary_path(config, campaign_id)
    if not path.exists():
        return [f"campaign scoring summary 不存在: {path}"]
    try:
        data = _read_yaml_mapping(path)
    except ScoringError as exc:
        return [str(exc)]
    errors: list[str] = []
    if data.get("campaign_id") != campaign_id:
        errors.append("campaign_id 必须与文件名一致。")
    if not isinstance(data.get("counts"), dict):
        errors.append("counts 必须是 YAML mapping。")
    if not isinstance(data.get("rows"), list):
        errors.append("rows 必须是 YAML list。")
    if "formal" not in str(data.get("policy_zh") or ""):
        errors.append("policy_zh 必须说明该 summary 不写入 formal records。")
    return errors


def _validate_scoring_mapping(
    data: dict[str, Any], *, expected_paper_id: str
) -> list[str]:
    errors: list[str] = []
    required = [
        "paper_id",
        "schema_version",
        "generated_at",
        "scoring_status",
        "evidence_level",
        "score_confidence",
        "ai_review_decision",
        "scores",
        "quality_rubric",
        "evidence_signals",
        "scoring_basis",
        "provenance",
        "limitations_zh",
        "human_review",
        "review_history",
        "formal_record_policy_zh",
    ]
    for field in required:
        if field not in data:
            errors.append(f"缺少必填字段: {field}")
    if data.get("paper_id") != expected_paper_id:
        errors.append(
            f"paper_id 必须与文件名一致: expected {expected_paper_id}, got {data.get('paper_id')}"
        )
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 不支持: {data.get('schema_version')}")
    if data.get("scoring_status") not in SCORING_STATUSES:
        errors.append(f"scoring_status 不支持: {data.get('scoring_status')}")
    if data.get("evidence_level") not in SCORING_EVIDENCE_LEVELS:
        errors.append(f"evidence_level 不支持: {data.get('evidence_level')}")
    if data.get("score_confidence") not in SCORE_CONFIDENCE_LEVELS:
        errors.append(f"score_confidence 不支持: {data.get('score_confidence')}")
    if data.get("ai_review_decision") not in AI_REVIEW_DECISIONS:
        errors.append(f"ai_review_decision 不支持: {data.get('ai_review_decision')}")

    scores = data.get("scores")
    if not isinstance(scores, dict):
        errors.append("scores 必须是 YAML mapping。")
    else:
        for field in SCORE_FIELDS:
            if field not in scores:
                errors.append(f"scores 缺少 {field}")
                continue
            try:
                _coerce_score(scores[field], f"scores.{field}")
            except ScoringError as exc:
                errors.append(str(exc))

    rubric = data.get("quality_rubric")
    if not isinstance(rubric, dict):
        errors.append("quality_rubric 必须是 YAML mapping。")
    else:
        for field in QUALITY_RUBRIC_FIELDS:
            item = rubric.get(field)
            if not isinstance(item, dict):
                errors.append(f"quality_rubric.{field} 必须是 mapping。")
                continue
            try:
                _coerce_score(item.get("score_10"), f"quality_rubric.{field}.score_10")
            except ScoringError as exc:
                errors.append(str(exc))
            if _is_blank(item.get("rationale_zh")):
                errors.append(f"quality_rubric.{field}.rationale_zh 不能为空。")

    if not isinstance(data.get("evidence_signals"), dict):
        errors.append("evidence_signals 必须是 YAML mapping。")
    if not isinstance(data.get("scoring_basis"), dict):
        errors.append("scoring_basis 必须是 YAML mapping。")
    if not isinstance(data.get("provenance"), dict):
        errors.append("provenance 必须是 YAML mapping。")
    if not isinstance(data.get("limitations_zh"), list):
        errors.append("limitations_zh 必须是 YAML list。")
    human = data.get("human_review")
    if not isinstance(human, dict):
        errors.append("human_review 必须是 YAML mapping。")
    else:
        for field in [
            "reviewed",
            "final_decision",
            "reviewer",
            "reviewed_at",
            "override_scores",
            "change_reason_zh",
            "policy_zh",
        ]:
            if field not in human:
                errors.append(f"human_review 缺少 {field}")
        if human.get("final_decision") not in FINAL_DECISIONS | {None}:
            errors.append(
                f"human_review.final_decision 不支持: {human.get('final_decision')}"
            )
    if not isinstance(data.get("review_history"), list):
        errors.append("review_history 必须是 YAML list。")
    policy = str(data.get("formal_record_policy_zh") or "")
    if not policy or ("formal" not in policy and "正式" not in policy):
        errors.append("formal_record_policy_zh 必须说明该评分不是正式记录。")
    return errors


def _compute_scores(
    signals: dict[str, Any]
) -> tuple[
    dict[str, int],
    dict[str, dict[str, Any]],
    dict[str, list[str] | str],
    str,
    str,
    str,
    str,
]:
    text = signals["text_signals"]
    visual = signals["visual_signals"]
    topic = signals["topic_signals"]
    uncertainty = set(signals["uncertainty_signals"])

    relevance = 4
    relevance_basis = []
    if topic.get("topic_profile"):
        relevance += 2
        relevance_basis.append("存在 topic_profile，可与当前研究主题对齐。")
    priority_questions = topic.get("priority_questions") or []
    if priority_questions:
        relevance += min(2, len(priority_questions))
        relevance_basis.append("metadata/campaign 提供 priority_question 线索。")
    if text["problem_signal"] or text["method_signal"] or text["finding_signal"]:
        relevance += 2
        relevance_basis.append("reading note 中存在问题、方法或发现相关信号。")
    relevance = _clamp_score(relevance)

    positive = []
    negative = []
    rubric_scores = {
        "method_clarity": 6 if text["method_signal"] else 4,
        "experiment_strength": 6 if text["experiment_signal"] else 3,
        "comparison_fairness": 5
        if _text_contains_any(text, ["comparison", "baseline", "对比", "基线"])
        else 3,
        "reproducibility_signals": 5
        if text["dataset_signal"] or text["metric_signal"]
        else 3,
        "limitation_awareness": 6 if text["limitation_signal"] else 3,
    }
    high_visual = sum(
        1
        for item in visual.get("candidates", [])
        if item.get("confidence") == "high"
        and item.get("evidence_level") in {"caption_visual_text", "caption_and_visual"}
    )
    if high_visual:
        rubric_scores["experiment_strength"] += 1
        rubric_scores["reproducibility_signals"] += 1
        positive.append("高置信视觉证据增强了实验结果或可复核性信号。")
    if visual.get("visual_candidate_ids"):
        positive.append("存在可回链的视觉证据候选，可辅助人工复核。")
    else:
        negative.append("缺少视觉证据候选，质量评分不使用图表支撑。")
    if "low_confidence_visual_evidence" in uncertainty:
        rubric_scores["experiment_strength"] -= 1
        negative.append("存在低置信视觉证据，只能作为弱信号。")
    if "ocr_partial_success" in uncertainty:
        rubric_scores["reproducibility_signals"] -= 1
        negative.append("OCR/区域文本不完整，视觉证据可复核性降低。")

    rubric = {
        field: {
            "score_10": _clamp_score(score),
            "rationale_zh": _rubric_rationale(field, _clamp_score(score)),
        }
        for field, score in rubric_scores.items()
    }
    quality = round(
        sum(item["score_10"] for item in rubric.values()) / len(QUALITY_RUBRIC_FIELDS)
    )

    confidence = "medium"
    if high_visual and not uncertainty:
        confidence = "high"
    if {
        "missing_source_grounded_claims",
        "partial_full_text",
        "missing_full_text_source",
        "low_confidence_visual_evidence",
        "ocr_partial_success",
    } & uncertainty:
        confidence = "low" if "missing_source_grounded_claims" in uncertainty else "medium"

    priority = round(relevance * 0.45 + quality * 0.35)
    if confidence == "high":
        priority += 1
    if confidence == "low":
        priority -= 1
    if "text_visual_conflict" in uncertainty:
        priority -= 1
    priority = _clamp_score(priority)

    if "text_visual_conflict" in uncertainty:
        decision = "needs_review"
        status = "needs_review"
    elif priority >= 6 and confidence != "low":
        decision = "recommend_pass"
        status = "scored"
    elif priority >= 6:
        decision = "needs_review"
        status = "needs_review"
    else:
        decision = "recommend_defer"
        status = "scored"

    evidence_level = "text_and_visual" if visual.get("visual_candidate_ids") else "text_only"
    if "missing_source_grounded_claims" in uncertainty:
        evidence_level = "partial"

    basis = {
        "relevance_signals": relevance_basis or ["未发现强 topic 匹配，只能低置信排序。"],
        "quality_signals_positive": positive,
        "quality_signals_negative": negative,
        "read_priority_factors": [
            f"relevance={relevance}/10",
            f"quality={quality}/10",
            f"confidence={confidence}",
            ">=6 仅表示进入 staging supervision queue，不是正式通过。",
        ],
        "threshold_semantics_zh": (
            "8-10 建议优先阅读或重点复核；6-7 表示 AI 初审建议进入监管队列；"
            "0-5 表示低优先级或暂缓。该建议不是 formal approval。"
        ),
    }
    scores = {
        "ai_relevance_score_10": relevance,
        "ai_quality_score_10": quality,
        "ai_read_priority_score_10": priority,
    }
    return scores, rubric, basis, confidence, evidence_level, decision, status


def _build_visual_signals(
    config: ProjectConfig, paper_id: str
) -> tuple[dict[str, Any], list[str], bool]:
    path = visual_candidate_path(config, paper_id)
    if not path.exists():
        return {
            "visual_candidate_ids": [],
            "candidates": [],
            "degraded_reasons_zh": ["缺少视觉证据候选，评分不会因为图表缺失而直接阻塞。"],
        }, ["missing_visual_evidence"], False

    validation_errors = validate_visual_candidate_file(config, paper_id)
    data = load_visual_candidates(config, paper_id)
    candidates = data.get("candidates") if isinstance(data.get("candidates"), list) else []
    out = []
    limitations = []
    conflict = False
    degraded = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        reason = _visual_degraded_reason(item)
        if reason:
            degraded.append(reason)
        if item.get("confidence") == "low":
            limitations.append("low_confidence_visual_evidence")
        if item.get("status") == "ocr_partial":
            limitations.append("ocr_partial_success")
        if item.get("status") in {"blocked", "needs_review"}:
            limitations.append("visual_needs_review")
        if _has_conflict([item.get("source_text"), item.get("warning_zh"), item.get("reason_zh")]):
            conflict = True
        out.append(
            {
                "visual_candidate_id": item.get("candidate_id"),
                "visual_type": item.get("visual_type"),
                "page": item.get("page"),
                "region_bbox": item.get("region_bbox"),
                "evidence_level": item.get("evidence_level"),
                "confidence": item.get("confidence"),
                "status": item.get("status"),
                "degraded_reason_zh": reason,
                "source_text": _limit_text(item.get("source_text")),
                "visual_context_packet": item.get("visual_context_packet"),
            }
        )
    if validation_errors:
        limitations.append("invalid_visual_candidate_schema")
        degraded.append(
            "visual_evidence_candidates.yaml 存在 schema 问题，视觉信号只用于提示人工复核。"
        )
    return {
        "visual_candidate_ids": [item.get("visual_candidate_id") for item in out],
        "candidates": out,
        "degraded_reasons_zh": _unique(degraded),
    }, _unique(limitations), conflict


def _write_review_packet(
    config: ProjectConfig, paper_id: str, record: dict[str, Any]
) -> Path:
    path = review_packet_path(config, paper_id)
    scores = record.get("scores", {})
    human = record.get("human_review", {})
    provenance = record.get("provenance", {})
    limitations = record.get("limitations_zh") or []
    visual = record.get("evidence_signals", {}).get("visual_signals", {})
    lines = [
        f"# Phase 9 评分监管包: {paper_id}",
        "",
        "## 当前 AI 建议",
        "",
        f"- `ai_review_decision`: `{record.get('ai_review_decision')}`",
        f"- `score_confidence`: `{record.get('score_confidence')}`",
        f"- `evidence_level`: `{record.get('evidence_level')}`",
        f"- `ai_relevance_score_10`: {scores.get('ai_relevance_score_10')}/10",
        f"- `ai_quality_score_10`: {scores.get('ai_quality_score_10')}/10",
        f"- `ai_read_priority_score_10`: {scores.get('ai_read_priority_score_10')}/10",
        "",
        "6 分以上只表示 AI 建议进入 staging supervision queue，不代表正式通过、正式学术评价或 formal write approval。",
        "",
        "## 相关链接",
        "",
        f"- scoring YAML: `{_display_path(config, scoring_path(config, paper_id))}`",
        f"- metadata: `{provenance.get('metadata')}`",
        f"- reading note: `{provenance.get('reading_note')}`",
        f"- visual candidates: `{provenance.get('visual_candidates')}`",
        "",
        "## 视觉证据候选",
        "",
        f"- candidate_count: {len(visual.get('visual_candidate_ids') or [])}",
    ]
    for candidate in visual.get("candidates") or []:
        lines.append(
            "- "
            f"`{candidate.get('visual_candidate_id')}` | "
            f"type={candidate.get('visual_type')} | "
            f"confidence={candidate.get('confidence')} | "
            f"evidence_level={candidate.get('evidence_level')} | "
            f"status={candidate.get('status')} | "
            f"degraded={candidate.get('degraded_reason_zh') or '无'}"
        )
    lines.extend(
        [
            "",
            "## 局限与人工监管重点",
            "",
        ]
    )
    if limitations:
        lines.extend(f"- {item}" for item in limitations)
    else:
        lines.append("- 暂无额外局限记录；仍建议抽查关键证据。")
    lines.extend(
        [
            "",
            "## 人工监管结果",
            "",
            f"- reviewed: `{human.get('reviewed')}`",
            f"- final_decision: `{human.get('final_decision')}`",
            f"- reviewer: `{human.get('reviewer')}`",
            f"- change_reason_zh: {human.get('change_reason_zh')}",
            "",
            "## Formal Record Boundary",
            "",
            record.get("formal_record_policy_zh", ""),
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _ensure_metadata(config: ProjectConfig, paper_id: str) -> None:
    _require_paper_id(paper_id)
    errors = validate_metadata_record(_metadata_path(config, paper_id))
    if errors:
        raise ScoringError(
            f"{paper_id} 正式 metadata 无效，不能生成 Phase 9 评分: " + "; ".join(errors)
        )


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


def _require_paper_id(paper_id: str) -> None:
    if not PAPER_ID_PATTERN.match(str(paper_id)):
        raise ScoringError(f"paper_id 必须匹配 P###: {paper_id}")


def _require_campaign_id(campaign_id: str) -> None:
    if not CAMPAIGN_ID_PATTERN.match(str(campaign_id)):
        raise ScoringError(f"campaign_id 必须匹配 C###: {campaign_id}")


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ScoringError(f"无法读取 YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ScoringError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ScoringError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list_values(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list_values(value) if isinstance(item, dict)]


def _join_text(values: list[Any]) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, dict):
            parts.extend(str(item) for item in value.values() if item is not None)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        else:
            parts.append(str(value or ""))
    return "\n".join(parts)


def _signal_items(
    claims: list[dict[str, Any]], text_pool: str, keywords: list[str]
) -> list[dict[str, Any]]:
    lowered = text_pool.lower()
    if not any(keyword.lower() in lowered for keyword in keywords):
        return []
    items = []
    for claim in claims:
        claim_text = _claim_text(claim).lower()
        if any(keyword.lower() in claim_text for keyword in keywords):
            items.append(_claim_summary(claim))
    if not items and claims:
        items.append(_claim_summary(claims[0]))
    return items


def _claim_text(claim: dict[str, Any]) -> str:
    return " ".join(
        str(claim.get(field) or "")
        for field in ["claim_zh", "evidence_section", "evidence_snippet"]
    )


def _claim_summary(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_zh": claim.get("claim_zh"),
        "source_chunk_id": claim.get("source_chunk_id"),
        "evidence_page": claim.get("evidence_page"),
        "evidence_section": claim.get("evidence_section"),
    }


def _visual_degraded_reason(item: dict[str, Any]) -> str | None:
    if item.get("confidence") == "low":
        return "该视觉候选 confidence=low，只能作为弱信号，不能直接支撑学术判断。"
    if item.get("status") == "ocr_partial":
        return "该视觉候选 OCR/区域文本只部分成功，需要人工查看截图和原 PDF。"
    if item.get("status") in {"needs_review", "blocked"}:
        return str(item.get("warning_zh") or "该视觉候选需要人工复核。")
    if item.get("evidence_level") in {"visual_only", "blocked"}:
        return "该视觉候选缺少可验证文本或 caption，评分时会降权。"
    return None


def _visual_limitation_text(code: str) -> str:
    mapping = {
        "missing_visual_evidence": "缺少视觉证据候选；评分不会因此阻塞，但质量/优先级解释会标记证据范围有限。",
        "low_confidence_visual_evidence": "存在低置信视觉候选；该候选只作为弱信号。",
        "ocr_partial_success": "存在 OCR/区域文本 partial 成功；需要人工查看截图。",
        "visual_needs_review": "存在需要人工复核或 blocked 的视觉候选。",
        "invalid_visual_candidate_schema": "视觉候选 schema 存在问题，不能作为强证据。",
    }
    return mapping.get(code, code)


def _has_conflict(values: Any) -> bool:
    text = str(values).lower()
    return any(token in text for token in ["conflict", "contradict", "冲突", "矛盾", "不一致"])


def _text_contains_any(text_signals: dict[str, list[Any]], keywords: list[str]) -> bool:
    text = str(text_signals).lower()
    return any(keyword.lower() in text for keyword in keywords)


def _rubric_rationale(field: str, score: int) -> str:
    names = {
        "method_clarity": "方法清晰度",
        "experiment_strength": "实验支撑强度",
        "comparison_fairness": "对比公平性",
        "reproducibility_signals": "可复现信号",
        "limitation_awareness": "局限意识",
    }
    level = "较强" if score >= 7 else "中等" if score >= 5 else "偏弱"
    return f"{names.get(field, field)}当前为{level}信号；这是 Phase 9 辅助评分，不是正式评价。"


def _load_existing_or_empty(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    path = scoring_path(config, paper_id)
    if not path.exists():
        return {}
    try:
        return _read_yaml_mapping(path)
    except ScoringError:
        return {}


def _coerce_score(value: Any, field: str) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ScoringError(f"{field} 必须是 0 到 10 的整数。") from exc
    if score < 0 or score > 10:
        raise ScoringError(f"{field} 必须在 0 到 10 之间。")
    return score


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clamp_score(value: int | float) -> int:
    return max(0, min(10, int(round(value))))


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _contains_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def _limit_text(value: Any, limit: int = 300) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return None
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _unique(values: list[Any]) -> list[Any]:
    out = []
    seen = set()
    for value in values:
        marker = str(value)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(value)
    return out
