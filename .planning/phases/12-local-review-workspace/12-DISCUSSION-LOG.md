# Phase 12 Discussion Log: Local Review Workspace

**Date:** 2026-05-27
**Status:** Closed
**Context:** `12-CONTEXT.md`

## Summary

Phase 12 was narrowed to a local static supervision package plus CLI command entrypoints. The workspace helps a Chinese user monitor automated literature processing outputs, inspect evidence links and choose validated CLI actions. It does not run a server, mutate files from HTML, auto-refresh, perform formal writes or replace existing campaign/workflow/scoring commands.

## Accepted Decisions

| ID | Decision | Result |
|---|---|---|
| D-01 | Local workspace shape | Static package plus CLI commands. |
| D-02 | Default entry | Unified review entry. |
| D-03 | Grouping | Urgency-first groups. |
| D-04 | Object content | Summary, evidence links and suggested actions. |
| D-05 | Operation model | Show commands; execution remains in CLI. |
| D-06 | Manifest | Generate machine-readable workspace manifest. |
| D-07 | Scope | Support campaign and paper entrypoints. |
| D-08 | Pages | `index.html`, `groups/*.html`, `objects/*.html`. |
| D-09 | Links | Relative links with explicit Chinese missing markers. |
| D-10 | Checklist | Generate advisory actions checklist. |
| D-11 | Notes | Use CLI `--reason`/`--reviewer`; no inline editing. |
| D-12 | Commands | Add `rsa review build` under a new `review` group. |
| D-13 | Rebuild policy | Overwrite generated artifacts, preserve user records. |
| D-14 | Helpers | Add `status`, `open`, `clean --generated-only`. |
| D-15 | Closure | No more Phase 12 discussion needed before planning. |

## Scope Guardrails

- All user-facing labels, warnings, reasons and command explanations are Chinese-first.
- Field names, CLI flags and schema keys remain English for stability.
- Formal write gate remains mandatory and cannot be bypassed by the workspace.
- Static HTML is generated output, not a source of truth.
- `review_decision` and score review decisions are supervision signals, not formal approval.

## Deferred

- Local Web UI and static package auto-refresh.
- Inline edit controls.
- Background worker/scheduled automation.
- Advanced analytics or knowledge graph UI.
- New formal metadata write paths.
