# Phase 08 Discussion Log

**Date:** 2026-05-16  
**Mode:** Inline `$gsd-discuss-phase 8`, no subagents  
**Outcome:** Context captured and ready for planning

## Decisions Captured

- `rsa note draft P###` is the Phase 8 automated reading draft entry point.
- Phase 8 reads formal metadata plus local/user-provided/authorized full text only.
- Source selection defaults to source ledger priority and can be overridden with `--source-file`.
- Existing notes are protected; only draft notes can be overwritten with `--overwrite-draft`.
- Local extraction cache lives under `01_literature/extracted/P###/` and stays out of git.
- LLM-assisted drafting is required for semantic reading summaries, with fail-closed schema validation.
- User-facing content remains Chinese-first while field names and parameters remain English.
- AI initial review can move a note to `ready_for_review`, but never to `approved`.
- `agent_review_score_10` rates reading-note readiness only; 6+ plus hard gates is required for `ready_for_review`.
- Review packet links related records for user supervision and remains staging-only.
- Phase 8 only emits candidate `asset_suggestions`; Phase 8.1 handles visual evidence extraction.
- Phase 9 handles quality/relevance/priority scoring; Phase 8 does not score papers.

## Key Boundaries

- No automatic formal writes.
- No automatic paper-quality or academic-value judgment.
- No long copyrighted text copied into tracked notes.
- No API keys, cookies, account credentials, or full prompts/responses in tracked files.
- No automatic PDF downloading or browser-session work inside Phase 8.

## Planning Handoff

Planning should produce implementation work for:

- Source selection, extraction cache, prompt packet, and dependency/config gates.
- LLM-assisted structured reading draft generation, AI initial review, and review packet creation.
- CLI integration, templates, tests, docs, and verification summaries.
