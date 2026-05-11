---
phase: 01-harness-foundation
plan: 03
subsystem: research-rounds
tags: [python, cli, rounds, filesystem, guardrails]

requires:
  - phase: 01-01
    provides: CLI scaffold, config loader, templates, and literature foundation
  - phase: 01-02
    provides: Topic profile validator and round config accessors
provides:
  - Bounded research round creation service
  - rsa new-round CLI command
  - CLI smoke tests for init, validate-profile, and new-round
  - AGENTS.md guidance for CLI use, evidence hierarchy, local-only assets, and human confirmation
affects: [phase-01, phase-02, phase-03, research-rounds, formal-record-guardrails]

tech-stack:
  added: []
  patterns: [bounded-round-creation, staging-only-writes, cli-error-rendering, temp-root-smoke-tests]

key-files:
  created:
    - src/rsa_cli/rounds.py
    - tests/test_rounds.py
    - tests/test_cli.py
  modified:
    - src/rsa_cli/cli.py
    - AGENTS.md

key-decisions:
  - "Round creation validates the topic profile before any round directory is created."
  - "Round creation enforces the hard candidate cap before writing files."
  - "Smoke tests run in temporary project roots so fake R001 rounds do not pollute real research staging."

patterns-established:
  - "Expected CLI errors return concise stderr messages and nonzero exit codes without tracebacks."
  - "Round archives write only README.md and final_round_summary.md during Phase 1."
  - "Formal records are never touched by round creation."

requirements-completed: [ROUND-01, DOCS-01, PROF-01, PROF-02]

duration: 18 min
completed: 2026-05-11
---

# Phase 01 Plan 03: Round Initialization Summary

**Bounded `rsa new-round` workflow with profile validation, candidate caps, staging-only writes, and CLI smoke coverage**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-11T16:08:16+08:00
- **Completed:** 2026-05-11T16:26:20+08:00
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added `create_research_round` with profile validation, safe slugging, round number allocation, candidate cap enforcement, and required round files.
- Added `rsa new-round` with topic, objective, name, max-candidate, allowed-tool, output-policy, approval-mode, and campaign-id options.
- Added tests proving invalid profiles, unsafe names, and cap overflow fail before round payloads are written.
- Updated `AGENTS.md` with Phase 1 CLI entry points, evidence hierarchy, local-only asset policy, and human-confirmed formal write rules.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement bounded round creation service** - `0e01bd6` (`feat(01-03)`)
2. **Task 2: Wire new-round CLI and smoke tests** - `f093910` (`feat(01-03)`)
3. **Task 3: Finalize project guidance and run SAR starter smoke path** - `aa60762` (`docs(01-03)`)

## Files Created/Modified

- `src/rsa_cli/rounds.py` - bounded round service and guardrails.
- `src/rsa_cli/cli.py` - `new-round` command.
- `tests/test_rounds.py` - service-level round creation and failure tests.
- `tests/test_cli.py` - CLI smoke and error rendering tests.
- `AGENTS.md` - future-agent guidance for CLI and evidence policy.

## Decisions Made

- `rsa new-round` resolves relative topic paths against the configured project root.
- Smoke round creation is tested in a temporary project root to avoid creating a fake permanent R001 round in real research staging.
- Only `README.md` and `final_round_summary.md` are required for Phase 1 round archives; optional templates remain available but are not auto-created.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** No scope change.

## Issues Encountered

- Two early tests treated `agent_outputs/.gitkeep` as a round payload. The assertions were corrected to ignore `.gitkeep` and check for actual round payloads.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/test_cli.py tests/test_config.py tests/test_profiles.py tests/test_skeleton.py tests/test_rounds.py -q` - passed, 27 tests.
- `python -m pip install -e ".[dev]"` - passed.
- `rsa init` via user-script path - passed.
- `rsa validate-profile 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml` - passed.
- `rsa new-round --topic 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml --objective "Smoke test SAR starter profile" --name "sar starter smoke" --max-candidates 5` - passed in a temporary project root.
- Confirmed the smoke round created `README.md` and `final_round_summary.md`; confirmed no formal metadata file was created.

## Next Phase Readiness

Phase 1 now has a usable local harness: `rsa init`, `rsa validate-profile`, and `rsa new-round` are implemented, tested, and documented. Phase 2 can build metadata-first records on top of this foundation.

---
*Phase: 01-harness-foundation*
*Completed: 2026-05-11*
