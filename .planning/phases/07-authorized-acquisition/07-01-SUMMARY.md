---
phase: 07-authorized-acquisition
plan: 07-01
subsystem: acquisition
tags: [python, cli, yaml, source-candidates, provider-config]
requires:
  - phase: 06-asset-source-foundation
    provides: source ledger, PDF local-only policy, asset foundation
provides:
  - Structured `source_candidates/P###.yaml` records.
  - `source_discovery` config accessors and custom provider schema validation.
  - Chinese-first `source_candidates.yaml` template.
affects: [phase-08-auto-reading-draft, phase-10-workflow-orchestrator]
tech-stack:
  added: []
  patterns: [local Markdown/YAML records, Chinese-first schema comments, deterministic validation]
key-files:
  created:
    - src/rsa_cli/acquisition.py
    - templates/source_candidates.yaml
    - tests/test_acquisition.py
  modified:
    - src/rsa_cli/config.py
    - src/rsa_cli/skeleton.py
    - src/rsa_cli/templates.py
    - tests/test_config.py
    - tests/test_skeleton.py
    - tests/test_templates.py
key-decisions:
  - "source_candidates/P###.yaml is the staging layer for acquisition evidence; it is not a formal academic conclusion."
  - "Custom providers are loaded from merged config, but private provider examples should live in .rsa/local.yaml."
  - "title_only candidates are review-only and cannot trigger automatic download."
patterns-established:
  - "Provider schema validation returns Chinese actionable errors while preserving English YAML keys."
  - "Candidate records preserve match evidence, authorization mode, access mode and Chinese reason text."
requirements-completed:
  - V2-DL-01
  - V2-DL-03
  - V2-DL-04
  - V2-DL-05
  - LANG-04
duration: 18min
completed: 2026-05-14
---

# Phase 7 Plan 07-01: Source Candidate Model And Provider Configuration Summary

**Structured acquisition candidate records with provider schema validation, deterministic match evidence, and Chinese-first user guidance**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-14T20:27:00+08:00
- **Completed:** 2026-05-14T20:45:00+08:00
- **Tasks:** 7
- **Files modified:** 8

## Accomplishments

- Added `source_candidates_root` and `source_discovery` config accessors.
- Added `source_candidates.yaml` template with Chinese explanations for stable English keys.
- Added candidate record helpers, custom provider schema validation, built-in DOI/arXiv/official URL candidate discovery and title-only blocking.

## Task Commits

1. **Candidate model and provider configuration** - `7cfc3fb` (feat)

**Plan metadata:** included in this summary commit.

## Files Created/Modified

- `src/rsa_cli/acquisition.py` - candidate model, provider validation and candidate generation.
- `src/rsa_cli/config.py` - source discovery defaults and accessors.
- `src/rsa_cli/skeleton.py` - `source_candidates/` initialization.
- `src/rsa_cli/templates.py` and `templates/source_candidates.yaml` - Chinese-first candidate template.
- `tests/test_acquisition.py`, `tests/test_config.py`, `tests/test_skeleton.py`, `tests/test_templates.py` - focused coverage.

## Decisions Made

- The candidate layer is the auditable staging record for acquisition; it does not update formal metadata.
- Built-in DOI candidates prove identity but do not by themselves prove PDF authorization.
- `title_only` is intentionally blocked from automatic download.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial decision coverage during planning required explicit D-xx references; fixed before execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 07-02 download engine integration.

---
*Phase: 07-authorized-acquisition*
*Completed: 2026-05-14*
