---
phase: "16"
title: "Research Plan Driven Literature Discovery"
status: completed_inline
created: 2026-05-31
subagents: none
---

# Phase 16 Research

This research was completed inline because the user explicitly required no subagents.

## Current Codebase Findings

- `src/rsa_cli/campaign.py` already supports campaign creation, CSV/TSV/YAML import, dedup keys, linked/queued states, metadata intake requests, review queue and batch reporting.
- `src/rsa_cli/acquisition.py` already contains source provider safety rules, custom provider validation, blocked states and Chinese failure messages.
- `src/rsa_cli/config.py` already merges `rsa.yaml` and `.rsa/local.yaml`, making it suitable for `discovery` configuration without new storage primitives.
- `src/rsa_cli/cli.py` uses one `_run_<domain>_command()` handler per command group and Chinese-first user output.
- Templates and tests already enforce candidate staging language: candidates do not create formal metadata until verified and human-confirmed.

## Recommended Implementation Shape

- Add `src/rsa_cli/discovery.py` as the dedicated Phase 16 module.
- Store artifacts under `01_literature/discovery/`.
- Add `ProjectConfig.discovery_root` and `ProjectConfig.discovery`.
- Add a small `rsa discovery` command group:
  - `run`
  - `validate`
  - `status`
- Keep provider search testable and fail-closed. Use standard-library HTTP clients so no new dependency is required.
- Reuse `create_campaign()` and `import_campaign_items()` instead of creating a parallel queue.

## Risks

- Network providers can rate-limit or change response format. Mitigate by storing provider status and using tests with mocked provider calls.
- Chinese research plans may not contain enough English search terms. Mitigate by generating a query bundle with confidence and allowing manual/provider extension later.
- Discovery can be confused with formal metadata ingestion. Mitigate by keeping all outputs in discovery/campaign staging and refusing formal writes.

## Non-Goals

- No vector database.
- No deep Zotero/OpenAlex/Crossref synchronization.
- No direct PDF download in discovery.
- No formal metadata write.
- No subagent orchestration.

