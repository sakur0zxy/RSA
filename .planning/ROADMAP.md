# Roadmap: RSA 科研 Agent Harness

## 里程碑

- **v1.0 Local Harness** - Phase 1-5，已于 2026-05-13 发布。详见 `.planning/milestones/v1.0-ROADMAP.md`。
- **v2.0 Scaled Literature Workstation** - Phase 6-13 与插入 Phase 7.1、Phase 8.1 为核心范围；重型 metadata 集成、高级图表智能和 multi-agent 编排为延后范围。

## v2 全局原则

- 默认自动运行，用户主要负责监管、异常审阅、人工覆盖和 formal 批准。
- 所有 AI 产物默认只进入 staging / review packet，不直接进入 formal records。
- 所有自动产物必须标记 `evidence_level`；失败必须记录 `blocked` 或 `partial` 状态和中文原因。
- 视觉证据只作为候选证据，不直接形成正式学术结论。
- `formal write gate` 不得被 orchestrator、batch、UI 或后续 agent 编排绕过。

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
- [ ] Phase 9: Evidence Signals & AI Scoring - 融合正文证据和视觉证据候选，生成 relevance、quality、read priority 辅助评分。
- [ ] Phase 10: Workflow Orchestrator - 串联 v1/v2 命令，默认自动跑到 review packet，并让用户监控关键环节和调整流程。
- [ ] Phase 11: Campaign & Batch Review - 支持批量候选导入、去重、review queue、状态流转和排序。
- [ ] Phase 12: Local Review Workspace - 提供本地监管台审阅候选、PDF、阅读草稿、视觉证据、评分和 formal write 请求。
- [ ] Phase 13: Writing Safety & Hardening - 做 claim-level citation check，并增强 eval、回归测试、prompt/template drift 检测和 guardrails。

</details>

## 下一步

当前执行目标：**进入 Phase 9: Evidence Signals & AI Scoring 规划**。

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

Deferred items：Crossref/OpenAlex/Zotero 等重型 scholarly metadata 深集成、高级图表智能、复杂多 agent 编排。轻量 DOI/BibTeX 补全、title/author/year 标准化和 dedup 辅助可在 Phase 9 内按主闭环需要处理。

## 进度

| Milestone | Phases | Plans Complete | 状态 | 完成时间 |
|-----------|--------|----------------|------|----------|
| v1.0 Local Harness | 1-5 | 14/14 | 已发布 | 2026-05-13 |
| v2.0 Scaled Literature Workstation | 6-13 core + 7.1, 8.1 and 8.2 inserted; deferred advanced integrations | 14/14 completed for Phase 6-8.2 | Phase 8.2 complete，next plan Phase 9 | 2026-05-19 |

---

*Roadmap updated after Phase 8.2 campaign foundation implementation: 2026-05-19*
