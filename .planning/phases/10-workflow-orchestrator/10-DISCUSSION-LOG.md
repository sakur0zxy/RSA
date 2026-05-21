# Phase 10: Workflow Orchestrator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-21  
**Phase:** 10-workflow-orchestrator  
**Areas discussed:** automatic chain and stop gates, workflow entry point, run state and resume model, monitoring and user controls, project-wide parallelism placement, advanced figure intelligence interface

---

## Automatic Chain And Stop Gates

| Option | Description | Selected |
|--------|-------------|----------|
| Run to review packet | Run acquisition, reading draft, visual extraction, scoring, and review packet; stop before formal writes. | ✓ |
| Run to scoring only | Stop earlier after scoring, leaving review packet aggregation separate. | |
| Scheduling skeleton only | Implement run/resume/status without a full default research chain. | |

**User's choice:** Run to review packet.

**Notes:** The user also reviewed a proposal for layered parallelism. Final decision: Phase 10 is a single-paper sequential workflow primitive; Phase 11 handles campaign-level controlled parallelism.

---

## Partial, Blocked, And Needs Review

| State | Behavior | Selected |
|-------|----------|----------|
| `partial` continues | Continue to review packet if core artifacts are usable, with explicit evidence limitations. | ✓ |
| `blocked` stops | Stop the current paper workflow and fail closed with Chinese repair hints. | ✓ |
| `needs_review` continues to review packet | Gather available artifacts, then stop for user supervision. | ✓ |

**User's choice:** `partial` and `needs_review` continue to review packet; `blocked` stops current paper workflow.

**Notes:** `partial` must never look like normal success. `needs_review` must not become formal approval. `blocked` must not generate a normal completed review packet.

---

## Visual Extraction And Advanced Figure Interface

| Option | Description | Selected |
|--------|-------------|----------|
| Conservative visual extraction by default | Run existing `rsa visual extract P###`, keep LLM image understanding and advanced analysis as `not_run`. | ✓ |
| Skip visual extraction by default | Faster workflow but weaker scoring/review evidence. | |
| Run LLM image understanding by default | Stronger automation but expands Phase 10 and requires new advanced figure implementation. | |

**User's choice:** Run conservative visual extraction by default.

**Notes:** The user asked whether prior work already implemented advanced figure intelligence. Code and docs show Phase 8.1 implemented conservative visual candidate extraction and placeholders only. Decision: keep interfaces for future advanced figure intelligence, but Phase 10 does not execute it.

---

## Workflow Entry Point

| Option | Description | Selected |
|--------|-------------|----------|
| Single paper as core entry | `rsa workflow run P001`; campaign ids are optional context only. | ✓ |
| Paper and campaign as equal entries | Support both `P###` and `C###` as Phase 10 run targets. | |
| Campaign only | Use campaign as the main workflow entry. | |

**User's choice:** Single paper as core entry.

**Notes:** Campaign in Phase 10 is context and provenance, not a batch scheduler. Phase 11 uses campaign as the primary entry point.

---

## Run State Location

| Option | Description | Selected |
|--------|-------------|----------|
| Per-paper run files | Store runs under `01_literature/workflows/P001/RUN-001.yaml`. | ✓ |
| Global `runs.yaml` | Centralize all workflow runs in one file. | |
| Review packet only | No independent run state. | |

**User's choice:** Per-paper run files.

**Notes:** This supports single-paper recovery now and campaign aggregation later.

---

## Step Ledger Detail

| Option | Description | Selected |
|--------|-------------|----------|
| Full step ledger | Record step id, command, status, timestamps, inputs, artifacts, errors, repair hints, retry flags. | ✓ |
| Current step and final result only | Smaller but weaker for recovery and audit. | |
| Full stdout/stderr | Maximum raw logs but noisy and risky. | |

**User's choice:** Full step ledger.

**Notes:** Full stdout/stderr should not go into main run YAML; store concise Chinese summaries and artifact links instead.

---

## Resume And Artifact Reuse

| Option | Description | Selected |
|--------|-------------|----------|
| Resume from unfinished/failed/retryable step | Reuse completed valid artifacts, continue from the right point. | ✓ |
| Resume from the beginning | Simple but wasteful and may repeat downloads/model calls. | |
| Only manually specified step | Precise but too manual. | |

**User's choice:** Resume from unfinished, failed, or retryable step.

**Notes:** Completed steps require lightweight artifact validation before reuse. `--from-step` remains available for manual override.

---

## Monitoring And User Controls

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal run/resume/status/report | Enough for basic monitoring, less implementation work. | |
| Full run/resume/status/report/stop/rerun | More user control over workflow execution. | ✓ |
| Run and resume only | Too little supervision for this project. | |

**User's choice:** Full control command set.

**Notes:** The user chose option 2 after comparing what option 1 omitted. `stop` and `rerun` are included. `stop` must prevent automatic resume, and `rerun` must explain artifact reuse/overwrite.

---

## Step Toggles

| Option | Description | Selected |
|--------|-------------|----------|
| Local config and command flags | Allow defaults in config and per-run overrides. | ✓ |
| Command flags only | Simpler but repetitive. | |
| No skipping | Stable but too rigid. | |

**User's choice:** Local config and command flags.

**Notes:** Skipped steps must be visible in run state and report with `skipped_reason_zh`; skipped is not success.

---

## Agent Discretion

- Exact run id naming and YAML ordering.
- Exact internal helper/module split.
- Exact initial set of skip flags, provided required workflow controls are present.
- Exact report format, provided it is Chinese-first and links important artifacts.

## Deferred Ideas

- Campaign-level controlled pipeline parallelism and worker queues.
- Campaign ranking/filtering and batch exception aggregation.
- Local review workspace UI.
- Claim-level citation hardening.
- True advanced figure intelligence, including LLM image understanding, curve/numeric extraction, advanced table reconstruction, and chart-claim binding.
