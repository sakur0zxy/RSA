# Phase 08 Verification: Auto Reading Draft

**Date:** 2026-05-16  
**Verdict:** PASS  
**Execution mode:** Inline, no subagents

## Goal-Backward Verification

Phase 8 promised an automated single-paper reading draft workflow based on formal metadata plus local/user-provided/authorized full text.

Implemented:

- `rsa note draft P###` selects a source from source ledger or explicit `--source-file`.
- Local extraction cache is written under `01_literature/extracted/P###/`.
- Prompt packet is stored as a local-only, de-sensitized YAML summary.
- LLM-assisted draft generation supports deterministic `mock` provider for local testing and fail-closed real-provider configuration.
- Reading notes include structured Chinese fields, source-grounded claims, short quotes, uncertain points, and candidate `asset_suggestions`.
- AI initial review writes `agent_review_score_10`, score breakdown, warnings, and recommended human action.
- `ready_for_review` requires score threshold plus hard gates, and never sets `approved` or `human_confirmed: true`.
- Review packet links metadata, source, note, extraction cache, prompt packet, and Phase 8.1 visual target.

## Safety Verification

- Missing source, empty extraction, missing provider, unsupported provider, or schema failure blocks normal note generation.
- Existing `ready_for_review`, `approved`, or human-confirmed notes are not overwritten automatically.
- Full extracted text stays in local-only cache and is git-ignored.
- Formal write boundaries remain unchanged: `formal apply-note` still requires `approved` and human confirmation.
- Phase 8 does not produce paper quality, relevance, or read-priority scores.

## Tests

```powershell
python -m pytest tests/test_config.py tests/test_skeleton.py tests/test_notes.py tests/test_cli.py tests/test_templates.py -q
python -m pytest -q
```

Result:

- Targeted suite: `52 passed`.
- Full suite: `131 passed`.

## Residual Risks

- Real LLM provider behavior depends on user configuration and API compatibility; unsupported or missing configuration fails closed.
- `rsa doctor` remains a future global dependency task, although Phase 8 command-level fail-closed paths are implemented.
- PDF extraction quality depends on PDF text availability; scanned-image PDFs will require Phase 8.1 or later OCR work.

## Next Phase Readiness

Phase 8.1 can consume `asset_suggestions`, source files, extraction cache, and review packets to implement candidate visual evidence extraction.
