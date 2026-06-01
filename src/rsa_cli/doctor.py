from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .codex_oauth import codex_oauth_status, status_as_dict
from .config import ProjectConfig


DOCTOR_STATUSES = {"OK", "WARN", "BLOCKED"}


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    summary_zh: str
    affected_commands: list[str]
    repair_hint_zh: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DoctorReport:
    project_root: str
    literature_root: str
    overall_status: str
    checks: list[DoctorCheck]
    reading_draft_provider: str | None
    discovery: dict[str, Any]
    codex_oauth: dict[str, Any]


def playwright_repair_hint_zh() -> str:
    return (
        "请运行 `python -m pip install -e .` 安装基础 Python 依赖；"
        "首次使用浏览器登录前，再运行 `python -m playwright install chromium`。"
    )


def _find_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _check(
    *,
    name: str,
    status: str,
    summary_zh: str,
    affected_commands: list[str],
    repair_hint_zh: str,
    details: dict[str, Any] | None = None,
) -> DoctorCheck:
    if status not in DOCTOR_STATUSES:
        raise ValueError(f"unknown doctor status: {status}")
    return DoctorCheck(
        name=name,
        status=status,
        summary_zh=summary_zh,
        affected_commands=affected_commands,
        repair_hint_zh=repair_hint_zh,
        details=details or {},
    )


def _import_check(
    *,
    name: str,
    module_name: str,
    package_hint: str,
    affected_commands: list[str],
) -> DoctorCheck:
    available = _find_spec(module_name)
    if available:
        return _check(
            name=name,
            status="OK",
            summary_zh=f"已找到 Python 模块 `{module_name}`。",
            affected_commands=affected_commands,
            repair_hint_zh="无需修复。",
            details={"module": module_name, "package_hint": package_hint},
        )
    return _check(
        name=name,
        status="BLOCKED",
        summary_zh=f"未找到 Python 模块 `{module_name}`，相关核心命令不能可靠运行。",
        affected_commands=affected_commands,
        repair_hint_zh=f"请运行 `python -m pip install -e .` 安装基础依赖，其中应包含 `{package_hint}`。",
        details={"module": module_name, "package_hint": package_hint},
    )


def _check_playwright_chromium() -> DoctorCheck:
    if not _find_spec("playwright"):
        return _check(
            name="Playwright Chromium",
            status="BLOCKED",
            summary_zh="未找到 Playwright Python 包，暂时无法检查 Chromium 运行资源。",
            affected_commands=["rsa source login"],
            repair_hint_zh=playwright_repair_hint_zh(),
        )
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            executable = Path(playwright.chromium.executable_path)
        exists = executable.exists()
    except Exception as exc:  # pragma: no cover - depends on local Playwright install.
        return _check(
            name="Playwright Chromium",
            status="BLOCKED",
            summary_zh="Playwright Chromium 检查失败，浏览器登录功能暂不可用。",
            affected_commands=["rsa source login"],
            repair_hint_zh=playwright_repair_hint_zh(),
            details={"error": str(exc)},
        )
    if exists:
        return _check(
            name="Playwright Chromium",
            status="OK",
            summary_zh="已找到 Playwright Chromium 运行资源。",
            affected_commands=["rsa source login"],
            repair_hint_zh="无需修复。",
            details={"executable": str(executable)},
        )
    return _check(
        name="Playwright Chromium",
        status="BLOCKED",
        summary_zh="未找到 Playwright Chromium 运行资源，浏览器登录功能暂不可用。",
        affected_commands=["rsa source login"],
        repair_hint_zh="请运行 `python -m playwright install chromium`。",
        details={"expected_executable": str(executable)},
    )


def _check_python_version() -> DoctorCheck:
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):
        return _check(
            name="Python version",
            status="OK",
            summary_zh=f"当前 Python {current} 满足 `>=3.11` 要求。",
            affected_commands=["rsa"],
            repair_hint_zh="无需修复。",
            details={"current": current, "required": ">=3.11"},
        )
    return _check(
        name="Python version",
        status="BLOCKED",
        summary_zh=f"当前 Python {current} 低于项目要求 `>=3.11`。",
        affected_commands=["rsa"],
        repair_hint_zh="请切换到 Python 3.11 或更新版本后重新安装 RSA。",
        details={"current": current, "required": ">=3.11"},
    )


def _check_paths(config: ProjectConfig) -> list[DoctorCheck]:
    checks = [
        _check(
            name="Project root",
            status="OK" if config.root.exists() else "BLOCKED",
            summary_zh=(
                f"项目根目录可访问: {config.root}"
                if config.root.exists()
                else f"项目根目录不可访问: {config.root}"
            ),
            affected_commands=["rsa"],
            repair_hint_zh="无需修复。" if config.root.exists() else "请确认 `--root` 指向 RSA 项目根目录。",
        )
    ]
    if config.literature_root.exists():
        checks.append(
            _check(
                name="Literature workspace",
                status="OK",
                summary_zh=f"文献工作区已存在: {config.literature_root}",
                affected_commands=["rsa init", "rsa note", "rsa campaign", "rsa discovery"],
                repair_hint_zh="无需修复。",
            )
        )
    else:
        checks.append(
            _check(
                name="Literature workspace",
                status="WARN",
                summary_zh=f"文献工作区尚不存在: {config.literature_root}",
                affected_commands=["rsa init"],
                repair_hint_zh="请运行 `rsa init` 创建本地文献工作区。",
            )
        )
    return checks


def _check_discovery_config(config: ProjectConfig) -> DoctorCheck:
    default_provider = config.discovery_default_provider
    allowed = config.discovery_allowed_providers
    if default_provider in allowed:
        return _check(
            name="Discovery provider config",
            status="OK",
            summary_zh="文献发现 provider 配置有效。",
            affected_commands=["rsa discovery run", "rsa discovery validate", "rsa discovery status"],
            repair_hint_zh="无需修复。",
            details={
                "default_provider": default_provider,
                "allowed_providers": allowed,
                "automation_mode": config.discovery_automation_mode,
            },
        )
    return _check(
        name="Discovery provider config",
        status="BLOCKED",
        summary_zh="discovery.default_provider 不在 discovery.allowed_providers 中。",
        affected_commands=["rsa discovery run"],
        repair_hint_zh="请修改 `rsa.yaml`，确保 discovery.default_provider 属于 discovery.allowed_providers。",
        details={"default_provider": default_provider, "allowed_providers": allowed},
    )


def _check_codex_oauth(config: ProjectConfig) -> tuple[DoctorCheck, dict[str, Any]]:
    status = codex_oauth_status(config)
    payload = status_as_dict(status)
    if status.configured and status.status == "blocked":
        check_status = "BLOCKED"
    elif status.configured and status.status in {"ok", "available"}:
        check_status = "OK"
    else:
        check_status = "WARN"
    return (
        _check(
            name="Codex OAuth provider",
            status=check_status,
            summary_zh=status.message_zh,
            affected_commands=["rsa llm codex status", "rsa note draft"],
            repair_hint_zh=status.repair_hint_zh,
            details={
                "configured": status.configured,
                "provider_status": status.status,
                "auth_store_exists": status.auth_store_exists,
                "codex_auth_exists": status.codex_auth_exists,
            },
        ),
        payload,
    )


def _overall_status(checks: list[DoctorCheck]) -> str:
    statuses = {check.status for check in checks}
    if "BLOCKED" in statuses:
        return "BLOCKED"
    if "WARN" in statuses:
        return "WARN"
    return "OK"


def build_doctor_report(config: ProjectConfig) -> DoctorReport:
    checks: list[DoctorCheck] = []
    checks.append(_check_python_version())
    checks.extend(_check_paths(config))
    checks.extend(
        [
            _import_check(
                name="PyYAML",
                module_name="yaml",
                package_hint="PyYAML",
                affected_commands=["rsa init", "rsa validate-profile", "rsa campaign", "rsa discovery"],
            ),
            _import_check(
                name="pypdf",
                module_name="pypdf",
                package_hint="pypdf",
                affected_commands=["rsa note draft"],
            ),
            _import_check(
                name="PyMuPDF",
                module_name="fitz",
                package_hint="PyMuPDF",
                affected_commands=["rsa visual extract", "rsa workflow run"],
            ),
            _import_check(
                name="Playwright",
                module_name="playwright",
                package_hint="playwright",
                affected_commands=["rsa source login"],
            ),
            _check_playwright_chromium(),
            _check_discovery_config(config),
        ]
    )
    codex_check, codex_payload = _check_codex_oauth(config)
    checks.append(codex_check)
    return DoctorReport(
        project_root=str(config.root),
        literature_root=str(config.literature_root),
        overall_status=_overall_status(checks),
        checks=checks,
        reading_draft_provider=config.reading_draft_llm.get("provider"),
        discovery={
            "default_provider": config.discovery_default_provider,
            "allowed_providers": config.discovery_allowed_providers,
            "automation_mode": config.discovery_automation_mode,
        },
        codex_oauth=codex_payload,
    )


def doctor_report_as_dict(report: DoctorReport) -> dict[str, Any]:
    data = asdict(report)
    data["checks"] = [asdict(check) for check in report.checks]
    return data
