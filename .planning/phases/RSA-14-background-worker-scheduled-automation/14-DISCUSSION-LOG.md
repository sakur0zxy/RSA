# Phase 14 Discussion Log

## Completed Decisions

1. Use a local queue plus one-shot runner, not a persistent daemon v1.
2. Store worker state under `01_literature/workers/`.
3. Reuse Phase 10/11/12/13 primitives instead of reimplementing automation logic.
4. Support campaign-first worker task types: campaign run/resume/queue/report/safety and review workspace generation.
5. Schedules enqueue tasks; execution remains visible through queue records.
6. Worker never executes formal write commands.
7. Add explicit cancel and recovery semantics.
8. Keep all user-visible text Chinese-first.

## Reserved Interfaces

- `daemon_mode`
- `external_scheduler`
- `task_lock`
- `heartbeat`
- `worker_id`
- `max_runtime_seconds`
- `failure_detector_plugins`
- future task registry entries for paper-level workflow tasks

## Deferred

- True long-running background service.
- Web UI live refresh.
- Cloud queue.
- Multi-agent orchestration.
- Formal write automation.
