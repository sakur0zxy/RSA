import json
from pathlib import Path

import pytest

from rsa_cli.browser_session import (
    BrowserSessionError,
    browser_session_status,
    clear_browser_session,
    cookie_header_for_url,
    get_browser_session_provider,
    login_browser_session,
    validate_browser_session_provider_fields,
)
from rsa_cli.config import load_project_config


def write_provider(root: Path, *, provider_id: str = "library", **overrides):
    values = {
        "provider_id": provider_id,
        "enabled": True,
        "name_zh": "学校图书馆浏览器会话",
        "provider_type": "browser_session",
        "base_url": "https://library.example.edu",
        "login_url": "https://library.example.edu/login",
        "session_storage": f".rsa/sessions/{provider_id}.storage_state.json",
        "session_required": True,
        "query_mode": "url_template",
        "query_template": "https://library.example.edu/papers/{doi}.pdf",
        "allowed_domains": ["library.example.edu"],
        "allowed_result_types": ["pdf"],
        "access_mode": "institutional_subscription",
        "requires_login": True,
        "user_access_confirmed": True,
        "authorization_policy": "user_authorized_access",
        "usage_restriction_zh": "仅供个人科研阅读，不得公开分发 PDF。",
        "notes_zh": "用户通过学校账号自行登录；RSA 不保存账号密码。",
    }
    values.update(overrides)
    local_yaml = root / ".rsa" / "local.yaml"
    local_yaml.parent.mkdir(parents=True, exist_ok=True)
    lines = ["source_discovery:", "  custom_providers:"]
    lines.extend(_yaml_lines(values, indent=4))
    local_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return values


def _yaml_lines(data, indent=0):
    lines = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, bool):
            lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"{prefix}  - {item!r}")
        else:
            lines.append(f"{prefix}{key}: {value!r}")
    lines[0] = " " * (indent - 2) + "- " + lines[0].lstrip()
    return lines


def fake_login_runner(_provider, session_path: Path) -> None:
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(
        json.dumps(
            {
                "cookies": [
                    {
                        "name": "SESSION",
                        "value": "abc123",
                        "domain": "library.example.edu",
                        "path": "/",
                    }
                ],
                "origins": [],
            }
        ),
        encoding="utf-8",
    )


def test_browser_session_provider_schema_and_safe_path(tmp_path):
    provider = write_provider(tmp_path)
    config = load_project_config(tmp_path)

    loaded = get_browser_session_provider(config, "library")

    assert loaded["provider_type"] == "browser_session"
    assert validate_browser_session_provider_fields(provider, config=config) == []

    bad = dict(provider)
    bad["session_storage"] = "../escape.json"
    errors = validate_browser_session_provider_fields(bad, config=config)
    assert any(".rsa/sessions" in error for error in errors)


def test_login_status_cookie_header_and_clear_are_local_only(tmp_path):
    write_provider(tmp_path)
    config = load_project_config(tmp_path)

    result = login_browser_session(config, "library", login_runner=fake_login_runner)
    status = browser_session_status(config, "library")
    cookie_header = cookie_header_for_url(
        config,
        "library",
        "https://library.example.edu/papers/10.1234-demo.pdf",
    )

    assert result.cookie_count == 1
    assert status.exists is True
    assert status.cookie_count == 1
    assert "SESSION=abc123" == cookie_header
    assert result.session_path == tmp_path / ".rsa" / "sessions" / "library.storage_state.json"
    metadata_text = result.metadata_path.read_text(encoding="utf-8")
    assert "abc123" not in metadata_text
    assert "SESSION" not in metadata_text

    removed = clear_browser_session(config, "library")
    assert result.session_path in removed
    assert result.metadata_path in removed
    assert browser_session_status(config, "library").exists is False


def test_cookie_header_fails_closed_for_missing_or_wrong_domain_session(tmp_path):
    write_provider(tmp_path)
    config = load_project_config(tmp_path)

    with pytest.raises(BrowserSessionError, match="尚未登录"):
        cookie_header_for_url(config, "library", "https://library.example.edu/paper.pdf")

    login_browser_session(config, "library", login_runner=fake_login_runner)

    with pytest.raises(BrowserSessionError, match="allowed_domains"):
        cookie_header_for_url(config, "library", "https://evil.example/paper.pdf")


def test_missing_playwright_error_is_chinese_and_actionable(tmp_path):
    write_provider(tmp_path)
    config = load_project_config(tmp_path)

    def missing_runner(_provider, _path):
        raise BrowserSessionError(
            "浏览器登录需要可选依赖 Playwright；请安装 `rsa-research-agent[browser]`，然后运行 `python -m playwright install chromium`。"
        )

    with pytest.raises(BrowserSessionError, match="Playwright"):
        login_browser_session(config, "library", login_runner=missing_runner)
