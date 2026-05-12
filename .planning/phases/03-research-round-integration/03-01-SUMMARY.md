---
phase: 03-research-round-integration
plan: "01"
subsystem: round-archive-validation
tags: [python, markdown, yaml, rounds, validation, cli]
requires:
  - phase: 02-literature-records-pipeline
    provides: Candidate review template and formal metadata gate
provides:
  - YAML-frontmatter final_round_summary.md template
  - Read-only round archive validation
  - CLI commands round validate and round complete-check
affects: [phase-03, formal-write-requests, map-proposals]
tech-stack:
  added: []
  patterns: [read-only-validation, chinese-user-facing-errors, frontmatter-schema]
key-files:
  created:
    - tests/test_round_completion.py
  modified:
    - src/rsa_cli/rounds.py
    - src/rsa_cli/cli.py
    - src/rsa_cli/templates.py
    - templates/final_round_summary.md
    - tests/test_rounds.py
    - tests/test_cli.py
    - tests/test_templates.py
key-decisions:
  - "`final_round_summary.md` now stores machine-readable `status`, `included_files`, `formal_write_requests`, and human confirmation fields."
  - "`round validate` is read-only; `round complete-check` blocks `completed` unless `human_confirmed`, `confirmed_by`, and `confirmed_at` are present."
  - "`formal_write_requests` is validated as a request queue only; no metadata or map records are written by this plan."
patterns-established:
  - "Archive validation resolves `R###_name` under `agent_outputs/` and rejects unsafe paths."
  - "Candidate review tables are parsed and checked for resolved decision, reason, and last_checked fields."
requirements-completed: [ROUND-02]
duration: inline
completed: 2026-05-12
---

# Phase 03 Plan 01 Summary

Round archive validation is implemented.

## Performance

- **Duration:** inline
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 4

## Accomplishments

- Added YAML frontmatter to `final_round_summary.md` with Chinese explanations and stable English schema keys.
- Added read-only round archive validation for required files, declared optional files, completion status, candidate review rows, and formal write request schema.
- Added `rsa round validate` and `rsa round complete-check` while preserving the existing `rsa new-round` command.
- Added regression tests for archive readiness, completion blocking, candidate row validation, request schema validation, and CLI behavior.

## Files Created/Modified

- `src/rsa_cli/rounds.py` - round summary parsing and archive validation.
- `src/rsa_cli/cli.py` - grouped `round` validation commands.
- `templates/final_round_summary.md` and `src/rsa_cli/templates.py` - frontmatter-enabled summary template.
- `tests/test_round_completion.py` - round completion and request-schema tests.

## Deviations from Plan

None.

## Issues Encountered

None.

## Verification

- `python -m pytest tests/test_round_completion.py tests/test_rounds.py tests/test_templates.py tests/test_cli.py -q` passed: 34 tests.

## User Setup Required

None.

## Next Phase Readiness

03-02 can now read validated round summaries and use `formal_write_requests` for map proposal generation without weakening formal write guardrails.

---
*Phase: 03-research-round-integration*
*Completed: 2026-05-12*
