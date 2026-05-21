# Phase 10: Workflow Orchestrator - Context

**Gathered:** 2026-05-21  
**Status:** Ready for planning  
**Source:** `$gsd-discuss-phase` inline discussion, no subagents

<domain>

## Phase Boundary

Phase 10 delivers a single-paper workflow orchestrator for RSA. It chains the already implemented v1/v2 commands into a reliable, resumable, monitorable workflow primitive for one formal paper at a time.

The default single-paper chain is:

```text
acquisition -> reading draft -> visual extraction -> scoring -> review packet
```

Phase 10 automatically advances ordinary steps until a review packet, status report, blocked state, or formal-write boundary is reached. It must preserve Chinese-first user-facing output, stable English machine-readable keys, step-level provenance, and fail-closed behavior.

Phase 10 does not implement campaign-level worker queues, multi-paper parallel scheduling, campaign ranking/filtering, Local Review Workspace UI, claim-level citation hardening, true advanced figure intelligence, or formal writes. Campaign-level controlled parallelism belongs to Phase 11. Advanced figure intelligence remains deferred, though Phase 10 must keep compatible artifact links and run-state fields for future integration.

</domain>

<decisions>

## Implementation Decisions

### Workflow Chain And Stop Gates

- **D-01:** Phase 10 orchestrates one paper internally as a sequential chain: `acquisition -> reading draft -> visual extraction -> scoring -> review packet`.
- **D-02:** Phase 10 provides a workflow primitive that Phase 11 can later call for many papers. It must not implement campaign worker queues, stage-level concurrency limits, campaign ranking, or batch exception aggregation.
- **D-03:** `partial` does not stop the workflow when source, schema, and core upstream artifacts remain usable. The workflow continues to review packet and records `partial_reason_zh`, `evidence_level`, affected step, and supervision guidance.
- **D-04:** `blocked` stops the current paper workflow immediately and fails closed. The run state and step report must record Chinese failure reasons and repair hints; normal completed review packets must not be generated for blocked runs.
- **D-05:** `needs_review` continues to review packet, then stops for user supervision. The review packet, run state, and status output must highlight the reason, evidence links, and recommended action.
- **D-06:** Formal write requests always stop before formal records. No workflow command may bypass `rsa formal ...` gates or human confirmation.
- **D-07:** Phase 10 defaults to running the existing conservative `rsa visual extract P###` step, but it does not run true LLM image interpretation or advanced figure intelligence.
- **D-08:** Phase 10 must preserve future advanced figure intelligence interfaces by carrying links/status for `llm_visual_analysis`, `advanced_analysis.curve_extraction`, `advanced_analysis.table_structure`, and `advanced_analysis.multimodal_interpretation`. Current default remains `not_run` with Chinese explanation.

### Entry Point And Campaign Context

- **D-09:** The main entry point is a single formal paper id: `rsa workflow run P001`.
- **D-10:** Campaign context is optional metadata, not a Phase 10 batch entry point. Supported shape should include `--campaign-id C001` and `--campaign-item-id CI001`.
- **D-11:** Phase 10 must not accept `rsa workflow run C001` as a batch scheduler. Campaign traversal, parallelism, ranking, and aggregation belong to Phase 11.
- **D-12:** When campaign context is provided, Phase 10 may read `topic_profile`, `priority_question`, campaign objective, import source, dedup/linking data, and use them in scoring, review packet text, and run state.
- **D-13:** Run state should record `campaign_id` and `campaign_item_id` so Phase 11 can aggregate single-paper results back into a campaign review queue.

### Run State And Resume Model

- **D-14:** Store workflow state per paper, not in one global file. Preferred path shape: `01_literature/workflows/P001/RUN-001.yaml`.
- **D-15:** Each run file must contain a full step ledger. Each step should record at least `step_id`, `command`, `status`, `started_at`, `finished_at`, input summary, artifact links, `error_zh`, `repair_hint_zh`, `retryable`, and `needs_user_action`.
- **D-16:** Main run YAML must not store full stdout/stderr. It should store concise Chinese summaries and artifact paths to avoid log noise, secrets, credentials, or copyrighted content in tracked records.
- **D-17:** `rsa workflow resume P###` resumes from the last unfinished, failed, or retryable step by default.
- **D-18:** Completed steps may be reused only after lightweight artifact validation: file exists, schema is valid, paper/run/source identifiers match, and status is safe to reuse.
- **D-19:** If artifact validation fails, workflow must rerun from that step or stop to repair. It must not trust `completed` in run state alone.
- **D-20:** `--from-step <step_id>` is allowed for manual resume override, with Chinese warnings about which artifacts may be reused, overwritten, or regenerated.

### Monitoring And User Controls

- **D-21:** Phase 10 should expose a complete control surface:
  - `rsa workflow run P001`
  - `rsa workflow resume P001`
  - `rsa workflow status P001`
  - `rsa workflow report P001`
  - `rsa workflow stop P001`
  - `rsa workflow rerun P001 --from-step visual_extraction`
- **D-22:** `stop` marks the current workflow run as user-paused or user-stopped and records a Chinese reason. If implementation is synchronous CLI-only, `stop` must at least prevent later automatic `resume` from continuing without explicit user action.
- **D-23:** `rerun` is the explicit user command for recalculating a step or restarting from a step. It must say which artifacts are reused, overwritten, or regenerated.
- **D-24:** `resume --from-step` is for recovery; `rerun --from-step` is for user-requested recomputation.
- **D-25:** Users must be able to monitor important points through `status` and `report`, and adjust flow through `stop`, `rerun`, `resume`, local config, and command flags.
- **D-26:** Workflow steps may be skipped via local configuration or command flags. Command flags have higher priority than local defaults.
- **D-27:** Skipped steps must be recorded as `status: skipped` with `skipped_reason_zh`. Skipping must not look like successful completion.

### Project-Wide Parallelism Placement

- **D-28:** Use layered parallelism at the project level: one paper is sequential inside Phase 10; many papers may later run with controlled pipeline parallelism in Phase 11.
- **D-29:** Phase 10 run schema must be batch-ready with fields such as `run_id`, `paper_id`, `campaign_id`, `campaign_item_id`, `step_id`, `step_status`, `artifacts`, `blocked_reason_zh`, `partial_reason_zh`, and `retry_policy`.
- **D-30:** Phase 11 owns campaign-level worker queues, per-stage concurrency limits, campaign sorting/filtering, and batch exception aggregation.

### Agent Discretion

- Planner may choose exact module names, dataclasses, YAML field ordering, run id format, and helper split as long as decisions above hold.
- Planner may decide whether `report` writes a Markdown file only, prints a concise terminal summary, or does both.
- Planner may implement conservative initial step toggles first, then leave additional aliases or convenience flags for later if they are not needed for the core loop.
- Planner should keep the existing local Markdown/YAML and argparse style unless current code clearly requires another local pattern.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Policy

- `.planning/PROJECT.md` - Project positioning, Chinese-first policy, formal-record philosophy, dependency strategy, and v2 automation split.
- `.planning/REQUIREMENTS.md` - Phase 10 requirements `V2-WORKFLOW-01` through `V2-WORKFLOW-06`, Phase 11 campaign requirements, and global language/dependency requirements.
- `.planning/ROADMAP.md` - Phase 10/11 boundary: single-paper workflow primitive in Phase 10, campaign controlled parallelism in Phase 11.
- `.planning/STATE.md` - Current state, cumulative decisions, and roadmap evolution.
- `.planning/LANGUAGE-POLICY.md` - Chinese-first user-facing text with stable English schema identifiers.
- `.planning/DEPENDENCY-POLICY.md` - Base dependency, doctor/preflight, and fail-closed expectations.

### Upstream Phase Context

- `.planning/phases/07-authorized-acquisition/07-CONTEXT.md` - Authorized acquisition policy, source candidates, and monitored automation.
- `.planning/phases/07.1-browser-session-provider/07.1-CONTEXT.md` - Browser session provider boundaries and local-only session rules.
- `.planning/phases/08-auto-reading-draft/08-CONTEXT.md` - Reading draft workflow, note status semantics, review packet, `asset_suggestions`, and source/cache links.
- `.planning/phases/08.1-visual-evidence-extraction/08.1-CONTEXT.md` - Visual candidate schema, conservative extraction, `visual_context_packet`, and `llm_visual_analysis: not_run` boundary.
- `.planning/phases/08.2-campaign-foundation/08.2-CONTEXT.md` - Campaign queue, dedup/linking semantics, and Phase 11 boundary.
- `.planning/phases/09-evidence-signals-ai-scoring/09-CONTEXT.md` - Scoring schema, review guidance boundary, human override model, campaign scoring summary, and visual signal degradation.

### Current Implementation

- `src/rsa_cli/cli.py` - Existing argparse command grouping and Chinese-first CLI output pattern.
- `src/rsa_cli/acquisition.py` - Source candidate discovery/download, authorization checks, blocked/failed/duplicate handling.
- `src/rsa_cli/assets.py` - Source ledger and asset manifest helpers.
- `src/rsa_cli/reading_draft.py` - Reading draft source selection, extraction cache, note generation, status, and review packet generation.
- `src/rsa_cli/visual.py` - Visual candidate extraction, visual status, context packets, advanced-analysis placeholders, and fail-closed behavior.
- `src/rsa_cli/scoring.py` - Evidence signals, scoring record, review packet, campaign scoring summary, human review override.
- `src/rsa_cli/campaign.py` - Campaign queue creation/import/validate/status, dedup keys, and metadata linking.
- `src/rsa_cli/config.py` - Project path configuration; Phase 10 needs workflow paths.
- `src/rsa_cli/skeleton.py` - Workspace skeleton; Phase 10 needs `01_literature/workflows/`.
- `tests/test_acquisition.py`, `tests/test_notes.py`, `tests/test_visual.py`, `tests/test_scoring.py`, `tests/test_campaign.py`, `tests/test_cli.py`, `tests/test_skeleton.py`, `tests/test_templates.py` - Closest regression patterns for orchestration.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `src/rsa_cli/acquisition.py` already handles source candidates, authorization mode, access mode, blocked/failed/duplicate outcomes, and source-ledger integration.
- `src/rsa_cli/reading_draft.py` already provides the single-paper reading draft command target, extraction cache, prompt/review packets, and note status semantics.
- `src/rsa_cli/visual.py` already provides conservative visual extraction, local crop/context artifacts, visual candidate validation, and `advanced_analysis` / `llm_visual_analysis` placeholders.
- `src/rsa_cli/scoring.py` already consumes reading notes and visual candidates, produces scoring YAML and review packets, and preserves formal-record boundaries.
- `src/rsa_cli/campaign.py` already gives Phase 10 optional campaign context and gives Phase 11 a queue to consume.
- `src/rsa_cli/cli.py` already contains Chinese-first subcommands and read-only `validate`/`status` patterns to mirror.

### Established Patterns

- Local Markdown/YAML is the persistence layer.
- User-facing text is Chinese-first; schema keys, CLI flags, status enum values, and code identifiers stay English.
- `validate` and `status` commands are read-only.
- Generated artifacts may guide review, but formal records require explicit `rsa formal ...` gates.
- Missing dependencies, invalid schema, missing evidence, or unsafe writes fail closed with Chinese reason and repair guidance.
- Local-only binary artifacts, extracted text, sessions, and prompt/cache data must not be tracked.

### Integration Points

- Phase 10 should call or reuse existing module functions behind the CLI steps rather than duplicating acquisition, reading, visual, or scoring logic.
- `ProjectConfig` needs a workflow root path, likely under `01_literature/workflows/`.
- `skeleton.py` should create the workflow directory during `rsa init`.
- CLI should add a `workflow` command group.
- Phase 10 reports should link to metadata, source candidates/source ledger, reading note, visual candidates/context packets, scoring YAML, scoring review packet, and any workflow run YAML.
- Phase 11 should be able to read Phase 10 run files and aggregate by `campaign_id` / `campaign_item_id`.

</code_context>

<specifics>

## Specific Ideas

- The user wants high automation: ordinary steps should run without step-by-step user confirmation.
- The user wants supervision: important failures, low-confidence evidence, `needs_review`, and formal write candidates must be easy to inspect and adjust.
- The user explicitly accepted `partial -> continue to review packet`, `needs_review -> continue to review packet then stop`, and `blocked -> stop current paper workflow`.
- The user asked whether campaign should be part of Phase 10. The locked answer is: campaign is only optional context in Phase 10; Phase 11 owns campaign as a primary entry point.
- The user asked about advanced figure intelligence. The locked answer is: keep interfaces and artifact links now, execute real advanced figure intelligence later.
- The user chose the fuller command surface so they can actively monitor and control workflow runs.

</specifics>

<deferred>

## Deferred Ideas

- Campaign-level controlled pipeline parallelism, worker queues, campaign ranking/filtering, and batch exception aggregation belong to Phase 11.
- Local Review Workspace UI for supervising candidates, PDFs, reading drafts, visual evidence, scoring, and formal write requests belongs to Phase 12.
- Claim-level citation checks and writing safety hardening belong to Phase 13.
- True advanced figure intelligence is deferred: LLM image understanding, curve/axis/legend/numeric extraction, advanced table reconstruction, chart-claim binding, and multimodal figure-driven conclusions.

</deferred>

---

*Phase: 10-Workflow Orchestrator*  
*Context gathered: 2026-05-21*
