# Phase 3: Research Round Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 03-research-round-integration
**Areas discussed:** Round completion package, Literature mapping format, Research gap report, Formal write guardrails

---

## Round Completion Package

| Option | Description | Selected |
|--------|-------------|----------|
| Completion checklist mode | Required files are `README.md` and `final_round_summary.md`; optional files are listed and checked only when used. | Yes |
| Strict file packet mode | Every round always includes all optional templates, even when empty. | |
| Lightweight summary mode | Only `README.md` and `final_round_summary.md` are required; everything else is manual. | |

**User's choice:** Completion checklist mode.
**Notes:** User selected the recommended option.

| Option | Description | Selected |
|--------|-------------|----------|
| Four statuses | `draft`, `ready_for_review`, `completed`, `blocked`. | Yes |
| Two statuses | `draft`, `completed`. | |
| Fine-grained statuses | Add extra states such as `abandoned`, `reopened`, or `needs_search`. | |

**User's choice:** Four statuses.
**Notes:** Status values must be explained in Chinese.

| Option | Description | Selected |
|--------|-------------|----------|
| Per-candidate review required | Every candidate needs `decision`, `reason`, and `last_checked`. | Yes |
| Candidate list only | `search_candidates.md` is enough. | |
| Summary-only result | Only the final summary describes outcomes. | |

**User's choice:** Per-candidate review required.
**Notes:** Valid decisions remain `verified`, `rejected`, and `uncertain`.

| Option | Description | Selected |
|--------|-------------|----------|
| Summary manifest | `final_round_summary.md` lists actual optional files in `included_files`. | Yes |
| Directory scan | CLI accepts whatever files are present. | |
| Natural-language note | Human-readable explanation only. | |

**User's choice:** Summary manifest.
**Notes:** Validation should check declared files.

| Option | Description | Selected |
|--------|-------------|----------|
| YAML frontmatter | `status` and `included_files` live in frontmatter. | Yes |
| Markdown table | Use a body table for manifest data. | |
| Bullet list | Use a simple list. | |

**User's choice:** YAML frontmatter.
**Notes:** Body remains Chinese-readable.

| Option | Description | Selected |
|--------|-------------|----------|
| Completion requires human confirmation | `completed` requires `human_confirmed`, `confirmed_by`, and `confirmed_at`. | Yes |
| Only review requires confirmation | Completion can be automatic after review. | |
| No structured confirmation | Keep confirmation only in prose. | |

**User's choice:** Completion requires human confirmation.
**Notes:** Without confirmation, status can be at most `ready_for_review`.

| Option | Description | Selected |
|--------|-------------|----------|
| Allow completion with formal write requests | Verified candidates can remain pending if listed in `formal_write_requests`. | Yes |
| Block completion until metadata exists | Verified candidates must be written before round completion. | |
| Auto-ingest metadata | Completion automatically writes metadata. | |

**User's choice:** User delegated this choice to the agent.
**Notes:** Selected "allow completion with formal write requests" because it preserves the Phase 2 `add-paper --human-confirmed` gate while still letting a round close.

---

## Literature Mapping Format

| Option | Description | Selected |
|--------|-------------|----------|
| Formal Markdown map table | Use `01_literature/literature_map.md` with stable English columns and Chinese guidance. | Yes |
| Per-paper mapping YAML | Add one mapping YAML per paper. | |
| Freeform map notes | Let users write prose. | |

**User's choice:** User delegated this area to the agent.
**Notes:** Selected formal Markdown map table to stay local-first, diffable, and consistent with existing formal seed files.

---

## Research Gap Report

| Option | Description | Selected |
|--------|-------------|----------|
| Topic-question coverage report | Compare topic profile `priority_questions` with approved map rows. | Yes |
| Metadata-only count report | Count metadata records without map roles. | |
| Manual gap notes | User writes gap notes manually. | |

**User's choice:** User delegated this area to the agent.
**Notes:** Selected topic-question coverage because it directly satisfies MAP-02 and keeps gap claims traceable.

---

## Formal Write Guardrails

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit guarded writes | Formal writes require explicit CLI action and `--human-confirmed --confirmed-by`. | Yes |
| Round completion writes formal records | Completion can promote proposals automatically. | |
| Manual-only edits | No CLI guardrails for formal files. | |

**User's choice:** User delegated this area to the agent.
**Notes:** Selected explicit guarded writes to preserve the project's evidence hierarchy and avoid agent_outputs becoming formal truth.

---

## Adopted Review Suggestions

| Suggestion | Decision |
|------------|----------|
| Add recommended implementation order | Adopted; validation-first order added to CONTEXT.md. |
| Define `formal_write_requests` schema | Adopted; fixed schema added without introducing `C001` candidate IDs. |
| Split `weak` reasons | Adopted; `weak_reason` values added to gap report decisions. |
| Clarify `ready_for_review` vs `completed` | Adopted; automated flow may only suggest `ready_for_review`. |
| Add `literature_map.md` example row | Adopted; example row added to specifics. |
| Plan CLI command groups | Adopted as recommended shape, with planner allowed to adjust exact names. |
| Add hard "MUST NOT" guardrails | Adopted as D-31 through D-35. |
| Rename `the agent's Discretion` | Adopted as `Planner Discretion`. |

---

## Planner Discretion

- Exact CLI subcommand names.
- Exact Markdown table formatting beyond required columns.
- Whether gap report generation and validation are one command or two commands.

## Deferred Ideas

- Web UI for approvals and conflicts.
- Citation manager sync.
- Real scholarly API search adapters.
- Phase 4 full-text reading-note generation.
