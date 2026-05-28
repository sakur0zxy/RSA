# Phase 14: Background Worker & Scheduled Automation - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning
**Source:** gsd-discuss-phase 14, completed inline; user delegated decisions to the agent

<domain>
## Phase Boundary

Phase 14 upgrades RSA from manually-triggered CLI automation into local background-style automation. It does not add new literature understanding logic. It wraps the existing Phase 10 single-paper workflow, Phase 11 campaign scheduling, Phase 12 review workspace and Phase 13 safety checks in a local worker queue and scheduled enqueue layer.

The phase delivers a synchronous, testable local worker v1:

- a persistent local task queue;
- one-shot worker execution that can be run repeatedly or by an external scheduler;
- scheduled campaign task enqueue;
- long-task recovery/status semantics;
- Chinese status, logs and summaries.

This phase must not become a cloud service, web server, multi-agent router, or formal write bypass.
</domain>

<decisions>
## Implementation Decisions

### D-01: Local worker shape

- Decision: `local_queue_plus_one_shot_runner`.
- Add a `rsa worker` command group.
- Store task queue and schedule files under `01_literature/workers/`.
- The worker runner processes queued tasks synchronously and exits by default.
- This makes v1 usable from CLI, Windows Task Scheduler, cron, or future daemon wrappers.
- Reserve interfaces for a later daemon/service mode, but do not implement a persistent service in this phase.

### D-02: Worker task types

- Decision: `campaign_first_reuse_existing_primitives`.
- Phase 14 task types:
  - `campaign_run`
  - `campaign_resume`
  - `campaign_queue`
  - `campaign_report`
  - `campaign_safety`
  - `review_workspace`
- Each task calls existing RSA functions instead of reimplementing campaign/workflow/review/safety logic.
- Future task types can be added through a registry-style dispatch function.

### D-03: Formal write boundary

- Decision: `worker_never_executes_formal_write`.
- The worker must not execute `rsa formal ...`.
- It may run campaign automation, review queue generation, review workspace build and safety checks.
- If a campaign pauses because of a pending formal write request, worker records that as completed worker execution with `result_status: paused` and Chinese next action.
- Formal records remain behind human confirmation.

### D-04: Schedule semantics

- Decision: `schedule_enqueues_tasks_not_background_magic`.
- A schedule does not execute work directly.
- `rsa worker schedule due` converts due schedules into queued worker tasks.
- `rsa worker run --include-due` first enqueues due tasks, then processes queued tasks.
- Schedules record `schedule_id`, `task_type`, `target_id`, `interval_hours`, `next_run_at`, `enabled`, `last_enqueued_at` and Chinese explanation.
- This keeps scheduled automation observable and easy to test.

### D-05: Monitoring and logs

- Decision: `machine_readable_queue_plus_chinese_log`.
- Worker state includes queue counts, running/failed/completed counts, last run summary and schedule counts.
- Logs are summarized in `worker_log.md`; YAML queue/schedule files remain the machine-readable source.
- Logs must avoid secrets, cookies, passwords, full PDFs or large LLM prompts.

### D-06: Recovery semantics

- Decision: `stale_running_tasks_are_requeued_explicitly`.
- A queued task can be cancelled.
- A stale `running` task can be requeued by an explicit recovery command.
- Recovery writes a Chinese reason and increments attempts.
- The default worker does not silently assume a running task is safe to re-run.

### D-07: User monitoring model

- Decision: `automatic_progress_user_supervision`.
- Worker automation can run reading/scoring/review preparation without user intervention.
- Users supervise through `rsa worker status`, `rsa worker logs`, Phase 12 review workspace and Phase 13 safety reports.
- Human approval remains required for formal records.

### D-08: Chinese-first outputs

- Decision: `zh_first_worker_outputs`.
- CLI help, success messages, errors, log summaries and README explanations must be Chinese-first.
- Schema keys and command flags stay English and stable.

### D-09: Reserved interfaces

- Decision: `future_daemon_interfaces_reserved`.
- Reserve fields for:
  - `daemon_mode`
  - `external_scheduler`
  - `task_lock`
  - `heartbeat`
  - `worker_id`
  - `max_runtime_seconds`
  - `failure_detector_plugins`
- Current values stay `not_run` or `not_enabled`.
</decisions>

<must_not>
## Phase 14 MUST NOT

- Reimplement Phase 10 workflow internals.
- Reimplement Phase 11 campaign scheduling logic.
- Execute formal write commands.
- Start a cloud service or require a remote queue.
- Implement multi-agent orchestration.
- Store account passwords, browser cookies, PDF contents or full prompts in worker logs.
- Run forever by default.
</must_not>

<success>
## Success Criteria

- `rsa worker enqueue campaign-run C001` creates a queued task.
- `rsa worker run --max-tasks 1` executes queued campaign automation through existing functions.
- `rsa worker status` and `rsa worker logs` provide Chinese-readable monitoring.
- `rsa worker schedule add ...` and `rsa worker schedule due` support scheduled task enqueue.
- Recovery/cancel commands mutate only worker queue records.
- README and tests document worker boundaries and formal gate safety.
</success>
