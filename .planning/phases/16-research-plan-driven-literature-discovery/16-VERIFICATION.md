# Phase 16 Verification: Research Plan Driven Literature Discovery

## Requirement Coverage

| Requirement | Evidence |
|---|---|
| `V2-DISCOVERY-01` | `create_discovery_profile()` accepts `.md`/`.txt` plan files, direct `objective` and optional topic profile; tests confirm no formal metadata is written. |
| `V2-DISCOVERY-02` | `DR###_profile.yaml`, `DR###_queries.yaml` and `DR###_results.yaml` preserve stable English keys and include `field_explanations_zh` / `reason_zh`. |
| `V2-DISCOVERY-03` | Query records include `query_id`, `query`, `query_text`, `query_terms`, `rationale_zh`, `confidence`, `evidence_level` and status. |
| `V2-DISCOVERY-04` | Provider registry is limited to `openalex`, `crossref` and `offline`; unsupported providers fail closed; no unauthorized mirrors or paywall bypass are implemented. |
| `V2-DISCOVERY-05` | Export maps discovered candidates into campaign import rows with source ids, query ids and rationale; metadata and paper index are untouched. |
| `V2-DISCOVERY-06` | `export_discovery_to_campaign()` reuses Phase 8.2 campaign import semantics instead of creating a separate queue. |
| `V2-DISCOVERY-07` | Empty/missing plan input, unsupported provider and provider failures raise `DiscoveryError` or write blocked/not_run status with Chinese guidance. |
| `V2-DISCOVERY-08` | `future_interfaces` reserves query refinement, provider plugins, eval and Web UI without implementing broad extra scope. |

## Commands Run

- `python -m pytest tests/test_discovery.py tests/test_cli.py::test_cli_discovery_run_validate_status_no_search tests/test_cli.py::test_help_lists_expected_subcommands tests/test_config.py tests/test_skeleton.py -q`
- `python -m pytest tests/test_discovery.py tests/test_cli.py::test_cli_discovery_run_validate_status_no_search tests/test_cli.py::test_cli_llm_codex_status_import_clear_and_doctor tests/test_config.py tests/test_skeleton.py -q`
- `python -m pytest tests/test_discovery.py tests/test_campaign.py tests/test_cli.py tests/test_config.py tests/test_skeleton.py tests/test_templates.py -q`
- `python -m pytest -q` -> 206 passed
- `python -m rsa_cli.cli --root . doctor` -> global dependency/provider diagnostics produced Chinese `OK` / `WARN` / `BLOCKED` guidance
- `python -m rsa_cli.cli --root . doctor --strict` -> correctly returned non-zero because Playwright is not installed in the current Python environment
- `python -m rsa_cli.cli --root . eval compare` -> 0 regressions
- `gsd-sdk query init.phase-op 16` -> phase found, 3 plans, verification present
- `gsd-sdk query state.validate` -> valid true, no warnings

## Remaining Risk

- Live OpenAlex/Crossref availability is network-dependent; tests use deterministic mocked provider responses.
- Custom provider plugins and Web review UI are intentionally reserved interfaces, not Phase 16 v1 behavior.
