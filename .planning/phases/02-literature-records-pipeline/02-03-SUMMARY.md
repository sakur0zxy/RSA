---
phase: 02-literature-records-pipeline
plan: "03"
subsystem: cli-index
tags: [python, markdown, index, validation, cli]
requires:
  - phase: 02-literature-records-pipeline
    provides: Validated formal metadata records
provides:
  - Deterministic paper_index.md renderer
  - Read-only index validation
  - Explicit index regeneration command
affects: [phase-03, literature-map, formal-records]
tech-stack:
  added: []
  patterns: [generated-human-readable-index, read-only-validation]
key-files:
  created:
    - src/rsa_cli/index.py
    - tests/test_index.py
  modified:
    - src/rsa_cli/cli.py
    - 01_literature/paper_index.md
    - tests/test_cli.py
key-decisions:
  - "`paper_index.md` 是人类可读索引，正式事实源仍是 formal metadata YAML。"
  - "`validate-index` 只读并报告差异，`regenerate-index` 才写文件。"
patterns-established:
  - "Render expected content, compare exactly, and require explicit regenerate for repair."
requirements-completed: [META-02, META-03, META-01]
duration: inline
completed: 2026-05-11
---

# Phase 02 Plan 03 Summary

**`paper_index.md` 现在由正式 metadata 确定性生成，并支持只读一致性校验。**

## Performance

- **Duration:** inline with full Phase 2 execution
- **Started:** 2026-05-11
- **Completed:** 2026-05-11
- **Tasks:** 3
- **Implementation commit:** `7294afa`

## Accomplishments

- 新增 `src/rsa_cli/index.py`，实现 metadata 收集、索引渲染、校验和重建。
- 新增 `rsa validate-index` 与 `rsa regenerate-index`。
- 更新 committed empty-index seed，使 `01_literature/paper_index.md` 与空 metadata 渲染结果一致。

## Task Commits

Inline execution used one integrated implementation commit:

1. **Index renderer, CLI commands and smoke tests** - `7294afa`

## Files Created/Modified

- `src/rsa_cli/index.py` - paper index renderer and consistency checks.
- `src/rsa_cli/cli.py` - `validate-index` and `regenerate-index`.
- `01_literature/paper_index.md` - generated empty-index seed.
- `tests/test_index.py` - renderer, stale mismatch and regenerate tests.
- `tests/test_cli.py` - full CLI smoke flow.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `python -m pytest tests/test_metadata.py tests/test_templates.py tests/test_index.py tests/test_cli.py -q` passed.
- Full test suite passed: `54 passed`.
- Manual temp smoke passed: `rsa init`, `rsa add-paper`, `rsa regenerate-index`, `rsa validate-index`, and `assets/P001/.gitkeep` existence check.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Later phases can safely read formal metadata and the generated paper index without treating the index as an independent source of truth.

---
*Phase: 02-literature-records-pipeline*
*Completed: 2026-05-11*
