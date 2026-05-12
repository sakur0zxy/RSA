---
phase: 03-research-round-integration
plan: "03"
subsystem: formal-map-writer
tags: [python, cli, guardrails, formal-records, approval-gate]
requires:
  - phase: 03-research-round-integration
    provides: Round archive validation and structured literature map renderer
provides:
  - Human-confirmed formal map writer
  - Source-round preflight for completed summaries
  - Conflict and unsafe-write blocking
affects: [literature-map, phase-04-reading-notes, formal-records]
tech-stack:
  added: []
  patterns: [explicit-human-confirmation, all-or-nothing-formal-write, structured-renderer]
key-files:
  created:
    - src/rsa_cli/formal.py
    - tests/test_formal.py
  modified:
    - src/rsa_cli/cli.py
    - tests/test_cli.py
key-decisions:
  - "`rsa formal apply-map` is the only Phase 3 command that writes to `literature_map.md`."
  - "Source rounds must be `completed` and human-confirmed before their map requests can be applied."
  - "`add_metadata` requests are parsed and counted, but never create `metadata/P###.yaml` in Phase 3."
patterns-established:
  - "Formal writes preflight every row, then write through the structured map renderer only after all checks pass."
  - "Duplicate or conflicting map rows block the whole operation and leave the formal map unchanged."
requirements-completed: [GUARD-01, MAP-01]
duration: inline
completed: 2026-05-12
---

# Phase 03 Plan 03 Summary

The formal map write guardrail is implemented.

## Performance

- **Duration:** inline
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 4

## Accomplishments

- Added `src/rsa_cli/formal.py` with source-round preflight, request parsing, map-row validation, and all-or-nothing formal map application.
- Added `rsa formal apply-map --source-round ... --human-confirmed --confirmed-by ...`.
- Reused the structured map parser/renderer from 03-02 to avoid ad hoc Markdown edits.
- Added regression tests for missing CLI confirmation, uncompleted source rounds, skipped `add_metadata` requests, missing metadata, invalid roles, duplicates, and CLI success/failure behavior.

## Files Created/Modified

- `src/rsa_cli/formal.py` - formal write guardrail and application logic.
- `src/rsa_cli/cli.py` - grouped `formal apply-map` command.
- `tests/test_formal.py` - formal write regression tests.
- `tests/test_cli.py` - top-level help coverage for `formal`.

## Deviations from Plan

None.

## Issues Encountered

None.

## Verification

- `python -m pytest tests/test_formal.py tests/test_map.py tests/test_cli.py tests/test_metadata.py -q` passed: 34 tests.

## User Setup Required

None.

## Next Phase Readiness

Phase 3 now has a safe path from completed round summaries to formal literature map updates. Phase 4 can build reading-note approval flows on the same formal-write boundary.

---
*Phase: 03-research-round-integration*
*Completed: 2026-05-12*
