---
phase: 02-literature-records-pipeline
plan: "02"
subsystem: templates-staging
tags: [markdown, templates, staging, verification-review]
requires:
  - phase: 02-literature-records-pipeline
    provides: Formal metadata writer and human confirmation gate
provides:
  - Chinese candidate review template
  - Chinese search candidate staging template
  - Regression tests for candidate/formal boundary
affects: [phase-03, search-candidates, review-staging]
tech-stack:
  added: []
  patterns: [staging-before-formal-write, chinese-field-guide]
key-files:
  created:
    - tests/test_templates.py
  modified:
    - src/rsa_cli/templates.py
    - templates/verification_review.md
    - templates/search_candidates.md
    - tests/test_cli.py
key-decisions:
  - "`verified` in review means source/identity check passed, not formal metadata intake."
  - "候选文献继续保留在 Markdown staging，不引入 C001.yaml 或候选 YAML schema。"
patterns-established:
  - "Template fallbacks and root templates mirror the same Chinese guidance."
requirements-completed: [SRCH-01, SRCH-02, META-01]
duration: inline
completed: 2026-05-11
---

# Phase 02 Plan 02 Summary

**候选文献 review/search 模板已本地化，并明确保持在 staging 边界内。**

## Performance

- **Duration:** inline with full Phase 2 execution
- **Started:** 2026-05-11
- **Completed:** 2026-05-11
- **Tasks:** 3
- **Implementation commit:** `7294afa`

## Accomplishments

- `verification_review.md` 改为 `# 候选文献核验记录`，保留 `candidate_title`、`source`、`doi_or_url`、`decision`、`reason`、`last_checked`。
- `search_candidates.md` 改为中文 staging 模板，明确候选不能直接创建正式 metadata 记录。
- 新增模板回归测试，覆盖中文说明、英文字段名、状态枚举和 `C001.yaml` 禁止项。

## Task Commits

Inline execution used one integrated implementation commit:

1. **Candidate staging templates and tests** - `7294afa`

## Files Created/Modified

- `templates/verification_review.md` - candidate review staging template.
- `templates/search_candidates.md` - search candidate staging template.
- `src/rsa_cli/templates.py` - built-in fallback templates.
- `tests/test_templates.py` - localization and staging-boundary tests.
- `tests/test_cli.py` - init writes updated templates.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `python -m pytest tests/test_templates.py tests/test_cli.py -q` passed.
- `Select-String` confirmed `candidate_title`, `verified`, `rejected`, `uncertain`, `human_confirmed`, `verification_review.md`, and the formal metadata path wording.
- Full test suite passed: `54 passed`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Candidate staging is ready for later round integration without weakening the formal metadata gate.

---
*Phase: 02-literature-records-pipeline*
*Completed: 2026-05-11*
