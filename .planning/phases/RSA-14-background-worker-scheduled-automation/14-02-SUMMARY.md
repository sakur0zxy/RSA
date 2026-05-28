# Phase 14-02 Summary: Worker CLI, Schedule And Recovery

**Completed:** 2026-05-29

## What Changed

- Added the `rsa worker` command group:
  - `rsa worker enqueue <task_type> <C###>`
  - `rsa worker run [--max-tasks N] [--include-due]`
  - `rsa worker status`
  - `rsa worker logs`
  - `rsa worker cancel WT###`
  - `rsa worker recover WT###`
  - `rsa worker schedule add ...`
  - `rsa worker schedule list`
  - `rsa worker schedule due`
- Added one-shot worker execution: it processes queued tasks and exits.
- Added schedule semantics: schedules enqueue due tasks, but do not directly execute them.
- Added cancel/recover semantics for local queue records.

## Boundary

- `rsa worker run` continues after individual task failures and records Chinese repair hints.
- `rsa worker schedule due` is explicit and inspectable.
- Recovery of stale `running` or failed tasks requires an explicit command.

## Requirement Coverage

- V2-WORKER-03: status monitoring, scheduled enqueue, long-task recovery and worker log summaries are implemented.
- V2-WORKER-04: commands do not call formal write functions.

