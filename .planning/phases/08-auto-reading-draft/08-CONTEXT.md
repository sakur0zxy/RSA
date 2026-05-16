# Phase 08: Auto Reading Draft - Context

**Gathered:** 2026-05-16  
**Status:** Ready for planning  
**Source:** `$gsd-discuss-phase 8` inline discussion, no subagents

<domain>
## Phase Boundary

Phase 8 delivers an automated single-paper reading draft workflow. It starts from formal `metadata/P###.yaml` plus a local, user-provided, or already authorized full-text source, extracts text locally, asks an LLM to produce a structured Chinese reading draft, runs an AI initial review, and generates a compact review packet for user supervision.

Phase 8 does not discover or download papers, does not run batch campaigns, does not score paper quality/relevance, does not crop figures, does not write formal records, and does not mark notes as `approved`.
</domain>

<decisions>
## Locked Decisions

### User-Facing Language
- User-facing text, CLI output, validation errors, templates, review packets, and repair guidance must be Chinese-first.
- YAML keys, CLI flags, status enum names, and code identifiers remain English and stable.
- Any English field intended for users must have nearby Chinese explanation.

### Entry Point
- Add `rsa note draft P###` as the main automated reading draft command.
- Keep `rsa note create` as the lower-level blank/structured note creation command.
- `rsa note draft` selects a source from `sources/P###.yaml` by default and accepts `--source-file <path>` as an explicit override.

### Source Selection
- Prefer `is_primary: true`, `status: available`, and `source_type: pdf`.
- If no primary source exists, choose an available PDF by version priority: `publisher_version`, `accepted_manuscript`, `repository_copy`, `arxiv_preprint`, then other available PDFs.
- Missing, unavailable, unauthorized, broken, encrypted, or empty sources must fail closed and write a Chinese blocked/partial status record.

### Overwrite Policy
- Existing reading notes are not overwritten by default.
- `--overwrite-draft` may overwrite only an existing `note_status: draft` note.
- `ready_for_review`, `approved`, or human-confirmed notes must not be overwritten automatically.

### Extraction And Cache
- Phase 8 introduces local PDF/text extraction and stores extracted text/chunk metadata under local-only `01_literature/extracted/P###/`.
- The reading note stores only short snippets, page/section/chunk references, and concise evidence summaries, not full extracted text.
- Cache and prompt packets must stay out of git.

### LLM Drafting
- `rsa note draft` reads non-sensitive LLM settings from project config and `.rsa/local.yaml`.
- Allowed LLM config fields include `provider`, `model`, `api_key_env`, `base_url`, `timeout_seconds`, `max_chunks`, `max_input_tokens`, `temperature`, `language`, and `prompt_profile`.
- API keys, cookies, refresh tokens, passwords, and institution credentials must never be written to tracked files, notes, prompt packets, or planning docs.
- LLM output must validate against a fixed schema. Invalid output fails closed and must not create a normal-looking note.

### Reading Draft Schema
- Frontmatter must include `paper_id`, `metadata`, `note_status`, `source_file`, `source_id`, `source_hash`, `extraction_status`, `evidence_level`, `llm_provider`, `llm_model`, `prompt_version`, `draft_created_at`, `prompt_packet`, `review_packet`, and human-review fields.
- Structured Chinese sections must include `research_problem_zh`, `method_summary_zh`, `experiment_summary_zh`, `dataset_or_scene_zh`, `metrics_zh`, `main_findings_zh`, `limitations_zh`, `topic_relevance_zh`, and `uncertain_points_zh`.
- `source_grounded_claims` must carry `claim_zh`, `evidence_page`, `evidence_section`, `source_chunk_id`, `evidence_snippet`, and `needs_human_check`.
- `short_quotes` must remain short and contain `quote`, `page`, `section`, and `reason_zh`.
- `asset_suggestions` are only candidate suggestions for later Phase 8.1 visual evidence work; they are not formal claims.

### AI Initial Review
- Phase 8 may automatically move a note to `ready_for_review` after AI initial review.
- `ready_for_review` means “AI has completed a structural/evidence/risk initial review and the user should supervise final acceptance.”
- It never means `approved`, `human_confirmed`, paper quality approval, or formal write permission.
- Add `agent_review_status`, `agent_reviewed_at`, `agent_review_score_10`, `agent_review_grade`, `agent_review_rationale_zh`, `score_breakdown`, `agent_review_warnings`, `recommended_human_action_zh`, and `needs_human_review: true`.

### Review Score Gate
- `agent_review_score_10` is a 10-point readiness score for the reading note itself, not a paper-quality or relevance score.
- Rubric: structure completeness 2, evidence grounding 3, risk/uncertainty disclosure 2, short quote compliance 1, source/cache/packet links 1, Chinese readability and checklist clarity 1.
- `agent_review_score_10 >= 6` is required for `ready_for_review`, but hard gates must also pass.
- Hard gates: source not blocked, extraction usable, schema valid, no severe ungrounded claims, no long quotes, and no sensitive/fulltext leakage.

### Review Packet
- Generate `01_literature/notes/P###_review_packet.md` as a Chinese supervision entry point.
- The packet must link to metadata, reading note, source ledger, PDF/status records, extracted cache, prompt packet, asset suggestions, and the expected Phase 8.1 visual output location.
- The packet is staging/review material only and must not write formal map/research notes.

### Phase 8.1 And Phase 9 Handoff
- Phase 8 outputs candidate `asset_suggestions`; Phase 8.1 handles visual evidence candidate extraction.
- Phase 9 consumes reading notes, review packets, text evidence, and later visual evidence to perform AI-assisted scoring.
- Phase 8 must not produce `ai_quality_score`, `ai_relevance_score`, or `ai_read_priority_score`.
</decisions>

<canonical_refs>
## Canonical References

Downstream planning and implementation must read:

- `.planning/PROJECT.md` - v2 phase chain and Chinese-first project positioning.
- `.planning/REQUIREMENTS.md` - v2 reading, visual, scoring, dependency, and language requirements.
- `.planning/DEPENDENCY-POLICY.md` - base/runtime/optional/external dependency rules and fail-closed behavior.
- `.planning/phases/04-reading-note-workflow/04-CONTEXT.md` - original reading note formal-write boundaries.
- `.planning/phases/06-asset-source-foundation/06-CONTEXT.md` - local asset/source ledger boundaries.
- `.planning/phases/07-authorized-acquisition/07-CONTEXT.md` - authorized acquisition rules.
- `.planning/phases/07.1-browser-session-provider/07.1-CONTEXT.md` - browser session source rules.
- `.planning/phases/08-auto-reading-draft/08-DISCUSSION-WIP.md` - full interactive discussion scratchpad.
</canonical_refs>

<specifics>
## Implementation Notes

- Add base dependency support for PDF parsing while keeping deterministic fallback behavior for tests.
- Add local-only extracted cache directory and gitignore rules.
- Add a mock/deterministic LLM provider for local tests, plus fail-closed handling for unsupported or unconfigured real providers.
- Prefer preserving existing Markdown/YAML patterns and current argparse CLI style.
- Keep `formal apply-note` unchanged in spirit: only `approved + human_confirmed` can affect formal records.
</specifics>

<deferred>
## Deferred Ideas

- Advanced figure intelligence: curve data extraction, table structure reconstruction, numeric value recovery, and visual-question answering.
- AI paper quality/relevance/read-priority scoring, handled in Phase 9.
- Batch campaigns and review queues, handled in Phase 11.
- Local review UI/workspace, handled in Phase 12.
- Claim-level citation hardening, handled in Phase 13.
</deferred>

---

*Phase: 08-auto-reading-draft*  
*Context gathered: 2026-05-16 via inline GSD discussion*
