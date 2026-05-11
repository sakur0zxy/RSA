# Phase 1: Harness Foundation - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes the local harness foundation for RSA 科研 Agent. It must define configurable project settings, directory skeleton, topic profile schema, starter SAR profile, bounded research round contract, and a minimal runnable `rsa` CLI. It must not implement real literature search, metadata verification, mapping, reading-note generation, LLM calls, or full campaign synthesis; those belong to later phases.

</domain>

<decisions>
## Implementation Decisions

### Directory Skeleton
- **D-01:** Formal research records default to `01_literature/`, but the path must be read from runtime settings rather than hard-coded.
- **D-02:** Use `rsa.yaml` for project defaults that can be committed, and `.rsa/local.yaml` for user-local overrides.
- **D-03:** The local default should point formal research records to `01_literature/`.
- **D-04:** Phase 1 creates the full literature foundation: `metadata/`, `topic_profiles/`, `agent_outputs/`, `notes/`, `synthesis/`, `pdfs/`, `assets/`, `paper_index.md`, `literature_map.md`, `research_tables.md`, and `agent_research_notes.md`.
- **D-05:** Templates live in a project-root `templates/` directory, separate from formal research records.

### Topic Profile Shape
- **D-06:** Topic profiles use a generic schema; SAR is only the first starter profile instance and must not be hard-coded into core harness logic.
- **D-07:** Topic profile validation requires: `topic_id`, `topic_name`, `core_keywords`, `priority_questions`, `important_metrics`, `preferred_sources`, `exclude_scope`, `grade_rules`, and `required_outputs`.
- **D-08:** `grade_rules` evaluate candidate paper priority, such as A/B/C/Reject, based on relevance, source reliability, and usefulness as baseline/theory evidence.
- **D-09:** Phase 1 includes a detailed SAR starter profile migrated from the old plan, covering noncontinuous aperture, wide-angle/wide-aperture SAR, multi-aspect/subaperture SAR, distributed SAR, cross-channel coherence, phase-history recovery, ghost metrics, failure boundaries, and physics-constrained learning.

### Research Round Contract
- **D-10:** A research round defaults to at most 5 candidate papers, allows per-round override, and enforces a hard upper limit of 20.
- **D-11:** Large-scale literature review should be handled by future campaign/batch orchestration made of multiple bounded rounds, not by making one round huge.
- **D-12:** Phase 1 should reserve `campaign_id` or equivalent metadata fields, but should not force nested campaign directories yet.
- **D-13:** Ordinary round archives use `R001_short_topic_name` naming.
- **D-14:** Each round archive requires `README.md` and `final_round_summary.md`.
- **D-15:** Optional round files include `search_candidates.md`, `verification_review.md`, `map_integration.md`, `pdf_acquisition_report.md`, and `reading_batch_report.md`.
- **D-16:** Legally obtained or user-provided PDF source files are stored under `01_literature/pdfs/`.
- **D-17:** Important screenshots and result assets are stored under `01_literature/assets/P001/`-style per-paper folders.
- **D-18:** Metadata records should reference `local_pdf`, `assets`, asset source page/description, and `used_for`; `agent_outputs/` should only reference asset paths, not store PDFs/screenshots directly.
- **D-19:** PDFs and screenshots are local-only by default and should be ignored by git.
- **D-20:** Human confirmation is required before writing to formal records: metadata, `paper_index.md`, `literature_map.md`, `notes`, and formal asset indexes. Agent-generated candidates and suggestions can remain in staging/agent_outputs without confirmation.

### Phase 1 Implementation Depth
- **D-21:** Phase 1 builds a minimal runnable CLI harness.
- **D-22:** The CLI reads `rsa.yaml` and `.rsa/local.yaml`.
- **D-23:** The CLI validates topic profile schema and emits actionable validation errors.
- **D-24:** The CLI can create the full `01_literature/` foundation from configured settings.
- **D-25:** The CLI can create an `agent_outputs/R001_xxx/` round directory with required placeholder files.
- **D-26:** Phase 1 does not perform real search, PDF acquisition, metadata verification, mapping, reading, or LLM calls.
- **D-27:** Use a single `rsa` command entry point with subcommands such as `rsa init`, `rsa validate-profile`, and `rsa new-round`.

### the agent's Discretion
- Exact YAML formatting and validation library choice are open, provided no new heavyweight dependency is introduced without clear need.
- Exact template wording can be chosen during planning, as long as it preserves the evidence hierarchy and human-review rules above.
- Exact `.gitignore` patterns can be chosen during implementation, as long as PDFs, screenshots/assets, and `.rsa/local.yaml` are local-only by default.

</decisions>

<specifics>
## Specific Ideas

- The old `00_plan` literature workflow is the main behavioral reference for directory names, round archives, and topic profile fields.
- The SAR starter profile should be detailed enough to smoke-test realistic research use, not just a placeholder.
- The user explicitly wants PDFs and important screenshots preserved locally for later paper writing.
- Large-scale literature review should remain possible through campaign/batch design, but Phase 1 only needs to reserve the relevant fields and avoid one-round overload.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project planning
- `.planning/PROJECT.md` — Project identity, core value, constraints, and evidence hierarchy.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements: `PROF-01`, `PROF-02`, `ROUND-01`, and `DOCS-01`.
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, and plan outline.
- `.planning/STATE.md` — Current project state and known setup notes.
- `AGENTS.md` — Project-local agent behavior, workflow enforcement, and evidence rules.

### Prior research workflow reference
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/agent_literature_workflow_plan.md` — Old literature agent workflow, directory conventions, metadata fields, round archive rules, and anti-features.
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/phase_0_literature_research_plan.md` — Detailed SAR research topics, priority questions, output tables, and first-stage boundaries.
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/research_question_boundary.md` — SAR research boundary, relationship to sparse aperture/wide-angle/distributed SAR, and failure conditions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No application source code exists yet. Phase 1 starts from planning artifacts only.
- Existing GSD artifacts provide the phase boundary, requirements, and project rules.

### Established Patterns
- Project is local-first and git-tracked.
- Planning docs are committed; local-only research assets should be ignored.
- Formal records outrank agent outputs.
- Configuration should separate project defaults (`rsa.yaml`) from local overrides (`.rsa/local.yaml`).

### Integration Points
- New code should connect to the project root through a single `rsa` CLI entry point.
- The CLI should create and validate files under the configured literature root, defaulting to `01_literature/`.
- Phase 1 output should prepare later phases to add candidate search, metadata verification, formal writer, reading notes, and evals.

</code_context>

<deferred>
## Deferred Ideas

- Full campaign/batch orchestration for large-scale literature review is deferred. Phase 1 only reserves fields and keeps rounds bounded.
- Real search, metadata verification, literature mapping, reading-note generation, PDF acquisition workflow, and LLM-backed agent behavior are deferred to later phases.
- Web UI, citation-manager sync, and large batch processing remain v2 scope.

</deferred>

---

*Phase: 01-harness-foundation*
*Context gathered: 2026-05-11*
