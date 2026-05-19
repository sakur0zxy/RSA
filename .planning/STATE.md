---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Scaled Literature Workstation
status: Phase 8.2 context refreshed; next recommended step is Phase 9 planning
stopped_at: "Phase 8.2 context refreshed after retrospective discuss; next recommended step is $gsd-plan-phase 9"
last_updated: "2026-05-19T13:15:00+08:00"
last_activity: 2026-05-19 -- 完成 Phase 8.2 Campaign Foundation 实现与验证
progress:
  total_phases: 16
  completed_phases: 11
  total_plans: 28
  completed_plans: 28
  percent: 69
---

# 项目状态

## 项目引用

参见: `.planning/PROJECT.md`

**核心价值:** 让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

**当前重点:** Phase 9 Evidence Signals & AI Scoring

## 当前位置

Phase: 8.2 Campaign Foundation
Plan: 1 plan completed
Status: Phase 8.2 complete；下一步建议规划 Phase 9
Last activity: 2026-05-19 -- 完成 Phase 8.2 Campaign Foundation 实现与验证

进度: [███████░░░] 69%

## 进度指标

**速度:**

- 已完成 plans: 28
- 平均耗时: N/A
- 总执行时间: 0 hours

**按 Phase:**

| Phase | Plans | 状态 |
|-------|-------|------|
| 1 | 3 | complete |
| 2 | 4 | complete |
| 3 | 3 | complete |
| 4 | 2 | complete |
| 5 | 2 | complete |
| 6 | 2 | complete |
| 7 | 3 | complete |
| 7.1 | 2 | complete |
| 8 | 3 | complete |
| 8.1 | 3 | complete |
| 8.2 | 1 | complete |

## 累积上下文

### 决策

- v1 是本地优先的 Python/Markdown/YAML research harness，不是 Web 平台。
- Formal records 的权威性高于 `agent_outputs`；formal writes 需要 validation 和 human approval。
- SAR noncontinuous aperture 是 starter topic profile，不是硬编码产品假设。
- Phase 5 eval fixtures 是 deterministic local checks，不是 LLM grading 或网络调研。
- Phase 6 source ledger 和 asset manifest 可以记录本地来源/资产，但不得自动修改 formal metadata。
- Phase 6 binary PDFs/assets local-only；可审计 manifest/source YAML 可以进入 git。
- Phase 7 `rsa source find P###` 默认 monitored_auto：自动发现、审查并下载规则允许的授权 PDF。
- Phase 7 自定义 provider 放在 `.rsa/local.yaml`，不得配置 Sci-Hub、盗版镜像、账号密码保存、模拟登录或访问控制绕过。
- Phase 7 PDF 下载使用 `.tmp`、PDF 校验、`sha256` 去重、多版本保存和主版本选择。
- Phase 7.1 Browser Session Provider 支持用户自行登录资料库后复用本地授权浏览器会话；session 文件 local-only，不保存密码，不从已有浏览器静默提取 cookies，不绕过验证码/SSO/paywall。
- Phase 7.1 v1 支持 cookie-based direct PDF URL；复杂 DOM 搜索、点击下载和 JS 下载流后续再做。
- v2 resequence: Phase 10 定为 Workflow Orchestrator，用于串联已有命令并自动跑到 review packet；原 Campaign/Metadata/UI/Writing/Multi-Agent 阶段顺延。
- Phase 8 Auto Reading Draft 支持 `rsa note draft P###`，从 source ledger 或 `--source-file` 生成中文自动阅读草稿、AI 初审分、review packet、local-only extraction cache 和 prompt packet。
- Phase 8 `ready_for_review` 只表示 AI 初审后建议人工监管，不等于 `approved`，也不允许绕过 formal write gate。

### 待办

无。

### 阻塞和关注点

- Phase 8.1 已完成视觉候选提取闭环：`rsa visual extract|validate|status`、`visual_evidence_candidates.yaml`、local-only crops/context packets 和 PyMuPDF fail-closed 边界。
- Phase 8.2 已完成不依赖 Phase 9/10 的 campaign foundation：`rsa campaign create|import|validate|status`、`01_literature/campaigns/C###.yaml`、CSV/TSV/YAML 导入、轻量去重和 formal metadata 链接。
- Phase 9 需要消费正文证据与 Phase 8.1 视觉候选，但仍不能把未人工确认的 AI 评分或图像解释写入 formal records。
- Browser session 下载得到的 PDF 只是本地授权阅读材料，不能自动写入 metadata、literature_map、agent_research_notes 或论文正文。

## 会话连续性

Last session: Phase 8.2 context refreshed after retrospective discuss
Stopped at: Phase 8.2 context refreshed; next recommended step is `$gsd-plan-phase 9`
Resume file: `.planning/phases/08.2-campaign-foundation/08.2-CONTEXT.md`

**已计划 Phase:** 03 (Research Round Integration) - 3 plans - 2026-05-12T02:12:01.988Z
**已完成 Phase:** 03 (Research Round Integration) - 3 plans - 2026-05-12
**已计划 Phase:** 04 (Reading Note Workflow) - 2 plans - 2026-05-12
**已完成 Phase:** 04 (Reading Note Workflow) - 2 plans - 2026-05-12
**已计划 Phase:** 05 (Evaluation and Hardening) - 2 plans - 2026-05-13
**已完成 Phase:** 05 (Evaluation and Hardening) - 2 plans - 2026-05-13
**已归档里程碑:** v1.0 (Local Harness) - 5 phases / 14 plans - 2026-05-13
**已计划 Phase:** 06 (Asset & Source Foundation) - 2 plans - 2026-05-13
**已完成 Phase:** 06 (Asset & Source Foundation) - 2 plans - 2026-05-13
**已调整 Roadmap:** Phase 10 (Workflow Orchestrator) 成为自动工作流调度阶段 - 2026-05-14
**已计划 Phase:** 07 (Authorized Acquisition) - 3 plans - 2026-05-14
**已完成 Phase:** 07 (Authorized Acquisition) - 3 plans - 2026-05-14
**已插入 Phase:** 07.1 (Browser Session Provider) - 2026-05-14
**已计划 Phase:** 07.1 (Browser Session Provider) - 2 plans - 2026-05-14
**已完成 Phase:** 07.1 (Browser Session Provider) - 2 plans - 2026-05-14
**已计划 Phase:** 08 (Auto Reading Draft) - 3 plans - 2026-05-16
**已完成 Phase:** 08 (Auto Reading Draft) - 3 plans - 2026-05-16

**Planned Phase:** 08.1 (visual-evidence-extraction) — 3 plans — 2026-05-19T02:54:58.164Z
**Completed Phase:** 08.1 (visual-evidence-extraction) — 3 plans — 2026-05-19
**Inserted Phase:** 08.2 (campaign-foundation) — 1 plan — 2026-05-19
**Completed Phase:** 08.2 (campaign-foundation) — 1 plan — 2026-05-19
