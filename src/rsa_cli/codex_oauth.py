from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig


PROVIDER_ID = "codex_oauth"
DEFAULT_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_RESPONSE_ENDPOINT = f"{DEFAULT_BASE_URL}/responses"
TOKEN_EXPIRY_SKEW_SECONDS = 120


class CodexOAuthError(ValueError):
    """Raised when the Codex OAuth provider must fail closed."""


@dataclass(frozen=True)
class CodexOAuthStatus:
    configured: bool
    provider: str | None
    model: str | None
    auth_store_path: Path
    auth_store_exists: bool
    codex_auth_path: Path
    codex_auth_exists: bool
    token_source: str
    logged_in: bool
    access_token_present: bool
    expires_at: int | None
    expires_at_iso: str | None
    expired: bool | None
    refresh_supported: bool
    status: str
    message_zh: str
    repair_hint_zh: str


@dataclass(frozen=True)
class CodexAuthImportResult:
    auth_store_path: Path
    source_path: Path
    expires_at_iso: str | None


@dataclass(frozen=True)
class CodexCredentials:
    access_token: str
    model: str
    endpoint: str
    timeout_seconds: int
    temperature: float
    account_id: str | None


def _now_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _iso_from_timestamp(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CodexOAuthError(f"Codex OAuth 本地凭据文件无法解析: {path}") from exc
    if not isinstance(loaded, dict):
        raise CodexOAuthError(f"Codex OAuth 本地凭据文件必须是 YAML mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _read_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CodexOAuthError(f"Codex CLI auth.json 无法解析: {path}") from exc
    if not isinstance(loaded, dict):
        raise CodexOAuthError(f"Codex CLI auth.json 必须是 JSON object: {path}")
    return loaded


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    try:
        loaded = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def token_expires_at(token: str) -> int | None:
    payload = decode_jwt_payload(token)
    exp = payload.get("exp")
    try:
        return int(exp)
    except (TypeError, ValueError):
        return None


def token_is_expired(token: str) -> bool | None:
    expires_at = token_expires_at(token)
    if expires_at is None:
        return None
    return expires_at <= _now_timestamp() + TOKEN_EXPIRY_SKEW_SECONDS


def _codex_oauth_settings(config: ProjectConfig) -> dict[str, Any]:
    return config.reading_draft_llm_codex_oauth


def codex_auth_store_path(config: ProjectConfig) -> Path:
    settings = _codex_oauth_settings(config)
    raw = settings.get("auth_store") or ".rsa/auth/codex_oauth.yaml"
    return config.resolve_path(str(raw))


def codex_cli_auth_path(config: ProjectConfig) -> Path:
    settings = _codex_oauth_settings(config)
    codex_home = settings.get("codex_home")
    if codex_home:
        return config.resolve_path(str(codex_home)) / "auth.json"
    import os

    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home).expanduser() / "auth.json"
    return Path.home() / ".codex" / "auth.json"


def _extract_tokens(data: dict[str, Any]) -> dict[str, Any]:
    tokens = data.get("tokens") if isinstance(data.get("tokens"), dict) else data
    return {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "id_token": tokens.get("id_token"),
        "account_id": tokens.get("account_id") or data.get("account_id"),
    }


def _redacted_token_summary(tokens: dict[str, Any]) -> dict[str, Any]:
    access_token = str(tokens.get("access_token") or "")
    return {
        "access_token_present": bool(access_token),
        "refresh_token_present": bool(tokens.get("refresh_token")),
        "id_token_present": bool(tokens.get("id_token")),
        "account_id_present": bool(tokens.get("account_id")),
        "expires_at": token_expires_at(access_token) if access_token else None,
    }


def _load_auth_from_store(config: ProjectConfig) -> dict[str, Any]:
    return _read_yaml_mapping(codex_auth_store_path(config))


def _load_auth_from_codex_cli(config: ProjectConfig) -> dict[str, Any]:
    return _read_json_mapping(codex_cli_auth_path(config))


def import_codex_cli_auth(config: ProjectConfig) -> CodexAuthImportResult:
    source_path = codex_cli_auth_path(config)
    source_data = _load_auth_from_codex_cli(config)
    if not source_data:
        raise CodexOAuthError(
            f"没有找到 Codex CLI 登录凭据: {source_path}；请先完成 Codex 登录，再运行 rsa llm codex import。"
        )

    tokens = _extract_tokens(source_data)
    access_token = str(tokens.get("access_token") or "")
    if not access_token:
        raise CodexOAuthError("Codex CLI auth.json 缺少 access_token，无法导入 RSA 本地凭据。")
    if token_is_expired(access_token) is True:
        raise CodexOAuthError("Codex CLI access_token 已过期；请先刷新或重新登录 Codex。")

    auth_store = codex_auth_store_path(config)
    expires_at = token_expires_at(access_token)
    data = {
        "provider": PROVIDER_ID,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "source": "codex_cli_auth_json",
        "source_path": str(source_path),
        "tokens": tokens,
        "token_summary": _redacted_token_summary(tokens),
        "future_interfaces": {
            "refresh_command": _codex_oauth_settings(config).get("refresh_command"),
            "refresh_supported": False,
            "alternative_token_sources": ["codex_cli", "external_command"],
        },
    }
    _write_yaml(auth_store, data)
    return CodexAuthImportResult(
        auth_store_path=auth_store,
        source_path=source_path,
        expires_at_iso=_iso_from_timestamp(expires_at),
    )


def clear_codex_oauth_auth(config: ProjectConfig) -> Path:
    path = codex_auth_store_path(config)
    if path.exists():
        path.unlink()
    return path


def _status_from_tokens(
    *,
    config: ProjectConfig,
    tokens: dict[str, Any],
    auth_store_exists: bool,
    codex_auth_exists: bool,
) -> CodexOAuthStatus:
    llm = config.reading_draft_llm
    settings = _codex_oauth_settings(config)
    provider = llm.get("provider")
    model = llm.get("model")
    configured = str(provider or "").lower() == PROVIDER_ID
    access_token = str(tokens.get("access_token") or "")
    expires_at = token_expires_at(access_token) if access_token else None
    expired = token_is_expired(access_token) if access_token else None
    token_source = str(settings.get("token_source") or "rsa_store")
    if not access_token and not configured:
        status = "not_configured"
        message = "codex_oauth 未启用；当前 RSA 会继续使用已配置的其它 LLM provider 或保持未配置状态。"
        hint = "需要使用 Codex/ChatGPT 账号会话时，再设置 provider: codex_oauth 并运行 rsa llm codex import。"
    elif not access_token:
        status = "blocked"
        message = "没有可用的 Codex OAuth access_token。"
        hint = "先完成 Codex 登录，然后运行 rsa llm codex import。"
    elif expired is True:
        status = "blocked"
        message = "Codex OAuth access_token 已过期。"
        hint = "重新登录或刷新 Codex 凭据后，再运行 rsa llm codex import。"
    elif not model and configured:
        status = "blocked"
        message = "已选择 codex_oauth，但缺少 reading_draft.llm.model。"
        hint = "在 .rsa/local.yaml 中设置 reading_draft.llm.model，例如 gpt-5。"
    elif configured:
        status = "ok"
        message = "Codex OAuth provider 已配置，凭据可用于受支持的 RSA AI 任务。"
        hint = "可以运行 rsa note draft P###；产物仍然只进入 staging/review。"
    else:
        status = "available"
        message = "检测到 Codex OAuth 凭据，但当前 reading_draft.llm.provider 不是 codex_oauth。"
        hint = "需要使用时，在 .rsa/local.yaml 中设置 provider: codex_oauth。"

    return CodexOAuthStatus(
        configured=configured,
        provider=str(provider) if provider else None,
        model=str(model) if model else None,
        auth_store_path=codex_auth_store_path(config),
        auth_store_exists=auth_store_exists,
        codex_auth_path=codex_cli_auth_path(config),
        codex_auth_exists=codex_auth_exists,
        token_source=token_source,
        logged_in=bool(access_token and expired is not True),
        access_token_present=bool(access_token),
        expires_at=expires_at,
        expires_at_iso=_iso_from_timestamp(expires_at),
        expired=expired,
        refresh_supported=False,
        status=status,
        message_zh=message,
        repair_hint_zh=hint,
    )


def codex_oauth_status(config: ProjectConfig) -> CodexOAuthStatus:
    store_path = codex_auth_store_path(config)
    cli_path = codex_cli_auth_path(config)
    token_source = str(_codex_oauth_settings(config).get("token_source") or "rsa_store")
    store_data = _load_auth_from_store(config)
    cli_data = _load_auth_from_codex_cli(config)
    if token_source == "codex_cli":
        tokens = _extract_tokens(cli_data)
    else:
        tokens = _extract_tokens(store_data) if store_data else {}
    return _status_from_tokens(
        config=config,
        tokens=tokens,
        auth_store_exists=store_path.exists(),
        codex_auth_exists=cli_path.exists(),
    )


def _account_id_from_token_or_auth(access_token: str, tokens: dict[str, Any]) -> str | None:
    if tokens.get("account_id"):
        return str(tokens["account_id"])
    payload = decode_jwt_payload(access_token)
    for key in [
        "chatgpt_account_id",
        "https://api.openai.com/auth.chatgpt_account_id",
        "account_id",
    ]:
        value = payload.get(key)
        if value:
            return str(value)
    return None


def resolve_codex_credentials(config: ProjectConfig) -> CodexCredentials:
    llm = config.reading_draft_llm
    model = llm.get("model")
    if not model:
        raise CodexOAuthError(
            "缺少 reading_draft.llm.model，无法使用 codex_oauth；请在 .rsa/local.yaml 中设置模型名。"
        )
    settings = _codex_oauth_settings(config)
    token_source = str(settings.get("token_source") or "rsa_store")
    if token_source == "codex_cli":
        auth_data = _load_auth_from_codex_cli(config)
        source_desc = f"Codex CLI auth.json: {codex_cli_auth_path(config)}"
    else:
        auth_data = _load_auth_from_store(config)
        source_desc = f"RSA 本地 auth store: {codex_auth_store_path(config)}"
        if not auth_data and codex_cli_auth_path(config).exists():
            raise CodexOAuthError(
                "RSA 本地 Codex OAuth 凭据不存在；已检测到 Codex CLI auth.json，请先运行 rsa llm codex import。"
            )
    if not auth_data:
        raise CodexOAuthError(
            f"没有可用的 Codex OAuth 凭据来源：{source_desc}。请先完成 Codex 登录并运行 rsa llm codex import。"
        )

    tokens = _extract_tokens(auth_data)
    access_token = str(tokens.get("access_token") or "")
    if not access_token:
        raise CodexOAuthError("Codex OAuth 凭据缺少 access_token，已阻止 LLM 调用。")
    if token_is_expired(access_token) is True:
        raise CodexOAuthError("Codex OAuth access_token 已过期，已阻止 LLM 调用。请重新登录或重新导入。")

    base_url = str(settings.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    endpoint = str(settings.get("response_endpoint") or f"{base_url}/responses")
    timeout = int(llm.get("timeout_seconds") or 60)
    temperature = float(llm.get("temperature") or 0)
    return CodexCredentials(
        access_token=access_token,
        model=str(model),
        endpoint=endpoint,
        timeout_seconds=timeout,
        temperature=temperature,
        account_id=_account_id_from_token_or_auth(access_token, tokens),
    )


def _extract_response_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        try:
            content = choices[0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = None
        if isinstance(content, str) and content.strip():
            return content
    fragments: list[str] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    text = block.get("text") or block.get("output_text")
                    if isinstance(text, str) and text.strip():
                        fragments.append(text)
            text = item.get("text") or item.get("output_text")
            if isinstance(text, str) and text.strip():
                fragments.append(text)
    if fragments:
        return "\n".join(fragments)
    raise CodexOAuthError("Codex OAuth provider 响应中没有可解析的文本输出。")


def call_codex_responses(
    config: ProjectConfig,
    prompt: str,
    *,
    system_prompt: str | None = None,
) -> str:
    credentials = resolve_codex_credentials(config)
    body = {
        "model": credentials.model,
        "input": prompt,
        "store": False,
        "temperature": credentials.temperature,
    }
    if system_prompt:
        body["instructions"] = system_prompt
    headers = {
        "Authorization": f"Bearer {credentials.access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "rsa-cli codex_oauth",
    }
    if credentials.account_id:
        headers["ChatGPT-Account-ID"] = credentials.account_id

    request = urllib.request.Request(
        credentials.endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=credentials.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise CodexOAuthError(
            f"Codex OAuth provider HTTP {exc.code}，已阻止生成假结果。详情: {detail}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise CodexOAuthError(f"Codex OAuth provider 调用失败，已阻止生成假结果: {exc}") from exc
    if not isinstance(payload, dict):
        raise CodexOAuthError("Codex OAuth provider 响应不是 JSON object。")
    return _extract_response_text(payload)


def status_as_dict(status: CodexOAuthStatus) -> dict[str, Any]:
    return {
        "configured": status.configured,
        "provider": status.provider,
        "model": status.model,
        "auth_store_path": str(status.auth_store_path),
        "auth_store_exists": status.auth_store_exists,
        "codex_auth_path": str(status.codex_auth_path),
        "codex_auth_exists": status.codex_auth_exists,
        "token_source": status.token_source,
        "logged_in": status.logged_in,
        "access_token_present": status.access_token_present,
        "expires_at": status.expires_at,
        "expires_at_iso": status.expires_at_iso,
        "expired": status.expired,
        "refresh_supported": status.refresh_supported,
        "status": status.status,
        "message_zh": status.message_zh,
        "repair_hint_zh": status.repair_hint_zh,
    }
