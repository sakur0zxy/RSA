# Phase 1: Harness Foundation - Research

**Researched:** 2026-05-11
**Domain:** Local-first Python CLI harness for research records
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Formal research records default to `01_literature/`, read from runtime settings rather than hard-coded.
- Use `rsa.yaml` for project defaults and `.rsa/local.yaml` for user-local overrides.
- Create the full literature foundation: `metadata/`, `topic_profiles/`, `agent_outputs/`, `notes/`, `synthesis/`, `pdfs/`, `assets/`, `paper_index.md`, `literature_map.md`, `research_tables.md`, and `agent_research_notes.md`.
- Templates live in project-root `templates/`.
- Topic profiles use a generic schema; SAR is only the first starter profile instance.
- Required topic profile fields: `topic_id`, `topic_name`, `core_keywords`, `priority_questions`, `important_metrics`, `preferred_sources`, `exclude_scope`, `grade_rules`, `required_outputs`.
- `grade_rules` evaluate candidate paper priority.
- Round archives use `R001_short_topic_name`.
- Each round archive requires `README.md` and `final_round_summary.md`.
- Round default max candidates is 5, with per-round override and hard cap 20.
- PDFs live under `01_literature/pdfs/`; assets live under `01_literature/assets/P001/`-style folders; both are local-only and ignored by git.
- Human confirmation is required before formal-record writes.
- Phase 1 builds a minimal runnable CLI and does not perform real search, PDF acquisition, metadata verification, mapping, reading, or LLM calls.
- Use a single `rsa` command with subcommands such as `rsa init`, `rsa validate-profile`, and `rsa new-round`.

### the agent's Discretion
- Exact YAML formatting and validation library choice are open if no heavyweight dependency is introduced without need.
- Exact template wording is open if evidence hierarchy and human review rules are preserved.
- Exact `.gitignore` patterns are open if local-only files remain untracked.

### Deferred Ideas (OUT OF SCOPE)
- Full campaign/batch orchestration for large-scale literature review.
- Real search, metadata verification, literature mapping, reading notes, PDF workflow, and LLM-backed agent behavior.
- Web UI, citation-manager sync, and large batch processing.
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

Single-tier local CLI application — all Phase 1 capabilities reside in local filesystem + Python CLI.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Settings loading | Local CLI | Filesystem | Reads project defaults and local overrides from YAML files. |
| Directory creation | Local CLI | Filesystem | Creates deterministic project folders and placeholder Markdown files. |
| Topic profile validation | Local CLI | Filesystem | Parses YAML and validates required schema fields before later workflows use profiles. |
| Round initialization | Local CLI | Filesystem | Creates bounded round archive directories and required placeholder files. |
| Local-only asset protection | Filesystem | Git config | `.gitignore` prevents PDFs/assets/local settings from entering commits. |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 1 should be implemented as a small Python package with a single `rsa` console entry point. Use the standard-library `argparse` module for subcommands because Phase 1 command needs are simple and Python documents `argparse` as the default standard library CLI parser. Use PyYAML for YAML parsing, because Python has no standard-library YAML parser and this project explicitly uses `rsa.yaml` and topic profile YAML files.

The implementation should prioritize deterministic filesystem behavior over clever abstractions. Commands should be idempotent where possible: `rsa init` should create missing directories/files without destroying user edits; `rsa validate-profile` should report all missing/invalid fields; `rsa new-round` should refuse invalid names, cap candidate counts, and create the two required round files.

**Primary recommendation:** Build a minimal Python package using `argparse`, `pathlib`, and PyYAML `safe_load`, with focused tests around config merge, profile validation, init idempotence, local-only gitignore rules, and round creation.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.x in local environment | Runtime | Already available locally; good fit for file-based research tooling. |
| argparse | stdlib | CLI subcommands | Built into Python and adequate for `init`, `validate-profile`, and `new-round`. |
| pathlib | stdlib | Cross-platform paths | Safer than string paths on Windows and supports `Path` operations. |
| PyYAML | >=6.0.3 | YAML parse/write | PyPI has a recent release with Python 3.14 wheels; use `safe_load`. |
| pytest | latest compatible | Tests | Common, lightweight Python test runner. |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| dataclasses | Structured config/profile objects | Keep schema validation explicit without extra modeling dependency. |
| re | Slug and round-name validation | Validate `R001_short_topic_name` and safe folder names. |
| shutil/tempfile | Test fixtures and smoke runs | Keep filesystem tests isolated. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse | Click/Typer | Better UX later, but unnecessary dependency for Phase 1. |
| PyYAML | Hand-rolled parser | Avoids dependency but risks incorrect YAML behavior and unsafe edge cases. |
| pytest | unittest | `unittest` is stdlib, but pytest gives clearer fixtures and faster iteration. |

**Installation:**
```powershell
python -m pip install -e ".[dev]"
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### System Architecture Diagram

```text
User command
  -> argparse subcommand router
  -> config loader (rsa.yaml + .rsa/local.yaml)
  -> path resolver (literature_root, templates_root, local-only paths)
  -> command handler
       -> init: create skeleton and placeholder files
       -> validate-profile: parse YAML and report schema errors
       -> new-round: validate topic/round name/candidate cap and create archive
  -> terminal summary + exit code
```

### Recommended Project Structure
```text
pyproject.toml
rsa.yaml
.gitignore
src/
  rsa_cli/
    __init__.py
    cli.py
    config.py
    profiles.py
    rounds.py
    skeleton.py
    templates.py
templates/
  paper_metadata.yaml
  paper_note.md
  round_readme.md
  final_round_summary.md
tests/
  test_config.py
  test_profiles.py
  test_skeleton.py
  test_rounds.py
```

### Pattern 1: Config Merge
**What:** Load project defaults first, then overlay local settings recursively.
**When to use:** Any command needing `literature_root`, round limits, templates, or local preferences.

### Pattern 2: Schema Validation
**What:** Validate required fields and basic types with explicit code, returning a list of actionable errors.
**When to use:** `rsa validate-profile` and `rsa new-round --topic`.

### Pattern 3: Idempotent File Creation
**What:** Create missing directories/files; do not overwrite existing user-edited files unless a future explicit `--force` option is added.
**When to use:** `rsa init` and `rsa new-round`.

### Anti-Patterns to Avoid
- **Hard-coded `01_literature/`:** Violates the configuration decision.
- **Using `yaml.load`:** Unsafe for untrusted input; use `safe_load`.
- **Overwriting formal records:** `rsa init` should not replace edited Markdown/YAML files.
- **Implementing search in Phase 1:** Out of scope and would blur Phase 2/3 responsibilities.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | PyYAML `safe_load` | YAML edge cases and safety are easy to get wrong. |
| CLI parser | Manual `sys.argv` parsing | argparse | Subcommands, help text, and exit codes are solved. |
| Test temp dirs | Manual cleanup paths | pytest `tmp_path` | Safer tests on Windows. |

**Key insight:** The harness should be boring and auditable. Dependencies are acceptable when they remove parser/security footguns, but avoid framework-like dependencies until the CLI grows beyond Phase 1.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Local Assets Accidentally Tracked
**What goes wrong:** PDFs or screenshots enter git history.
**Why it happens:** `.gitignore` misses `01_literature/pdfs/`, `01_literature/assets/`, or `.rsa/local.yaml`.
**How to avoid:** Add ignore rules in Phase 1 and verify with `git status --ignored`.
**Warning signs:** `git status` shows PDFs/assets under untracked files.

### Pitfall 2: Config Override Ambiguity
**What goes wrong:** User cannot predict whether project or local setting wins.
**Why it happens:** Merge order not documented or tested.
**How to avoid:** Project defaults load first; local overrides win; document this in `rsa.yaml` comments or docs.
**Warning signs:** Same setting behaves differently across commands.

### Pitfall 3: Profile Schema Too Loose
**What goes wrong:** Later phases assume fields exist, but starter profiles are incomplete.
**Why it happens:** Validation only checks parseability.
**How to avoid:** Validate all required fields and list all missing fields at once.
**Warning signs:** `new-round` can run with a topic profile that lacks `priority_questions` or `grade_rules`.

### Pitfall 4: Phase 1 Scope Creep
**What goes wrong:** Planning expands into search, DOI verification, PDF processing, or LLM behavior.
**Why it happens:** The term "agent" pulls implementation toward full workflow automation.
**How to avoid:** Limit Phase 1 commands to config, init, validation, and round folder creation.
**Warning signs:** Plan tasks mention external APIs, model calls, or metadata verification.
</common_pitfalls>

<code_examples>
## Code Examples

### Safe YAML Loading
```python
from pathlib import Path
import yaml

def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}
```

### argparse Subcommands
```python
import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rsa")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init")
    subcommands.add_parser("validate-profile")
    subcommands.add_parser("new-round")
    return parser
```

### Idempotent File Creation
```python
def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True
```
</code_examples>

<sota_updates>
## State of the Art (2024-2026)

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `yaml.load` for convenience | `yaml.safe_load` | Prevents unsafe object construction from YAML input. |
| Heavy CLI frameworks for small tools | stdlib `argparse` first | Keeps Phase 1 dependency surface small. |
| One huge literature run | Bounded rounds plus future campaign grouping | Preserves evidence traceability and human review. |

**New tools/patterns to consider later:**
- Typer/Rich for nicer CLI once command surface grows.
- OpenAI Agents SDK only when LLM/tool orchestration begins in later phases.

**Deprecated/outdated:**
- Treating agent outputs as a source of truth; this project explicitly separates auxiliary outputs from formal records.
</sota_updates>

<validation_architecture>
## Validation Architecture

Phase 1 should use pytest as the execution-time feedback loop.

| Validation Target | Automated Test |
|-------------------|----------------|
| Config merge | Project defaults load, local overrides win, missing local file is tolerated. |
| Skeleton creation | `rsa init` creates all required directories/files and is idempotent. |
| Topic profile validation | Complete SAR profile passes; incomplete profile reports all missing fields. |
| Round creation | `rsa new-round` creates `R001_short_topic_name`, caps candidate count, and writes required files. |
| Local-only assets | `.gitignore` includes `.rsa/local.yaml`, `01_literature/pdfs/`, and `01_literature/assets/`. |
| CLI smoke | `rsa --help`, `rsa init`, `rsa validate-profile`, and `rsa new-round` return expected exit codes. |
</validation_architecture>

<open_questions>
## Open Questions

1. **Package name and console script name**
   - What we know: User chose `rsa` CLI.
   - What's unclear: Python distribution name can be `rsa-research-agent` or similar to avoid collision with existing `rsa` package if published.
   - Recommendation: Use local package module `rsa_cli` with console script `rsa`; publishing is out of scope.

2. **YAML writing style**
   - What we know: Config and profile files are YAML.
   - What's unclear: Whether comments should be preserved on future writes.
   - Recommendation: Phase 1 should generate initial YAML files but avoid rewriting user-edited YAML except when explicitly asked.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Python 3.14 argparse docs — stdlib CLI parser and subcommands: https://docs.python.org/3.14/library/argparse.html
- PyYAML documentation — warns against unsafe `yaml.load` and points to `safe_load`: https://pyyaml.org/wiki/PyYAMLDocumentation
- PyYAML PyPI — current package release includes Python 3.14 wheels: https://pypi.org/pypi/PyYAML

### Project Sources (HIGH confidence)
- `.planning/phases/01-harness-foundation/01-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/agent_literature_workflow_plan.md`
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Python CLI, YAML config, local filesystem harness.
- Ecosystem: argparse, pathlib, PyYAML, pytest.
- Patterns: Config merge, schema validation, idempotent file creation, local-only asset protection.
- Pitfalls: unsafe YAML loading, git-tracked assets, over-loose schema, Phase 1 scope creep.

**Confidence breakdown:**
- Standard stack: HIGH - Python and PyYAML are stable, and local environment has Python 3.14.
- Architecture: HIGH - project is greenfield and scope is narrow.
- Pitfalls: HIGH - directly derived from CONTEXT.md and common CLI/YAML risks.
- Code examples: MEDIUM - examples are representative patterns to implement, not copied from official docs.

**Research date:** 2026-05-11
**Valid until:** 2026-06-10
</metadata>

---

*Phase: 01-harness-foundation*
*Research completed: 2026-05-11*
*Ready for planning: yes*
