# Phase 4: Reading Note Workflow - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 adds a single-paper reading note workflow for already verified formal papers. It may create and validate structured reading notes from local, user-provided, or otherwise authorized full text. It may also route approved note-derived map or research-note requests through the existing formal-write guardrails.

This phase does not download PDFs, bypass publisher access controls, perform batch literature ingestion, write thesis prose, or treat agent summaries as final academic conclusions.
</domain>

<decisions>
## Implementation Decisions

### Authorized Input
- **D-01:** Reading notes require an existing formal `metadata/P###.yaml` record that passes metadata validation.
- **D-02:** A reading note can be created only when the user supplies an existing local `source_file` and labels it with `authorization` equal to `provided`, `local`, or `authorized`.
- **D-03:** If the source file is missing or not authorized, the command must record a status row in `pdf_acquisition_report.md` and must not create a fake reading note.

### Reading Note Schema
- **D-04:** Reading notes live under `01_literature/notes/P###_reading_note.md`.
- **D-05:** Each note uses YAML frontmatter with stable English keys and Chinese-readable Markdown body text.
- **D-06:** The note schema must distinguish `source_grounded_claims`, `short_quotes`, `agent_summary`, and `human_decision`.
- **D-07:** `short_quotes` are only short excerpts for auditability. Long copied passages are out of scope.

### Approval And Formal Influence
- **D-08:** Note status values are `draft`, `ready_for_review`, `approved`, and `blocked`.
- **D-09:** `approved` requires `human_confirmed: true`, non-empty `confirmed_by`, and non-empty `confirmed_at`.
- **D-10:** A reading note may contain `note_integration_requests`, but those requests are only suggestions until a formal command applies them.
- **D-11:** `rsa formal apply-note --source-note P### --human-confirmed --confirmed-by "name"` is the only Phase 4 path that lets a note affect `literature_map.md` or `agent_research_notes.md`.
- **D-12:** Formal note application must fail on malformed requests, missing metadata, invalid map rows, duplicate research-note IDs, or conflicts. It must not overwrite formal records.

### User-Facing Language
- **D-13:** User-facing templates, help text, validation errors, and generated reports must be Chinese-readable while field names, YAML keys, table columns, and CLI flags remain English.

### Phase 4 MUST NOT
- **D-14:** Phase 4 must not download unauthorized PDFs.
- **D-15:** Phase 4 must not infer detailed reading conclusions from missing or unavailable full text.
- **D-16:** Phase 4 must not mark notes approved without human confirmation fields.
- **D-17:** Phase 4 must not write map or research-note formal records except through explicit `formal apply-note`.
</decisions>

<specifics>
## Specific Ideas

- The user asked the agent to decide Phase 4 details without further prompts, so the recommended conservative defaults are locked.
- v1 does not introduce a PDF parser or LLM summarizer. The CLI creates a structured, auditable note shell and enforces authorization, schema, and approval boundaries.
- Approved note integration requests support:
  - `add_map_row` to append approved `literature_map.md` rows through the map validator.
  - `add_research_note` to append approved rows to `agent_research_notes.md`.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` - project identity, local-first constraints, evidence hierarchy.
- `.planning/REQUIREMENTS.md` - `NOTE-01` and `NOTE-02`.
- `.planning/ROADMAP.md` - Phase 4 goal and success criteria.
- `.planning/STATE.md` - current phase position.
- `AGENTS.md` - project-local workflow and evidence rules.

### Prior Phase Decisions
- `.planning/phases/01-harness-foundation/01-CONTEXT.md` - local directory, PDF and asset policy.
- `.planning/phases/02-literature-records-pipeline/02-CONTEXT.md` - metadata gate and Chinese user-facing requirement.
- `.planning/phases/03-research-round-integration/03-CONTEXT.md` - formal-write guardrails and map/gap rules.
- `.planning/phases/03-research-round-integration/03-03-SUMMARY.md` - existing formal map writer.

### Existing Harness Code
- `src/rsa_cli/config.py` - project paths.
- `src/rsa_cli/cli.py` - argparse command style.
- `src/rsa_cli/metadata.py` - formal metadata validation.
- `src/rsa_cli/formal.py` - formal write confirmation pattern.
- `src/rsa_cli/map.py` - map parser, renderer, and validation.
- `src/rsa_cli/templates.py` - root and fallback templates.
- `templates/paper_note.md` - reading note seed template.
- `templates/pdf_acquisition_report.md` - blocked source status report.
</canonical_refs>

<code_context>
## Existing Code Insights

- The formal metadata writer already enforces `verified + human_confirmed`, so Phase 4 should reuse `validate_metadata_record` instead of trusting free-form paper IDs.
- `formal.apply_map_requests` already shows the all-or-nothing write pattern for formal Markdown records.
- `map.MapRow` and `validate_map_rows` should be reused for note-derived map rows.
- `TEMPLATE_FILES` mirrors root templates, so user-facing template changes must be made in both places.
</code_context>

<deferred>
## Deferred Ideas

- PDF text extraction and automatic summarization are deferred until the harness has dedicated evals for source-grounded note quality.
- Batch reading workflows remain v2 or later.
- Citation manager sync and Web UI remain v2.
</deferred>

---

*Phase: 04-reading-note-workflow*
*Context gathered: 2026-05-12*
