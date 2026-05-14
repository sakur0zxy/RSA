from __future__ import annotations

import hashlib
import re
import shutil
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN, load_metadata_record, validate_metadata_record
from .notes import record_pdf_status


MATCH_BASIS = {
    "doi",
    "official_url",
    "arxiv_id",
    "title_year_first_author",
    "title_only",
}
AUTHORIZATION_MODES = {
    "open_access",
    "direct_access",
    "user_authorized_access",
    "institutional_subscription",
    "personal_subscription",
    "provided",
    "local",
    "unknown",
    "blocked",
}
ACCESS_MODES = AUTHORIZATION_MODES
CANDIDATE_STATUSES = {
    "candidate",
    "approved_for_download",
    "downloaded",
    "blocked",
    "failed",
    "duplicate",
    "skipped",
}
RESULT_TYPES = {"pdf", "publisher_page", "database_record", "repository_record", "web_page"}
PROVIDER_REQUIRED_FIELDS = {
    "provider_id",
    "enabled",
    "name_zh",
    "provider_type",
    "base_url",
    "query_mode",
    "query_template",
    "allowed_domains",
    "allowed_result_types",
    "access_mode",
    "requires_login",
    "user_access_confirmed",
    "authorization_policy",
    "usage_restriction_zh",
    "notes_zh",
}
SUBSCRIPTION_ACCESS_MODES = {"institutional_subscription", "personal_subscription"}
VERSION_PRIORITY = [
    "publisher_version",
    "accepted_manuscript",
    "institutional_subscription",
    "repository_copy",
    "arxiv_preprint",
    "preprint",
    "unknown",
]
FORBIDDEN_PROVIDER_PATTERNS = [
    "sci-hub",
    "scihub",
    "libgen",
    "library genesis",
    "z-library",
    "zlibrary",
]


class AcquisitionError(ValueError):
    """Raised when source discovery or acquisition cannot safely proceed."""


@dataclass(frozen=True)
class CandidateStatus:
    path: Path
    total_count: int
    approved_count: int
    downloaded_count: int
    duplicate_count: int
    blocked_count: int
    failed_count: int


@dataclass(frozen=True)
class FindResult:
    path: Path
    candidates_found: int
    approved_count: int
    downloaded_count: int
    duplicate_count: int
    blocked_count: int
    failed_count: int


@dataclass(frozen=True)
class DownloadResult:
    candidate_id: str
    status: str
    source_id: str | None
    local_path: Path | None
    sha256: str | None
    reason_zh: str


def candidate_record_path(config: ProjectConfig, paper_id: str) -> Path:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise AcquisitionError(f"paper_id 必须匹配 P###: {paper_id}")
    return config.source_candidates_root / f"{paper_id}.yaml"


def _metadata_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.metadata_root / f"{paper_id}.yaml"


def _ensure_formal_paper(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise AcquisitionError(f"paper_id 必须匹配 P###: {paper_id}")
    path = _metadata_path(config, paper_id)
    errors = validate_metadata_record(path)
    if errors:
        raise AcquisitionError(f"{paper_id} metadata 无效或不存在: " + "; ".join(errors))
    return load_metadata_record(path)


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


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned or "source"


def _load_mapping(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise AcquisitionError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise AcquisitionError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_mapping(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id(entries: list[Any], *, key: str, prefix: str) -> str:
    highest = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(?P<number>\d{{3}})$")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        match = pattern.match(str(entry.get(key, "")))
        if match:
            highest = max(highest, int(match.group("number")))
    return f"{prefix}{highest + 1:03d}"


def _source_record_path(config: ProjectConfig, paper_id: str) -> Path:
    return config.sources_root / f"{paper_id}.yaml"


def _load_source_record(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    return _load_mapping(
        _source_record_path(config, paper_id),
        default={"paper_id": paper_id, "sources": []},
    )


def _write_source_record(config: ProjectConfig, paper_id: str, record: dict[str, Any]) -> None:
    record["paper_id"] = paper_id
    _write_mapping(_source_record_path(config, paper_id), record)


def load_candidate_record(config: ProjectConfig, paper_id: str) -> dict[str, Any]:
    _ensure_formal_paper(config, paper_id)
    return _load_mapping(
        candidate_record_path(config, paper_id),
        default={
            "paper_id": paper_id,
            "generated_at": None,
            "automation_mode": config.source_discovery_automation_mode,
            "default_auto_download": config.source_discovery_default_auto_download,
            "candidates": [],
        },
    )


def write_candidate_record(config: ProjectConfig, paper_id: str, record: dict[str, Any]) -> Path:
    _ensure_formal_paper(config, paper_id)
    if record.get("paper_id") not in (None, paper_id):
        raise AcquisitionError(f"candidate record paper_id 与文件名不一致: {record.get('paper_id')}")
    candidates = record.get("candidates")
    if not isinstance(candidates, list):
        raise AcquisitionError("candidates 必须是 YAML list")
    record["paper_id"] = paper_id
    path = candidate_record_path(config, paper_id)
    _write_mapping(path, record)
    return path


def _domain_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower()


def _contains_forbidden_provider_text(provider: dict[str, Any]) -> bool:
    text = yaml.safe_dump(provider, allow_unicode=True).lower()
    return any(pattern in text for pattern in FORBIDDEN_PROVIDER_PATTERNS)


def validate_custom_providers(config: ProjectConfig) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    providers = config.custom_source_providers
    for index, provider in enumerate(providers, start=1):
        if not isinstance(provider, dict):
            errors.append(f"custom_providers 第 {index} 项必须是 mapping")
            continue
        missing = sorted(field for field in PROVIDER_REQUIRED_FIELDS if field not in provider)
        if missing:
            errors.append(f"custom_providers 第 {index} 项缺少字段: {', '.join(missing)}")
            continue
        provider_id = str(provider.get("provider_id", "")).strip()
        if not provider_id:
            errors.append(f"custom_providers 第 {index} 项 provider_id 不能为空")
        elif provider_id in seen:
            errors.append(f"custom_providers 第 {index} 项 provider_id 重复: {provider_id}")
        else:
            seen.add(provider_id)
        if provider.get("query_mode") != "url_template":
            errors.append(f"{provider_id} query_mode 目前只支持 url_template")
        if not isinstance(provider.get("allowed_domains"), list) or not provider.get("allowed_domains"):
            errors.append(f"{provider_id} allowed_domains 必须是非空 list")
        if (
            not isinstance(provider.get("allowed_result_types"), list)
            or not provider.get("allowed_result_types")
        ):
            errors.append(f"{provider_id} allowed_result_types 必须是非空 list")
        if provider.get("access_mode") not in ACCESS_MODES:
            errors.append(f"{provider_id} access_mode 不支持: {provider.get('access_mode')}")
        if _is_blank(provider.get("usage_restriction_zh")):
            errors.append(f"{provider_id} 必须填写 usage_restriction_zh 中文使用限制")
        if _contains_forbidden_provider_text(provider):
            errors.append(f"{provider_id} 不允许配置 Sci-Hub、盗版镜像或绕过访问控制的来源")
    return errors


def _title_words(title: str) -> str:
    return "+".join(word for word in re.split(r"\s+", title.strip()) if word)


def _first_author(metadata: dict[str, Any]) -> str:
    authors = metadata.get("authors")
    if isinstance(authors, list) and authors:
        return str(authors[0]).split(",")[0].split()[-1]
    return ""


def _detect_arxiv_id(metadata: dict[str, Any]) -> str | None:
    values = [str(metadata.get("doi") or ""), str(metadata.get("official_url") or "")]
    pattern = re.compile(r"(?:arxiv[:/]|arxiv\.org/(?:abs|pdf)/)(?P<id>\d{4}\.\d{4,5})(?:v\d+)?", re.I)
    for value in values:
        match = pattern.search(value)
        if match:
            return match.group("id")
    return None


def _result_type_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    return "publisher_page"


def _candidate(
    *,
    candidate_id: str,
    provider_id: str,
    provider_name_zh: str,
    source_url: str,
    result_type: str,
    match_basis: str,
    match_evidence: dict[str, Any],
    authorization_mode: str,
    access_mode: str,
    authorization_basis_zh: str,
    usage_restriction_zh: str,
    version_label: str,
    approved_for_download: bool,
    reason_zh: str,
) -> dict[str, Any]:
    status = "approved_for_download" if approved_for_download else "candidate"
    if authorization_mode == "blocked":
        status = "blocked"
    return {
        "candidate_id": candidate_id,
        "provider_id": provider_id,
        "provider_name_zh": provider_name_zh,
        "source_url": source_url,
        "result_type": result_type,
        "match_basis": match_basis,
        "match_evidence": match_evidence,
        "authorization_mode": authorization_mode,
        "access_mode": access_mode,
        "authorization_basis_zh": authorization_basis_zh,
        "usage_restriction_zh": usage_restriction_zh,
        "version_label": version_label,
        "approved_for_download": bool(approved_for_download),
        "status": status,
        "reason_zh": reason_zh,
        "local_path": None,
        "sha256": None,
        "downloaded_source_id": None,
        "duplicate_of": None,
        "created_at": _today(),
    }


def _can_auto_download(provider: dict[str, Any], *, match_basis: str, result_type: str) -> tuple[bool, str]:
    access_mode = str(provider.get("access_mode", "unknown"))
    if match_basis == "title_only":
        return False, "title_only 只能进入候选审查，不能自动下载。"
    if result_type != "pdf":
        return False, "候选不是直接 PDF，暂不自动下载。"
    if access_mode in {"unknown", "blocked"}:
        return False, "授权模式不明确，已阻止自动下载。"
    if access_mode in SUBSCRIPTION_ACCESS_MODES and provider.get("user_access_confirmed") is not True:
        return False, "订阅来源需要 user_access_confirmed: true 后才允许自动下载。"
    return True, "匹配证据和授权记录满足自动下载规则。"


def _render_url_template(template: str, metadata: dict[str, Any], paper_id: str) -> str:
    return template.format(
        doi=str(metadata.get("doi") or ""),
        title=_title_words(str(metadata.get("title") or "")),
        year=str(metadata.get("year") or ""),
        first_author=_first_author(metadata),
        paper_id=paper_id,
    )


def _custom_provider_candidates(
    config: ProjectConfig,
    metadata: dict[str, Any],
    paper_id: str,
    existing: list[dict[str, Any]],
    provider_filter: str | None,
) -> list[dict[str, Any]]:
    errors = validate_custom_providers(config)
    if errors:
        raise AcquisitionError("; ".join(errors))
    candidates: list[dict[str, Any]] = []
    for provider in config.custom_source_providers:
        if provider.get("enabled") is not True:
            continue
        if provider_filter and provider.get("provider_id") != provider_filter:
            continue
        source_url = _render_url_template(str(provider["query_template"]), metadata, paper_id)
        result_types = [str(item) for item in provider.get("allowed_result_types", [])]
        result_type = "pdf" if "pdf" in result_types else result_types[0]
        basis = "doi" if metadata.get("doi") else "title_year_first_author"
        if not metadata.get("doi") and not metadata.get("year"):
            basis = "title_only"
        approved, reason = _can_auto_download(provider, match_basis=basis, result_type=result_type)
        source_domain_allowed = _domain_from_url(source_url) in [
            str(domain).lower() for domain in provider.get("allowed_domains", [])
        ]
        if not source_domain_allowed:
            approved = False
            reason = "候选 URL 域名不在 allowed_domains 中，已阻止自动下载。"
        provider_id = str(provider["provider_id"])
        candidates.append(
            _candidate(
                candidate_id=_next_id(existing + candidates, key="candidate_id", prefix="SC"),
                provider_id=provider_id,
                provider_name_zh=str(provider["name_zh"]),
                source_url=source_url,
                result_type=result_type,
                match_basis=basis,
                match_evidence={
                    "doi_match": bool(metadata.get("doi")),
                    "title_match_score": 1.0 if metadata.get("title") else 0.0,
                    "year_match": bool(metadata.get("year")),
                    "author_match": bool(_first_author(metadata)),
                    "source_domain_allowed": source_domain_allowed,
                },
                authorization_mode=str(provider.get("authorization_policy") or provider.get("access_mode")),
                access_mode=str(provider["access_mode"]),
                authorization_basis_zh=str(provider.get("notes_zh") or "用户配置的自定义来源。"),
                usage_restriction_zh=str(provider["usage_restriction_zh"]),
                version_label="institutional_subscription"
                if provider.get("access_mode") in SUBSCRIPTION_ACCESS_MODES
                else "repository_copy",
                approved_for_download=approved,
                reason_zh=reason,
            )
        )
    return candidates


def discover_source_candidates(
    config: ProjectConfig,
    paper_id: str,
    *,
    provider_filter: str | None = None,
    max_results: int | None = None,
) -> Path:
    metadata = _ensure_formal_paper(config, paper_id)
    candidates: list[dict[str, Any]] = []
    doi = str(metadata.get("doi") or "").strip()
    official_url = str(metadata.get("official_url") or "").strip()
    usage = "仅供个人科研阅读，不得公开分发 PDF。"

    if doi and provider_filter in (None, "doi"):
        candidates.append(
            _candidate(
                candidate_id=_next_id(candidates, key="candidate_id", prefix="SC"),
                provider_id="doi",
                provider_name_zh="DOI 官方解析",
                source_url=f"https://doi.org/{doi}",
                result_type="publisher_page",
                match_basis="doi",
                match_evidence={
                    "doi_match": True,
                    "title_match_score": None,
                    "year_match": bool(metadata.get("year")),
                    "author_match": bool(_first_author(metadata)),
                    "source_domain_allowed": True,
                },
                authorization_mode="unknown",
                access_mode="unknown",
                authorization_basis_zh="DOI 只能证明论文身份，不能单独证明 PDF 授权。",
                usage_restriction_zh=usage,
                version_label="unknown",
                approved_for_download=False,
                reason_zh="DOI 候选需要进一步解析到授权 PDF 后才能下载。",
            )
        )

    arxiv_id = _detect_arxiv_id(metadata)
    if arxiv_id and provider_filter in (None, "arxiv"):
        candidates.append(
            _candidate(
                candidate_id=_next_id(candidates, key="candidate_id", prefix="SC"),
                provider_id="arxiv",
                provider_name_zh="arXiv 预印本",
                source_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                result_type="pdf",
                match_basis="arxiv_id",
                match_evidence={
                    "doi_match": False,
                    "title_match_score": 1.0,
                    "year_match": bool(metadata.get("year")),
                    "author_match": bool(_first_author(metadata)),
                    "source_domain_allowed": True,
                },
                authorization_mode="open_access",
                access_mode="open_access",
                authorization_basis_zh="arXiv 预印本为开放访问来源。",
                usage_restriction_zh=usage,
                version_label="arxiv_preprint",
                approved_for_download=True,
                reason_zh="arXiv ID 命中，允许自动下载开放访问 PDF。",
            )
        )

    if official_url and provider_filter in (None, "official_url"):
        result_type = _result_type_from_url(official_url)
        approved = result_type == "pdf"
        candidates.append(
            _candidate(
                candidate_id=_next_id(candidates, key="candidate_id", prefix="SC"),
                provider_id="official_url",
                provider_name_zh="正式 metadata official_url",
                source_url=official_url,
                result_type=result_type,
                match_basis="official_url",
                match_evidence={
                    "doi_match": bool(doi),
                    "title_match_score": 1.0,
                    "year_match": bool(metadata.get("year")),
                    "author_match": bool(_first_author(metadata)),
                    "source_domain_allowed": True,
                },
                authorization_mode="direct_access" if approved else "unknown",
                access_mode="direct_access" if approved else "unknown",
                authorization_basis_zh="metadata official_url 指向直接 PDF。"
                if approved
                else "metadata official_url 不是直接 PDF，需人工或 provider 进一步确认。",
                usage_restriction_zh=usage,
                version_label="publisher_version" if approved else "unknown",
                approved_for_download=approved,
                reason_zh="official_url 是直接 PDF，允许自动下载。"
                if approved
                else "official_url 不是直接 PDF，暂不自动下载。",
            )
        )

    candidates.extend(_custom_provider_candidates(config, metadata, paper_id, candidates, provider_filter))
    if not candidates:
        title = str(metadata.get("title") or "")
        candidates.append(
            _candidate(
                candidate_id="SC001",
                provider_id="title_search",
                provider_name_zh="标题检索占位",
                source_url="",
                result_type="database_record",
                match_basis="title_only",
                match_evidence={
                    "doi_match": False,
                    "title_match_score": 1.0 if title else 0.0,
                    "year_match": False,
                    "author_match": False,
                    "source_domain_allowed": False,
                },
                authorization_mode="blocked",
                access_mode="blocked",
                authorization_basis_zh="只有标题信息，不能证明来源身份或下载授权。",
                usage_restriction_zh=usage,
                version_label="unknown",
                approved_for_download=False,
                reason_zh="title_only 只能生成候选，不得触发自动下载。",
            )
        )
    if max_results is not None:
        candidates = candidates[: max(0, max_results)]

    record = {
        "paper_id": paper_id,
        "generated_at": _now(),
        "automation_mode": config.source_discovery_automation_mode,
        "default_auto_download": config.source_discovery_default_auto_download,
        "candidates": candidates,
    }
    return write_candidate_record(config, paper_id, record)


def validate_candidate_record(config: ProjectConfig, paper_id: str) -> list[str]:
    try:
        _ensure_formal_paper(config, paper_id)
        path = candidate_record_path(config, paper_id)
        if not path.exists():
            return [f"source candidate record 不存在: {path}"]
        data = _load_mapping(path, default={})
    except AcquisitionError as exc:
        return [str(exc)]

    errors: list[str] = []
    if data.get("paper_id") != paper_id:
        errors.append(f"paper_id 必须与文件名一致: expected {paper_id}, got {data.get('paper_id')}")
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        return errors + ["candidates 必须是 YAML list"]
    seen: set[str] = set()
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            errors.append(f"candidates 第 {index} 项必须是 mapping")
            continue
        candidate_id = candidate.get("candidate_id")
        if not re.match(r"^SC\d{3}$", str(candidate_id or "")):
            errors.append(f"candidates 第 {index} 项 candidate_id 必须匹配 SC###")
        elif str(candidate_id) in seen:
            errors.append(f"candidates 第 {index} 项 candidate_id 重复: {candidate_id}")
        else:
            seen.add(str(candidate_id))
        for field in ["provider_id", "authorization_basis_zh", "usage_restriction_zh", "reason_zh"]:
            if _is_blank(candidate.get(field)):
                errors.append(f"candidates 第 {index} 项缺少 {field}")
        if candidate.get("status") not in CANDIDATE_STATUSES:
            errors.append(f"candidates 第 {index} 项 status 不支持: {candidate.get('status')}")
        if candidate.get("match_basis") not in MATCH_BASIS:
            errors.append(f"candidates 第 {index} 项 match_basis 不支持: {candidate.get('match_basis')}")
        if candidate.get("authorization_mode") not in AUTHORIZATION_MODES:
            errors.append(
                f"candidates 第 {index} 项 authorization_mode 不支持: {candidate.get('authorization_mode')}"
            )
        if candidate.get("access_mode") not in ACCESS_MODES:
            errors.append(f"candidates 第 {index} 项 access_mode 不支持: {candidate.get('access_mode')}")
        if not isinstance(candidate.get("match_evidence"), dict):
            errors.append(f"candidates 第 {index} 项 match_evidence 必须是 mapping")
        if candidate.get("match_basis") == "title_only" and candidate.get("approved_for_download"):
            errors.append("title_only 候选不得 approved_for_download")
        local_path = candidate.get("local_path")
        if not _is_blank(local_path) and not _resolve_project_path(config, str(local_path)).is_file():
            errors.append(f"candidates 第 {index} 项 local_path 不存在: {local_path}")
        if candidate.get("status") == "downloaded" and _is_blank(candidate.get("downloaded_source_id")):
            errors.append(f"candidates 第 {index} 项 downloaded 状态缺少 downloaded_source_id")
    return errors


def candidate_status(config: ProjectConfig, paper_id: str) -> CandidateStatus:
    path = candidate_record_path(config, paper_id)
    if not path.exists():
        return CandidateStatus(path=path, total_count=0, approved_count=0, downloaded_count=0, duplicate_count=0, blocked_count=0, failed_count=0)
    data = _load_mapping(path, default={"paper_id": paper_id, "candidates": []})
    candidates = data.get("candidates") if isinstance(data.get("candidates"), list) else []
    return CandidateStatus(
        path=path,
        total_count=len(candidates),
        approved_count=sum(1 for item in candidates if isinstance(item, dict) and item.get("approved_for_download")),
        downloaded_count=sum(1 for item in candidates if isinstance(item, dict) and item.get("status") == "downloaded"),
        duplicate_count=sum(1 for item in candidates if isinstance(item, dict) and item.get("status") == "duplicate"),
        blocked_count=sum(1 for item in candidates if isinstance(item, dict) and item.get("status") == "blocked"),
        failed_count=sum(1 for item in candidates if isinstance(item, dict) and item.get("status") == "failed"),
    )


def _download_to_tmp(config: ProjectConfig, source_url: str, tmp_path: Path) -> None:
    parsed = urllib.parse.urlparse(source_url)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    if parsed.scheme == "file":
        shutil.copy2(Path(urllib.request.url2pathname(parsed.path)), tmp_path)
        return
    resolved = _resolve_project_path(config, source_url)
    if parsed.scheme == "" and resolved.exists():
        shutil.copy2(resolved, tmp_path)
        return
    with urllib.request.urlopen(source_url, timeout=30) as response:
        with tmp_path.open("wb") as target:
            shutil.copyfileobj(response, target)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_pdf(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise AcquisitionError("下载结果为空，未写入 source ledger")
    with path.open("rb") as handle:
        header = handle.read(5)
    if header != b"%PDF-":
        raise AcquisitionError("下载结果不是 PDF 文件，已阻止写入 source ledger")


def _existing_source_by_hash(sources: list[Any], sha256: str) -> dict[str, Any] | None:
    for source in sources:
        if isinstance(source, dict) and source.get("sha256") == sha256:
            return source
    return None


def _version_rank(version_label: str | None) -> int:
    value = version_label if version_label in VERSION_PRIORITY else "unknown"
    return VERSION_PRIORITY.index(str(value))


def _select_primary(sources: list[Any]) -> None:
    pdf_sources = [source for source in sources if isinstance(source, dict) and source.get("source_type") == "pdf"]
    if not pdf_sources:
        return
    primary = min(pdf_sources, key=lambda source: _version_rank(source.get("version_label")))
    for source in pdf_sources:
        is_primary = source is primary
        source["is_primary"] = is_primary
        source["primary_reason_zh"] = (
            f"按版本优先级选择 {source.get('version_label', 'unknown')} 作为主版本。"
            if is_primary
            else "已有更高优先级 PDF 版本作为主版本。"
        )


def _update_candidate(
    config: ProjectConfig,
    paper_id: str,
    candidate_id: str,
    updates: dict[str, Any],
) -> None:
    record = load_candidate_record(config, paper_id)
    candidates = record.get("candidates")
    if not isinstance(candidates, list):
        raise AcquisitionError("candidates 必须是 YAML list")
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            candidate.update(updates)
            write_candidate_record(config, paper_id, record)
            return
    raise AcquisitionError(f"candidate 不存在: {candidate_id}")


def _next_source_id(sources: list[Any]) -> str:
    return _next_id(sources, key="source_id", prefix="S")


def _append_source_from_tmp(
    config: ProjectConfig,
    paper_id: str,
    candidate: dict[str, Any],
    tmp_path: Path,
    sha256: str,
) -> tuple[str, Path]:
    source_record = _load_source_record(config, paper_id)
    if source_record.get("paper_id") not in (None, paper_id):
        raise AcquisitionError(f"source record paper_id 与文件名不一致: {source_record.get('paper_id')}")
    sources = source_record.get("sources")
    if not isinstance(sources, list):
        raise AcquisitionError("sources 必须是 YAML list")

    source_id = _next_source_id(sources)
    provider_id = _safe_filename(str(candidate.get("provider_id") or "provider"))
    version_label = _safe_filename(str(candidate.get("version_label") or "unknown"))
    target = config.pdfs_root / paper_id / f"{source_id}_{provider_id}_{version_label}.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.replace(target)
    entry = {
        "source_id": source_id,
        "source_type": "pdf",
        "authorization": candidate.get("authorization_mode"),
        "authorization_mode": candidate.get("authorization_mode"),
        "access_mode": candidate.get("access_mode"),
        "authorization_basis_zh": candidate.get("authorization_basis_zh"),
        "usage_restriction_zh": candidate.get("usage_restriction_zh"),
        "license_note": candidate.get("usage_restriction_zh"),
        "source_url": candidate.get("source_url"),
        "original_path": candidate.get("source_url"),
        "local_path": _display_path(config, target),
        "sha256": sha256,
        "version_label": candidate.get("version_label") or "unknown",
        "is_primary": False,
        "primary_reason_zh": None,
        "status": "available",
        "added_by": "rsa source acquisition",
        "added_at": _today(),
    }
    sources.append(entry)
    _select_primary(sources)
    source_record["sources"] = sources
    _write_source_record(config, paper_id, source_record)
    return source_id, target


def _load_candidate(config: ProjectConfig, paper_id: str, candidate_id: str) -> dict[str, Any]:
    record = load_candidate_record(config, paper_id)
    candidates = record.get("candidates")
    if not isinstance(candidates, list):
        raise AcquisitionError("candidates 必须是 YAML list")
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            return candidate
    raise AcquisitionError(f"candidate 不存在: {candidate_id}")


def _preflight_download(candidate: dict[str, Any]) -> None:
    if candidate.get("match_basis") == "title_only":
        raise AcquisitionError("title_only 候选不能自动下载")
    if candidate.get("result_type") != "pdf":
        raise AcquisitionError("候选不是直接 PDF，不能下载")
    if candidate.get("authorization_mode") in {"unknown", "blocked", None}:
        raise AcquisitionError("authorization_mode 不明确或已阻止，不能下载")
    if candidate.get("access_mode") in {"unknown", "blocked", None}:
        raise AcquisitionError("access_mode 不明确或已阻止，不能下载")
    for field in ["authorization_basis_zh", "usage_restriction_zh"]:
        if _is_blank(candidate.get(field)):
            raise AcquisitionError(f"缺少 {field}，不能下载")


def download_candidate(config: ProjectConfig, paper_id: str, candidate_id: str) -> DownloadResult:
    _ensure_formal_paper(config, paper_id)
    candidate = _load_candidate(config, paper_id, candidate_id)
    tmp_path = config.pdfs_root / paper_id / f".{candidate_id}.pdf.tmp"
    try:
        _preflight_download(candidate)
        _download_to_tmp(config, str(candidate.get("source_url") or ""), tmp_path)
        _verify_pdf(tmp_path)
        sha256 = _sha256(tmp_path)
        source_record = _load_source_record(config, paper_id)
        sources = source_record.get("sources")
        if not isinstance(sources, list):
            raise AcquisitionError("sources 必须是 YAML list")
        duplicate = _existing_source_by_hash(sources, sha256)
        if duplicate:
            tmp_path.unlink(missing_ok=True)
            reason = f"内容 hash 与已有来源 {duplicate.get('source_id')} 相同，未重复保存 PDF。"
            _update_candidate(
                config,
                paper_id,
                candidate_id,
                {
                    "status": "duplicate",
                    "approved_for_download": False,
                    "sha256": sha256,
                    "duplicate_of": duplicate.get("source_id"),
                    "reason_zh": reason,
                },
            )
            record_pdf_status(
                config,
                paper_id=paper_id,
                pdf_status="duplicate",
                local_path=str(duplicate.get("local_path") or ""),
                source_or_authorization=str(candidate.get("authorization_mode")),
                notes=reason,
            )
            return DownloadResult(candidate_id, "duplicate", None, None, sha256, reason)
        source_id, local_path = _append_source_from_tmp(config, paper_id, candidate, tmp_path, sha256)
        reason = "已通过授权审查并保存 PDF。"
        display = _display_path(config, local_path)
        _update_candidate(
            config,
            paper_id,
            candidate_id,
            {
                "status": "downloaded",
                "approved_for_download": False,
                "local_path": display,
                "sha256": sha256,
                "downloaded_source_id": source_id,
                "reason_zh": reason,
            },
        )
        record_pdf_status(
            config,
            paper_id=paper_id,
            pdf_status="available",
            local_path=display,
            source_or_authorization=str(candidate.get("authorization_mode")),
            notes=reason,
        )
        return DownloadResult(candidate_id, "downloaded", source_id, local_path, sha256, reason)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        reason = str(exc)
        _update_candidate(
            config,
            paper_id,
            candidate_id,
            {"status": "failed", "approved_for_download": False, "reason_zh": reason},
        )
        record_pdf_status(
            config,
            paper_id=paper_id,
            pdf_status="failed",
            local_path=str(candidate.get("source_url") or ""),
            source_or_authorization=str(candidate.get("authorization_mode") or "unknown"),
            notes=reason,
        )
        raise AcquisitionError(reason) from exc


def download_best_candidate(config: ProjectConfig, paper_id: str) -> DownloadResult:
    record = load_candidate_record(config, paper_id)
    candidates = record.get("candidates")
    if not isinstance(candidates, list):
        raise AcquisitionError("candidates 必须是 YAML list")
    for candidate in candidates:
        if (
            isinstance(candidate, dict)
            and candidate.get("approved_for_download") is True
            and candidate.get("status") == "approved_for_download"
        ):
            return download_candidate(config, paper_id, str(candidate["candidate_id"]))
    raise AcquisitionError("没有可自动下载的候选来源")


def download_direct_url(
    config: ProjectConfig,
    paper_id: str,
    *,
    url: str,
    authorization_mode: str,
    access_mode: str,
    usage_restriction_zh: str,
    authorization_basis_zh: str | None = None,
    provider_id: str = "manual_url",
    version_label: str = "publisher_version",
) -> DownloadResult:
    _ensure_formal_paper(config, paper_id)
    if authorization_mode not in AUTHORIZATION_MODES or authorization_mode in {"unknown", "blocked"}:
        raise AcquisitionError("手动 URL 下载必须提供明确且允许的 authorization_mode")
    if access_mode not in ACCESS_MODES or access_mode in {"unknown", "blocked"}:
        raise AcquisitionError("手动 URL 下载必须提供明确且允许的 access_mode")
    if _is_blank(usage_restriction_zh):
        raise AcquisitionError("手动 URL 下载必须提供 --usage-restriction-zh 中文使用限制")
    record = load_candidate_record(config, paper_id)
    candidates = record.get("candidates")
    if not isinstance(candidates, list):
        raise AcquisitionError("candidates 必须是 YAML list")
    candidate_id = _next_id(candidates, key="candidate_id", prefix="SC")
    candidate = _candidate(
        candidate_id=candidate_id,
        provider_id=provider_id,
        provider_name_zh="手动授权 URL",
        source_url=url,
        result_type="pdf",
        match_basis="official_url",
        match_evidence={
            "doi_match": False,
            "title_match_score": None,
            "year_match": None,
            "author_match": None,
            "source_domain_allowed": True,
        },
        authorization_mode=authorization_mode,
        access_mode=access_mode,
        authorization_basis_zh=authorization_basis_zh or "用户显式提供授权下载 URL。",
        usage_restriction_zh=usage_restriction_zh,
        version_label=version_label,
        approved_for_download=True,
        reason_zh="用户显式提供授权 URL，允许下载。",
    )
    candidates.append(candidate)
    record["generated_at"] = record.get("generated_at") or _now()
    record["automation_mode"] = config.source_discovery_automation_mode
    record["default_auto_download"] = config.source_discovery_default_auto_download
    write_candidate_record(config, paper_id, record)
    return download_candidate(config, paper_id, candidate_id)


def find_sources(
    config: ProjectConfig,
    paper_id: str,
    *,
    auto_download: bool | None = None,
    provider_filter: str | None = None,
    max_results: int | None = None,
) -> FindResult:
    path = discover_source_candidates(
        config,
        paper_id,
        provider_filter=provider_filter,
        max_results=max_results,
    )
    should_download = (
        config.source_discovery_default_auto_download
        if auto_download is None
        else auto_download
    )
    if should_download:
        while True:
            try:
                download_best_candidate(config, paper_id)
            except AcquisitionError as exc:
                if "没有可自动下载的候选来源" in str(exc):
                    break
                continue
    status = candidate_status(config, paper_id)
    return FindResult(
        path=path,
        candidates_found=status.total_count,
        approved_count=status.approved_count,
        downloaded_count=status.downloaded_count,
        duplicate_count=status.duplicate_count,
        blocked_count=status.blocked_count,
        failed_count=status.failed_count,
    )
