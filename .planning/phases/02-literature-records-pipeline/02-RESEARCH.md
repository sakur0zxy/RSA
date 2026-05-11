---
phase: 02
slug: literature-records-pipeline
status: complete
created: 2026-05-11
mode: inline-fallback
---

# Phase 02 Research: Literature Records Pipeline

## RESEARCH COMPLETE

## Scope Reading

Phase 2 should turn Phase 1's skeleton into a metadata-first literature record pipeline. The phase is bounded to local Markdown/YAML records and CLI checks:

- formal paper records under `01_literature/metadata/`
- human-readable index at `01_literature/paper_index.md`
- per-round candidate review in `verification_review.md`
- no real search adapters, PDF download automation, reading notes, topic map writes, or LLM orchestration

The older literature workflow confirms the same shape: `metadata/` is the source of truth, `paper_index.md` is for browsing, candidates are checked by a verification review step, and formal records outrank `agent_outputs/`.

## Existing Implementation Surface

### Reusable code

- `src/rsa_cli/config.py` already centralizes project paths and can grow `metadata_root`, `paper_index_path`, `assets_root`, and `pdfs_root` accessors.
- `src/rsa_cli/cli.py` already uses `argparse`, explicit subcommands, concise expected errors, and nonzero exit codes.
- `src/rsa_cli/templates.py` and root `templates/` already support template defaults with project-level overrides.
- `src/rsa_cli/skeleton.py` already creates `metadata/`, `paper_index.md`, `agent_outputs/`, `pdfs/`, and `assets/`.

### Current gaps

- `paper_metadata.yaml` is too small and has no Chinese field explanations.
- `paper_index.md` is a placeholder and is not generated from metadata.
- No module validates metadata schema or human confirmation.
- No command writes formal `metadata/P###.yaml`.
- No command validates or regenerates `paper_index.md`.
- `verification_review.md` does not match the Phase 2 lightweight evidence fields or Chinese user-facing requirements.

## Recommended Architecture

### 1. Metadata module

Create `src/rsa_cli/metadata.py` with:

- `METADATA_FIELDS`: ordered standard field list from CONTEXT D-10.
- `FIELD_DESCRIPTIONS_ZH`: Chinese explanations for every English YAML key.
- `MetadataError`: expected CLI-safe error type.
- `load_metadata_record(path) -> dict`
- `validate_metadata_record(path) -> list[str]`
- `next_paper_id(metadata_root) -> str`
- `write_metadata_record(config, values, human_confirmed, confirmed_by, confirmed_at) -> Path`

Validation should be strict enough to protect formal records:

- filename must match `P###.yaml`
- `paper_id` must match filename stem
- `verification_status` must be `verified`
- `human_confirmed` must be `true`
- `confirmed_by` and `confirmed_at` required when `human_confirmed` is true
- identity/source minimum: `title`, `authors`, `year`, `venue`, and either `doi` or `official_url`
- require `source_reliability`, `decision`, `decision_reason`, `last_checked`, `pdf_status`
- `authors`, `assets`, `priority_questions`, `used_for`, and `research_roles` must be lists

### 2. Index module

Create `src/rsa_cli/index.py` with:

- `render_paper_index(records) -> str`
- `generate_paper_index(config) -> str`
- `validate_paper_index(config) -> list[str]`
- `write_paper_index(config) -> Path`

The index is derived from metadata and should not be treated as a second fact source. Sort by `paper_id` ascending and render concise columns:

`paper_id`, `year`, `title`, `venue`, `decision`, `used_for`, `pdf_status`

User-facing output should be Chinese. Keep English field names in a field reference section so the user can map table content back to YAML keys.

### 3. Candidate review templates

Update `templates/verification_review.md` and `TEMPLATE_FILES["verification_review.md"]` to use the Phase 2 lightweight review table:

- `candidate_title`
- `source`
- `doi_or_url`
- `decision`
- `reason`
- `last_checked`

Allowed `decision` values: `verified`, `rejected`, `uncertain`.

The template should clearly state in Chinese that `verified` means source verification passed and does not automatically write formal metadata.

### 4. CLI commands

Add Phase 2 subcommands without changing existing Phase 1 commands:

- `rsa validate-metadata <path>`
- `rsa add-paper --title ... --author ... --year ... --venue ... --doi ... --official-url ... --source-reliability ... --decision ... --decision-reason ... --last-checked ... --pdf-status ... --used-for ... --research-role ... --topic-profile ... --priority-question ... --asset ... --local-pdf ... --notes ... --human-confirmed --confirmed-by ... [--confirmed-at ...]`
- `rsa validate-index`
- `rsa regenerate-index`

`add-paper` should fail before writing if `--human-confirmed` or `--confirmed-by` is missing. It should allocate the next `P###` only after validation passes, then write `metadata/P###.yaml`, create `assets/P###/.gitkeep`, and report a Chinese success message with the English ID.

`validate-index` should never modify files. If mismatches exist, it reports them and tells the user to run `rsa regenerate-index`.

### 5. Tests

Add focused tests:

- metadata template includes all required keys and Chinese field explanations
- valid metadata passes validation
- missing identity/source/human confirmation fields produce actionable errors
- `add-paper` refuses to write without `--human-confirmed`
- `add-paper` writes `P001.yaml`, then `P002.yaml`, with matching `paper_id`
- rejected/uncertain candidates do not consume `P###`
- `paper_index.md` generation sorts by `paper_id`
- `validate-index` detects stale or manually edited index without modifying it
- `regenerate-index` rewrites index from metadata
- CLI expected errors have no traceback

## Plan Slicing

Roadmap's 3 plans are still the right execution structure:

1. `02-01`: metadata schema, metadata validation, ID allocation, formal add-paper command.
2. `02-02`: candidate review template and review-output constraints.
3. `02-03`: index generation, index validation, regenerate command, consistency tests.

Dependencies:

- `02-02` can run after `02-01` or in parallel if it only touches templates/tests.
- `02-03` depends on `02-01` because it reads valid metadata records.

## Threat Model Notes

- **T-02-01 Unconfirmed formal write:** agent or user accidentally writes formal metadata without explicit human confirmation. Mitigation: `add-paper` requires `--human-confirmed` and `--confirmed-by`; validator rejects `human_confirmed: false`.
- **T-02-02 ID drift:** failed writes consume or skip `P###`, breaking asset references. Mitigation: allocate ID only after validation inputs pass and write atomically to `metadata/P###.yaml`.
- **T-02-03 Index as false source:** manual edits make `paper_index.md` disagree with metadata. Mitigation: validate-index fails on mismatch and regenerate-index is explicit.
- **T-02-04 User-facing ambiguity:** English field names confuse review. Mitigation: every template/help page with English keys includes Chinese field descriptions.

## Validation Architecture

Use existing pytest infrastructure. No new test framework is needed.

Quick command: `python -m pytest tests/test_metadata.py tests/test_index.py tests/test_cli.py -q`

Full command: `python -m pytest -q`

Required automated coverage:

- `META-01`: metadata schema validation and formal write command tests.
- `META-02`: paper index generation and validation tests.
- `META-03`: DOI/official URL/source reliability/PDF status/local path/last_checked fields required or checked.
- `SRCH-01`: candidate review template stays outside formal metadata and does not allocate IDs.
- `SRCH-02`: review template supports `verified`, `rejected`, `uncertain`, with reason and source evidence fields.

Nyquist sampling should run quick tests after each task commit and full pytest after each plan wave. All Phase 2 behavior can be verified automatically; no manual-only checks are required beyond human approval semantics being represented by CLI flags and metadata fields.

