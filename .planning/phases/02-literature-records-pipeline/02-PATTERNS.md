# Phase 02 Pattern Map: Literature Records Pipeline

**Generated:** 2026-05-11
**Mode:** inline fallback after subagent timeout

## Files to Create or Modify

| Target | Role | Closest Existing Analog | Pattern to Reuse |
|--------|------|-------------------------|------------------|
| `src/rsa_cli/metadata.py` | Formal metadata schema, validation, ID allocation, write gate | `src/rsa_cli/profiles.py`, `src/rsa_cli/config.py` | Return aggregated validation errors; use `yaml.safe_load`; raise expected error classes for CLI-safe failures |
| `src/rsa_cli/index.py` | Generate/validate/regenerate `paper_index.md` from metadata | `src/rsa_cli/templates.py`, `src/rsa_cli/skeleton.py` | Deterministic Markdown rendering; write only through explicit command |
| `src/rsa_cli/cli.py` | Add `validate-metadata`, `add-paper`, `validate-index`, `regenerate-index` | Existing `init`, `validate-profile`, `new-round` commands | Argparse subcommands; concise stdout/stderr; nonzero return codes without tracebacks |
| `src/rsa_cli/config.py` | Add metadata/index/assets path accessors | Existing `literature_root`, `agent_outputs_root` accessors | Resolve relative paths from project root |
| `src/rsa_cli/templates.py` | Expand metadata/review/index templates with Chinese explanations | Existing `TEMPLATE_FILES` and `FORMAL_RECORD_FILES` | Default string constants mirrored into root `templates/` by skeleton |
| `templates/paper_metadata.yaml` | User-facing metadata template | Existing minimal template | English YAML keys plus Chinese comments/explanation nearby |
| `templates/verification_review.md` | Candidate review staging table | Existing minimal template | Markdown table with English field names and Chinese field guide |
| `01_literature/paper_index.md` | Generated human-readable index | Existing formal record seed file | Chinese prose/table generated from metadata |
| `tests/test_metadata.py` | Metadata validation and write-gate tests | `tests/test_profiles.py`, `tests/test_rounds.py` | Temp-project fixtures, aggregated errors, no formal writes on failure |
| `tests/test_index.py` | Index generation/validation tests | `tests/test_skeleton.py`, `tests/test_cli.py` | Deterministic content checks and stale-file mismatch tests |
| `tests/test_templates.py` | Chinese field explanation and review template tests | `tests/test_skeleton.py` | Read root templates and assert required strings |
| `tests/test_cli.py` | CLI command coverage | Existing CLI tests | `main([...])`, capsys, temp directories, no traceback assertions |
| `templates/topic_profile.yaml` | Phase 1 topic template localization | Existing topic template | Preserve English keys; add Chinese field guide/comments |
| `templates/round_readme.md` | Round archive README localization | Existing round template placeholders | Preserve `{round_id}` and other format placeholders |
| `templates/final_round_summary.md` | Round summary localization | Existing summary headings | Chinese headings; preserve human confirmation section |
| `templates/paper_note.md` | Paper-note seed localization | Existing note template | Chinese guidance only; no Phase 4 reading behavior |
| `templates/map_integration.md` | Map-integration seed localization | Existing map template | Chinese guidance only; no Phase 3 map writer behavior |
| `templates/pdf_acquisition_report.md` | PDF status report localization | Existing PDF report template | Chinese copyright/authorization warning; no download automation |
| `templates/reading_batch_report.md` | Reading batch report localization | Existing reading report template | Chinese guidance only; no reading-note generator |
| `01_literature/literature_map.md` | Formal map seed localization | Existing formal record seed | Chinese placeholder explaining Phase 3 will own updates |
| `01_literature/research_tables.md` | Research tables seed localization | Existing formal record seed | Chinese placeholder for human-reviewed tables |
| `01_literature/agent_research_notes.md` | Agent notes seed localization | Existing formal record seed | Chinese auxiliary-status warning |

## Data Flow

1. Candidate evidence is staged in `agent_outputs/R###_.../verification_review.md`.
2. A `verified` candidate remains a suggestion until the user runs a formal write command with explicit human confirmation.
3. `add-paper` validates inputs, allocates the next available `P###`, writes `metadata/P###.yaml`, and creates `assets/P###/.gitkeep`.
4. `regenerate-index` reads all valid metadata records and rewrites `paper_index.md`.
5. `validate-index` reads metadata and `paper_index.md`, reports mismatches, and never writes files.

## Code Excerpts to Follow

### CLI expected-error style

`src/rsa_cli/cli.py` uses:

```python
except ConfigError as exc:
    print(f"Configuration error: {exc}", file=sys.stderr)
    return 2
```

Phase 2 should add `MetadataError` / `IndexError` handling in the same style.

### Validation returns all actionable errors

`src/rsa_cli/profiles.py` pattern should be reused for metadata validation: collect every missing or malformed field in one pass and print all errors in CLI output.

### Path accessors

`ProjectConfig` already exposes path properties. Add:

```python
metadata_root = literature_root / "metadata"
paper_index_path = literature_root / "paper_index.md"
assets_root = literature_root / "assets"
pdfs_root = literature_root / "pdfs"
```

## Planning Constraints

- Keep YAML keys and CLI argument names in English.
- User-facing Markdown, CLI help, success messages, and error messages must include Chinese explanations.
- Do not allocate or write `P###` for `rejected` or `uncertain` candidates.
- Do not modify `paper_index.md` during validation; only `regenerate-index` may rewrite it.
- Do not add external dependencies unless a standard-library/PyYAML solution is insufficient.
- Localize remaining Phase 1 user-facing templates and seed files without introducing Phase 3/4 behavior.
