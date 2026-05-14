---
phase: 07-authorized-acquisition
plan: 07-03
subsystem: cli
tags: [python, argparse, cli, documentation, chinese-first]
requires:
  - phase: 07-02
    provides: authorized acquisition engine and source ledger integration
provides:
  - `rsa source find|candidates|download` CLI workflow.
  - README and AGENTS documentation for monitored automation and custom providers.
  - Full regression coverage for Phase 7 CLI behavior.
affects: [phase-08-auto-reading-draft, phase-10-workflow-orchestrator, phase-11-campaign-batch-review]
tech-stack:
  added: []
  patterns: [argparse subcommands, Chinese-first expected errors, read-only status commands]
key-files:
  created: []
  modified:
    - src/rsa_cli/cli.py
    - README.md
    - AGENTS.md
    - tests/test_cli.py
    - tests/test_templates.py
key-decisions:
  - "`rsa source find P001` defaults to monitored automation; `--no-download` preserves a candidate-only monitoring path."
  - "`rsa source candidates P001` and `rsa source status P001` are read-only monitoring commands."
  - "README and AGENTS document the no Sci-Hub/no bypass boundary in Chinese-first language."
patterns-established:
  - "CLI commands expose stable English flags with Chinese help and error text."
  - "Automatic acquisition reports counts for candidates, approved, downloaded, duplicates, blocked and failed."
requirements-completed:
  - V2-DL-01
  - V2-DL-02
  - V2-DL-03
  - V2-DL-04
  - V2-DL-05
  - LANG-04
duration: 17min
completed: 2026-05-14
---

# Phase 7 Plan 07-03: CLI Workflow, Documentation And Regression Coverage Summary

**Chinese-first monitored acquisition CLI with find/candidates/download commands, safety documentation and full regression coverage**

## Performance

- **Duration:** 17 min
- **Started:** 2026-05-14T21:07:00+08:00
- **Completed:** 2026-05-14T21:24:00+08:00
- **Tasks:** 6
- **Files modified:** 5

## Accomplishments

- Added `rsa source find P001`, `rsa source candidates P001` and `rsa source download P001`.
- Added `--no-download`, `--best`, `--candidate`, `--url`, `--authorization-mode`, `--access-mode` and `--usage-restriction-zh`.
- Updated README and AGENTS with Phase 7 workflow, custom provider template guidance, monitored automation and authorization boundaries.

## Task Commits

1. **CLI workflow, documentation and regression coverage** - `7cfc3fb` (feat)

**Plan metadata:** included in this summary commit.

## Files Created/Modified

- `src/rsa_cli/cli.py` - Phase 7 source subcommands and Chinese summaries.
- `README.md` - Phase 7 capability, commands, project structure and safety boundary.
- `AGENTS.md` - project agent guidance for Phase 7 acquisition commands.
- `tests/test_cli.py` - CLI help, no-download, default download and manual URL error coverage.

## Decisions Made

- Expected CLI failures are reported as Chinese `来源操作失败` messages with no traceback.
- `status` includes both Phase 6 source ledger counts and Phase 7 candidate/download counts.
- Direct URL download is supported only through explicit user authorization fields.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 7 is ready for verification and completion. Phase 8 can consume local authorized PDFs through source ledger and candidate records.

---
*Phase: 07-authorized-acquisition*
*Completed: 2026-05-14*
