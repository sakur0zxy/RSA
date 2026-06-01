# Phase 14-01 Summary: Worker Queue Foundation

**Completed:** 2026-05-29

## What Changed

- Added `ProjectConfig.workers_root`.
- Added `01_literature/workers/` to the initialized literature skeleton.
- Added `src/rsa_cli/worker.py` with a local `queue.yaml`, worker task ids, schedule ids, Chinese messages and reserved future interfaces.
- Added supported task types:
  - `campaign_run`
  - `campaign_resume`
  - `campaign_queue`
  - `campaign_report`
  - `campaign_safety`
  - `review_workspace`

## Boundary

- Worker state is local Markdown/YAML-style project state.
- Worker tasks keep `formal_write_allowed: false`.
- The worker does not execute `rsa formal ...`.

## Requirement Coverage

- V2-WORKER-01: implemented after Phase 11/12/13 contracts.
- V2-WORKER-02: task execution delegates to existing campaign/review/safety functions.
- V2-WORKER-04: queue records explicitly preserve formal-write boundaries.

