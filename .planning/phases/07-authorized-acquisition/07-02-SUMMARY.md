---
phase: 07-authorized-acquisition
plan: 07-02
subsystem: acquisition
tags: [python, cli, yaml, pdf, sha256, source-ledger]
requires:
  - phase: 07-01
    provides: source candidate records and provider schema validation
provides:
  - Authorized PDF download helpers.
  - Safe `.tmp` file handling, PDF verification, sha256 deduplication and source ledger writes.
  - Multi-version primary selection for downloaded PDFs.
affects: [phase-08-auto-reading-draft, phase-09-evidence-signals-ai-scoring]
tech-stack:
  added: []
  patterns: [fail-closed authorization checks, atomic local file writes, hash-based deduplication]
key-files:
  created:
    - src/rsa_cli/acquisition.py
  modified:
    - src/rsa_cli/assets.py
    - tests/test_acquisition.py
    - tests/test_assets.py
key-decisions:
  - "Automatic download requires direct PDF result type plus explicit authorization/access mode."
  - "Duplicate PDFs are detected by sha256 and do not overwrite existing local files."
  - "Downloaded source ledger entries include authorization_mode, access_mode, usage_restriction_zh, sha256, version_label and primary selection fields."
patterns-established:
  - "Download attempts always leave candidate/report trail: downloaded, duplicate, failed or blocked."
  - "Primary PDF version is selected by deterministic version priority."
requirements-completed:
  - V2-DL-02
  - V2-DL-03
  - V2-DL-05
  - LANG-04
duration: 22min
completed: 2026-05-14
---

# Phase 7 Plan 07-02: Authorized Download Engine And Source Ledger Integration Summary

**Fail-closed authorized PDF download engine with temporary-file safety, sha256 deduplication and source ledger integration**

## Performance

- **Duration:** 22 min
- **Started:** 2026-05-14T20:45:00+08:00
- **Completed:** 2026-05-14T21:07:00+08:00
- **Tasks:** 8
- **Files modified:** 3

## Accomplishments

- Added `download_best_candidate`, `download_candidate` and `download_direct_url`.
- Implemented PDF-like validation, `.tmp` cleanup, atomic move, sha256 deduplication and multi-version primary selection.
- Extended source ledger validation to accept Phase 7 authorization/access modes while preserving Phase 6 compatibility.

## Task Commits

1. **Authorized download engine and ledger integration** - `7cfc3fb` (feat)

**Plan metadata:** included in this summary commit.

## Files Created/Modified

- `src/rsa_cli/acquisition.py` - download engine, deduplication and ledger integration.
- `src/rsa_cli/assets.py` - extended source authorization enum compatibility.
- `tests/test_acquisition.py` - download, duplicate, failure cleanup and primary version tests.

## Decisions Made

- Direct URL downloads require explicit authorization mode, access mode and Chinese usage restriction.
- Non-PDF downloads fail before source ledger write.
- Hash-identical PDFs are recorded as duplicates, not saved twice.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Added an extra safety refinement during execution: automatic download continues to later approved candidates after one candidate fails.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 07-03 CLI and documentation integration.

---
*Phase: 07-authorized-acquisition*
*Completed: 2026-05-14*
