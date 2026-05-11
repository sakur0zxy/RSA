# Phase 1: Harness Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 01-Harness Foundation
**Areas discussed:** Directory Skeleton, Topic Profile Shape, Research Round Contract, Phase 1 Implementation Depth

---

## Directory Skeleton

| Option | Description | Selected |
|--------|-------------|----------|
| Use `01_literature/` | Keep old plan naming and make research records obvious | Yes |
| Use generic `research/` | More generic, higher migration cost | |
| Use hidden `.rsa/` | Cleaner engineering surface, less visible for research records | |

**User's choice:** Use `01_literature/` as the local default, but read it from settings and allow user override.
**Notes:** Settings split is `rsa.yaml` for project defaults and `.rsa/local.yaml` for local overrides. Templates belong in project-root `templates/`. Phase 1 should create a full `01_literature/` foundation, including local-only `pdfs/` and `assets/`.

---

## Topic Profile Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Generic schema plus SAR starter profile | Reusable harness with realistic first profile | Yes |
| SAR-only first | Fastest for current topic, weaker generality | |
| Minimal generic profile | Quick, but too weak for harness constraints | |

**User's choice:** Use a generic schema, with detailed SAR starter profile as the first instance.
**Notes:** Required fields are complete: `topic_id`, `topic_name`, `core_keywords`, `priority_questions`, `important_metrics`, `preferred_sources`, `exclude_scope`, `grade_rules`, `required_outputs`. `grade_rules` evaluate paper candidate priority, not agent output quality.

---

## Research Round Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Max 5 candidates | Quality-first default with low review burden | Yes |
| Max 10 candidates | More throughput, weaker review quality | |
| User-specified only | Flexible but less automated | |

**User's choice:** Default 5 candidates, allow per-round override, hard cap 20.
**Notes:** For large-scale literature review, reserve campaign/batch fields and split work into multiple bounded rounds instead of making one round huge. Ordinary round naming is `R001_short_topic_name`. Required round files are `README.md` and `final_round_summary.md`; task-specific files are optional.

### Asset Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Local-only PDFs/assets, not in git | Preserves assets without bloating repo or risking copyright issues | Yes |
| PDFs not in git, screenshots may be in git | Easier sync for figures, more copyright caution needed | |
| Everything in git | Convenient but heavy and risky | |

**User's choice:** Store PDFs and important screenshots locally, ignored by git.
**Notes:** PDFs go under `01_literature/pdfs/`. Screenshots/assets go under `01_literature/assets/P001/`-style folders. Metadata references them; `agent_outputs/` does not store them directly.

### Human Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Before formal-record writes | Efficient while protecting formal records | Yes |
| Every step | Safest but slow | |
| Only high-risk items | Fast but too risky early | |

**User's choice:** Human confirmation before formal-record writes.
**Notes:** Applies to metadata, paper index, literature map, notes, and formal asset indexes.

---

## Phase 1 Implementation Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal runnable CLI | Validates Phase 1 behavior without doing real research | Yes |
| Only templates and directories | Fast but weak acceptance | |
| Full agent flow | Too large; belongs to later phases | |

**User's choice:** Build a minimal runnable CLI harness.
**Notes:** The CLI reads config, validates topic profiles, creates the full literature foundation, creates a round directory, and generates required placeholder files. It does not search, call LLMs, acquire PDFs, or write formal metadata.

### CLI Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Single `rsa` entry point with subcommands | Cleanest path for future growth | Yes |
| Direct Python scripts | Simple but scattered | |
| Defer CLI shape | Avoids early choice, weakens planning | |

**User's choice:** Use `rsa` subcommands such as `rsa init`, `rsa validate-profile`, and `rsa new-round`.

---

## the agent's Discretion

- Exact validation library and YAML formatting.
- Exact template prose.
- Exact `.gitignore` patterns, as long as local-only files remain untracked.

## Deferred Ideas

- Full campaign/batch orchestration for large-scale literature review.
- Real search, verification, mapping, reading notes, PDF workflow, and LLM-backed agent behavior.
