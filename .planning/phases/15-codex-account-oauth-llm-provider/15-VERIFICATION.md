# Phase 15 Verification: Codex Account OAuth LLM Provider

## Result

Phase 15 is complete. RSA now has an optional `codex_oauth` LLM provider that can import local Codex CLI auth material into `.rsa/auth/codex_oauth.yaml`, inspect provider status, clear the local RSA credential copy, report provider preflight through `rsa doctor`, and use the provider in `rsa note draft`.

## Verification Commands

```powershell
python -m pytest tests/test_codex_oauth.py tests/test_config.py tests/test_cli.py::test_help_lists_expected_subcommands tests/test_cli.py::test_cli_llm_codex_status_import_clear_and_doctor tests/test_templates.py::test_readme_documents_phase15_codex_oauth_provider -q
python -m py_compile src/rsa_cli/codex_oauth.py src/rsa_cli/config.py src/rsa_cli/reading_draft.py src/rsa_cli/cli.py
python -m pytest tests/test_codex_oauth.py tests/test_cli.py tests/test_config.py tests/test_templates.py tests/test_notes.py -q
python -m pytest tests/test_workflow.py tests/test_worker.py tests/test_evals.py -q
python -m pytest -q
python -m rsa_cli.cli --root . doctor
python -m rsa_cli.cli --root . eval compare
gsd-sdk query state.validate
gsd-sdk query init.phase-op 15
```

## Verification Results

- Focused Phase 15 tests: 14 passed.
- CLI/config/templates/notes regression: 67 passed.
- Workflow/worker/eval regression: 16 passed.
- Python compile check: passed.
- Full pytest suite: 199 passed.
- `rsa doctor`: passed; current root reports `codex_oauth` as `not_configured` and detects the Codex CLI auth path without printing tokens.
- `rsa eval compare`: passed with 0 regressions.
- `gsd-sdk query state.validate`: valid with no warnings.
- `gsd-sdk query init.phase-op 15`: phase found, 2 plans, context and verification present.

## Requirement Coverage

- `V2-CODEX-01`: covered by `codex_oauth` config, status and reading draft provider branch.
- `V2-CODEX-02`: covered by explicit import path and no web/cookie/password implementation.
- `V2-CODEX-03`: covered by `.rsa/auth/**`, clear command and `.gitignore`.
- `V2-CODEX-04`: covered by `rsa llm codex status`, `rsa doctor` and Chinese repair hints.
- `V2-CODEX-05`: covered by missing/expired credential blocking and provider response parsing failures.
- `V2-CODEX-06`: covered by reuse of reading draft staging/review path and unchanged formal gates.

## Residual Risks

- The Codex/ChatGPT backend endpoint is unofficial from RSA's perspective and may change. The provider therefore remains optional and fails closed.
- Token refresh is intentionally reserved as a future extension; users must refresh/re-login through Codex and re-import when needed.
- Phase 15 only connects reading draft. Scoring, visual LLM analysis and safety review can reuse the provider later.
