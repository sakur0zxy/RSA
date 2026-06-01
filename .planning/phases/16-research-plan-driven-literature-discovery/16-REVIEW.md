# Phase 16 Code Review

**Date:** 2026-06-01  
**Mode:** Inline review, no subagents  
**Scope:** Phase 16 discovery implementation plus closeout changes for global dependency doctor and GitHub-facing docs.

## Files Reviewed

- `src/rsa_cli/discovery.py`
- `src/rsa_cli/doctor.py`
- `src/rsa_cli/cli.py`
- `src/rsa_cli/config.py`
- `src/rsa_cli/skeleton.py`
- `src/rsa_cli/browser_session.py`
- `src/rsa_cli/codex_oauth.py`
- `src/rsa_cli/reading_draft.py`
- `tests/test_discovery.py`
- `tests/test_codex_oauth.py`
- `tests/test_cli.py`
- `tests/test_config.py`
- `tests/test_skeleton.py`
- `tests/test_templates.py`
- `README.md`
- `.planning/DEPENDENCY-POLICY.md`
- `.planning/REQUIREMENTS.md`

## Findings

No blocking code issues found after the closeout fixes.

## Checks Performed

- Confirmed discovery artifacts stay in staging/campaign files and set `formal_write_allowed: false`.
- Confirmed unsupported providers, unreadable plans and no-candidate provider failures fail closed instead of creating fake candidates.
- Confirmed `rsa doctor` reports `OK` / `WARN` / `BLOCKED`, affected commands and Chinese repair hints.
- Confirmed `rsa source login` and doctor share the same Playwright repair guidance.
- Confirmed Codex OAuth status/import output does not print token values.
- Confirmed README documents Phase 16 discovery, dependency layers and formal write boundaries.

## Verification Commands

```powershell
python -m compileall -q src\rsa_cli
python -m pytest tests/test_cli.py::test_cli_llm_codex_status_import_clear_and_doctor tests/test_cli.py::test_cli_discovery_run_validate_status_no_search tests/test_templates.py::test_dependency_policy_matches_base_runtime_and_doctor_contract tests/test_browser_session.py::test_missing_playwright_error_is_chinese_and_actionable -q
python -m pytest tests/test_discovery.py tests/test_codex_oauth.py tests/test_cli.py tests/test_config.py tests/test_skeleton.py tests/test_templates.py -q
python -m rsa_cli.cli --root . doctor
python -m rsa_cli.cli --root . doctor --strict
```

`rsa doctor --strict` correctly returned non-zero in the current environment because Playwright is not installed in this Python environment; this proves strict mode blocks when a core runtime dependency is missing.

## Residual Risk

- Live OpenAlex/Crossref searches remain network-dependent; tests use deterministic mocked provider responses.
- Current local Python environment does not have Playwright installed even though `pyproject.toml` includes it in base dependencies. Users should run `python -m pip install -e .` and then `python -m playwright install chromium` before browser-session acquisition.
- Advanced provider plugins, discovery evals and Web review UI are reserved interfaces only; they are intentionally not implemented in Phase 16.
