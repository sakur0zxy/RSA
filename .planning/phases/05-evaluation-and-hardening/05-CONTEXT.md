# Phase 5: Evaluation and Hardening - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 adds local regression fixtures, trace summaries, baseline comparison and hardening guidance so future prompt, template, tool or workflow changes cannot quietly corrupt formal research records.

This phase does not add a Web UI, external scholarly API integration, PDF parsing, LLM-based grading, or full multi-agent orchestration. The goal is deterministic local harness checks that can run before or after changes.
</domain>

<decisions>
## Implementation Decisions

### Eval Fixture Scope
- **D-01:** v1 eval fixtures are deterministic Python checks, not LLM judgments.
- **D-02:** `rsa eval run` runs all built-in fixtures and writes a Chinese-readable report under `01_literature/synthesis/`.
- **D-03:** Required fixtures cover metadata hallucination, unauthorized PDF behavior, formal-record conflicts, output format drift and scope creep.
- **D-04:** Each fixture has an English `case_id`, pass/fail result, Chinese detail and remediation guidance.

### Baseline And Regression Comparison
- **D-05:** `rsa eval baseline` records the current fixture results as a local YAML baseline.
- **D-06:** `rsa eval compare` reruns fixtures, compares against the baseline and writes a regression report.
- **D-07:** A baseline passing case that now fails is a regression and must make compare exit nonzero.

### Round Trace Summaries
- **D-08:** Every newly created research round should include `trace_summary.md`.
- **D-09:** `rsa round trace R###_name` regenerates a trace summary from `README.md`, `final_round_summary.md` and optional `verification_review.md`.
- **D-10:** Trace summaries list tools used, candidate decisions, rejected items, uncertain items, formal-write requests and human approvals.
- **D-11:** Trace summaries are audit artifacts. They do not write formal metadata, map rows, reading notes or thesis prose.

### User-Facing Language
- **D-12:** User-facing templates, help text, validation errors and reports must be Chinese-readable while field names, YAML keys, table columns and CLI flags remain English.

### Phase 5 MUST NOT
- **D-13:** Phase 5 must not weaken existing formal-write gates.
- **D-14:** Phase 5 must not add network access or external API dependency to evals.
- **D-15:** Phase 5 must not treat eval reports as academic conclusions.
- **D-16:** Phase 5 must not require subagents or multi-agent execution.
</decisions>

<specifics>
## Specific Ideas

- The user asked the agent to decide Phase 5 details and run without subagents, so the recommended deterministic local approach is locked.
- Eval reports should be useful for humans: concise pass/fail table plus remediation notes for known failure modes.
- Trace summaries should be easy to inspect in a round archive and safe to regenerate.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` - local-first harness and evidence hierarchy.
- `.planning/REQUIREMENTS.md` - `EVAL-01` and `EVAL-02`.
- `.planning/ROADMAP.md` - Phase 5 goal and success criteria.
- `.planning/STATE.md` - current phase position.
- `AGENTS.md` - project-local workflow and evidence rules.

### Prior Phase Decisions
- `.planning/phases/03-research-round-integration/03-CONTEXT.md` - round archive and formal write guardrails.
- `.planning/phases/04-reading-note-workflow/04-CONTEXT.md` - reading-note authorization and approval boundaries.
- `.planning/phases/04-reading-note-workflow/04-VERIFICATION.md` - residual risk that Phase 5 should cover with evals.

### Existing Harness Code
- `src/rsa_cli/cli.py` - argparse command style.
- `src/rsa_cli/rounds.py` - round creation, validation and candidate review parsing patterns.
- `src/rsa_cli/metadata.py` - metadata hallucination and human confirmation gate.
- `src/rsa_cli/formal.py` - formal conflict and write guardrail behavior.
- `src/rsa_cli/notes.py` - unauthorized PDF/source behavior.
- `src/rsa_cli/templates.py` - root and fallback templates.
</canonical_refs>

<code_context>
## Existing Code Insights

- Existing test helpers already create temp projects through `load_project_config` and `create_literature_skeleton`; eval fixtures can reuse the same safe pattern.
- `create_research_round` is the right place to emit an initial trace summary for new rounds.
- Existing renderers write deterministic Markdown; eval and trace reports should follow that style.
- Existing CLI commands catch expected errors and avoid Python tracebacks; Phase 5 should preserve this behavior.
</code_context>

<deferred>
## Deferred Ideas

- LLM-judged evaluation rubrics remain future work after deterministic fixtures are stable.
- Web dashboards for eval history remain v2.
- External citation or search API regression suites remain v2.
</deferred>

---

*Phase: 05-evaluation-and-hardening*
*Context gathered: 2026-05-13*
