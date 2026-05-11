---
phase: 01-harness-foundation
plan: 02
subsystem: profile-validation
tags: [python, yaml, validation, cli, research-profile]

requires:
  - phase: 01-01
    provides: CLI package scaffold, config loader, templates, and SAR starter profile
provides:
  - Explicit round configuration accessors and validation
  - Generic topic profile validator
  - rsa validate-profile CLI command
  - Tests for complete profiles, aggregated schema errors, invalid YAML, and SAR data genericity
affects: [phase-01, phase-02, phase-03, topic-profiles, research-rounds]

tech-stack:
  added: []
  patterns: [schema-validation-errors, safe-yaml-profile-load, generic-profile-data]

key-files:
  created:
    - src/rsa_cli/profiles.py
    - tests/test_profiles.py
  modified:
    - src/rsa_cli/config.py
    - src/rsa_cli/cli.py
    - tests/test_config.py

key-decisions:
  - "Profile validation returns aggregated actionable errors rather than failing on the first missing field."
  - "Grade rules must include A, B, C, and Reject candidate priority buckets."
  - "Round defaults, hard cap, output policy, approval mode, and campaign id are exposed through one config object."

patterns-established:
  - "Validators return structured error lists that CLI commands render without tracebacks for expected user errors."
  - "Starter profiles must pass the same generic validator as any future topic profile."

requirements-completed: [PROF-01, PROF-02, ROUND-01]

duration: 10 min
completed: 2026-05-11
---

# Phase 01 Plan 02: Topic Profile Validation Summary

**Generic YAML topic profile validator with aggregated errors, safe loading, and CLI validation**

## Performance

- **Duration:** 10 min
- **Started:** 2026-05-11T15:58:42+08:00
- **Completed:** 2026-05-11T16:08:15+08:00
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added explicit config properties for round limits, allowed tools, output policy, approval mode, and campaign id.
- Added `src/rsa_cli/profiles.py` with required-field, type, non-empty, and grade-rule validation.
- Added `rsa validate-profile PATH` with concise success/failure output and no traceback for expected profile errors.
- Added tests proving the SAR starter profile remains generic data and is not hard-coded in validator or CLI logic.

## Task Commits

Each task was committed atomically:

1. **Task 1: Harden config model for bounded rounds** - `c89898b` (`feat(01-02)`)
2. **Task 2: Implement topic profile validator and CLI command** - `51f572c` (`feat(01-02)`)
3. **Task 3: Verify starter SAR profile remains generic data** - `7ad9b93` (`test(01-02)`)

## Files Created/Modified

- `src/rsa_cli/config.py` - round config accessors and validation for policy fields.
- `src/rsa_cli/profiles.py` - generic topic profile schema validation using `yaml.safe_load`.
- `src/rsa_cli/cli.py` - `validate-profile` subcommand.
- `tests/test_config.py` - round config accessor tests.
- `tests/test_profiles.py` - validator, CLI, starter profile, and no-SAR-branch tests.

## Decisions Made

- Required fields are explicitly enumerated in `REQUIRED_PROFILE_FIELDS`.
- `grade_rules` must define candidate priority buckets `A`, `B`, `C`, and `Reject`.
- Expected profile errors are printed as user-facing validation messages, not Python tracebacks.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** No scope change.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/test_config.py tests/test_profiles.py -q` - passed, 11 tests.
- `rsa validate-profile 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml` - passed via user-script path.
- Temporary invalid profile missing seven fields reported all missing field names in one run.
- `Select-String` confirmed `yaml.safe_load` is present in config/profile loading and `yaml.load` is absent.

## Next Phase Readiness

The CLI can now trust topic profiles before round creation. Plan 01-03 can safely call the validator from `rsa new-round` and enforce the round candidate cap.

---
*Phase: 01-harness-foundation*
*Completed: 2026-05-11*
