---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Scaled Literature Workstation
status: milestone_complete
stopped_at: Milestone complete (Phase 14 was final phase)
last_updated: 2026-05-29T00:16:34+08:00
last_activity: 2026-05-29
progress:
  total_phases: 17
  completed_phases: 17
  total_plans: 46
  completed_plans: 46
  percent: 100
---

# 项目状态

## 项目引用

参见: `.planning/PROJECT.md`

**核心价值:** 让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

**当前重点:** v2.0 core complete; deferred enhancements or next milestone only

## 当前位置

Phase: 14
Plan: 3/3 complete
Status: Milestone complete
Last activity: 2026-05-29

进度: [██████████] 100%

## 进度指标

**速度:**

- 已完成 plans: 46
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
| 9 | 3 | complete |
| 10 | 3 | complete |
| 11 | 3 | complete |
| 12 | 3 | complete |
| 13 | 3 | complete |
| 14 | 3 | complete |

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
- Phase 9 Evidence Signals & AI Scoring 支持 `rsa score P###`、`rsa score validate|status|review P###` 和 `rsa score campaign C###`；评分只进入 scoring YAML、review packet 和 campaign scoring summary，不写入 formal records。
- Phase 11 已完成：campaign 批量处理采用 `linked` 自动 workflow、`queued` 自动 metadata intake request；多篇之间小规模流水线并行，每篇内部继续按 Phase 10 顺序链执行。
- Phase 11 review queue 是监管入口，不是 formal approval 列表；`accepted | deferred | rejected | needs_followup` 只表示队列项处理状态。
- Phase 11 不执行 formal write；metadata intake accepted 后只生成 formal write request，正式写入仍必须通过人工确认的 formal gate。
- Phase 14 已完成 Background Worker & Scheduled Automation：新增本地 worker queue、one-shot runner、schedule 入队、status/logs、cancel/recover，并继续保持不重写 Phase 10/11、不绕过 formal write gate、不做 multi-agent。

### 待办

无。

### 阻塞和关注点

- Phase 8.1 已完成视觉候选提取闭环：`rsa visual extract|validate|status`、`visual_evidence_candidates.yaml`、local-only crops/context packets 和 PyMuPDF fail-closed 边界。
- Phase 8.2 已完成不依赖 Phase 9/10 的 campaign foundation：`rsa campaign create|import|validate|status`、`01_literature/campaigns/C###.yaml`、CSV/TSV/YAML 导入、轻量去重和 formal metadata 链接。
- Phase 9 已完成正文证据、Phase 8.1 视觉候选和 campaign 队列的评分闭环，但仍不能把未人工确认的 AI 评分或图像解释写入 formal records。
- Phase 10 已完成单篇 workflow primitive：`rsa workflow run|resume|status|report|stop|rerun` 串联 acquisition、reading draft、visual extraction、scoring 和 review packet，并保持 formal write gate 不可绕过。
- Phase 12 已完成本地 review workspace：`rsa review build|status|open|clean` 生成静态监管台、`review_workspace_manifest.yaml`、分组页、对象页和 actions checklist；只做监管导航，不执行 formal write。
- Phase 13 已覆盖 claim-level citation check、failure scenario monitoring、prompt/template drift 和 writing safety hardening。
- Browser session 下载得到的 PDF 只是本地授权阅读材料，不能自动写入 metadata、literature_map、agent_research_notes 或论文正文。

- Phase 13 已完成 writing safety hardening：`rsa safety check|validate|status|campaign` 只写 `01_literature/safety/`，提供 claim-level citation review、campaign failure monitor、deterministic drift anchors 和 formal boundary 检查，不生成正式学术结论。

## 会话连续性

Last session: 2026-05-27T20:34:04+08:00
Stopped at: Milestone complete - Phase 14 completed
Resume file: .planning/phases/13-writing-safety-hardening/13-VERIFICATION.md

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
**Planned Phase:** 09 (evidence-signals-ai-scoring) — 3 plans — 2026-05-21
**Completed Phase:** 09 (evidence-signals-ai-scoring) — 3 plans — 2026-05-21
**Planned Phase:** 10 (workflow-orchestrator) — 3 plans — 2026-05-21
**Completed Phase:** 10 (workflow-orchestrator) — 3 plans — 2026-05-21
**Discussed Phase:** 11 (campaign-batch-review) — context complete — 2026-05-26
**Planned Phase:** 11 (campaign-batch-review) — 3 plans — 2026-05-26
**Completed Phase:** 11 (campaign-batch-review) — 3 plans — 2026-05-26
**Discussed Phase:** 12 (local-review-workspace) — context complete — 2026-05-27
**Planned Phase:** 12 (local-review-workspace) — 3 plans — 2026-05-27
**Completed Phase:** 12 (local-review-workspace) — 3 plans — 2026-05-27
**Discussed Phase:** 13 (writing-safety-hardening) - context complete - 2026-05-28
**Planned Phase:** 13 (writing-safety-hardening) - 3 plans - 2026-05-28
**Completed Phase:** 13 (writing-safety-hardening) - 3 plans - 2026-05-28
**Inserted Phase:** 14 (background-worker-scheduled-automation) — planned future runtime-shape upgrade — 2026-05-26
**Discussed Phase:** 14 (background-worker-scheduled-automation) - context complete - 2026-05-29
**Planned Phase:** 14 (background-worker-scheduled-automation) - 3 plans - 2026-05-29
**Completed Phase:** 14 (background-worker-scheduled-automation) - 3 plans - 2026-05-29

## Accumulated Context

### Roadmap Evolution

- Phase 10 edited: Phase 10/11 automation split: single-paper sequential workflow primitive in Phase 10; campaign controlled pipeline parallelism in Phase 11
