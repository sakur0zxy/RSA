---
phase: "12"
plan: "02"
subsystem: "review-workspace-cli"
status: complete
tags:
  - phase12
  - cli
  - static-html
key-files:
  created:
    - src/rsa_cli/review_workspace.py
  modified:
    - src/rsa_cli/cli.py
    - tests/test_cli.py
    - tests/test_review_workspace.py
metrics:
  tests: "python -m pytest tests/test_review_workspace.py tests/test_cli.py tests/test_templates.py tests/test_skeleton.py -q"
---

# Phase 12-02 Summary: Static HTML Renderer And Review CLI

## Commits

| Commit | Description |
|---|---|
| `f15ad3f` | Implemented static review pages, `rsa review` command group and CLI tests. |

## Completed Work

- Added static `index.html`, `groups/*.html` and `objects/*.html` rendering.
- Added `actions_checklist.md` generation with copyable CLI commands and Chinese explanations.
- Added `rsa review build --campaign C001` and `rsa review build --paper P001`.
- Added `rsa review status`, `rsa review open` and `rsa review clean --generated-only`.
- Kept page actions display-only; all actual state changes remain behind existing CLI validation and formal gates.

## Decisions Honored

- D-01 static package plus CLI.
- D-04 summary/evidence/action page content.
- D-05 show commands without executing them.
- D-08 index/group/object pages.
- D-09 relative links and missing markers.
- D-10 actions checklist.
- D-11 no inline editing.
- D-12 `rsa review build`.
- D-14 status/open/clean helpers.

## Deviations

None.

## Self-Check

PASSED. CLI and generated workspace behavior are covered by regression tests.
