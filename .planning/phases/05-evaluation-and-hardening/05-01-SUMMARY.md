---
phase: 05-evaluation-and-hardening
plan: "05-01"
subsystem: eval-fixtures-and-baseline
tags: [python, cli, evals, regression, guardrails]
requires:
  - phase: 04-reading-note-workflow
    provides: Metadata, note and formal-write guardrails to test
provides:
  - Local deterministic eval fixtures
  - Eval report generation
  - Eval baseline and regression comparison
affects: [cli, config, evals, synthesis]
tech-stack:
  added: []
  patterns: [temporary-project-fixtures, baseline-compare, chinese-user-facing-reports]
key-files:
  created:
    - src/rsa_cli/evals.py
    - tests/test_evals.py
    - 01_literature/synthesis/eval_report.md
    - 01_literature/synthesis/eval_baseline.yaml
    - 01_literature/synthesis/eval_regression_report.md
  modified:
    - src/rsa_cli/cli.py
    - src/rsa_cli/config.py
    - tests/test_cli.py
requirements-completed: [EVAL-01]
duration: inline
completed: 2026-05-13
---

# Phase 05 Plan 01 Summary

Local eval fixtures and regression comparison are implemented.

## Accomplishments

- Added `src/rsa_cli/evals.py` with five deterministic fixtures: metadata hallucination, unauthorized PDF behavior, formal-record conflict, output format drift and scope creep.
- Added `rsa eval run`, `rsa eval baseline` and `rsa eval compare`.
- Added config paths for `eval_report.md`, `eval_baseline.yaml` and `eval_regression_report.md`.
- Generated the current v1 baseline and regression report under `01_literature/synthesis/`.
- Added tests for fixture coverage, report writing, baseline writing, regression comparison and CLI behavior.

## Verification

- `python -m pytest tests/test_evals.py tests/test_trace.py tests/test_cli.py tests/test_rounds.py tests/test_templates.py -q` passed: 34 tests.
- `python -m pytest -q` passed: 94 tests.
- `python -m rsa_cli.cli --root . eval baseline` passed and wrote baseline/report files.
- `python -m rsa_cli.cli --root . eval compare` passed with `regressions=0`.

## User Setup Required

None.
