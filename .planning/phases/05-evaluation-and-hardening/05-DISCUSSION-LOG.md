# Phase 5 Discussion Log

**Phase:** 05 - Evaluation and Hardening
**Date:** 2026-05-13
**Mode:** agent-decided, no subagents

## Areas Considered

| Area | Decision | Result |
|------|----------|--------|
| Eval style | Deterministic local fixtures, no LLM grading or network calls. | Adopted |
| Fixture coverage | Metadata hallucination, unauthorized PDF, formal conflict, output drift, scope creep. | Adopted |
| Baseline comparison | Store local YAML baseline and compare current runs against it. | Adopted |
| Trace summaries | Emit `trace_summary.md` for rounds and regenerate with `rsa round trace`. | Adopted |
| Hardening docs | Keep remediation guidance in eval reports and Phase 5 hardening doc. | Adopted |

## Deferred

- LLM-based grading.
- Web UI eval dashboard.
- External scholarly API regression suites.
