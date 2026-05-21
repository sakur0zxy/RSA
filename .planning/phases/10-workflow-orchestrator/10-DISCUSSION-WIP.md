# Phase 10 Workflow Orchestrator - Discussion WIP

**Started:** 2026-05-21  
**Status:** discussing  
**Source:** `$gsd-discuss-phase` inline discussion, no subagents

## Phase Boundary

Phase 10 负责把已经实现的 v1/v2 命令串联成一个可监控、可恢复、可调整的自动工作流。它默认自动运行到 review packet 或需要人工监管的位置，但不得绕过 formal write gate。

Phase 10 不负责完整 batch review UI，不负责 Local Review Workspace，不负责 claim-level citation hardening，也不直接执行 formal writes。

## Carry-Forward Decisions

- 用户可见内容中文优先；英文 key、flag、status enum 和代码标识保持稳定。
- AI 产物默认进入 staging / review packet，不直接进入 formal records。
- `formal write gate` 不得被 orchestrator、batch、UI 或后续 agent 编排绕过。
- Phase 7 acquisition、Phase 8 reading draft、Phase 8.1 visual extraction、Phase 9 scoring 已有可调用 CLI。
- Phase 8.2 campaign foundation 已有队列基础，但完整 Campaign & Batch Review 仍属于 Phase 11。
- 用户希望系统自动化程度高：AI/自动流程可以自行推进普通步骤，用户主要监管关键环节、异常项和 formal approval。

## Candidate Gray Areas

1. **Workflow entry point and default unit**  
   决定 Phase 10 的最小运行对象是单篇 `P###`、campaign item，还是两者都支持但以单篇为核心。

2. **Automatic chain and stop gates**  
   决定 workflow 默认串联哪些步骤、什么情况下继续、什么情况下停止到 review。

3. **Run state and resume model**  
   决定 workflow run 的状态文件、step 记录、artifact link、resume/rerun/rollback 语义。

4. **Monitoring and user controls**  
   决定用户如何查看进度、调整步骤、禁用某些阶段、处理 blocked/partial/needs_review。

5. **Project-wide parallelism placement**  
   已安排到整体项目：Phase 10 做单篇顺序 workflow primitive，Phase 11 做 campaign 级受控并行。该分工已同步到 `.planning/PROJECT.md`、`.planning/ROADMAP.md` 和 `.planning/REQUIREMENTS.md`。

## Decisions Captured

### Area 1: Automatic Chain And Stop Gates

- **Selected first:** 自动链路与停止点。
- **Reason:** Phase 10 的核心价值是自动把已有 v1/v2 命令串起来，并在需要人工监管的位置停住；先锁定默认链路可以约束后续入口、状态恢复和监控设计。
- **Accepted recommendation:** 采用“单篇内部顺序链 + campaign 级受控并行留给 Phase 11”的边界。
- **Phase 10 decision:** 单篇论文内部按依赖顺序推进：acquisition -> reading draft -> visual extraction -> scoring -> review packet。默认自动跑到 review packet 或需要人工监管的位置。
- **Phase 10 boundary:** Phase 10 不实现多篇 worker queue、不做阶段并发限流、不做 campaign 排序运营；但 run state 和 step schema 要为 Phase 11 的受控并行调度保留字段，例如 `run_id`、`paper_id`、`campaign_id`、`step_id`、`step_status`、`artifacts`、`blocked_reason_zh`、`retry_policy`。
- **Phase 11 handoff:** 多篇论文之间可流水线式小并行；每篇内部仍顺序推进。并发控制建议由 Phase 11 处理，例如 acquisition 2-3、reading draft 2、visual extraction 1-2、scoring 2-3。
- **Stop gate decision:** formal write 一律不并行自动推进；遇到 formal request、授权错误、text/visual conflict、低置信度关键项、blocked/partial 状态时，Phase 10 停到 review packet 或 status report。
- **Re-evaluation:** 重新判断后仍确认该分工。Phase 10 的核心是把单篇链路变成可靠、可恢复、可监控的 workflow primitive；Phase 11 才适合在这些 primitive 之上做 campaign 级队列、并发、排序和批量异常聚合。这样既保留自动化扩展空间，又避免 Phase 10 同时承担 orchestrator 和 batch scheduler 两个职责。
- **Project-level placement:** 该想法不作为新 phase，不放 deferred；它成为 v2 的全局自动化调度原则，并分别落到 Phase 10 requirements 和 Phase 11 campaign requirements。

## Deferred Ideas

- Campaign 级受控并行、阶段 worker queue、campaign ranking/filtering 和总体 review queue 放入 Phase 11。
