from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from .campaign import (
    CampaignError,
    create_campaign,
    import_campaign_items,
)
from .config import ProjectConfig


DISCOVERY_ID_PATTERN = re.compile(r"^DR(?P<number>\d{3})$")
QUERY_ID_PATTERN = re.compile(r"^DQ(?P<number>\d{3})$")
CANDIDATE_ID_PATTERN = re.compile(r"^DC(?P<number>\d{3})$")
DISCOVERY_STATUSES = {
    "ready",
    "not_run",
    "running",
    "completed",
    "partial",
    "blocked",
    "needs_review",
}
PROVIDERS = {"openalex", "crossref", "offline"}
FUTURE_INTERFACES = [
    "llm_query_generation",
    "iterative_query_refinement",
    "provider_plugins",
    "scholarly_metadata_enrichment",
    "discovery_eval",
    "web_review_ui",
    "manual_override_history",
]
STOPWORDS = {
    "about",
    "above",
    "after",
    "analysis",
    "based",
    "between",
    "could",
    "from",
    "have",
    "into",
    "paper",
    "papers",
    "plan",
    "research",
    "study",
    "system",
    "that",
    "the",
    "their",
    "this",
    "using",
    "with",
}


JsonFetcher = Callable[[str], dict[str, Any]]


class DiscoveryError(ValueError):
    """Raised when research-plan discovery cannot safely continue."""


@dataclass(frozen=True)
class DiscoveryProfileResult:
    discovery_id: str
    profile_path: Path
    query_bundle_path: Path
    query_count: int


@dataclass(frozen=True)
class DiscoverySearchResult:
    discovery_id: str
    results_path: Path
    provider: str
    status: str
    candidate_count: int
    campaign_id: str | None = None
    campaign_path: Path | None = None


@dataclass(frozen=True)
class DiscoveryStatus:
    discovery_id: str
    profile_path: Path
    query_bundle_path: Path
    results_path: Path
    status: str
    query_count: int
    candidate_count: int
    campaign_id: str | None


def discovery_profile_path(config: ProjectConfig, discovery_id: str) -> Path:
    _validate_discovery_id(discovery_id)
    return config.discovery_root / f"{discovery_id}_profile.yaml"


def discovery_query_bundle_path(config: ProjectConfig, discovery_id: str) -> Path:
    _validate_discovery_id(discovery_id)
    return config.discovery_root / f"{discovery_id}_queries.yaml"


def discovery_results_path(config: ProjectConfig, discovery_id: str) -> Path:
    _validate_discovery_id(discovery_id)
    return config.discovery_root / f"{discovery_id}_results.yaml"


def discovery_report_path(config: ProjectConfig, discovery_id: str) -> Path:
    _validate_discovery_id(discovery_id)
    return config.discovery_root / f"{discovery_id}_report.md"


def discovery_campaign_import_path(config: ProjectConfig, discovery_id: str) -> Path:
    _validate_discovery_id(discovery_id)
    return config.discovery_root / f"{discovery_id}_campaign_import.yaml"


def next_discovery_id(config: ProjectConfig) -> str:
    highest = 0
    if config.discovery_root.exists():
        for path in config.discovery_root.glob("DR*_profile.yaml"):
            match = DISCOVERY_ID_PATTERN.match(path.name.split("_", 1)[0])
            if match:
                highest = max(highest, int(match.group("number")))
    return f"DR{highest + 1:03d}"


def create_discovery_profile(
    config: ProjectConfig,
    *,
    plan_file: str | None = None,
    objective: str | None = None,
    topic_profile: str | None = None,
    max_queries: int | None = None,
) -> DiscoveryProfileResult:
    text, source = _read_plan_input(config, plan_file=plan_file, objective=objective)
    query_limit = int(max_queries or config.discovery_default_max_queries)
    if query_limit <= 0:
        raise DiscoveryError("max_queries 必须为正整数。")

    discovery_id = next_discovery_id(config)
    profile_path = discovery_profile_path(config, discovery_id)
    query_path = discovery_query_bundle_path(config, discovery_id)
    profile_terms = _topic_profile_terms(config, topic_profile)
    research_questions = _extract_research_questions(text, profile_terms)
    keywords = _extract_keywords(text, profile_terms)
    query_bundle = _build_query_bundle(
        discovery_id,
        research_questions=research_questions,
        keywords=keywords,
        fallback_text=text,
        max_queries=query_limit,
    )
    if not query_bundle:
        raise DiscoveryError("无法从科研计划中生成检索式，请补充研究目标、关键词或问题描述。")

    profile_data = {
        "discovery_id": discovery_id,
        "status": "ready",
        "status_zh": "已从科研计划生成可审计的发现档案和检索式，尚未写入正式 metadata。",
        "plan_source": source,
        "topic_profile": topic_profile,
        "research_questions": research_questions,
        "keywords": keywords,
        "query_bundle": {
            "file": _rel(config, query_path),
            "query_count": len(query_bundle),
        },
        "query_bundle_file": _rel(config, query_path),
        "automation_mode": config.discovery_automation_mode,
        "formal_write_allowed": False,
        "repair_hint_zh": "如检索式过宽或过窄，可以修改科研计划、topic profile 或 --max-queries 后重新运行。",
        "field_explanations_zh": _field_explanations(),
        "future_interfaces": FUTURE_INTERFACES,
        "created_at": _now(),
        "updated_at": _now(),
    }
    query_data = {
        "discovery_id": discovery_id,
        "status": "ready",
        "queries": query_bundle,
        "provider_policy_zh": (
            "只允许使用合法、可审计的学术检索或开放元数据来源；不得配置未授权镜像、"
            "绕过访问控制或自动写入正式科研记录。"
        ),
        "created_at": _now(),
        "updated_at": _now(),
    }
    _write_yaml(profile_path, profile_data)
    _write_yaml(query_path, query_data)
    return DiscoveryProfileResult(
        discovery_id=discovery_id,
        profile_path=profile_path,
        query_bundle_path=query_path,
        query_count=len(query_bundle),
    )


def search_discovery(
    config: ProjectConfig,
    discovery_id: str,
    *,
    provider: str | None = None,
    max_results: int | None = None,
    fetcher: JsonFetcher | None = None,
) -> DiscoverySearchResult:
    provider_id = str(provider or config.discovery_default_provider)
    _validate_provider(config, provider_id)
    profile = _read_yaml_mapping(discovery_profile_path(config, discovery_id))
    query_data = _read_yaml_mapping(discovery_query_bundle_path(config, discovery_id))
    queries = query_data.get("queries")
    if not isinstance(queries, list) or not queries:
        raise DiscoveryError("query bundle 缺少 queries，无法进行发现检索。")

    results_limit = int(max_results or config.discovery_default_max_results)
    if results_limit <= 0:
        raise DiscoveryError("max_results 必须为正整数。")

    results_path = discovery_results_path(config, discovery_id)
    if provider_id == "offline":
        data = _results_skeleton(
            discovery_id,
            provider_id,
            status="not_run",
            reason_zh="provider=offline 仅生成检索式，不访问网络，也不创建候选。",
        )
        _write_yaml(results_path, data)
        _write_report(config, discovery_id)
        return DiscoverySearchResult(discovery_id, results_path, provider_id, "not_run", 0)

    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    client = fetcher or _fetch_json
    for query in queries:
        if len(candidates) >= results_limit:
            break
        query_id = str(query.get("query_id") or "")
        query_text = str(query.get("query") or "").strip()
        if not query_text:
            continue
        try:
            provider_items = _provider_search(provider_id, query_text, results_limit, client)
        except DiscoveryError as exc:
            errors.append({"query_id": query_id, "query": query_text, "error_zh": str(exc)})
            continue
        for item in provider_items:
            key = _candidate_key(item)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                _candidate_record(
                    item,
                    candidate_id=f"DC{len(candidates) + 1:03d}",
                    discovery_id=discovery_id,
                    provider=provider_id,
                    query_id=query_id,
                    query=query_text,
                    topic_profile=profile.get("topic_profile"),
                )
            )
            if len(candidates) >= results_limit:
                break

    if candidates and errors:
        status = "partial"
        reason = "部分检索式执行失败，已保留成功返回的候选，失败原因写入 search_errors。"
    elif candidates:
        status = "completed"
        reason = "合法 provider 检索完成，候选已进入 staging 结果文件，尚未写入正式 metadata。"
    else:
        status = "blocked"
        reason = "未获得可用候选；不会生成伪候选，也不会写入 campaign 或正式 metadata。"

    data = _results_skeleton(discovery_id, provider_id, status=status, reason_zh=reason)
    data["candidates"] = candidates
    data["search_errors"] = errors
    data["updated_at"] = _now()
    _write_yaml(results_path, data)
    _write_report(config, discovery_id)
    return DiscoverySearchResult(
        discovery_id=discovery_id,
        results_path=results_path,
        provider=provider_id,
        status=status,
        candidate_count=len(candidates),
    )


def export_discovery_to_campaign(
    config: ProjectConfig,
    discovery_id: str,
    *,
    campaign_id: str | None = None,
    name_zh: str | None = None,
    objective_zh: str | None = None,
    created_by: str | None = None,
) -> DiscoverySearchResult:
    profile = _read_yaml_mapping(discovery_profile_path(config, discovery_id))
    results_path = discovery_results_path(config, discovery_id)
    results = _read_yaml_mapping(results_path)
    candidates = results.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise DiscoveryError("发现结果没有候选，不能创建或导入 campaign。")

    target_campaign_id = campaign_id
    campaign_path: Path | None = None
    if target_campaign_id is None:
        created = create_campaign(
            config,
            name_zh=name_zh or f"科研计划发现 {discovery_id}",
            objective_zh=objective_zh or _default_objective_zh(profile),
            topic_profile=_clean(profile.get("topic_profile")),
            created_by=created_by,
        )
        target_campaign_id = created.campaign_id
        campaign_path = created.path

    import_path = discovery_campaign_import_path(config, discovery_id)
    import_rows = [_campaign_import_row(candidate) for candidate in candidates]
    _write_yaml(
        import_path,
        {
            "discovery_id": discovery_id,
            "target_campaign_id": target_campaign_id,
            "items": import_rows,
            "created_at": _now(),
            "updated_at": _now(),
        },
    )
    imported = import_campaign_items(config, target_campaign_id, source_file=str(import_path))
    results["campaign_export"] = {
        "campaign_id": imported.campaign_id,
        "campaign_path": _rel(config, imported.path),
        "campaign_import_file": _rel(config, import_path),
        "imported_count": imported.imported_count,
        "duplicate_count": imported.duplicate_count,
        "linked_count": imported.linked_count,
        "blocked_count": imported.blocked_count,
        "formal_write_allowed": False,
        "reason_zh": "候选已进入 campaign staging 队列；正式 metadata 写入仍需人工确认 gate。",
        "updated_at": _now(),
    }
    results["updated_at"] = _now()
    _write_yaml(results_path, results)
    _write_report(config, discovery_id)
    return DiscoverySearchResult(
        discovery_id=discovery_id,
        results_path=results_path,
        provider=str(results.get("source_provider") or ""),
        status=str(results.get("status") or ""),
        candidate_count=len(candidates),
        campaign_id=imported.campaign_id,
        campaign_path=campaign_path or imported.path,
    )


def run_discovery(
    config: ProjectConfig,
    *,
    plan_file: str | None = None,
    objective: str | None = None,
    topic_profile: str | None = None,
    provider: str | None = None,
    max_queries: int | None = None,
    max_results: int | None = None,
    no_search: bool = False,
    no_campaign: bool = False,
    campaign_id: str | None = None,
    name_zh: str | None = None,
    objective_zh: str | None = None,
    created_by: str | None = None,
    fetcher: JsonFetcher | None = None,
) -> DiscoverySearchResult:
    profile = create_discovery_profile(
        config,
        plan_file=plan_file,
        objective=objective,
        topic_profile=topic_profile,
        max_queries=max_queries,
    )
    if no_search:
        results = _results_skeleton(
            profile.discovery_id,
            "offline",
            status="not_run",
            reason_zh="用户选择 --no-search，仅生成发现档案和检索式。",
        )
        _write_yaml(discovery_results_path(config, profile.discovery_id), results)
        _write_report(config, profile.discovery_id)
        return DiscoverySearchResult(
            profile.discovery_id,
            discovery_results_path(config, profile.discovery_id),
            "offline",
            "not_run",
            0,
        )

    search_result = search_discovery(
        config,
        profile.discovery_id,
        provider=provider,
        max_results=max_results,
        fetcher=fetcher,
    )
    if no_campaign or search_result.candidate_count == 0:
        return search_result
    return export_discovery_to_campaign(
        config,
        profile.discovery_id,
        campaign_id=campaign_id,
        name_zh=name_zh,
        objective_zh=objective_zh,
        created_by=created_by,
    )


def validate_discovery(config: ProjectConfig, discovery_id: str) -> list[str]:
    errors: list[str] = []
    try:
        profile_path = discovery_profile_path(config, discovery_id)
        query_path = discovery_query_bundle_path(config, discovery_id)
    except DiscoveryError as exc:
        return [str(exc)]
    if not profile_path.exists():
        errors.append(f"discovery profile 不存在: {profile_path}")
    else:
        profile = _read_yaml_mapping(profile_path)
        if profile.get("discovery_id") != discovery_id:
            errors.append("profile.discovery_id 必须与文件名一致。")
        if profile.get("status") not in DISCOVERY_STATUSES:
            errors.append(f"profile.status 不支持: {profile.get('status')}")
        if profile.get("formal_write_allowed") is not False:
            errors.append("discovery profile 不允许 formal_write_allowed=true。")
        if not isinstance(profile.get("field_explanations_zh"), dict):
            errors.append("profile 必须包含 field_explanations_zh，方便中文用户理解字段。")
    if not query_path.exists():
        errors.append(f"query bundle 不存在: {query_path}")
    else:
        query_data = _read_yaml_mapping(query_path)
        queries = query_data.get("queries")
        if not isinstance(queries, list) or not queries:
            errors.append("query bundle 必须包含非空 queries。")
        else:
            for index, query in enumerate(queries, start=1):
                if not isinstance(query, dict):
                    errors.append(f"queries 第 {index} 项必须是 mapping。")
                    continue
                if not QUERY_ID_PATTERN.match(str(query.get("query_id") or "")):
                    errors.append(f"queries 第 {index} 项 query_id 必须匹配 DQ###。")
                if not _clean(query.get("query")):
                    errors.append(f"queries 第 {index} 项缺少 query。")
                if not _clean(query.get("reason_zh")):
                    errors.append(f"queries 第 {index} 项缺少 reason_zh。")
    results_path = discovery_results_path(config, discovery_id)
    if results_path.exists():
        results = _read_yaml_mapping(results_path)
        if results.get("discovery_id") != discovery_id:
            errors.append("results.discovery_id 必须与文件名一致。")
        if results.get("status") not in DISCOVERY_STATUSES:
            errors.append(f"results.status 不支持: {results.get('status')}")
        candidates = results.get("candidates", [])
        if not isinstance(candidates, list):
            errors.append("results.candidates 必须是 list。")
        else:
            seen: set[str] = set()
            for index, candidate in enumerate(candidates, start=1):
                if not isinstance(candidate, dict):
                    errors.append(f"candidates 第 {index} 项必须是 mapping。")
                    continue
                candidate_id = str(candidate.get("candidate_id") or "")
                if not CANDIDATE_ID_PATTERN.match(candidate_id):
                    errors.append(f"candidates 第 {index} 项 candidate_id 必须匹配 DC###。")
                elif candidate_id in seen:
                    errors.append(f"candidate_id 重复: {candidate_id}")
                seen.add(candidate_id)
                if not _clean(candidate.get("title")) and not _clean(candidate.get("doi")):
                    errors.append(f"candidates 第 {index} 项必须至少包含 title 或 doi。")
                if not _clean(candidate.get("reason_zh")):
                    errors.append(f"candidates 第 {index} 项缺少 reason_zh。")
                if candidate.get("formal_write_allowed") is not False:
                    errors.append(f"candidates 第 {index} 项不允许 formal_write_allowed=true。")
    return errors


def discovery_status(config: ProjectConfig, discovery_id: str) -> DiscoveryStatus:
    profile_path = discovery_profile_path(config, discovery_id)
    query_path = discovery_query_bundle_path(config, discovery_id)
    results_path = discovery_results_path(config, discovery_id)
    status = "missing"
    query_count = 0
    candidate_count = 0
    campaign_id = None
    if query_path.exists():
        query_data = _read_yaml_mapping(query_path)
        queries = query_data.get("queries") if isinstance(query_data.get("queries"), list) else []
        query_count = len(queries)
    if results_path.exists():
        results = _read_yaml_mapping(results_path)
        status = str(results.get("status") or "missing")
        candidates = results.get("candidates") if isinstance(results.get("candidates"), list) else []
        candidate_count = len(candidates)
        export = results.get("campaign_export")
        if isinstance(export, dict):
            campaign_id = _clean(export.get("campaign_id"))
    elif profile_path.exists():
        profile = _read_yaml_mapping(profile_path)
        status = str(profile.get("status") or "ready")
    return DiscoveryStatus(
        discovery_id=discovery_id,
        profile_path=profile_path,
        query_bundle_path=query_path,
        results_path=results_path,
        status=status,
        query_count=query_count,
        candidate_count=candidate_count,
        campaign_id=campaign_id,
    )


def _validate_discovery_id(discovery_id: str) -> None:
    if not DISCOVERY_ID_PATTERN.match(str(discovery_id or "")):
        raise DiscoveryError(f"discovery_id 必须匹配 DR###: {discovery_id}")


def _validate_provider(config: ProjectConfig, provider: str) -> None:
    if provider not in PROVIDERS:
        raise DiscoveryError(f"不支持的 discovery provider: {provider}")
    if provider not in config.discovery_allowed_providers:
        raise DiscoveryError(f"当前配置未允许 discovery provider: {provider}")


def _read_plan_input(
    config: ProjectConfig,
    *,
    plan_file: str | None,
    objective: str | None,
) -> tuple[str, dict[str, Any]]:
    chunks: list[str] = []
    source: dict[str, Any] = {"source_type": "mixed" if plan_file and objective else "objective"}
    if plan_file:
        path = _resolve_project_path(config, plan_file)
        if not path.is_file():
            raise DiscoveryError(f"科研计划文件不存在或不是普通文件: {path}")
        if path.suffix.lower() not in {".md", ".txt"}:
            raise DiscoveryError("v1 只接受 .md 或 .txt 科研计划文件；.docx/BibTeX/Zotero 已预留为后续接口。")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise DiscoveryError("科研计划文件为空，无法生成检索式。")
        chunks.append(text)
        source.update(
            {
                "source_type": "file" if not objective else "mixed",
                "path": _rel(config, path),
                "format": path.suffix.lower().lstrip("."),
            }
        )
    if objective:
        clean_objective = objective.strip()
        if not clean_objective:
            raise DiscoveryError("objective 不能为空。")
        chunks.append(clean_objective)
        source["objective_zh"] = clean_objective
    if not chunks:
        raise DiscoveryError("必须提供 --plan-file 或 --objective，不能凭空发现文献。")
    text = "\n\n".join(chunks).strip()
    source["excerpt_zh"] = text[:500]
    return text, source


def _topic_profile_terms(config: ProjectConfig, topic_profile: str | None) -> list[str]:
    if not topic_profile:
        return []
    path = _resolve_topic_profile_path(config, topic_profile)
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    terms: list[str] = []
    for key in ("topic_name", "core_keywords", "priority_questions", "preferred_sources"):
        _flatten_terms(data.get(key), terms)
    return terms


def _resolve_topic_profile_path(config: ProjectConfig, value: str) -> Path:
    path = Path(value)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return _resolve_project_path(config, value)
    return config.topic_profiles_root / f"{value}.yaml"


def _flatten_terms(value: Any, output: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        if value.strip():
            output.append(value.strip())
        return
    if isinstance(value, dict):
        for item in value.values():
            _flatten_terms(item, output)
        return
    if isinstance(value, list):
        for item in value:
            _flatten_terms(item, output)


def _extract_research_questions(text: str, profile_terms: list[str]) -> list[str]:
    questions: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" -\t")
        if not line:
            continue
        if "?" in line or "？" in line or re.match(r"^(q\d+|问题|研究问题)[:：.\s]", line, flags=re.I):
            questions.append(line[:240])
    for term in profile_terms:
        if "?" in term or "？" in term:
            questions.append(term[:240])
    return _unique(questions)[:8]


def _extract_keywords(text: str, profile_terms: list[str]) -> list[str]:
    tokens: list[str] = []
    combined = text + "\n" + "\n".join(profile_terms)
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", combined):
        normalized = token.lower().strip("-_")
        if normalized and normalized not in STOPWORDS:
            tokens.append(normalized)
    for term in profile_terms:
        clean = re.sub(r"\s+", " ", str(term).strip())
        if clean and len(clean) <= 80:
            tokens.append(clean)
    return _unique(tokens)[:24]


def _build_query_bundle(
    discovery_id: str,
    *,
    research_questions: list[str],
    keywords: list[str],
    fallback_text: str,
    max_queries: int,
) -> list[dict[str, Any]]:
    raw_queries: list[tuple[str, str]] = []
    keyword_query = " ".join(keywords[:6])
    if keyword_query:
        raw_queries.append((keyword_query, "从科研计划和 topic profile 中抽取的核心关键词组合。"))
    for question in research_questions:
        question_terms = _extract_keywords(question, [])[:6]
        query = " ".join(question_terms) or _compact_free_text(question)
        raw_queries.append((query, "围绕科研计划中的研究问题生成的检索式。"))
    if not raw_queries:
        raw_queries.append((_compact_free_text(fallback_text), "科研计划缺少英文关键词时生成的保守全文检索式。"))

    queries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query, reason in raw_queries:
        compact = re.sub(r"\s+", " ", query).strip()
        if not compact or compact in seen:
            continue
        seen.add(compact)
        queries.append(
            {
                "query_id": f"DQ{len(queries) + 1:03d}",
                "discovery_id": discovery_id,
                "query": compact[:180],
                "query_text": compact[:180],
                "query_terms": _extract_keywords(compact, [])[:10],
                "language_hint": "mixed",
                "evidence_level": "plan_text_and_profile" if keywords else "plan_text_only",
                "rationale_zh": reason,
                "reason_zh": reason,
                "confidence": "medium" if keywords else "low",
                "status": "ready",
            }
        )
        if len(queries) >= max_queries:
            break
    return queries


def _provider_search(
    provider: str,
    query: str,
    max_results: int,
    fetcher: JsonFetcher,
) -> list[dict[str, Any]]:
    if provider == "openalex":
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"search": query, "per-page": max_results}
        )
        data = fetcher(url)
        return [_openalex_item(item) for item in data.get("results", []) if isinstance(item, dict)]
    if provider == "crossref":
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
            {"query": query, "rows": max_results}
        )
        data = fetcher(url)
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        return [_crossref_item(item) for item in message.get("items", []) if isinstance(item, dict)]
    raise DiscoveryError(f"不支持的 discovery provider: {provider}")


def _openalex_item(item: dict[str, Any]) -> dict[str, Any]:
    authorships = item.get("authorships") if isinstance(item.get("authorships"), list) else []
    first_author = None
    if authorships:
        author = authorships[0].get("author") if isinstance(authorships[0], dict) else {}
        if isinstance(author, dict):
            first_author = _clean(author.get("display_name"))
    primary_location = item.get("primary_location") if isinstance(item.get("primary_location"), dict) else {}
    return {
        "title": _clean(item.get("title") or item.get("display_name")),
        "doi": _normalize_doi(item.get("doi")),
        "official_url": _clean(primary_location.get("landing_page_url") or item.get("id")),
        "year": _clean(item.get("publication_year")),
        "first_author": first_author,
        "source_url": _clean(item.get("id")),
        "abstract_snippet": _abstract_from_inverted_index(item.get("abstract_inverted_index")),
    }


def _crossref_item(item: dict[str, Any]) -> dict[str, Any]:
    titles = item.get("title") if isinstance(item.get("title"), list) else []
    authors = item.get("author") if isinstance(item.get("author"), list) else []
    first_author = None
    if authors and isinstance(authors[0], dict):
        first_author = _clean(authors[0].get("family") or authors[0].get("name"))
    year = _crossref_year(item)
    return {
        "title": _clean(titles[0] if titles else None),
        "doi": _normalize_doi(item.get("DOI")),
        "official_url": _clean(item.get("URL")),
        "year": _clean(year),
        "first_author": first_author,
        "source_url": _clean(item.get("URL")),
        "abstract_snippet": _clean(item.get("abstract")),
    }


def _crossref_year(item: dict[str, Any]) -> str | None:
    for key in ("published-print", "published-online", "issued", "created"):
        value = item.get(key)
        if not isinstance(value, dict):
            continue
        parts = value.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            return str(parts[0][0])
    return None


def _candidate_record(
    item: dict[str, Any],
    *,
    candidate_id: str,
    discovery_id: str,
    provider: str,
    query_id: str,
    query: str,
    topic_profile: Any,
) -> dict[str, Any]:
    title = _clean(item.get("title"))
    doi = _normalize_doi(item.get("doi"))
    return {
        "candidate_id": candidate_id,
        "discovery_id": discovery_id,
        "source_provider": provider,
        "source_query_id": query_id,
        "source_query": query,
        "title": title,
        "doi": doi,
        "official_url": _clean(item.get("official_url")),
        "year": _clean(item.get("year")),
        "first_author": _clean(item.get("first_author")),
        "topic_profile": _clean(topic_profile),
        "source_url": _clean(item.get("source_url")),
        "abstract_snippet": _clean(item.get("abstract_snippet")),
        "evidence_level": "provider_metadata",
        "status": "candidate",
        "formal_write_allowed": False,
        "reason_zh": "由科研计划驱动的合法 provider 检索生成，仅作为候选进入 staging/campaign。",
        "created_at": _now(),
    }


def _campaign_import_row(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": candidate.get("title"),
        "doi": candidate.get("doi"),
        "official_url": candidate.get("official_url") or candidate.get("source_url"),
        "year": candidate.get("year"),
        "first_author": candidate.get("first_author"),
        "topic_profile": candidate.get("topic_profile"),
        "priority_question": candidate.get("source_query"),
        "candidate_key": f"{candidate.get('discovery_id')}:{candidate.get('candidate_id')}",
        "source_candidate_id": candidate.get("candidate_id"),
        "discovery_id": candidate.get("discovery_id"),
        "source_provider": candidate.get("source_provider"),
        "source_query_id": candidate.get("source_query_id"),
        "evidence_level": candidate.get("evidence_level"),
        "note_zh": candidate.get("reason_zh"),
    }


def _results_skeleton(
    discovery_id: str,
    provider: str,
    *,
    status: str,
    reason_zh: str,
) -> dict[str, Any]:
    return {
        "discovery_id": discovery_id,
        "search_run_id": f"{discovery_id}-S001",
        "source_provider": provider,
        "status": status,
        "reason_zh": reason_zh,
        "formal_write_allowed": False,
        "repair_hint_zh": "检查 provider 是否可用、科研计划是否足够具体；必要时先使用 --no-search 生成检索式人工审阅。",
        "candidates": [],
        "search_errors": [],
        "future_interfaces": {
            name: {"status": "not_enabled", "reason_zh": "预留接口，当前 v1 不启用。"}
            for name in FUTURE_INTERFACES
        },
        "created_at": _now(),
        "updated_at": _now(),
    }


def _write_report(config: ProjectConfig, discovery_id: str) -> Path:
    profile = _read_yaml_mapping(discovery_profile_path(config, discovery_id))
    results_path = discovery_results_path(config, discovery_id)
    results = _read_yaml_mapping(results_path) if results_path.exists() else {}
    queries_path = discovery_query_bundle_path(config, discovery_id)
    query_data = _read_yaml_mapping(queries_path) if queries_path.exists() else {}
    queries = query_data.get("queries") if isinstance(query_data.get("queries"), list) else []
    candidates = results.get("candidates") if isinstance(results.get("candidates"), list) else []
    errors = results.get("search_errors") if isinstance(results.get("search_errors"), list) else []
    campaign = results.get("campaign_export") if isinstance(results.get("campaign_export"), dict) else {}
    lines = [
        f"# Discovery Report: {discovery_id}",
        "",
        "## 中文摘要",
        "",
        f"- 状态: `{results.get('status') or profile.get('status')}`",
        f"- 检索来源: `{results.get('source_provider') or 'not_run'}`",
        f"- 检索式数量: {len(queries)}",
        f"- 候选数量: {len(candidates)}",
        f"- campaign: `{campaign.get('campaign_id') or '未导入'}`",
        "",
        "本报告只记录科研计划驱动的发现结果，所有候选都属于 staging/campaign 输入，不能直接写入正式 `metadata/P###.yaml`。",
        "",
        "## 检索式",
        "",
    ]
    for query in queries:
        lines.append(f"- `{query.get('query_id')}`: {query.get('query_text') or query.get('query')}")
        lines.append(f"  - 中文理由: {query.get('reason_zh')}")
        lines.append(f"  - evidence_level: `{query.get('evidence_level')}`")
    if not queries:
        lines.append("- 暂无检索式。")
    lines.extend(["", "## 候选文献", ""])
    for candidate in candidates:
        lines.append(
            f"- `{candidate.get('candidate_id')}` {candidate.get('title') or candidate.get('doi') or '未命名候选'}"
        )
        lines.append(f"  - provider: `{candidate.get('source_provider')}`")
        lines.append(f"  - reason_zh: {candidate.get('reason_zh')}")
    if not candidates:
        lines.append("- 暂无候选；系统不会创建伪候选。")
    if errors:
        lines.extend(["", "## 失败与修复", ""])
        for error in errors:
            lines.append(f"- `{error.get('query_id')}`: {error.get('error_zh')}")
        lines.append("- 修复建议: 检查网络/provider 配置，或先使用 `--no-search` 生成检索式进行人工审阅。")
    lines.extend(
        [
            "",
            "## 预留接口",
            "",
            "- `llm_query_generation`: 后续可接入 LLM 生成更好的检索式。",
            "- `iterative_query_refinement`: 后续可根据初次结果自动调整查询。",
            "- `provider_plugins`: 后续可加入更多合法 provider。",
            "- `discovery_eval`: 后续可评估发现质量和召回。",
            "- `web_review_ui`: 后续可在 Web 页面审阅候选。",
            "- `manual_override_history`: 后续可记录人工修改查询或候选的历史。",
            "",
        ]
    )
    report_path = discovery_report_path(config, discovery_id)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "rsa-research-agent/0.1 (+local research harness)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
    except OSError as exc:
        raise DiscoveryError(f"provider 请求失败: {exc}") from exc
    try:
        loaded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DiscoveryError(f"provider 返回的 JSON 无效: {exc}") from exc
    if not isinstance(loaded, dict):
        raise DiscoveryError("provider 返回值不是 JSON object。")
    return loaded


def _candidate_key(item: dict[str, Any]) -> str:
    doi = _normalize_doi(item.get("doi"))
    if doi:
        return "doi:" + doi
    title = re.sub(r"\s+", " ", str(item.get("title") or "").lower()).strip()
    year = str(item.get("year") or "")
    return "title:" + title + "|" + year


def _abstract_from_inverted_index(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    positions: list[tuple[int, str]] = []
    for word, indexes in value.items():
        if not isinstance(indexes, list):
            continue
        for index in indexes:
            if isinstance(index, int):
                positions.append((index, str(word)))
    if not positions:
        return None
    text = " ".join(word for _, word in sorted(positions)[:80])
    return text[:500]


def _default_objective_zh(profile: dict[str, Any]) -> str:
    questions = profile.get("research_questions")
    if isinstance(questions, list) and questions:
        return f"根据科研计划自动发现候选文献，优先覆盖：{questions[0]}"
    source = profile.get("plan_source") if isinstance(profile.get("plan_source"), dict) else {}
    excerpt = _clean(source.get("excerpt_zh"))
    if excerpt:
        return "根据科研计划自动发现候选文献：" + excerpt[:80]
    return "根据科研计划自动发现候选文献，供后续 campaign、阅读和人工监管使用。"


def _field_explanations() -> dict[str, str]:
    return {
        "discovery_id": "一次科研计划驱动发现任务的稳定编号。",
        "plan_source": "科研计划来源，可以是本地 .md/.txt 文件或用户提供的目标文本。",
        "research_questions": "从科研计划中抽取的研究问题候选，供检索式生成参考。",
        "keywords": "从科研计划和 topic profile 中抽取的关键词候选。",
        "query_bundle": "用于合法 provider 检索的查询集合。",
        "source_provider": "检索来源，例如 openalex 或 crossref。",
        "candidate_id": "发现候选编号；不等于正式 paper_id。",
        "evidence_level": "候选依据范围，帮助判断可信度。",
        "formal_write_allowed": "是否允许直接写入正式记录；发现阶段固定为 false。",
    }


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DiscoveryError(f"YAML 文件不存在: {path}")
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise DiscoveryError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise DiscoveryError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _resolve_project_path(config: ProjectConfig, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.root / path


def _rel(config: ProjectConfig, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(config.root.resolve()))
    except ValueError:
        return str(path)


def _compact_free_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:120]


def _normalize_doi(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    match = re.search(r"10\.\d{4,9}/\S+", text, flags=re.IGNORECASE)
    if match:
        return match.group(0).rstrip(".,;").lower()
    return text.lower() if text.lower().startswith("10.") else None


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = re.sub(r"\s+", " ", str(value).strip())
        key = clean.lower()
        if not clean or key in seen:
            continue
        seen.add(key)
        output.append(clean)
    return output


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
