---
phase: 01-harness-foundation
plan: 01
subsystem: cli-foundation
tags: [python, argparse, yaml, filesystem, pytest]

requires: []
provides:
  - Configurable Python CLI package with rsa init
  - Literature directory foundation and root templates
  - SAR starter profile stored as data, not Python logic
  - Local-only gitignore rules for settings, PDFs, and assets
affects: [phase-01, phase-02, topic-profiles, research-rounds]

tech-stack:
  added: [PyYAML, pytest, setuptools]
  patterns: [safe-yaml-load, recursive-config-merge, idempotent-file-creation, package-data-profiles]

key-files:
  created:
    - pyproject.toml
    - rsa.yaml
    - src/rsa_cli/config.py
    - src/rsa_cli/cli.py
    - src/rsa_cli/skeleton.py
    - src/rsa_cli/templates.py
    - src/rsa_cli/data/topic_profiles/sar_noncontinuous_aperture.yaml
    - templates/topic_profile.yaml
    - 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml
    - tests/test_config.py
    - tests/test_skeleton.py
  modified: []

key-decisions:
  - "Use PyYAML safe_load for all project YAML reads."
  - "Keep SAR starter profile content in YAML package data and project data, not Python profile-specific branches."
  - "Create skeleton files with write-if-missing behavior so edited formal records are not overwritten."

patterns-established:
  - "Config merge: built-in defaults -> committed project defaults -> optional user-local overrides, with local overrides winning."
  - "Filesystem writes are idempotent and leave user-edited Markdown/YAML files intact."
  - "PDF and screenshot payloads are local-only by default; .gitkeep files keep the folders visible."

requirements-completed: [DOCS-01, PROF-01]

duration: 26 min
completed: 2026-05-11
---

# Phase 01 Plan 01: Project Scaffold and Literature Foundation Summary

**Python CLI scaffold with safe YAML config, idempotent literature directories, root templates, and a data-backed SAR starter profile**

## Performance

- **Duration:** 26 min
- **Started:** 2026-05-11T15:32:50+08:00
- **Completed:** 2026-05-11T15:58:41+08:00
- **Tasks:** 3
- **Files modified:** 37

## Accomplishments

- Added the `rsa-research-agent` Python package with the `rsa` console script and `rsa init` command.
- Added safe project configuration loading from committed project defaults plus optional user-local overrides, with recursive local overrides.
- Created the full `01_literature/` foundation, root templates, local-only ignore rules, and SAR starter profile.
- Moved starter profile content into package/project YAML data so the Python harness remains topic-generic.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create package scaffold and config loader** - `c02229b` (`feat(01-01)`)
2. **Task 2: Create idempotent literature skeleton and template files** - `b8c23e4` (`feat(01-01)`)
3. **Task 3: Add generic topic template and SAR starter profile** - `71145d9` (`feat(01-01)`)

## Files Created/Modified

- `pyproject.toml` - package metadata, dependencies, console script, pytest config, package data.
- `rsa.yaml` - committed project defaults for literature root, template root, profile root, and round limits.
- `src/rsa_cli/config.py` - safe YAML loading, recursive merge, path resolution, and round limit validation.
- `src/rsa_cli/cli.py` - argparse entry point with `rsa init`.
- `src/rsa_cli/skeleton.py` - idempotent literature foundation creation.
- `src/rsa_cli/templates.py` - generic template and formal record seed content.
- `src/rsa_cli/data/topic_profiles/sar_noncontinuous_aperture.yaml` - built-in SAR starter profile data.
- `templates/` - root template files for topic, metadata, notes, and round artifacts.
- `01_literature/` - formal literature foundation and starter profile.
- `tests/test_config.py` and `tests/test_skeleton.py` - config, init, idempotence, ignore-rule, and starter profile tests.

## Decisions Made

- PyYAML is the only YAML parser and `yaml.safe_load` is used for config reads.
- Starter profiles are loaded from package data to keep Python code generic.
- `rsa init` uses write-if-missing behavior and does not overwrite existing formal records.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Moved starter SAR profile out of Python constants**
- **Found during:** Task 3 (Add generic topic template and SAR starter profile)
- **Issue:** The first implementation stored the SAR starter profile as a Python constant, which weakened the plan requirement that SAR be a data instance rather than harness logic.
- **Fix:** Added `src/rsa_cli/data/topic_profiles/sar_noncontinuous_aperture.yaml` and changed skeleton creation to discover built-in profile YAML files generically.
- **Files modified:** `pyproject.toml`, `src/rsa_cli/skeleton.py`, `src/rsa_cli/templates.py`, `src/rsa_cli/data/topic_profiles/sar_noncontinuous_aperture.yaml`, `tests/test_skeleton.py`
- **Verification:** `python -m pytest tests/test_skeleton.py tests/test_config.py -q`
- **Committed in:** `71145d9`

---

**Total deviations:** 1 auto-fixed (missing critical)
**Impact on plan:** The fix strengthened the intended topic-generic harness boundary without adding scope.

## Issues Encountered

- `pytest` was not installed initially. Resolved by running `python -m pip install -e ".[dev]"`.
- `rsa.exe` installed outside PATH on this Windows user install; verified the console script via its absolute user-script path and retained `python -m rsa_cli.cli` as a reliable local invocation.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/test_config.py tests/test_skeleton.py -q` - passed, 8 tests.
- `python -m pip install -e ".[dev]"` - passed.
- `rsa --help` via user-script path - passed.
- `python -m rsa_cli.cli --root . init` twice - passed, no new files created on rerun.
- `git check-ignore -v 01_literature/pdfs/sample.pdf 01_literature/assets/P001/screen.png` - confirmed payload files are ignored.
- `git check-ignore` on `.gitkeep` files - confirmed `.gitkeep` files are not ignored.

## Next Phase Readiness

The project now has the package, config loader, skeleton creator, templates, SAR starter profile, and tests needed for Plan 01-02 to add schema validation and round configuration behavior.

---
*Phase: 01-harness-foundation*
*Completed: 2026-05-11*
