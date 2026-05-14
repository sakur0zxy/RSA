# Roadmap: RSA 科研 Agent Harness

## 里程碑

- **v1.0 Local Harness** - Phase 1-5，已于 2026-05-13 发布。详见 `.planning/milestones/v1.0-ROADMAP.md`。
- **v2.0 Scaled Literature Workstation** - Phase 6-14 与插入 Phase 7.1 为核心范围；Phase 15 为可选延后范围。

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
- [x] Phase 7.1: Browser Session Provider (INSERTED) - 2/2 plans，完成于 2026-05-14；支持用户自行登录资料库后，RSA 复用本地授权浏览器会话检索和下载用户有权限访问的论文。
- [ ] Phase 8: Auto Reading Draft - 基于本地或已授权全文生成可审阅 reading note draft。
- [ ] Phase 9: Evidence Signals & AI Scoring - 抽取结构化证据，并生成 relevance、quality、read priority 辅助评分。
- [ ] Phase 10: Workflow Orchestrator - 串联 v1/v2 命令，默认自动跑到 review packet，并让用户监控关键环节和调整流程。
- [ ] Phase 11: Campaign & Batch Review - 支持批量候选导入、去重、review queue、状态流转和排序。
- [ ] Phase 12: Scholarly Metadata Integrations - 接入 DOI、Crossref、OpenAlex、BibTeX、Zotero 等，但只进入 staging。
- [ ] Phase 13: Local Review UI - 提供本地界面审阅候选、PDF、阅读草稿、评分和 formal write 请求。
- [ ] Phase 14: Writing Support & Hardening - 做 claim-level citation check，并增强 eval、回归测试和 guardrails。
- [ ] Phase 15: Multi-Agent Orchestration - 可选延后；仅在前面 guardrails 稳定后开启。

</details>

## 下一步

当前执行目标：**Phase 8: Auto Reading Draft**。

Phase 6 已完成本地资产和来源记录基础：

1. `01_literature/sources/P###.yaml`：记录授权来源、原始路径、本地副本、授权方式和 license note。
2. `01_literature/assets/P###/manifest.yaml`：记录截图、图表、结果图等本地资产 manifest。
3. `rsa source ...` 和 `rsa asset ...`：提供 CLI 添加、校验和查看状态。
4. 保持 PDF 和真实图片文件 local-only；只跟踪可审计 metadata/manifest。

Phase 7 已完成以下 3 个计划：

1. `07-01 Source Candidate Model And Provider Configuration`：建立候选来源记录、自定义 provider schema、匹配证据和自动下载资格判定。
2. `07-02 Authorized Download Engine And Source Ledger Integration`：实现授权下载、`.tmp` 临时文件、hash 去重、多版本主版本选择和 source ledger 写入。
3. `07-03 CLI Workflow, Documentation And Regression Coverage`：接入 `rsa source find|candidates|download`，补齐中文文档、监控入口和回归测试。

Phase 7.1 是 Phase 7 的插入增强，目标是在不保存账号密码、不绕过 SSO/验证码/paywall 的前提下，让用户可以打开自定义资料库登录页并自行登录；RSA 只保存本地-only browser session state，后续用该授权会话检索和下载用户有权限访问的其它论文。

Phase 7.1 已完成以下 2 个计划：

1. `07.1-01 Browser Session Provider Schema And Session CLI`：建立 `browser_session` provider schema、`.rsa/sessions/` local-only session、`rsa source login` 和 `rsa source session status|clear`。
2. `07.1-02 Session-Aware Acquisition Integration And Verification`：将 browser session provider 接入 Phase 7 source candidate、cookie-based direct PDF 下载、source ledger、PDF acquisition report 和中文文档。

Phase 8 将基于 Phase 7 / 7.1 获取到的本地 PDF/source ledger 生成可审阅的自动阅读草稿。

## 进度

| Milestone | Phases | Plans Complete | 状态 | 完成时间 |
|-----------|--------|----------------|------|----------|
| v1.0 Local Harness | 1-5 | 14/14 | 已发布 | 2026-05-13 |
| v2.0 Scaled Literature Workstation | 6-14 core + 7.1 inserted, 15 optional | 7/7 completed for Phase 6-7.1 | Phase 7.1 complete，next Phase 8 | 2026-05-14 |

---

*Roadmap updated after Phase 7.1 completion: 2026-05-14*
