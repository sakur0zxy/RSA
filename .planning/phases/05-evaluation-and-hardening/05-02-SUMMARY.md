---
phase: 05-evaluation-and-hardening
plan: "05-02"
subsystem: trace-summary-and-hardening-docs
tags: [python, cli, markdown, traceability, audit]
requires:
  - phase: 03-research-round-integration
    provides: Round archive and final summary schema
  - phase: 04-reading-note-workflow
    provides: Formal note approval boundary
provides:
  - Per-round trace summaries
  - Trace regeneration command
  - Hardening guidance for known failure modes
affects: [rounds, templates, cli, docs]
tech-stack:
  added: []
  patterns: [read-only-audit-artifacts, round-local-generated-files]
key-files:
  created:
    - src/rsa_cli/trace.py
    - templates/trace_summary.md
    - tests/test_trace.py
    - .planning/phases/05-evaluation-and-hardening/05-HARDENING.md
  modified:
    - src/rsa_cli/rounds.py
    - src/rsa_cli/cli.py
    - src/rsa_cli/templates.py
    - tests/test_rounds.py
    - tests/test_templates.py
    - tests/test_cli.py
requirements-completed: [EVAL-02]
duration: inline
completed: 2026-05-13
---

# Phase 05 Plan 02 Summary

Round trace summaries and hardening documentation are implemented.

## Accomplishments

- Added `trace_summary.md` root and fallback templates with stable English keys and Chinese explanations.
- Updated `create_research_round` so every new round starts with a trace summary file.
- Added `src/rsa_cli/trace.py` to regenerate trace summaries from `README.md`, `final_round_summary.md` and optional `verification_review.md`.
- Added `rsa round trace R###_name`.
- Added `05-HARDENING.md` with known failure modes, commands and remediation guidance.
- Added tests proving trace regeneration captures tools, decisions, rejected/uncertain items and approvals without modifying formal records.

## Verification

- `python -m pytest tests/test_evals.py tests/test_trace.py tests/test_cli.py tests/test_rounds.py tests/test_templates.py -q` passed: 34 tests.
- `python -m pytest -q` passed: 94 tests.

## User Setup Required

None.
