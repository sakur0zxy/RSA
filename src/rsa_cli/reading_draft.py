from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .assets import source_record_path
from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, load_metadata_record, validate_metadata_record
from .notes import NoteError, load_reading_note, note_path, record_pdf_status


PROMPT_VERSION = "reading-draft-v1"
SCHEMA_VERSION = "reading-draft-schema-v1"
TEXT_CHUNK_SIZE = 1800
VERSION_PRIORITY = {
    "publisher_version": 0,
    "accepted_manuscript": 1,
    "repository_copy": 2,
    "arxiv_preprint": 3,
}
REQUIRED_DRAFT_FIELDS = [
    "research_problem_zh",
    "method_summary_zh",
    "experiment_summary_zh",
    "dataset_or_scene_zh",
    "metrics_zh",
    "main_findings_zh",
    "limitations_zh",
    "topic_relevance_zh",
    "uncertain_points_zh",
    "source_grounded_claims",
    "short_quotes",
    "asset_suggestions",
]


class DraftError(NoteError):
    """Raised when automated reading draft generation must fail closed."""


@dataclass(frozen=True)
class SelectedSource:
    source_id: str
    path: Path
    display_path: str
    authorization: str
    source_hash: str
    source_record: Path | None


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    page: int
    section: str
    text: str


@dataclass(frozen=True)
class ExtractionResult:
    status: str
    parser: str
    chunks: list[TextChunk]
    cache_path: Path
    reason_zh: str | None = None


@dataclass(frozen=True)
class DraftResult:
    note_path: Path
    review_packet_path: Path
    extraction_cache_path: Path
    prompt_packet_path: Path
    note_status: str
    agent_review_score_10: int


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


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


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise DraftError(f"YAML 必须是 mapping: {_safe_path(path)}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _safe_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ensure_metadata(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise DraftError(f"paper_id 必须匹配 P###: {paper_id}")
    errors = validate_metadata_record(_metadata_path(config, paper_id))
    if errors:
        raise DraftError(f"{paper_id} metadata 无效，无法生成阅读草稿: " + "; ".join(errors))
    return load_metadata_record(_metadata_path(config, paper_id))


def _source_sort_key(entry: dict[str, Any]) -> tuple[int, int, str]:
    primary = 0 if entry.get("is_primary") is True else 1
    version = str(entry.get("version_label") or "")
    priority = VERSION_PRIORITY.get(version, 50)
    return primary, priority, str(entry.get("source_id") or "")


def select_reading_source(
    config: ProjectConfig, paper_id: str, source_file: str | None = None
) -> SelectedSource:
    if source_file:
        path = _resolve_project_path(config, source_file)
        if not path.is_file():
            record_pdf_status(
                config,
                paper_id=paper_id,
                pdf_status="blocked",
                local_path=_display_path(config, path),
                source_or_authorization="manual_override",
                notes="指定的 source_file 不存在，未生成自动阅读草稿。",
            )
            raise DraftError("指定的 source_file 不存在，未生成自动阅读草稿。")
        return SelectedSource(
            source_id="manual_override",
            path=path,
            display_path=_display_path(config, path),
            authorization="provided",
            source_hash=_sha256(path),
            source_record=None,
        )

    ledger_path = source_record_path(config, paper_id)
    ledger = _read_yaml_mapping(ledger_path)
    raw_sources = ledger.get("sources", [])
    if isinstance(raw_sources, list):
        candidates = [
            item
            for item in raw_sources
            if isinstance(item, dict)
            and item.get("status") == "available"
            and item.get("source_type") == "pdf"
            and item.get("local_path")
        ]
        candidates.sort(key=_source_sort_key)
        for entry in candidates:
            path = _resolve_project_path(config, str(entry["local_path"]))
            if path.is_file():
                return SelectedSource(
                    source_id=str(entry.get("source_id") or "source_ledger"),
                    path=path,
                    display_path=_display_path(config, path),
                    authorization=str(entry.get("authorization") or "authorized"),
                    source_hash=_sha256(path),
                    source_record=ledger_path,
                )

    metadata = load_metadata_record(_metadata_path(config, paper_id))
    local_pdf = metadata.get("local_pdf")
    if local_pdf:
        path = _resolve_project_path(config, str(local_pdf))
        if path.is_file():
            return SelectedSource(
                source_id="metadata_local_pdf",
                path=path,
                display_path=_display_path(config, path),
                authorization=str(metadata.get("pdf_status") or "local"),
                source_hash=_sha256(path),
                source_record=None,
            )

    record_pdf_status(
        config,
        paper_id=paper_id,
        pdf_status="blocked",
        local_path="",
        source_or_authorization="source_ledger",
        notes="没有找到可用的本地或已授权 PDF 来源，未生成自动阅读草稿。",
    )
    raise DraftError("没有找到可用的本地或已授权 PDF 来源，未生成自动阅读草稿。")


def _extract_with_pypdf(path: Path) -> tuple[list[tuple[int, str]], str] | None:
    try:
        from pypdf import PdfReader
    except Exception:
        return None
    try:
        reader = PdfReader(str(path))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                return [], "pypdf_encrypted"
        pages: list[tuple[int, str]] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((index, text.strip()))
        return pages, "pypdf"
    except Exception:
        return None


def _decode_text_fallback(path: Path) -> tuple[list[tuple[int, str]], str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return ([(1, text)] if text else []), "text_fallback"


def _build_chunks(pages: list[tuple[int, str]], max_chunks: int) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for page, text in pages:
        for start in range(0, len(text), TEXT_CHUNK_SIZE):
            segment = text[start : start + TEXT_CHUNK_SIZE].strip()
            if not segment:
                continue
            chunk_id = f"C{len(chunks) + 1:03d}"
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    page=page,
                    section="unknown",
                    text=segment,
                )
            )
            if len(chunks) >= max_chunks:
                return chunks
    return chunks


def extract_source_text(
    config: ProjectConfig, paper_id: str, source: SelectedSource
) -> ExtractionResult:
    max_chunks = int(config.reading_draft_llm.get("max_chunks") or 8)
    cache_dir = config.extracted_root / paper_id
    cache_path = cache_dir / "extraction.yaml"

    extracted = _extract_with_pypdf(source.path)
    if extracted is None:
        pages, parser = _decode_text_fallback(source.path)
    else:
        pages, parser = extracted
        if not pages:
            fallback_pages, fallback_parser = _decode_text_fallback(source.path)
            pages = fallback_pages
            parser = f"{parser}+{fallback_parser}"

    chunks = _build_chunks(pages, max_chunks=max_chunks)
    total_chars = sum(len(chunk.text) for chunk in chunks)
    if not chunks or total_chars < 20:
        data = {
            "paper_id": paper_id,
            "source_id": source.source_id,
            "source_file": source.display_path,
            "source_hash": source.source_hash,
            "parser": parser,
            "extraction_status": "blocked",
            "reason_zh": "PDF 或来源文件没有可用文本，未生成自动阅读草稿。",
            "chunks": [],
        }
        _write_yaml(cache_path, data)
        record_pdf_status(
            config,
            paper_id=paper_id,
            pdf_status="blocked",
            local_path=source.display_path,
            source_or_authorization=source.authorization,
            notes="PDF 或来源文件没有可用文本，自动阅读草稿已阻止。",
        )
        raise DraftError("PDF 或来源文件没有可用文本，未生成自动阅读草稿。")

    status = "full_text_read" if total_chars >= 500 else "partial"
    data = {
        "paper_id": paper_id,
        "source_id": source.source_id,
        "source_file": source.display_path,
        "source_hash": source.source_hash,
        "parser": parser,
        "extraction_status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "page": chunk.page,
                "section": chunk.section,
                "text": chunk.text,
            }
            for chunk in chunks
        ],
    }
    _write_yaml(cache_path, data)
    return ExtractionResult(
        status=status,
        parser=parser,
        chunks=chunks,
        cache_path=cache_path,
        reason_zh=None if status == "full_text_read" else "提取文本较短，草稿需要人工重点复核。",
    )


def _estimate_tokens(chunks: list[TextChunk]) -> int:
    return max(1, sum(len(chunk.text) for chunk in chunks) // 4)


def write_prompt_packet(
    config: ProjectConfig,
    *,
    paper_id: str,
    source: SelectedSource,
    extraction: ExtractionResult,
    status: str,
    diagnostics_zh: str | None = None,
) -> Path:
    llm = config.reading_draft_llm
    path = config.extracted_root / paper_id / "prompt_packet.yaml"
    packet = {
        "paper_id": paper_id,
        "source_id": source.source_id,
        "source_hash": source.source_hash,
        "chunk_ids": [chunk.chunk_id for chunk in extraction.chunks],
        "chunk_count": len(extraction.chunks),
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "llm_provider": llm.get("provider"),
        "llm_model": llm.get("model"),
        "language": llm.get("language", "zh"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_token_estimate": _estimate_tokens(extraction.chunks),
        "status": status,
        "diagnostics_zh": diagnostics_zh,
    }
    _write_yaml(path, packet)
    return path


def _first_sentence(text: str, *, limit: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    match = re.split(r"(?<=[。！？.!?])\s+", cleaned, maxsplit=1)
    sentence = match[0] if match else cleaned
    return sentence[:limit].strip()


def _quote_from_text(text: str) -> str:
    words = re.sub(r"\s+", " ", text).strip().split()
    if len(words) >= 3:
        return " ".join(words[: min(12, len(words))])
    return _first_sentence(text, limit=80)


def _mock_llm_draft(metadata: dict[str, Any], extraction: ExtractionResult) -> dict[str, Any]:
    first = extraction.chunks[0]
    snippet = _first_sentence(first.text)
    title = str(metadata.get("title") or "该论文")
    uncertain = []
    if extraction.status == "partial":
        uncertain.append("本次只提取到较短文本，方法、实验和限制部分需要人工回到 PDF 复核。")
    else:
        uncertain.append("自动草稿仍需要人工核对关键 claim 与原文页码是否一致。")

    assets = []
    if re.search(r"\b(fig|figure|table)\b|图|表", first.text, flags=re.IGNORECASE):
        assets.append(
            {
                "asset_request_type": "figure_or_table_candidate",
                "page": first.page,
                "figure_or_table": "unknown",
                "reason_zh": "正文片段中出现图表相关词，建议 Phase 8.1 作为候选视觉证据检查。",
                "confidence": "medium",
                "evidence_basis": first.chunk_id,
            }
        )

    return {
        "research_problem_zh": f"自动草稿根据授权全文片段识别到：{title} 需要围绕论文提出的问题进行人工复核。",
        "method_summary_zh": f"方法线索来自片段 {first.chunk_id}：{snippet}",
        "experiment_summary_zh": "自动草稿未把实验信息视为正式结论；请结合原文实验章节人工确认。",
        "dataset_or_scene_zh": "数据集、场景或仿真设置需要人工核对原文对应章节。",
        "metrics_zh": "评价指标需要人工核对原文实验或结果章节。",
        "main_findings_zh": f"可追溯初步发现来自第 {first.page} 页片段 {first.chunk_id}，不得直接视为正式学术结论。",
        "limitations_zh": "自动阅读草稿可能遗漏 PDF 中的图表、公式、脚注和扫描页内容。",
        "topic_relevance_zh": "该条目已进入正式 metadata，自动草稿仅辅助判断其与当前研究主题的关系。",
        "uncertain_points_zh": uncertain,
        "source_grounded_claims": [
            {
                "claim_zh": f"论文《{title}》的自动草稿中有一条需要人工复核的来源支撑信息。",
                "evidence_page": first.page,
                "evidence_section": first.section,
                "source_chunk_id": first.chunk_id,
                "evidence_snippet": snippet,
                "needs_human_check": True,
            }
        ],
        "short_quotes": [
            {
                "quote": _quote_from_text(first.text),
                "page": first.page,
                "section": first.section,
                "reason_zh": "用于帮助人工定位原文，不作为论文正文素材。",
            }
        ],
        "asset_suggestions": assets,
    }


def _json_from_model_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    loaded = json.loads(cleaned)
    if not isinstance(loaded, dict):
        raise DraftError("模型输出 JSON 必须是 object。")
    return loaded


def _build_prompt(metadata: dict[str, Any], extraction: ExtractionResult) -> str:
    chunks = [
        {
            "chunk_id": chunk.chunk_id,
            "page": chunk.page,
            "section": chunk.section,
            "text": chunk.text,
        }
        for chunk in extraction.chunks
    ]
    payload = {
        "instruction_zh": (
            "请只根据给定片段生成中文 reading draft JSON。不要编造没有证据的结论；"
            "证据不足写入 uncertain_points_zh。"
        ),
        "schema_fields": REQUIRED_DRAFT_FIELDS,
        "metadata": {
            "title": metadata.get("title"),
            "year": metadata.get("year"),
            "venue": metadata.get("venue"),
            "doi": metadata.get("doi"),
        },
        "chunks": chunks,
    }
    return json.dumps(payload, ensure_ascii=False)


def _call_openai_compatible(
    config: ProjectConfig, metadata: dict[str, Any], extraction: ExtractionResult
) -> dict[str, Any]:
    llm = config.reading_draft_llm
    api_key_env = llm.get("api_key_env")
    api_key = os.environ.get(str(api_key_env)) if api_key_env else None
    if not api_key:
        raise DraftError("缺少 LLM API key 环境变量，未生成自动阅读草稿。")
    model = llm.get("model")
    if not model:
        raise DraftError("缺少 reading_draft.llm.model，未生成自动阅读草稿。")
    base_url = str(llm.get("base_url") or "https://api.openai.com/v1/chat/completions")
    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = endpoint + "/chat/completions"
    body = {
        "model": model,
        "temperature": float(llm.get("temperature") or 0),
        "messages": [
            {
                "role": "system",
                "content": "你是科研文献阅读助手。必须输出合法 JSON，不要输出 Markdown。",
            },
            {"role": "user", "content": _build_prompt(metadata, extraction)},
        ],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    timeout = int(llm.get("timeout_seconds") or 60)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise DraftError(f"LLM 调用失败，未生成自动阅读草稿: {exc}") from exc
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DraftError("LLM 响应缺少 choices[0].message.content。") from exc
    return _json_from_model_text(str(content))


def call_llm_draft(
    config: ProjectConfig, metadata: dict[str, Any], extraction: ExtractionResult
) -> dict[str, Any]:
    llm = config.reading_draft_llm
    provider = llm.get("provider")
    if not provider:
        raise DraftError("缺少 reading_draft.llm.provider，未生成自动阅读草稿。")
    provider_name = str(provider).lower()
    if provider_name in {"mock", "local_mock", "deterministic"}:
        return _mock_llm_draft(metadata, extraction)
    if provider_name in {"openai", "openai_compatible", "compatible"}:
        return _call_openai_compatible(config, metadata, extraction)
    if provider_name in {"codex_oauth", "openai_codex"}:
        from .codex_oauth import CodexOAuthError, call_codex_responses

        try:
            content = call_codex_responses(
                config,
                _build_prompt(metadata, extraction),
                system_prompt=(
                    "你是科研文献阅读助手。必须只输出合法 JSON，不要输出 Markdown。"
                    "所有用户可读内容使用中文；证据不足时写入 uncertain_points_zh。"
                ),
            )
        except CodexOAuthError as exc:
            raise DraftError(f"Codex OAuth LLM 调用失败，未生成自动阅读草稿: {exc}") from exc
        return _json_from_model_text(content)
    raise DraftError(f"暂不支持 LLM provider: {provider}，未生成自动阅读草稿。")


def validate_llm_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_DRAFT_FIELDS:
        if field not in payload:
            errors.append(f"模型输出缺少字段: {field}")
    for field in [
        "research_problem_zh",
        "method_summary_zh",
        "experiment_summary_zh",
        "dataset_or_scene_zh",
        "metrics_zh",
        "main_findings_zh",
        "limitations_zh",
        "topic_relevance_zh",
    ]:
        if not isinstance(payload.get(field), str) or not payload.get(field, "").strip():
            errors.append(f"{field} 必须是非空中文文本")
    for field in [
        "uncertain_points_zh",
        "source_grounded_claims",
        "short_quotes",
        "asset_suggestions",
    ]:
        if not isinstance(payload.get(field), list):
            errors.append(f"{field} 必须是 list")
    for index, claim in enumerate(payload.get("source_grounded_claims") or [], start=1):
        if not isinstance(claim, dict):
            errors.append(f"source_grounded_claims 第 {index} 项必须是 mapping")
            continue
        for field in [
            "claim_zh",
            "evidence_page",
            "evidence_section",
            "source_chunk_id",
            "evidence_snippet",
            "needs_human_check",
        ]:
            if claim.get(field) in (None, ""):
                errors.append(f"source_grounded_claims 第 {index} 项缺少 {field}")
    return errors


def _contains_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def _quote_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("quote") or value.get("text") or "")
    return str(value or "")


def review_payload(
    *,
    config: ProjectConfig,
    payload: dict[str, Any],
    source: SelectedSource,
    extraction: ExtractionResult,
    prompt_packet_path: Path,
) -> dict[str, Any]:
    warnings: list[str] = []
    hard_gate_errors: list[str] = []
    score_breakdown: dict[str, int] = {}

    required_strings = [
        "research_problem_zh",
        "method_summary_zh",
        "experiment_summary_zh",
        "dataset_or_scene_zh",
        "metrics_zh",
        "main_findings_zh",
        "limitations_zh",
        "topic_relevance_zh",
    ]
    complete_strings = all(str(payload.get(field) or "").strip() for field in required_strings)
    score_breakdown["structure_completeness"] = 2 if complete_strings else 1

    claims = payload.get("source_grounded_claims") if isinstance(payload.get("source_grounded_claims"), list) else []
    grounded_claims = [
        claim
        for claim in claims
        if isinstance(claim, dict)
        and claim.get("evidence_page") not in (None, "")
        and claim.get("source_chunk_id")
        and claim.get("evidence_snippet")
    ]
    if not grounded_claims:
        hard_gate_errors.append("没有可定位的 source_grounded_claims。")
    score_breakdown["evidence_grounding"] = 3 if grounded_claims else 0

    uncertain = payload.get("uncertain_points_zh")
    has_uncertain = isinstance(uncertain, list)
    if extraction.status == "partial" and not uncertain:
        warnings.append("解析状态为 partial，但 uncertain_points_zh 没有说明限制。")
    score_breakdown["risk_uncertainty_disclosure"] = 2 if has_uncertain else 0

    quote_ok = True
    for index, quote in enumerate(payload.get("short_quotes") or [], start=1):
        if len(_quote_text(quote).split()) > 25:
            quote_ok = False
            hard_gate_errors.append(f"short_quotes 第 {index} 项过长。")
    score_breakdown["short_quote_compliance"] = 1 if quote_ok else 0

    links_ok = bool(source.display_path and source.source_hash and prompt_packet_path)
    score_breakdown["source_cache_packet_links"] = 1 if links_ok else 0

    chinese_ok = any(_contains_cjk(str(payload.get(field) or "")) for field in required_strings)
    score_breakdown["chinese_readability"] = 1 if chinese_ok else 0

    if extraction.status == "blocked":
        hard_gate_errors.append("解析状态 blocked。")
    if not source.path.is_file():
        hard_gate_errors.append("来源文件不存在。")

    score = sum(score_breakdown.values())
    threshold = config.reading_draft_ready_score_threshold
    ready = score >= threshold and not hard_gate_errors
    if not ready and score < threshold:
        warnings.append(f"AI 初审分数 {score}/10 低于阈值 {threshold}。")
    if extraction.status == "partial":
        warnings.append("文本提取为 partial，用户需要重点复核。")

    grade = "ready_for_review" if ready else "draft_needs_review"
    action = (
        "建议进入人工通过检查；请重点核对 claim 页码、短引用和 uncertain_points_zh。"
        if ready
        else "建议先修正自动草稿或补充来源后再进入人工通过检查。"
    )
    rationale = (
        f"AI 初审得分 {score}/10。"
        + ("硬门禁全部通过。" if not hard_gate_errors else "存在硬门禁问题: " + "；".join(hard_gate_errors))
    )
    return {
        "agent_review_status": "passed" if ready else "needs_revision",
        "agent_reviewed_at": datetime.now(timezone.utc).isoformat(),
        "agent_review_score_10": score,
        "agent_review_grade": grade,
        "agent_review_rationale_zh": rationale,
        "score_breakdown": score_breakdown,
        "agent_review_warnings": warnings,
        "hard_gate_errors": hard_gate_errors,
        "recommended_human_action_zh": action,
        "needs_human_review": True,
        "note_status": "ready_for_review" if ready else "draft",
    }


def _relative(config: ProjectConfig, path: Path | None) -> str | None:
    if path is None:
        return None
    return _display_path(config, path)


def render_draft_note(
    *,
    config: ProjectConfig,
    paper_id: str,
    metadata: dict[str, Any],
    source: SelectedSource,
    extraction: ExtractionResult,
    prompt_packet_path: Path,
    review_packet_path: Path,
    payload: dict[str, Any],
    review: dict[str, Any],
) -> str:
    prompt_display = _display_path(config, prompt_packet_path)
    review_display = _display_path(config, review_packet_path)
    extraction_display = _display_path(config, extraction.cache_path)
    frontmatter: dict[str, Any] = {
        "paper_id": paper_id,
        "metadata": _display_path(config, _metadata_path(config, paper_id)),
        "note_status": review["note_status"],
        "source_file": source.display_path,
        "source_id": source.source_id,
        "source_hash": source.source_hash,
        "authorization": source.authorization,
        "extraction_status": extraction.status,
        "evidence_level": "partial_full_text" if extraction.status == "partial" else "full_text_read",
        "extraction_cache": extraction_display,
        "llm_provider": config.reading_draft_llm.get("provider"),
        "llm_model": config.reading_draft_llm.get("model"),
        "prompt_version": PROMPT_VERSION,
        "prompt_packet": prompt_display,
        "review_packet": review_display,
        "draft_created_at": datetime.now(timezone.utc).isoformat(),
        **{field: payload.get(field) for field in REQUIRED_DRAFT_FIELDS},
        "agent_summary": {
            "research_problem_zh": payload.get("research_problem_zh"),
            "method_summary_zh": payload.get("method_summary_zh"),
            "main_findings_zh": payload.get("main_findings_zh"),
        },
        "agent_review_status": review["agent_review_status"],
        "agent_reviewed_at": review["agent_reviewed_at"],
        "agent_review_score_10": review["agent_review_score_10"],
        "agent_review_grade": review["agent_review_grade"],
        "agent_review_rationale_zh": review["agent_review_rationale_zh"],
        "score_breakdown": review["score_breakdown"],
        "agent_review_warnings": review["agent_review_warnings"],
        "recommended_human_action_zh": review["recommended_human_action_zh"],
        "needs_human_review": True,
        "human_decision": None,
        "human_confirmed": False,
        "confirmed_by": None,
        "confirmed_at": None,
        "note_integration_requests": [],
    }
    body = f"""# 文献阅读草稿: {paper_id}

## 字段说明

- `note_status`: 自动草稿状态；`ready_for_review` 只表示 AI 初审通过，仍需人工监管。
- `source_grounded_claims`: 带页码、章节和 chunk 的来源支撑判断。
- `short_quotes`: 必要短引用，仅用于定位原文，不作为论文正文素材。
- `asset_suggestions`: 候选图表/表格建议，供 Phase 8.1 后续处理，不是正式学术结论。
- `agent_review_score_10`: 阅读草稿就绪度评分，不是论文质量或相关性评分。
- `human_confirmed`: 仍为 `false`；只有人工确认后才可能进入 `approved` 或 formal write。

## 来源与追踪

- metadata: `{frontmatter["metadata"]}`
- source_file: `{source.display_path}`
- extraction_cache: `{extraction_display}`
- prompt_packet: `{prompt_display}`
- review_packet: `{review_display}`

## 研究问题

{payload.get("research_problem_zh")}

## 方法概括

{payload.get("method_summary_zh")}

## 实验与数据

{payload.get("experiment_summary_zh")}

{payload.get("dataset_or_scene_zh")}

{payload.get("metrics_zh")}

## 主要发现草稿

{payload.get("main_findings_zh")}

## 局限与不确定点

{payload.get("limitations_zh")}

{chr(10).join(f"- {item}" for item in payload.get("uncertain_points_zh", []))}

## 主题相关性草稿

{payload.get("topic_relevance_zh")}

## AI 初审

- score: {review["agent_review_score_10"]}/10
- grade: `{review["agent_review_grade"]}`
- rationale: {review["agent_review_rationale_zh"]}
- recommended_human_action_zh: {review["recommended_human_action_zh"]}

## 人工决策

- `human_decision`: 待填写
- `human_confirmed`: false
"""
    return (
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + body
    )


def render_review_packet(
    *,
    config: ProjectConfig,
    paper_id: str,
    note_file: Path,
    source: SelectedSource,
    extraction: ExtractionResult,
    prompt_packet_path: Path,
    payload: dict[str, Any],
    review: dict[str, Any],
) -> str:
    metadata_rel = _display_path(config, _metadata_path(config, paper_id))
    note_rel = _display_path(config, note_file)
    source_rel = _relative(config, source.source_record) or "manual_override"
    extraction_rel = _display_path(config, extraction.cache_path)
    prompt_rel = _display_path(config, prompt_packet_path)
    visual_target = _display_path(config, config.assets_root / paper_id / "visual_evidence")
    warnings = review.get("agent_review_warnings") or []
    claims = payload.get("source_grounded_claims") or []
    uncertain = payload.get("uncertain_points_zh") or []
    assets = payload.get("asset_suggestions") or []

    return f"""# 阅读草稿监管包: {paper_id}

## 当前建议

- `note_status`: `{review["note_status"]}`
- `agent_review_score_10`: {review["agent_review_score_10"]}/10
- `agent_review_grade`: `{review["agent_review_grade"]}`
- `recommended_human_action_zh`: {review["recommended_human_action_zh"]}

## 相关链接

- metadata: [{metadata_rel}](../../{metadata_rel})
- reading note: [{note_rel}](../../{note_rel})
- source ledger: `{source_rel}`
- source file: `{source.display_path}`
- extraction cache: `{extraction_rel}`
- prompt packet: `{prompt_rel}`
- Phase 8.1 visual target: `{visual_target}`

## AI 初审说明

{review["agent_review_rationale_zh"]}

## 分数拆解

| item | score |
|---|---:|
{chr(10).join(f"| `{key}` | {value} |" for key, value in review["score_breakdown"].items())}

## 需要人工重点查看

{chr(10).join(f"- {item}" for item in warnings) if warnings else "- 暂无自动警告；仍需人工抽查来源页码和短引用。"}

## 来源支撑 claims

{chr(10).join(f"- 第 {claim.get('evidence_page')} 页 `{claim.get('source_chunk_id')}`: {claim.get('claim_zh')}" for claim in claims if isinstance(claim, dict)) or "- 暂无。"}

## 不确定点

{chr(10).join(f"- {item}" for item in uncertain) if uncertain else "- 暂无。"}

## 候选视觉证据

{chr(10).join(f"- page={item.get('page')} `{item.get('figure_or_table')}`: {item.get('reason_zh')}" for item in assets if isinstance(item, dict)) or "- 暂无候选图表建议。"}

## 边界提醒

本文件只是 staging/review 材料，不是 formal record。它不能替代 `approved`，也不能绕过 `rsa formal apply-note --human-confirmed`。
"""


def _check_existing_note(config: ProjectConfig, paper_id: str, overwrite_draft: bool) -> None:
    path = note_path(config, paper_id)
    if not path.exists():
        return
    if not overwrite_draft:
        raise DraftError(f"阅读笔记已存在，默认不覆盖: {_display_path(config, path)}")
    note = load_reading_note(config, paper_id)
    status = note.frontmatter.get("note_status")
    if status != "draft":
        raise DraftError("只有 note_status: draft 的阅读笔记可以通过 --overwrite-draft 覆盖。")
    if note.frontmatter.get("human_confirmed") is True:
        raise DraftError("已有人工确认痕迹，不能自动覆盖。")


def draft_reading_note(
    config: ProjectConfig,
    paper_id: str,
    *,
    source_file: str | None = None,
    overwrite_draft: bool = False,
    retry: bool = False,
) -> DraftResult:
    _ensure_metadata(config, paper_id)
    _check_existing_note(config, paper_id, overwrite_draft=overwrite_draft)
    source = select_reading_source(config, paper_id, source_file=source_file)
    extraction = extract_source_text(config, paper_id, source)
    prompt_packet_path = write_prompt_packet(
        config,
        paper_id=paper_id,
        source=source,
        extraction=extraction,
        status="created",
    )

    try:
        payload = call_llm_draft(config, _ensure_metadata(config, paper_id), extraction)
    except DraftError as exc:
        write_prompt_packet(
            config,
            paper_id=paper_id,
            source=source,
            extraction=extraction,
            status="blocked",
            diagnostics_zh=str(exc),
        )
        record_pdf_status(
            config,
            paper_id=paper_id,
            pdf_status="blocked",
            local_path=source.display_path,
            source_or_authorization=source.authorization,
            notes=f"LLM 自动阅读草稿失败: {exc}",
        )
        raise

    schema_errors = validate_llm_payload(payload)
    if schema_errors and retry:
        payload = call_llm_draft(config, _ensure_metadata(config, paper_id), extraction)
        schema_errors = validate_llm_payload(payload)
    if schema_errors:
        message = "模型输出未通过 reading draft schema: " + "; ".join(schema_errors)
        write_prompt_packet(
            config,
            paper_id=paper_id,
            source=source,
            extraction=extraction,
            status="blocked",
            diagnostics_zh=message,
        )
        raise DraftError(message)

    review_packet_path = config.notes_root / f"{paper_id}_review_packet.md"
    review = review_payload(
        config=config,
        payload=payload,
        source=source,
        extraction=extraction,
        prompt_packet_path=prompt_packet_path,
    )
    note_file = note_path(config, paper_id)
    note_file.parent.mkdir(parents=True, exist_ok=True)
    note_file.write_text(
        render_draft_note(
            config=config,
            paper_id=paper_id,
            metadata=_ensure_metadata(config, paper_id),
            source=source,
            extraction=extraction,
            prompt_packet_path=prompt_packet_path,
            review_packet_path=review_packet_path,
            payload=payload,
            review=review,
        ),
        encoding="utf-8",
    )
    review_packet_path.write_text(
        render_review_packet(
            config=config,
            paper_id=paper_id,
            note_file=note_file,
            source=source,
            extraction=extraction,
            prompt_packet_path=prompt_packet_path,
            payload=payload,
            review=review,
        ),
        encoding="utf-8",
    )
    return DraftResult(
        note_path=note_file,
        review_packet_path=review_packet_path,
        extraction_cache_path=extraction.cache_path,
        prompt_packet_path=prompt_packet_path,
        note_status=str(review["note_status"]),
        agent_review_score_10=int(review["agent_review_score_10"]),
    )
