# Retrospective

## Milestone: v1.0 Local Harness

**Shipped:** 2026-05-13  
**Phases:** 5  
**Plans:** 14  
**Primary stack:** Python 3.11+, PyYAML, argparse, Markdown/YAML files, pytest

### What Was Built

- A local-first literature research harness with a stable `rsa` CLI.
- Formal metadata, paper index, candidate review, literature map, gap report and reading-note workflows.
- Human confirmation and conflict checks before formal writes.
- Local-only PDF/assets policy.
- Deterministic eval fixtures and trace summaries for regression visibility.
- GSD phase artifacts for context, plans, summaries and verification.

### What Worked

- Keeping formal records separate from `agent_outputs` made the system easier to reason about.
- English schema keys plus Chinese explanations gave stable machine-readable structure without sacrificing readability.
- Small deterministic tests caught accidental SAR hard-coding and unsafe write behavior.
- Phase-by-phase summaries made archive and README synthesis straightforward.

### What Was Inefficient

- Some earlier planning files had encoding artifacts, which makes later human reading less pleasant.
- Markdown table parsing is simple and effective for v1, but will become brittle if records grow more complex.
- GSD milestone audit helpers were not fully available in this runtime, so archive close used manual checks plus tests.

### Patterns Established

- `validate` means read-only.
- `generate` and `propose` can create generated artifacts but must not modify formal records.
- Formal writes require explicit `--human-confirmed` and `--confirmed-by`.
- Missing/unauthorized PDFs are represented as blocked status, not fabricated notes.
- Eval baselines live under `01_literature/synthesis/`.

### Key Lessons

- The harness should keep evidence admission, reading notes and formal synthesis as separate steps.
- Before scaling literature review, source retention and screenshot asset policy should be first-class.
- v2 should prioritize ergonomics around batch review, citation APIs and review UI without weakening v1 guardrails.

## Cross-Milestone Trends

| Theme | Observation |
|-------|-------------|
| Safety | Human-confirmed formal writes remain the central protection. |
| Ergonomics | CLI is workable for v1; batch review will need better surfaces. |
| Data model | Markdown/YAML is enough now; parser complexity should be monitored. |
| Evaluation | Deterministic evals are valuable but do not replace semantic research-quality checks. |
