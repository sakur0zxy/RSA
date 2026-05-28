# Phase 13: Writing Safety & Hardening - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning
**Source:** gsd-discuss-phase 13, completed inline without subagents

<domain>
## Phase Boundary

Phase 13 hardens the RSA writing and review chain before the later background worker phase. It adds claim-level citation checks, campaign failure monitoring, deterministic drift checks and stronger guardrails around staged AI outputs.

This phase is not a thesis-writing generator, not an automatic academic conclusion engine and not a new formal write path. Its outputs are Chinese-first review guidance under `01_literature/safety/`, and formal records still require the existing schema validation, conflict checks and explicit human confirmation.

Core product rule:

- 自动化可以完成文献阅读、视觉候选、AI 初审、评分、campaign 队列和 review packet。
- 写入 `metadata/`、`literature_map.md`、`agent_research_notes.md` 或论文正文前，必须经过人工监管和 formal write gate。
- Phase 13 负责告诉用户“哪些 claim、证据链、批量状态或模板契约需要复核”，不负责替用户断言最终学术结论。
</domain>

<decisions>
## Implementation Decisions

### D-01: Claim-level citation check scope

- Decision: `staging_claim_citation_review`.
- Check reading notes, scoring records, visual evidence candidates, workflow artifacts and formal write requests.
- The checker verifies whether each staged claim can link back to a paper, note, page/section/chunk/region or short quote.
- Output is review guidance only. It must not mark a claim as academically true and must not write formal records.

### D-02: Minimal extensible claim reference schema

- Decision: `claim_ref_v1_with_reserved_interfaces`.
- Each claim reference keeps stable English keys with Chinese explanations in reports.
- Required v1 fields:
  - `claim_id`
  - `claim_text_zh`
  - `source_type`
  - `source_path`
  - `paper_id`
  - `page`
  - `section`
  - `source_chunk_id`
  - `quote_id`
  - `visual_candidate_id`
  - `region_bbox`
  - `evidence_level`
  - `status`
  - `warning_zh`
  - `repair_hint_zh`
- Reserved future fields/interfaces:
  - `doi`
  - `paragraph_id`
  - `sentence_id`
  - `figure_id`
  - `table_id`
  - `confidence`
  - `llm_claim_review`
  - `citation_graph`
  - `advanced_figure_claim_binding`

### D-03: Safety command group

- Decision: `rsa_safety_group`.
- Add:
  - `rsa safety check P001`
  - `rsa safety validate P001`
  - `rsa safety status P001`
  - `rsa safety campaign C001`
- `check` and `campaign` may write safety audit records and Markdown reports under `01_literature/safety/`.
- `validate` and `status` are read-only.
- All user-facing success, warning and repair text is Chinese-first.

### D-04: Safety status semantics

- Decision: `passed_needs_review_blocked_missing`.
- `passed`: current staged claim evidence and guardrails have no deterministic warning.
- `needs_review`: evidence exists but has weak trace, missing optional link, low confidence or repair guidance.
- `blocked`: required formal metadata, reading note or core YAML structure is missing/invalid.
- `missing`: no safety audit record exists yet.
- These statuses are safety-review statuses, not formal approval.

### D-05: Campaign failure monitoring

- Decision: `deterministic_campaign_failure_monitor`.
- Monitor the Phase 11 failure cases required by `V2-WRITE-02`:
  - authorization errors
  - blocked/partial aggregation
  - review queue ordering regression
  - formal request non-execution
  - metadata intake not writing formal metadata
  - completed-item non-rerun
  - low-confidence/high-priority queue admission
  - campaign error-policy semantics
- The monitor may report missing evidence as `needs_review` but must not mutate campaign state or formal metadata.

### D-06: Drift checks

- Decision: `deterministic_prompt_template_schema_drift`.
- Phase 13 drift checks are local and deterministic.
- Check expected anchors in README, templates, generated skeleton directories and key YAML schemas.
- Do not add LLM-based grading in this phase.
- Future LLM evals may consume the same safety records through reserved fields.

### D-07: Formal boundary

- Decision: `safety_never_writes_formal_records`.
- Safety commands may write only `01_literature/safety/` artifacts.
- They must never create or update `metadata/P###.yaml`, `literature_map.md`, `agent_research_notes.md`, `paper_index.md` or thesis prose.
- Any future automation must reuse this boundary.

### D-08: Chinese-first user experience

- Decision: `zh_first_safety_outputs`.
- CLI help, errors, reports, warnings and repair hints must be readable by Chinese users.
- Schema keys, CLI flags and code identifiers remain English for stability.
</decisions>

<must_not>
## Phase 13 MUST NOT

- Generate thesis text as a final academic conclusion.
- Treat AI scoring or citation checks as formal approval.
- Bypass human confirmation for formal writes.
- Download new PDFs or run new acquisition logic.
- Add background workers, async daemons or scheduled runs.
- Add heavy LLM evaluation or advanced figure intelligence.
</must_not>

<success>
## Success Criteria

- `rsa safety check P001` creates a machine-readable safety YAML and Chinese Markdown report.
- Claim references preserve source links and repair hints.
- `rsa safety validate/status` are read-only.
- `rsa safety campaign C001` produces deterministic campaign hardening checks for Phase 11 failure semantics.
- README and tests document Phase 13 as review guidance, not formal conclusions.
- The initialized skeleton contains `01_literature/safety/`.
</success>
