---
phase: 04-reading-note-workflow
plan: "04-02"
subsystem: approved-note-formal-application
tags: [python, cli, formal-records, approval-gate, guardrails]
requires:
  - phase: 04-reading-note-workflow
    provides: Structured reading note frontmatter and validation
  - phase: 03-research-round-integration
    provides: Literature map parser, renderer and formal write confirmation pattern
provides:
  - Human-confirmed formal note application
  - Note-derived map row application
  - Note-derived agent research note application
affects: [literature-map, agent-research-notes, formal-records]
tech-stack:
  added: []
  patterns: [explicit-human-confirmation, all-or-nothing-formal-write, structured-renderer]
key-files:
  modified:
    - src/rsa_cli/formal.py
    - src/rsa_cli/cli.py
    - src/rsa_cli/notes.py
    - tests/test_formal.py
key-decisions:
  - "`rsa formal apply-note` is the only Phase 4 command that lets a reading note affect formal map or research note records."
  - "Only `note_status: approved` with `human_confirmed`, `confirmed_by` and `confirmed_at` can be applied."
  - "Duplicate or conflicting `agent_research_notes.md` rows block the whole formal write."
patterns-established:
  - "Note-derived map rows reuse the existing `MapRow` validator before any formal write."
  - "Map and research-note writes are preflighted together before either file is modified."
requirements-completed: [NOTE-02]
duration: inline
completed: 2026-05-12
---

# Phase 04 Plan 02 Summary

Approved reading notes can now be applied to formal records through guardrails.

## Accomplishments

- Added `apply_note_requests` and `validate_apply_note_requests` in `formal.py`.
- Added structured parsing/rendering for `agent_research_notes.md`.
- Added `rsa formal apply-note --source-note P### --human-confirmed --confirmed-by ...`.
- Added regression tests for missing confirmation, unapproved notes, map/research note application and duplicate blocking.

## Verification

- `python -m pytest tests/test_notes.py tests/test_formal.py tests/test_cli.py tests/test_templates.py -q` passed: 38 tests.
- `python -m pytest -q` passed: 88 tests.

## User Setup Required

None.

## Next Phase Readiness

Phase 5 can now add eval fixtures for unauthorized source behavior, note schema drift, formal-record conflicts and output trace summaries.
