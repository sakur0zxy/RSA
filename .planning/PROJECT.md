# RSA 科研 Agent

## What This Is

RSA 科研 Agent 是一个面向博士科研工作的轻量 agent harness 项目，优先服务 SAR 相关课题的长期文献调研、证据管理、阅读笔记和研究问题边界维护。它不是独立 agent 平台，也不是自动写论文系统，而是把模型能力放进可审计、可回滚、可评估的工作流里。

第一版以本地文件和 Markdown/YAML 为主，围绕 topic profile、文献元数据、候选文献核验、主题映射、PDF 状态、阅读笔记、人审入库和评估用例建立可靠地基。旧项目 `PhD_DistributedSAR_NoncontinuousAperture/00_plan` 只作为科研流程参考，不作为必须照搬的结构。

## Core Value

让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] 建立 topic profile 驱动的科研任务入口，使不同研究主题可以复用同一套 harness。
- [ ] 建立 metadata-first 的正式文献记录，候选、核验、阅读和映射状态必须可追踪。
- [ ] 建立轻量 agent_outputs 档案规则，保存每轮关键结论而不是堆积原始日志。
- [ ] 建立候选文献搜索、元数据核验、主题映射、PDF 状态和阅读笔记的分步流程。
- [ ] 建立人审门槛，未确认文献和 agent 推断不能自动进入正式记录。
- [ ] 建立评估与观测机制，用固定用例检查 hallucination、格式漂移、越权下载、正式记录污染和范围蔓延。
- [ ] 建立项目级指令文件，让后续 agent 明确读取代码/文档、保持最小改动、遵守证据优先级。

### Out of Scope

- 自动撰写综述正文或博士论文正文 - v1 只辅助调研和证据整理。
- 未授权 PDF 下载或绕过出版方访问控制 - 必须保留合法来源和获取状态。
- 复杂数据库、Web 平台或多人权限系统 - v1 先用本地文件验证流程。
- 把 agent_outputs 当作正式事实源 - 正式记录只来自 metadata、paper_index、notes 和人工确认后的研究记录。
- 一次性处理大量文献 - v1 以小批次、可审计、可复跑为原则。
- 完整 SAR 算法实现平台 - 该项目服务科研 agent harness，不直接实现 SAR 成像算法主线。

## Context

参考计划中已经明确了一个重要边界：科研 agent 的输出不是最终证据，正式记录优先级高于 agent 输出档案。旧计划建议的正式记录包括 `01_literature/metadata/`、`paper_index.md`、`literature_map.md`、`research_tables.md`、`agent_research_notes.md` 和 `notes/`；辅助档案放在 `agent_outputs/`。

旧计划还给出了适合迁移的 agent 角色：Search Candidates、Verification Review、Map Integration、PDF Acquisition、Paper Reading。新项目不必机械照搬多 agent 形式，但应保留这些职责边界，并用 harness 约束它们的输入、输出、状态和失败处理。

Harness engineering 在本项目中的实际含义：

- 文件级组件可观察：prompt、topic profile、模板、规则、评估用例、状态文件都要落盘。
- 经验可观察：每轮任务留下简短但足够的 evidence trail，包括候选来源、核验状态、拒绝原因和人工确认。
- 决策可观察：关键写入正式记录前必须能说明依据、风险和是否已人工确认。
- 工具权限受控：搜索、读取、PDF 状态、正式记录写入分层授权。
- 可评估：每次改 prompt、规则、工具或模板后，都能用固定小样本检查行为是否退化。

旧 SAR 课题方向可作为默认首个 topic profile：分布式 / 多平台 / 多视角 SAR 中的非连续孔径覆盖、相位历史恢复、跨通道相干约束和虚影抑制评价。

## Constraints

- **Storage**: v1 使用本地 Markdown/YAML 文件 - 便于人工审阅、git diff、回滚和迁移。
- **Authority**: 正式记录高于 agent 输出 - 冲突时以 metadata、paper_index、notes 和人工确认记录为准。
- **Copyright**: 不做未授权下载 - agent 只记录 PDF 状态、官方 URL、DOI、本地路径和获取待办。
- **Scope**: 先做科研调研 harness，不先做通用 agent 平台 - 避免过度工程化。
- **Batch size**: 小批量运行 - 每轮默认处理少量候选文献，优先质量和可追溯性。
- **Human review**: 正式入库需要人工确认 - 未核验候选只能停留在 staging 或 agent_outputs。
- **Evaluation**: prompt、模板、工具和规则变更必须配套评估用例 - 防止格式和学术可靠性回退。

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 采用本地文件 harness | 科研记录需要可审阅、可 diff、可回滚，数据库会过早增加复杂度 | Pending |
| metadata-first | 文献事实必须结构化、可核验，不能散落在 agent 摘要里 | Pending |
| agent_outputs 只做轻量档案 | 保留可追溯性，同时避免长期堆积噪声 | Pending |
| 不自动写正式综述正文 | 降低 hallucination 和学术责任风险 | Pending |
| 首个默认 topic profile 面向 SAR 非连续孔径 | 贴合当前博士课题，同时验证流程是否能承载真实科研需求 | Pending |
| harness 先于多 agent 编排 | 先保证工具、状态、权限、评估和证据链可靠，再扩展多 agent | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason
2. Requirements validated? Move to Validated with phase reference
3. New requirements emerged? Add to Active
4. Decisions to log? Add to Key Decisions
5. "What This Is" still accurate? Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-11 after initialization*
