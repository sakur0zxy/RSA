# Phase 3: Research Round Integration - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 turns bounded research rounds into traceable research packets, then connects verified papers to formal literature mapping and research-gap inspection through explicit guardrails. It may validate completed round archives, validate or update `literature_map.md`, generate gap reports, and enforce formal-write confirmation rules.

This phase does not implement real web search, automatic PDF download, full-text reading-note generation, Web UI, citation-manager sync, or automatic thesis/review prose writing. Candidate search and formal metadata already exist from Phase 2; Phase 3 integrates them into round completion, mapping, gap detection, and formal-write control.

</domain>

<decisions>
## Implementation Decisions

### Round Completion Package
- **D-01:** Round completion uses a checklist mode, not a strict "all template files must exist" packet. Required files are `README.md` and `final_round_summary.md`; optional files are checked only when declared.
- **D-02:** `final_round_summary.md` uses four `status` values: `draft`, `ready_for_review`, `completed`, and `blocked`. User-facing templates and CLI messages must explain these values in Chinese.
- **D-03:** A round cannot be considered complete unless every candidate row in `verification_review.md` has a `decision` of `verified`, `rejected`, or `uncertain`, plus non-empty `reason` and `last_checked`.
- **D-04:** Optional round files are recorded through a summary manifest. `final_round_summary.md` must list actual optional files under `included_files`, and validation checks that listed files exist and match their expected role.
- **D-05:** `final_round_summary.md` stores machine-readable completion metadata in YAML frontmatter, including at least `status`, `included_files`, and any formal write request fields. The Markdown body remains Chinese-readable.
- **D-06:** `status: completed` requires `human_confirmed: true`, non-empty `confirmed_by`, and non-empty `confirmed_at`. Without those fields, a valid round can be at most `ready_for_review`.
- **D-07:** If a round contains `verified` candidates that have not yet been written to formal metadata, completion is allowed only when they are listed under `formal_write_requests`. This is a request queue only; it never auto-creates `metadata/P###.yaml`.

### Literature Mapping Format
- **D-08:** The formal literature map remains `01_literature/literature_map.md`, using a Chinese-readable Markdown table with stable English column names.
- **D-09:** The mapping table columns are: `paper_id`, `topic_profile`, `priority_question`, `thesis_section`, `planned_output`, `research_role`, `evidence_note`, and `map_status`.
- **D-10:** `paper_id` values in the map must already exist as validated formal metadata files. Candidate titles or unassigned candidates cannot appear as formal map rows.
- **D-11:** One paper may map to multiple priority questions or roles. Use one row per paper-question-role relationship rather than packing multiple mappings into one cell.
- **D-12:** `research_role` should use a bounded set: `baseline`, `theory`, `method`, `evaluation`, `comparison`, `background`, and `risk_or_limitation`. User-facing docs must give Chinese explanations for each value.
- **D-13:** `map_status` uses `proposed`, `approved`, `needs_review`, and `deprecated`. Only `approved` rows count toward gap coverage.

### Research Gap Report
- **D-14:** Gap detection compares a topic profile's `priority_questions` against approved rows in `literature_map.md`.
- **D-15:** Gap output should be a Chinese-readable report under `01_literature/synthesis/`, plus concise CLI output. The report is generated; it is not a formal source of truth.
- **D-16:** Gap status values are `covered`, `weak`, and `missing`. `covered` means at least one approved non-background mapping exists; `weak` means only background/risk-limitation evidence or incomplete thesis/planned-output links exist; `missing` means no approved mapping exists.
- **D-17:** Gap reports should list the priority question, status, supporting `paper_id` values, research roles, and a short next-action note.

### Formal Write Guardrails
- **D-18:** Formal writes to `literature_map.md`, `research_tables.md`, `agent_research_notes.md`, or any future formal record must require explicit CLI action plus `--human-confirmed` and `--confirmed-by`.
- **D-19:** Round completion, map proposals, and gap reports may suggest formal writes, but they must not perform those writes automatically.
- **D-20:** Guardrails must validate that the source round is completed and human-confirmed before accepting formal writes derived from that round.
- **D-21:** Guardrails must block writes that reference missing `paper_id` metadata, non-verified metadata, missing included files, unknown `research_role` values, or conflicting duplicate map rows.
- **D-22:** On conflict, v1 should fail with actionable Chinese errors rather than silently overwriting. No automatic merge or force overwrite behavior is required in this phase.
- **D-23:** English field names and CLI parameters stay stable, but every user-facing template, help text, validation error, and report must include Chinese explanations.

### the agent's Discretion
- Exact CLI subcommand names may be chosen during planning, as long as they clearly separate validation, report generation, and formal writes.
- Exact Markdown rendering details are flexible, provided the machine-readable frontmatter and required table columns remain stable.
- The planner may decide whether gap reports are regenerated by a single command or separate validate/generate commands, as long as validation remains read-only and writes remain explicit.

</decisions>

<specifics>
## Specific Ideas

- User selected the recommended Round completion package defaults: checklist mode, four statuses, per-candidate review decisions, summary manifest, YAML frontmatter, and required human confirmation for `completed`.
- User then asked the agent to decide the remaining choices and report the result, so the mapping, gap report, and formal-write guardrail decisions above are locked recommended defaults.
- `formal_write_requests` should make it easy to preserve verified-but-not-yet-formal candidates without weakening the Phase 2 `add-paper --human-confirmed` gate.
- Gap reports should help the user decide what to read or search next, not pretend to make final academic judgments.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` — Project identity, evidence hierarchy, local-first constraints, and human-review principle.
- `.planning/REQUIREMENTS.md` — Phase 3 requirements: `ROUND-02`, `MAP-01`, `MAP-02`, and `GUARD-01`.
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria, dependencies, and plan count.
- `.planning/STATE.md` — Current project state and active phase position.
- `AGENTS.md` — Project-local agent instructions, evidence hierarchy, GSD workflow, and local-only asset policy.

### Prior Phase Decisions
- `.planning/phases/01-harness-foundation/01-CONTEXT.md` — Directory skeleton, bounded round contract, local PDF/assets policy, and formal-write principle.
- `.planning/phases/02-literature-records-pipeline/02-CONTEXT.md` — Metadata admission gate, candidate review fields, paper index rules, Chinese user-facing language, and formal source-of-truth boundaries.
- `.planning/phases/02-literature-records-pipeline/02-01-SUMMARY.md` — Implemented formal metadata writer and human-confirmed `P###` allocation.
- `.planning/phases/02-literature-records-pipeline/02-02-SUMMARY.md` — Implemented candidate review/search staging templates.
- `.planning/phases/02-literature-records-pipeline/02-03-SUMMARY.md` — Implemented generated paper index and read-only validation.
- `.planning/phases/02-literature-records-pipeline/02-04-SUMMARY.md` — Localized Phase 1 templates and formal seed files.

### Existing Harness Code
- `src/rsa_cli/config.py` — Project config loading and literature path accessors.
- `src/rsa_cli/cli.py` — Existing `argparse` CLI style, Chinese messages, and exception handling pattern.
- `src/rsa_cli/rounds.py` — Existing bounded round creation, round naming, and template rendering.
- `src/rsa_cli/metadata.py` — Formal metadata validation, `P###` allocation, and human confirmation gate.
- `src/rsa_cli/index.py` — Read-only validation and explicit regeneration pattern for generated formal views.
- `src/rsa_cli/templates.py` — Built-in templates and formal record seed text.
- `templates/final_round_summary.md` — Summary template to extend with YAML frontmatter and completion checklist.
- `templates/verification_review.md` — Candidate review table fields and status vocabulary.
- `templates/map_integration.md` — Existing mapping seed text that should evolve into Phase 3 map proposal guidance.
- `01_literature/literature_map.md` — Formal literature map seed to validate/update.
- `01_literature/research_tables.md` — Formal research table seed; writes require guardrails.
- `01_literature/agent_research_notes.md` — Auxiliary notes seed; promotion requires human confirmation.

### Prior Literature Workflow Reference
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/agent_literature_workflow_plan.md` — Old literature agent workflow, map integration role, review boundaries, and anti-features.
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/phase_0_literature_research_plan.md` — SAR priority questions and output expectations.
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/research_question_boundary.md` — SAR topic boundary and failure conditions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `create_research_round` already creates `README.md` and `final_round_summary.md`; Phase 3 should extend validation/completion around those files rather than replacing round creation.
- `metadata.validate_metadata_record` and `metadata.load_metadata_record` can be reused to prove mapped `paper_id` values are formal and verified.
- `index.py` establishes the pattern for generated Markdown views: render expected content, compare in validation, write only through explicit regenerate commands.
- `TEMPLATE_FILES` and root `templates/` already mirror user-editable templates and fallback templates.

### Established Patterns
- Local Markdown/YAML remains the primary storage model.
- Validation commands should be read-only.
- Commands that mutate formal records require explicit user intent and human confirmation.
- User-facing strings should be Chinese; machine-facing keys and CLI parameters stay English.

### Integration Points
- Round completion validation connects to `01_literature/agent_outputs/R###_.../final_round_summary.md` and `verification_review.md`.
- Mapping validation connects formal metadata under `01_literature/metadata/` to `01_literature/literature_map.md`.
- Gap reports connect topic profiles under `01_literature/topic_profiles/` to approved map rows.
- Formal write guardrails connect round summaries, metadata records, and formal Markdown files.

</code_context>

<deferred>
## Deferred Ideas

- Web UI for reviewing candidates, approvals, and conflicts remains v2 scope.
- Citation-manager sync remains v2 scope.
- Real scholarly API search adapters remain v2 or later.
- Reading-note generation from full text remains Phase 4.
- Automatic formal write execution from round completion is explicitly rejected for v1.

</deferred>

---

*Phase: 03-research-round-integration*
*Context gathered: 2026-05-11*
