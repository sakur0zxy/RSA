# Roadmap: RSA 科研 Agent Harness

## 里程碑

- **v1.0 Local Harness** - Phase 1-5，已于 2026-05-13 发布。详见 `.planning/milestones/v1.0-ROADMAP.md`。
- **v2.0 Scaled Literature Workstation** - Phase 6-14 与插入 Phase 7.1、Phase 8.1、Phase 8.2 为核心范围；重型 metadata 集成、高级图表智能和 multi-agent 编排为延后范围。

## v2 全局原则

- 默认自动运行，用户主要负责监管、异常审阅、人工覆盖和 formal 批准。
- 所有 AI 产物默认只进入 staging / review packet，不直接进入 formal records。
- 所有自动产物必须标记 `evidence_level`；失败必须记录 `blocked` 或 `partial` 状态和中文原因。
- 视觉证据只作为候选证据，不直接形成正式学术结论。
- `formal write gate` 不得被 orchestrator、batch、UI 或后续 agent 编排绕过。
- 自动化调度采用分层并行：Phase 10 提供单篇顺序 workflow primitive；Phase 11 在其上做 campaign 级受控并行、队列限流和批量异常聚合。

## Phase 概览

<details>
<summary>v1.0 Local Harness - 已发布 2026-05-13</summary>

- [x] Phase 1: Harness Foundation - 3/3 plans，完成于 2026-05-11。
- [x] Phase 2: Literature Records Pipeline - 4/4 plans，完成于 2026-05-11。
- [x] Phase 3: Research Round Integration - 3/3 plans，完成于 2026-05-12。
- [x] Phase 4: Reading Note Workflow - 2/2 plans，完成于 2026-05-12。
- [x] Phase 5: Evaluation and Hardening - 2/2 plans，完成于 2026-05-13。

</details>

<details open>
<summary>v2.0 Scaled Literature Workstation - 规划中</summary>

- [x] Phase 6: Asset & Source Foundation - 建立 PDF、截图、图表、结果图和 source ledger 的本地资产基础。
- [x] Phase 7: Authorized Acquisition - 3/3 plans，完成于 2026-05-14；支持 open access、用户提供和用户授权来源的自动全文获取，不绕过 paywall。
- [x] Phase 7.1: Browser Session Provider (INSERTED) - 2/2 plans，完成于 2026-05-14；作为 Phase 7 的浏览器会话子能力，支持用户自行登录资料库后，RSA 复用本地授权浏览器会话检索和下载用户有权限访问的论文。
- [x] Phase 8: Auto Reading Draft - 3/3 plans，完成于 2026-05-16；基于本地或已授权全文生成中文自动 reading note draft、AI 初审分、review packet，并输出候选 `asset_suggestions`。
- [x] Phase 8.1: Visual Evidence Extraction (INSERTED) - 3/3 plans，完成于 2026-05-19；基于 Phase 8 候选建议和授权/本地 PDF 生成图表/表格视觉证据候选、裁图、本地 context packet 和 page/region/source trace；输出只作为 staging/review 候选。
- [x] Phase 8.2: Campaign Foundation (INSERTED) - 1/1 plan，完成于 2026-05-19；提前实现不依赖 Phase 9/10 的批量候选队列、CSV/TSV/YAML 导入、轻量去重、正式 metadata 链接和只读状态校验。
- [x] Phase 9: Evidence Signals & AI Scoring - 3/3 plans，完成于 2026-05-21；融合正文证据、视觉证据候选和 campaign 队列，生成 relevance、quality、read priority 辅助评分、review packet 和 campaign scoring summary。
- [x] Phase 10: Workflow Orchestrator - 3/3 plans，完成于 2026-05-21；串联 v1/v2 命令，为单篇论文提供顺序、可恢复、可监控的 workflow primitive，默认自动跑到 review packet，并让用户监控关键环节和调整流程。
- [x] Phase 11: Campaign & Batch Review - 3/3 plans，完成于 2026-05-26；在 Phase 10 workflow primitive 之上支持批量候选、受控流水线并行、metadata intake、review queue、状态流转、排序和批量异常聚合。
- [ ] Phase 12: Local Review Workspace - 提供本地监管台审阅候选、PDF、阅读草稿、视觉证据、评分和 formal write 请求。
- [ ] Phase 13: Writing Safety & Hardening - 做 claim-level citation check，并增强 eval、回归测试、prompt/template drift 检测和 guardrails。
- [ ] Phase 14: Background Worker & Scheduled Automation - 作为运行形态升级，支持后台 worker、异步任务执行、长任务恢复、status 监控、定时 campaign run 和 worker 日志摘要。

</details>

## 下一步

当前执行目标：**Phase 11: Campaign & Batch Review 已完成，下一步进入 Phase 12 Local Review Workspace 讨论/计划**。

Phase 6 已完成本地资产和来源记录基础：

1. `01_literature/sources/P###.yaml`：记录授权来源、原始路径、本地副本、授权方式和 license note。
2. `01_literature/assets/P###/manifest.yaml`：记录截图、图表、结果图等本地资产 manifest。
3. `rsa source ...` 和 `rsa asset ...`：提供 CLI 添加、校验和查看状态。
4. 保持 PDF 和真实图片文件 local-only；只跟踪可审计 metadata/manifest。

Phase 7 已完成以下 3 个计划：

1. `07-01 Source Candidate Model And Provider Configuration`：建立候选来源记录、自定义 provider schema、匹配证据和自动下载资格判定。
2. `07-02 Authorized Download Engine And Source Ledger Integration`：实现授权下载、`.tmp` 临时文件、hash 去重、多版本主版本选择和 source ledger 写入。
3. `07-03 CLI Workflow, Documentation And Regression Coverage`：接入 `rsa source find|candidates|download`，补齐中文文档、监控入口和回归测试。

Phase 7.1 是 Phase 7 授权获取体系下的浏览器会话子能力，不是一套独立下载系统。它的目标是在不保存账号密码、不绕过 SSO/验证码/paywall 的前提下，让用户可以打开自定义资料库登录页并自行登录；RSA 只保存本地-only browser session state，后续用该授权会话检索和下载用户有权限访问的其它论文。

Phase 7.1 已完成以下 2 个计划：

1. `07.1-01 Browser Session Provider Schema And Session CLI`：建立 `browser_session` provider schema、`.rsa/sessions/` local-only session、`rsa source login` 和 `rsa source session status|clear`。
2. `07.1-02 Session-Aware Acquisition Integration And Verification`：将 browser session provider 接入 Phase 7 source candidate、cookie-based direct PDF 下载、source ledger、PDF acquisition report 和中文文档。

Phase 8 已基于 Phase 7 / 7.1 获取到的本地 PDF/source ledger 生成可审阅的自动阅读草稿。Phase 8 的 `asset_suggestions` 只表示候选视觉证据建议，必须记录推荐原因、置信度和证据依据；它不能直接断言某张图表已经是重要图表，也不负责裁图或 OCR。

Phase 8.1 已完成 Phase 8 之后的插入增强：在评分前处理最小必要视觉证据，从授权 PDF 或本地资产中生成裁图/裁表候选、提取 caption/region text、写入本地 context packet，并记录 page/region/source trace。Phase 8.1 不做曲线数据自动还原、高级表格结构理解、LLM 图像结论或图表驱动的自动结论生成；这些内容进入 Phase 9 或 deferred advanced figure intelligence。

Phase 8.2 已完成提前拆出的 Campaign Foundation：它只负责批量候选队列、导入、轻量去重、状态汇总和 formal metadata 轻量链接；不做 AI scoring、不调用 workflow orchestrator、不做 UI，也不执行 formal write。完整 Campaign & Batch Review 仍留在 Phase 11，并在 Phase 9/10 完成后接入评分和自动运行状态。

Phase 9 已完成 Evidence Signals & AI Scoring：它从正式 metadata、Phase 8 reading draft、Phase 8.1 视觉证据候选和 Phase 8.2 campaign 队列中生成结构化 evidence signals，并输出 `01_literature/scores/P###_scoring.yaml`、`P###_review_packet.md` 和 `campaigns/C###_scoring_summary.yaml`。AI 评分只作为 staging/review guidance，支持人工 review/override，不直接写入 formal records。

Phase 10/11 的自动化分工已经锁定为“单篇顺序链 + campaign 级受控并行”。Phase 10 只负责把单篇论文按 acquisition -> reading draft -> visual extraction -> scoring -> review packet 顺序跑成可靠 workflow primitive，并保留 `campaign_id`、`run_id`、`step_status`、`retry_policy`、`artifacts` 等字段供后续复用。Phase 11 才负责多篇论文之间的小规模流水线并行、阶段队列限流、campaign 排序和批量异常聚合。

Phase 10 已完成 Workflow Orchestrator：它新增 `rsa workflow run|resume|status|report|stop|rerun`，把单篇正式文献自动推进到中文 review packet；run state 写入 `01_literature/workflows/P###/RUN-###.yaml`，并保留 future interfaces 给后续 LLM visual analysis 和高级图表智能。Phase 10 不执行 campaign worker queue、不并行处理多篇论文、不绕过 formal write gate。

Phase 11 已完成：Phase 11 在 Phase 10 single-paper workflow primitive 之上实现 campaign 级小规模流水线并行、metadata intake request、formal write request 待审对象、review queue、batch report、pause/resume 和中文监管输出。Phase 11 默认自动推进阅读、分析、评分和 review packet，但正式写入仍必须通过人工确认的 formal gate。

Phase 14 已加入路线图，定位为 Background Worker & Scheduled Automation，即“运行形态升级”。它在 Phase 11 同步 CLI、Phase 12 本地监管台和 Phase 13 hardening 稳定后，再处理后台 worker、异步任务、长任务恢复、status 监控和定时 campaign run；它不重写 Phase 10/11 逻辑，不绕过 formal write gate，不做 multi-agent。

Deferred items：Crossref/OpenAlex/Zotero 等重型 scholarly metadata 深集成、高级图表智能、复杂多 agent 编排。轻量 DOI/BibTeX 补全、title/author/year 标准化和 dedup 辅助可在 Phase 9/11 内按主闭环需要处理。

## 进度

| Milestone | Phases | Plans Complete | 状态 | 完成时间 |
|-----------|--------|----------------|------|----------|
| v1.0 Local Harness | 1-5 | 14/14 | 已发布 | 2026-05-13 |
| v2.0 Scaled Literature Workstation | 6-14 core + 7.1, 8.1 and 8.2 inserted; deferred advanced integrations | 23/23 completed for Phase 6-11 planned | Phase 11 complete，next Phase 12 | 2026-05-26 |

---

*Roadmap updated after Phase 11 campaign implementation: 2026-05-26*

## GSD 解析索引

> 这一节是给本地 `gsd-sdk` 使用的 machine-readable phase index。  
> 原因：当前 SDK 主要识别 `### Phase N:` 形式的标题，并且会忽略 `<details>` 折叠块中的 phase checklist。  
> 人类阅读仍以上面的 Phase 概览和详细说明为主；后续新增或调整 phase 时，这里也要同步更新。

### Phase 1: Harness Foundation

Status: complete. v1.0 Local Harness phase.

### Phase 2: Literature Records Pipeline

Status: complete. v1.0 Local Harness phase.

### Phase 3: Research Round Integration

Status: complete. v1.0 Local Harness phase.

### Phase 4: Reading Note Workflow

Status: complete. v1.0 Local Harness phase.

### Phase 5: Evaluation and Hardening

Status: complete. v1.0 Local Harness phase.

### Phase 6: Asset & Source Foundation

Status: complete. Establish local assets, source ledger and auditable source/asset records.

### Phase 7: Authorized Acquisition

Status: complete. Discover, review and download authorized full-text sources without bypassing access controls.

### Phase 7.1: Browser Session Provider

Status: complete. Browser-session provider under Phase 7 authorized acquisition.

### Phase 8: Auto Reading Draft

Status: complete. Generate structured Chinese reading drafts, review packets and candidate `asset_suggestions`.

### Phase 8.1: Visual Evidence Extraction

Status: complete. Convert reading draft suggestions and authorized/local PDFs into visual evidence candidates.

### Phase 8.2: Campaign Foundation

Status: complete. Provide dependency-free campaign queue creation, import, dedup, linking and read-only status validation.

### Phase 9: Evidence Signals & AI Scoring

Status: complete. Fuse text evidence, visual candidates and campaign queues into AI-assisted relevance, quality and read-priority scoring.

### Phase 10: Workflow Orchestrator

Status: complete. Chain existing v1/v2 commands into a single-paper sequential, resumable and monitorable workflow primitive that automatically runs to review packet while preserving formal-write boundaries.

### Phase 11: Campaign & Batch Review

Status: complete. Integrate campaign queues with Phase 10 workflow runs, controlled pipeline parallelism, ranking, filtering, review queue automation and batch exception aggregation.

### Phase 12: Local Review Workspace

Status: planned. Provide a local supervision workspace for candidates, PDFs, reading drafts, visual evidence, scoring and formal write requests.

### Phase 13: Writing Safety & Hardening

Status: planned. Add claim-level citation checks, regression coverage, prompt/template drift detection and stronger guardrails.

### Phase 14: Background Worker & Scheduled Automation

Status: planned. Upgrade the runtime shape after Phase 11-13 by adding background workers, async task execution, long-task recovery, status monitoring, scheduled campaign runs and worker log summaries without bypassing formal-write gates.
