# Phase 09: Evidence Signals & AI Scoring - Context

**Gathered:** 2026-05-21T10:32:54+08:00  
**Status:** Ready for planning  
**Source:** `$gsd-discuss-phase 9` inline discussion, no subagents

<domain>

## Phase Boundary

Phase 9 delivers an AI-assisted evidence-signal and scoring layer for RSA. It consumes Phase 8 reading drafts, Phase 8.1 visual evidence candidates, and Phase 8.2 campaign queues, then generates staging/review scoring outputs for paper relevance, paper quality, and reading priority.

Phase 9 does not write formal records, does not perform workflow orchestration, does not build the local review workspace, and does not turn AI scores into final academic conclusions. It may automatically judge and sort papers at the staging/review layer, while preserving supervision, traceability, and later human correction.

</domain>

<decisions>

## Implementation Decisions

### Scoring Object And Entry Point

- **D-01:** Support both single-paper scoring and campaign-item scoring, with single-paper scoring as the core entry point.
- **D-02:** `rsa score P001` is the smallest verifiable unit. Campaign scoring must reuse this logic instead of implementing a separate scoring path.
- **D-03:** Campaign scoring may iterate, summarize, and record queue state, but Phase 9 must not become the full Phase 11 campaign review system.

### Scoring Output Location

- **D-04:** Store single-paper scoring results in `01_literature/scores/P###_scoring.yaml`.
- **D-05:** Store campaign scoring summaries in `01_literature/campaigns/C###_scoring_summary.yaml`.
- **D-06:** Keep Phase 8 `agent_review_score_10` as a reading-draft readiness score only. Phase 9 relevance, quality, and read-priority scores must not be written back into reading note frontmatter.
- **D-07:** Scoring YAML is staging/review machine-readable output, not a formal record. Markdown review packets are user-facing review aids, not the source of truth.

### Evidence Signals Schema

- **D-08:** Generate structured `evidence_signals` before scoring. These signals must support scoring, audit, batch comparison, and later regression tests.
- **D-09:** Text signals must cover at least `problem_signal`, `method_signal`, `experiment_signal`, `dataset_signal`, `metric_signal`, `finding_signal`, and `limitation_signal`.
- **D-10:** Visual signals must cover at least `visual_candidate_ids`, `visual_type`, `evidence_level`, `confidence`, and `degraded_reason_zh`.
- **D-11:** Topic signals must record matches to `topic_profile` and `priority_question`, with Chinese explanation for user review.
- **D-12:** Provenance links must trace back to reading note, source chunk, page/region, visual candidate id, and related artifact paths.
- **D-13:** Uncertainty signals must explicitly record abstract-only evidence, missing full text, low-confidence visual evidence, OCR partial success, and text/visual conflicts.

### Scoring Rubric

- **D-14:** Use a `0-10` scoring scale for enough separation during batch sorting and review.
- **D-15:** Keep three separate main scores:
  - `ai_relevance_score_10`: relevance to topic, priority question, and research scenario.
  - `ai_quality_score_10`: paper quality based on rubric subitems.
  - `ai_read_priority_score_10`: reading priority derived from relevance, quality, evidence level, paper role, and current research need.
- **D-16:** Quality scoring must be rubric-backed, not freeform. Subitems should include method clarity, experiment strength, comparison fairness, reproducibility signals, and limitation awareness.
- **D-17:** Chinese threshold semantics:
  - `>= 8`: priority reading /重点复核.
  - `6-7`: AI initial review recommends pass into user supervision queue.
  - `< 6`: low priority or defer.
- **D-18:** `6 分以上建议通过` means AI staging recommendation only. It is not formal approval and not an academic conclusion.

### Visual Evidence Use

- **D-19:** Phase 8.1 visual evidence candidates may participate as weighted signals in scoring.
- **D-20:** High-confidence visual evidence can strengthen quality subitems such as experiment strength, method comparison, result support, and reproducibility signals.
- **D-21:** Low-confidence visual evidence can only be a weak signal, must lower `score_confidence`, and must include `degraded_reason_zh`.
- **D-22:** Missing visual evidence must not block scoring, but scoring must state the evidence scope limitation in Chinese.
- **D-23:** Text/visual conflicts must set the scoring state to `needs_review`.
- **D-24:** Unconfirmed OCR or LLM visual interpretations must not enter formal records.

### Human Review Override

- **D-25:** Use the enhanced model: AI automatic judgment + user supervision/traceability + later human correction.
- **D-26:** AI may automatically write staging/review decisions:
  - `recommend_pass`
  - `recommend_defer`
  - `needs_review`
  - `blocked`
- **D-27:** AI may automatically sort, filter, advance review queue state, and generate candidate explanation text at the staging/review layer.
- **D-28:** Users do not need to confirm every AI initial judgment. They mainly supervise `needs_review`, `blocked`, low-confidence items, high-priority items, formal-write candidates, and text/visual conflicts.
- **D-29:** Later human correction must be supported. If a paper is later found problematic, the user can change scores, decisions, or handling outcome.
- **D-30:** Human changes must not silently overwrite previous judgment. Store traceable `human_review` and `review_history` fields, including reviewer, time, previous decision, new decision, changed scores, and `change_reason_zh`.
- **D-31:** `recommend_pass` is not `approved`. Formal approval remains behind human confirmation and formal write gates.

### CLI And Outputs

- **D-32:** Implement a minimal closed-loop score command group before larger orchestration or UI work:
  - `rsa score P001`
  - `rsa score validate P001`
  - `rsa score status P001`
  - `rsa score campaign C001`
  - `rsa score review P001 --final-decision approved|rejected|deferred --reviewer zxy --reason "中文原因"`
- **D-33:** Required outputs:
  - `01_literature/scores/P###_scoring.yaml`
  - `01_literature/scores/P###_review_packet.md`
  - `01_literature/campaigns/C###_scoring_summary.yaml`
- **D-34:** `validate` and `status` must be read-only.
- **D-35:** `review` may update human supervision and correction fields, but must not write formal records.
- **D-36:** User-facing CLI help, output, errors, review packets, and repair hints must be Chinese-first. YAML keys, CLI flags, status enum values, and code identifiers remain English with Chinese context.

### Agent Discretion

- Planner may decide exact module names, dataclasses, helper split, and scoring formula details, as long as the decisions above hold.
- Planner may choose deterministic mock scoring fixtures for tests, provided real/LLM scoring still fail closed when required inputs or config are missing.
- Planner may add schema helper functions and templates where useful, but must keep the existing local Markdown/YAML and argparse style.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Global Policy

- `.planning/PROJECT.md` - Chinese-first project positioning, formal-record philosophy, dependency strategy, and v2 chain.
- `.planning/REQUIREMENTS.md` - Phase 9 requirements `V2-SCORE-01` through `V2-SCORE-05`, plus global language/dependency requirements.
- `.planning/ROADMAP.md` - Phase 9 placement between visual evidence extraction/campaign foundation and workflow orchestration.
- `.planning/STATE.md` - Current project state and cumulative phase decisions.
- `.planning/LANGUAGE-POLICY.md` - Chinese-first user-facing text policy with stable English schema identifiers.
- `.planning/DEPENDENCY-POLICY.md` - Base dependency, doctor/preflight, and fail-closed expectations.

### Upstream Phase Context

- `.planning/phases/08-auto-reading-draft/08-CONTEXT.md` - Reading draft schema, `agent_review_score_10`, review packet, source chunks, and Phase 9 handoff.
- `.planning/phases/08.1-visual-evidence-extraction/08.1-CONTEXT.md` - Visual candidate schema, page/region/source trace, `llm_visual_analysis` handoff, and visual evidence boundaries.
- `.planning/phases/08.2-campaign-foundation/08.2-CONTEXT.md` - Campaign YAML queue, dedup/linking semantics, and Phase 9/11 boundary.

### Current Implementation

- `src/rsa_cli/cli.py` - Existing argparse command grouping and Chinese-first CLI output pattern.
- `src/rsa_cli/reading_draft.py` - Reading source selection, extraction cache, reading draft review score, source chunks, and review packet generation.
- `src/rsa_cli/visual.py` - Visual candidate schema, statuses, confidence/evidence levels, visual context packets, and fail-closed behavior.
- `src/rsa_cli/campaign.py` - Campaign queue creation/import/validate/status, dedup keys, linked metadata semantics.
- `src/rsa_cli/config.py` - Project path configuration; Phase 9 needs `scores` output paths.
- `src/rsa_cli/skeleton.py` - Workspace skeleton; Phase 9 needs `01_literature/scores/`.
- `tests/test_notes.py`, `tests/test_visual.py`, `tests/test_campaign.py`, `tests/test_cli.py`, `tests/test_templates.py` - Closest test patterns for Phase 9.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `src/rsa_cli/reading_draft.py` already provides text extraction, local extraction cache, source chunk ids, `source_grounded_claims`, `short_quotes`, `asset_suggestions`, and a Chinese review packet. Phase 9 should consume these rather than re-extracting PDFs.
- `src/rsa_cli/visual.py` already provides `visual_evidence_candidates.yaml`, `visual_context_packet`, page/region/source trace, confidence levels, evidence levels, and fail-closed visual status handling.
- `src/rsa_cli/campaign.py` already provides `01_literature/campaigns/C###.yaml`, `CI###` items, dedup keys, formal metadata linking, and read-only validation/status.
- `src/rsa_cli/cli.py` already uses grouped subcommands, read-only validate/status patterns, and Chinese user-facing messages.

### Established Patterns

- Local Markdown/YAML files remain the default persistence layer.
- User-facing content is Chinese-first; stable schema and code identifiers remain English.
- `validate` and `status` commands are read-only.
- Generated staging/review artifacts may guide user work but cannot replace formal records.
- Missing inputs, missing dependencies, invalid schema, unavailable evidence, or unsafe writes must fail closed with Chinese reasons.
- Formal writes require explicit human confirmation and are handled through `rsa formal ...`, not through generated artifacts.

### Integration Points

- Phase 9 consumes Phase 8 reading notes and extraction cache for text signals.
- Phase 9 consumes Phase 8.1 visual candidates and visual context packets for visual signals.
- Phase 9 consumes Phase 8.2 campaign queues for batch scoring and campaign summary.
- Phase 10 can later call the Phase 9 score commands as workflow steps.
- Phase 11 can later build ranking/filtering/review queues on top of Phase 9 scoring summaries.
- Phase 12 can present Phase 9 review packets and history for local supervision.
- Phase 13 can harden claim-level citation checks without changing Phase 9 into formal academic judgment.

</code_context>

<specifics>

## Specific Ideas

- The user wants high automation: AI should be allowed to make staging/review judgments automatically.
- The user also wants supervision and traceability: humans can inspect the reasoning, links, evidence scope, and history.
- If a paper is later found problematic, the user must be able to correct the score or decision and preserve the correction history.
- Review packets should contain links to relevant records and artifacts so a Chinese user can follow the trail without reading raw YAML first.

</specifics>

<deferred>

## Deferred Ideas

- Full workflow automation belongs in Phase 10.
- Full campaign ranking/filtering/review queue belongs in Phase 11.
- Local review workspace UI belongs in Phase 12.
- Claim-level citation verification and writing safety belong in Phase 13.
- Advanced figure intelligence such as curve recovery, numeric chart extraction, and advanced table reconstruction remains deferred.

</deferred>

---

*Phase: 09-Evidence Signals & AI Scoring*  
*Context gathered: 2026-05-21T10:32:54+08:00*
