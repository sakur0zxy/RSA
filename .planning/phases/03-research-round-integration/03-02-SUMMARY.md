---
phase: 03-research-round-integration
plan: "02"
subsystem: literature-map-gap-report
tags: [python, markdown, map, gap-report, validation, cli]
requires:
  - phase: 03-research-round-integration
    provides: Round summary frontmatter and formal_write_requests validation
provides:
  - Literature map parser and renderer
  - Read-only map validation
  - Generated map proposal files
  - Generated/read-only research gap reports
affects: [phase-03, formal-apply-map, phase-04-reading-notes]
tech-stack:
  added: []
  patterns: [structured-markdown-table, read-only-validation, generated-guidance]
key-files:
  created:
    - src/rsa_cli/map.py
    - tests/test_map.py
  modified:
    - src/rsa_cli/config.py
    - src/rsa_cli/cli.py
    - src/rsa_cli/templates.py
    - 01_literature/literature_map.md
    - templates/map_integration.md
    - tests/test_cli.py
    - tests/test_templates.py
key-decisions:
  - "`literature_map.md` now uses the D-09 columns with bounded `research_role` and `map_status` values."
  - "`rsa map validate` is read-only; `rsa map propose` creates generated guidance only."
  - "`rsa gap generate` writes a generated report, while `rsa gap validate` checks staleness without rewriting."
patterns-established:
  - "Formal map data is parsed as structured rows before validation or rendering."
  - "Gap reports classify priority questions as `covered`, `weak`, or `missing`, with `weak_reason` values."
requirements-completed: [MAP-01, MAP-02]
duration: inline
completed: 2026-05-12
---

# Phase 03 Plan 02 Summary

Literature map validation and gap reporting are implemented.

## Performance

- **Duration:** inline
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 4

## Accomplishments

- Added `src/rsa_cli/map.py` for map parsing, rendering, validation, map proposal generation, and gap report generation/validation.
- Updated `literature_map.md` and `map_integration.md` to the Phase 3 D-09 column schema with Chinese explanations.
- Added CLI commands `rsa map validate`, `rsa map propose --round ...`, `rsa gap generate --topic ...`, and `rsa gap validate --topic ...`.
- Added tests for map vocabulary, metadata linkage, duplicate/conflict detection, proposal write boundaries, and gap report status classification.

## Files Created/Modified

- `src/rsa_cli/map.py` - structured map and gap report logic.
- `src/rsa_cli/config.py` - `literature_map_path` and `synthesis_root` accessors.
- `src/rsa_cli/cli.py` - grouped `map` and `gap` commands.
- `01_literature/literature_map.md` - Phase 3 map seed.
- `templates/map_integration.md` and `src/rsa_cli/templates.py` - map proposal guidance.
- `tests/test_map.py` - map/gap regression tests.

## Deviations from Plan

None.

## Issues Encountered

- Existing template regression expected the previous "不会因为填写本模板而自动写入正式记录" phrase; the new template keeps that safety sentence and adds the formal `literature_map.md` boundary explicitly.

## Verification

- `python -m pytest tests/test_map.py tests/test_cli.py tests/test_templates.py tests/test_metadata.py tests/test_profiles.py -q` passed: 45 tests.

## User Setup Required

None.

## Next Phase Readiness

03-03 can reuse the structured map renderer and validator to apply approved map rows through a single human-confirmed formal write path.

---
*Phase: 03-research-round-integration*
*Completed: 2026-05-12*
