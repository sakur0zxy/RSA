# Phase 11: Campaign & Batch Review - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `11-CONTEXT.md`; this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 11-campaign-batch-review
**Areas discussed:** campaign input automation, metadata intake, formal write request, controlled parallelism, review queue, run state, report location, CLI commands, implementation split, tests, future worker phase

---

## Campaign 批量运行入口

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 只自动处理 `linked` items，`queued` 完全留给人工处理。 | |
| 2 | `linked` 自动运行，`queued` 自动生成 metadata intake request。 | ✓ |
| 3 | 所有 `queued` 也自动创建 formal metadata。 | |

**User's choice:** 方案 2。  
**Notes:** 用户强调整体系统应尽量自动化，但正式科研记录不能被未核验候选污染。

---

## Metadata Intake Request 存放与状态

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 每个 campaign 旁边放 `C001_metadata_requests.yaml`，但 request 按独立对象设计。 | ✓ |
| 2 | 直接把 request 嵌入 campaign YAML。 | |
| 3 | 立即建立全局 `metadata_requests/` 待办池。 | |

**User's choice:** 当前采用方案 1，并保留升级到方案 3 的结构。  
**Notes:** 默认状态采用收缩版 `auto_triaged`。该状态表示机器已初步分诊并给出建议，不表示人工审阅通过，也不能写 formal metadata。讨论中将 `approved` 收紧为 `accepted`，避免和 formal approval 混淆。

---

## Formal Write Request

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Phase 11 只生成 formal write request，正式写入仍由人工确认 gate 执行。 | ✓ |
| 2 | Phase 11 自动调用 formal apply。 | |
| 3 | Phase 11 不生成 formal write request，只显示人工提示。 | |

**User's choice:** 方案 1。  
**Notes:** 用户希望 AI 自动初审，人工做最后监管；formal request 进入待审队列，但不得自动执行。

---

## Campaign 受控并行

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 小规模流水线并行，多篇之间并行，每篇内部顺序。 | ✓ |
| 2 | 全批次阶段栅栏，每阶段全完成后进入下一阶段。 | |
| 3 | 直接并发启动多个完整 workflow。 | |

**User's choice:** 方案 1，具体参数可调整。  
**Notes:** 默认并发为 acquisition 2、reading draft 2、visual extraction 1、scoring 2。CLI flag 可覆盖 `.rsa/local.yaml` 的长期配置。

---

## Review Queue 排序与决策

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 状态分组加组内优先级排序。 | ✓ |
| 2 | 只列异常项。 | |
| 3 | 所有 processed 项都进入人工队列。 | |

**User's choice:** 方案 1。  
**Notes:** 用户希望 AI 帮用户初审，用户最后监管。review decision 使用 `accepted | deferred | rejected | needs_followup`，不用 `approved`。

---

## Artifact Links 与扩展接口

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Review queue item 必须带关键 artifact links，并保留可扩展 map。 | ✓ |
| 2 | 只保存文本路径说明。 | |

**User's choice:** 方案 1。  
**Notes:** 用户认为链接有必要，方便找到相关文档记录。后续新增链接应容易扩展，旧 parser 忽略未知 key。

---

## Run State 与报告位置

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 放在 campaign 目录同级：`C001_run.yaml`、`C001_review_queue.yaml`、`C001_batch_report.md`。 | ✓ |
| 2 | 建立全局 run history 目录。 | |
| 3 | 写回 campaign YAML 本体。 | |

**User's choice:** 方案 1。  
**Notes:** v1 以本地 Markdown/YAML 和用户可读监管为主。未来可升级到 `campaign_runs/C001/RUN-###.yaml`。

---

## Background Worker

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Phase 11 v1 做同步 CLI，worker 延后。 | |
| 2 | 将后台 worker 作为独立后续 phase。 | ✓ |
| 3 | 立即把 worker 加进 Phase 11。 | |

**User's choice:** 方案 2。  
**Notes:** 后台 worker / scheduled automation 被放入 Phase 14，作为运行形态升级，不提前挤进 Phase 11。

---

## Campaign CLI 命令组

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 扩展现有 `rsa campaign`。 | ✓ |
| 2 | 新增 `rsa batch` 命令组。 | |
| 3 | 新增 `rsa campaign-run` 命令组。 | |

**User's choice:** 方案 1。  
**Notes:** 新增 `run`、`resume`、`pause`、`queue`、`report`。默认 run 只处理未完成项，rerun 语义后续扩展。

---

## 实现计划切分

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 拆成 3 个 plans：schema/state、pipeline、queue/report/docs/tests。 | ✓ |
| 2 | 全部放进一个大 plan。 | |
| 3 | 拆得更细并提前做 worker。 | |

**User's choice:** 方案 1。  
**Notes:** 该切分保持数据模型、运行引擎和用户监管输出边界清晰。

---

## Failure Monitoring 与 Eval

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Phase 11 做 deterministic pytest，失败场景监测纳入 Phase 13。 | ✓ |
| 2 | Phase 11 立即扩展完整 `rsa eval`。 | |

**User's choice:** 方案 1。  
**Notes:** 用户同意将失败场景监测加入后续可能会做的功能，并明确放到 Phase 13。

---

## Context 收口

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | 同步 `11-CONTEXT.md`、`11-DISCUSSION-LOG.md`、ROADMAP、REQUIREMENTS、STATE。 | ✓ |
| 2 | 只保留 WIP，不更新项目状态。 | |

**User's choice:** 方案 1。  
**Notes:** Phase 11 discussion 完成后进入 plan phase。

---

## Agent Discretion

- Phase 11 内部模块命名、helper 拆分、错误消息细节和测试文件布局由 agent 在计划和执行时决定。
- Agent 可以调整最小实现顺序，但不能改变 formal gate 边界、中文用户可见原则、状态语义和 Phase 14 deferred worker 决策。

## Deferred Ideas

- Phase 13: campaign failure monitoring、eval/regression hardening、writing safety。
- Phase 14: Background Worker & Scheduled Automation，包含后台 worker、异步任务、长任务恢复、status 监控、定时 campaign run、worker 日志摘要。
- Future: global metadata request pool、global formal write request pool、campaign run history、campaign rerun。
- Deferred advanced: Crossref/OpenAlex/Zotero 深集成、高级图表智能、复杂 multi-agent 编排。
