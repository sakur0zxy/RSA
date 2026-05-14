from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import yaml

from .config import ProjectConfig


BROWSER_SESSION_REQUIRED_FIELDS = {
    "login_url",
    "session_storage",
    "session_required",
}
BROWSER_PROVIDER_TYPE = "browser_session"
FORBIDDEN_SESSION_PATTERNS = [
    "sci-hub",
    "scihub",
    "libgen",
    "library genesis",
    "z-library",
    "zlibrary",
]


class BrowserSessionError(ValueError):
    """Raised when browser session configuration or state is unsafe."""


@dataclass(frozen=True)
class BrowserSessionLoginResult:
    provider_id: str
    session_path: Path
    metadata_path: Path
    cookie_count: int
    origin_count: int


@dataclass(frozen=True)
class BrowserSessionStatus:
    provider_id: str
    provider_name_zh: str
    exists: bool
    session_path: Path
    metadata_path: Path
    cookie_count: int
    origin_count: int
    updated_at: str | None
    allowed_domains: list[str]
    login_url: str
    reason_zh: str


LoginRunner = Callable[[dict[str, Any], Path], None]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _provider_text(provider: dict[str, Any]) -> str:
    return yaml.safe_dump(provider, allow_unicode=True, sort_keys=False).lower()


def _normalize_domain(value: str) -> str:
    raw = str(value).strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        parsed = urlparse(raw)
        raw = parsed.netloc
    return raw.strip().lstrip(".").split("/")[0]


def normalize_allowed_domains(provider: dict[str, Any]) -> list[str]:
    values = provider.get("allowed_domains")
    if not isinstance(values, list):
        return []
    return [domain for domain in (_normalize_domain(str(item)) for item in values) if domain]


def domain_matches(host: str, allowed_domain: str) -> bool:
    host = _normalize_domain(host)
    allowed = _normalize_domain(allowed_domain)
    return host == allowed or host.endswith(f".{allowed}")


def provider_allows_url(provider: dict[str, Any], url: str) -> bool:
    host = urlparse(url).netloc
    if not host:
        return True
    return any(domain_matches(host, allowed) for allowed in normalize_allowed_domains(provider))


def _load_session_state(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BrowserSessionError(f"browser session JSON 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise BrowserSessionError(f"browser session 必须是 JSON object: {path}")
    return loaded


def _state_counts(path: Path) -> tuple[int, int]:
    state = _load_session_state(path)
    cookies = state.get("cookies", [])
    origins = state.get("origins", [])
    cookie_count = len(cookies) if isinstance(cookies, list) else 0
    origin_count = len(origins) if isinstance(origins, list) else 0
    return cookie_count, origin_count


def _metadata_path_for_session(path: Path, provider_id: str) -> Path:
    return path.with_name(f"{provider_id}.session.yaml")


def resolve_session_storage(config: ProjectConfig, provider: dict[str, Any]) -> Path:
    provider_id = str(provider.get("provider_id") or "").strip()
    if not provider_id:
        raise BrowserSessionError("browser_session provider 缺少 provider_id")
    storage = str(provider.get("session_storage") or f"{provider_id}.storage_state.json").strip()
    if not storage:
        raise BrowserSessionError(f"{provider_id} session_storage 不能为空")
    storage_path = Path(storage)
    if storage_path.is_absolute():
        raise BrowserSessionError(f"{provider_id} session_storage 必须是 .rsa/sessions/ 下的相对路径")

    sessions_root = config.sessions_root.resolve()
    if storage_path.parts[:2] == (".rsa", "sessions"):
        resolved = (config.root / storage_path).resolve()
    else:
        resolved = (sessions_root / storage_path).resolve()
    if not resolved.is_relative_to(sessions_root):
        raise BrowserSessionError(f"{provider_id} session_storage 必须位于 .rsa/sessions/ 下")
    if resolved.suffix.lower() != ".json":
        raise BrowserSessionError(f"{provider_id} session_storage 必须使用 .json 文件")
    return resolved


def validate_browser_session_provider_fields(
    provider: dict[str, Any],
    *,
    config: ProjectConfig | None = None,
) -> list[str]:
    errors: list[str] = []
    provider_id = str(provider.get("provider_id") or "<unknown>")
    missing = sorted(field for field in BROWSER_SESSION_REQUIRED_FIELDS if field not in provider)
    if missing:
        errors.append(f"{provider_id} browser_session 缺少字段: {', '.join(missing)}")
    if provider.get("session_required") is not True:
        errors.append(f"{provider_id} browser_session 必须设置 session_required: true")
    login_url = str(provider.get("login_url") or "").strip()
    parsed_login = urlparse(login_url)
    if parsed_login.scheme not in {"http", "https"} or not parsed_login.netloc:
        errors.append(f"{provider_id} login_url 必须是 http(s) 登录页面")
    allowed_domains = normalize_allowed_domains(provider)
    if not allowed_domains:
        errors.append(f"{provider_id} allowed_domains 必须是非空 list")
    elif login_url and not provider_allows_url(provider, login_url):
        errors.append(f"{provider_id} login_url 域名必须包含在 allowed_domains 中")
    if any(pattern in _provider_text(provider) for pattern in FORBIDDEN_SESSION_PATTERNS):
        errors.append(f"{provider_id} 不允许配置 Sci-Hub、盗版镜像或绕过访问控制的来源")
    if config is not None and "session_storage" in provider:
        try:
            resolve_session_storage(config, provider)
        except BrowserSessionError as exc:
            errors.append(str(exc))
    return errors


def get_browser_session_provider(config: ProjectConfig, provider_id: str) -> dict[str, Any]:
    for provider in config.custom_source_providers:
        if str(provider.get("provider_id")) == provider_id:
            if provider.get("provider_type") != BROWSER_PROVIDER_TYPE:
                raise BrowserSessionError(
                    f"{provider_id} 不是 browser_session provider，不能用于浏览器登录。"
                )
            errors = validate_browser_session_provider_fields(provider, config=config)
            if errors:
                raise BrowserSessionError("; ".join(errors))
            return dict(provider)
    raise BrowserSessionError(f"未找到 browser_session provider: {provider_id}")


def _playwright_login_runner(
    provider: dict[str, Any],
    session_path: Path,
    *,
    headless: bool = False,
    wait_seconds: int | None = None,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BrowserSessionError(
            "浏览器登录需要可选依赖 Playwright；请安装 "
            "`rsa-research-agent[browser]`，然后运行 `python -m playwright install chromium`。"
        ) from exc

    if headless and wait_seconds is None:
        raise BrowserSessionError("headless 登录必须提供 --wait-seconds，否则无法等待用户完成登录。")

    session_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(str(provider["login_url"]))
        if wait_seconds is None:
            input("请在打开的浏览器中完成登录，完成后回到终端按 Enter 保存 session。")
        else:
            page.wait_for_timeout(wait_seconds * 1000)
        context.storage_state(path=str(session_path))
        browser.close()


def login_browser_session(
    config: ProjectConfig,
    provider_id: str,
    *,
    headless: bool = False,
    wait_seconds: int | None = None,
    login_runner: LoginRunner | None = None,
) -> BrowserSessionLoginResult:
    provider = get_browser_session_provider(config, provider_id)
    session_path = resolve_session_storage(config, provider)
    runner = login_runner
    if runner is None:
        def runner(provider_arg: dict[str, Any], session_path_arg: Path) -> None:
            _playwright_login_runner(
                provider_arg,
                session_path_arg,
                headless=headless,
                wait_seconds=wait_seconds,
            )

    session_path.parent.mkdir(parents=True, exist_ok=True)
    runner(provider, session_path)
    if not session_path.exists():
        raise BrowserSessionError("登录流程未生成 browser session 文件。")
    cookie_count, origin_count = _state_counts(session_path)
    metadata_path = _metadata_path_for_session(session_path, provider_id)
    existing = {}
    if metadata_path.exists():
        loaded = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            existing = loaded
    created_at = existing.get("created_at") or _now()
    metadata = {
        "provider_id": provider_id,
        "provider_type": BROWSER_PROVIDER_TYPE,
        "name_zh": provider.get("name_zh"),
        "login_url": provider.get("login_url"),
        "allowed_domains": normalize_allowed_domains(provider),
        "session_file": _display_path(config, session_path),
        "cookie_count": cookie_count,
        "origin_count": origin_count,
        "usage_restriction_zh": provider.get("usage_restriction_zh"),
        "created_at": created_at,
        "updated_at": _now(),
        "notes_zh": "本文件只记录 session metadata；真实 cookies 保存在同目录 JSON，且不会进入 git。",
    }
    metadata_path.write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return BrowserSessionLoginResult(provider_id, session_path, metadata_path, cookie_count, origin_count)


def browser_session_status(config: ProjectConfig, provider_id: str) -> BrowserSessionStatus:
    provider = get_browser_session_provider(config, provider_id)
    session_path = resolve_session_storage(config, provider)
    metadata_path = _metadata_path_for_session(session_path, provider_id)
    if not session_path.exists():
        return BrowserSessionStatus(
            provider_id=provider_id,
            provider_name_zh=str(provider.get("name_zh") or provider_id),
            exists=False,
            session_path=session_path,
            metadata_path=metadata_path,
            cookie_count=0,
            origin_count=0,
            updated_at=None,
            allowed_domains=normalize_allowed_domains(provider),
            login_url=str(provider.get("login_url") or ""),
            reason_zh="尚未登录或 session 文件不存在。",
        )
    cookie_count, origin_count = _state_counts(session_path)
    updated_at = datetime.fromtimestamp(
        session_path.stat().st_mtime,
        tz=timezone.utc,
    ).isoformat()
    return BrowserSessionStatus(
        provider_id=provider_id,
        provider_name_zh=str(provider.get("name_zh") or provider_id),
        exists=True,
        session_path=session_path,
        metadata_path=metadata_path,
        cookie_count=cookie_count,
        origin_count=origin_count,
        updated_at=updated_at,
        allowed_domains=normalize_allowed_domains(provider),
        login_url=str(provider.get("login_url") or ""),
        reason_zh="session 文件存在，可用于允许域名下的 cookie-based 下载。",
    )


def clear_browser_session(config: ProjectConfig, provider_id: str) -> list[Path]:
    provider = get_browser_session_provider(config, provider_id)
    session_path = resolve_session_storage(config, provider)
    metadata_path = _metadata_path_for_session(session_path, provider_id)
    removed: list[Path] = []
    for path in [session_path, metadata_path]:
        if path.exists():
            path.unlink()
            removed.append(path)
    return removed


def _cookie_domain_matches(cookie: dict[str, Any], url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    domain = _normalize_domain(str(cookie.get("domain") or ""))
    if not domain:
        return False
    if not domain_matches(host, domain):
        return False
    path = str(cookie.get("path") or "/")
    if path and not parsed.path.startswith(path.rstrip("/") or "/"):
        return False
    expires = cookie.get("expires")
    if isinstance(expires, (int, float)) and expires > 0 and expires < datetime.now(timezone.utc).timestamp():
        return False
    if cookie.get("secure") is True and parsed.scheme != "https":
        return False
    return True


def cookie_header_for_url(config: ProjectConfig, provider_id: str, url: str) -> str:
    provider = get_browser_session_provider(config, provider_id)
    if not provider_allows_url(provider, url):
        raise BrowserSessionError(f"{provider_id} 目标 URL 不在 allowed_domains 中，已阻止下载。")
    session_path = resolve_session_storage(config, provider)
    if not session_path.exists():
        raise BrowserSessionError(f"{provider_id} 尚未登录，缺少 browser session 文件。")
    state = _load_session_state(session_path)
    cookies = state.get("cookies")
    if not isinstance(cookies, list):
        raise BrowserSessionError(f"{provider_id} browser session 中 cookies 字段无效。")
    pairs: list[str] = []
    for cookie in cookies:
        if not isinstance(cookie, dict):
            continue
        name = str(cookie.get("name") or "")
        value = str(cookie.get("value") or "")
        if name and _cookie_domain_matches(cookie, url):
            pairs.append(f"{name}={value}")
    if not pairs:
        raise BrowserSessionError(f"{provider_id} browser session 没有匹配目标域名的 cookie。")
    return "; ".join(pairs)


def has_browser_session(config: ProjectConfig, provider_id: str) -> bool:
    try:
        return browser_session_status(config, provider_id).exists
    except BrowserSessionError:
        return False


def looks_like_browser_session_provider(provider: dict[str, Any]) -> bool:
    return provider.get("provider_type") == BROWSER_PROVIDER_TYPE


def safe_provider_id(value: str) -> bool:
    return re.match(r"^[A-Za-z0-9_.-]+$", value) is not None
