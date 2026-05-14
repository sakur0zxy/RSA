# Phase 6: Asset & Source Foundation - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** `gsd-discuss-phase` inline, no subagents, agent-selected decisions

<domain>

## Phase Boundary

Phase 6 establishes local asset and source-record foundations for v2. It covers registering user-provided/local/authorized source files, tracking local PDF copies, and tracking screenshots/figures/tables/results through auditable manifests.

This phase does **not** implement automatic network download, automatic reading, AI scoring, batch campaign queues, scholarly API lookup, review UI or multi-agent orchestration.

</domain>

<decisions>

## Implementation Decisions

### Source ledger

- **D-01:** Use per-paper YAML records at `01_literature/sources/P###.yaml`.
- **D-02:** Source records may copy a user-provided local file into `01_literature/pdfs/P###/`, but must not modify formal metadata automatically.
- **D-03:** Supported authorization values for Phase 6: `provided`, `local`, `authorized`, `open_access`, `user_authorized`.
- **D-04:** Missing or invalid source files must fail closed and leave no fake reading note.
- **D-05:** Source records must include Chinese-readable license/authorization explanation fields while keeping YAML keys English.

### Asset manifest

- **D-06:** Use per-paper asset manifests at `01_literature/assets/P###/manifest.yaml`.
- **D-07:** Binary assets remain local-only; manifests are auditable text records.
- **D-08:** Supported asset kinds: `figure`, `table`, `result`, `screenshot`, `supplement`, `other`.
- **D-09:** Adding an asset copies the file into `01_literature/assets/P###/` and appends an entry to `manifest.yaml`.
- **D-10:** Adding an asset must not directly edit `metadata/P###.yaml`; formal metadata remains protected by existing gates.

### CLI behavior

- **D-11:** Add `rsa source add|validate|status`.
- **D-12:** Add `rsa asset add|validate|status`.
- **D-13:** `validate` and `status` commands are read-only.
- **D-14:** User-facing CLI output and errors must be Chinese-first.

### the agent's Discretion

- Exact internal helper names, YAML ordering, filename sanitization and copy naming strategy.
- Whether `status` prints compact text or table-like text, as long as it is useful and testable.

</decisions>

<specifics>

## Specific Ideas

- Keep source/asset metadata in YAML so it is readable in git diffs.
- Keep actual PDF/images ignored by git.
- Use `paper_id` as the stable join key across source records, asset manifests and future reading/scoring phases.

</specifics>

<canonical_refs>

## Canonical References

### v2 scope

- `.planning/v2-DISCUSSION.md` - v2 source, asset, automatic reading and AI scoring direction.
- `.planning/REQUIREMENTS.md` - v2 requirements and Phase 6 requirement IDs.
- `.planning/ROADMAP.md` - Phase 6 boundary and future phase split.

### Existing implementation

- `src/rsa_cli/config.py` - project path configuration.
- `src/rsa_cli/skeleton.py` - initialized directory structure.
- `src/rsa_cli/metadata.py` - formal metadata validation and paper ID rules.
- `src/rsa_cli/notes.py` - existing authorization and PDF status behavior.
- `src/rsa_cli/cli.py` - argparse command style and Chinese-first output.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `ProjectConfig` already exposes `assets_root` and `pdfs_root`.
- `metadata.PAPER_ID_PATTERN` and `validate_metadata_record` can guard that source/asset commands only work for formal papers.
- `notes.record_pdf_status` can update `pdf_acquisition_report.md` when a source is registered.

### Established Patterns

- CLI subcommands use argparse groups with small `_run_*_command` dispatchers.
- YAML files are written with `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)`.
- `validate` commands are read-only and return a list of user-facing errors.

### Integration Points

- New source and asset commands should integrate with `cli.py`.
- Skeleton should create `01_literature/sources/` and templates for source/asset records.
- Tests should cover function behavior and CLI surface.

</code_context>

<deferred>

## Deferred Ideas

- Automatic download from web sources - Phase 7.
- Automatic PDF parsing and reading note drafts - Phase 8.
- Structured evidence extraction and AI scoring - Phase 9.
- Workflow orchestrator - Phase 10.
- Batch campaign queues - Phase 11.
- Local review UI - Phase 13.

</deferred>

---

*Phase: 06-asset-source-foundation*
*Context gathered: 2026-05-13*
