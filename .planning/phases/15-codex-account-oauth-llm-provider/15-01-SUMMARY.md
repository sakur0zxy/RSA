# Phase 15-01 Summary: Codex OAuth Provider Foundation

## Completed

- Added `src/rsa_cli/codex_oauth.py` with local credential discovery, explicit Codex CLI auth import, RSA auth store status, token expiry checks, clear support and a reusable provider call helper.
- Added config defaults for `reading_draft.llm.codex_oauth` and `ProjectConfig.auth_root`.
- Added `.rsa/auth/**` to `.gitignore` so imported OAuth/session material stays local-only.
- Added `rsa llm codex status|import|clear`.
- Added `rsa doctor` provider preflight output with Chinese diagnostics and repair hints.

## Boundaries Preserved

- No ChatGPT web UI automation.
- No browser cookie scraping.
- No password storage.
- No automatic token refresh in this phase.
- No formal write path changes.

## Tests

- `tests/test_codex_oauth.py`
- `tests/test_cli.py::test_cli_llm_codex_status_import_clear_and_doctor`
- `tests/test_config.py`

