# Roadmap: RSA 科研 Agent Harness

## 里程碑

- **v1.0 Local Harness** - Phase 1-5，已于 2026-05-13 发布。详见 `.planning/milestones/v1.0-ROADMAP.md`。
- **v2.0 Scaled Literature Workstation** - Phase 6-13 为核心范围；Phase 14 为可选延后范围。

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
- [ ] Phase 7: Authorized Acquisition - 支持 open access、用户提供和用户授权来源的自动全文获取，不绕过 paywall。
- [ ] Phase 8: Auto Reading Draft - 基于本地或已授权全文生成可审阅 reading note draft。
- [ ] Phase 9: Evidence Signals & AI Scoring - 抽取结构化证据，并生成 relevance、quality、read priority 辅助评分。
- [ ] Phase 10: Campaign & Batch Review - 支持批量候选导入、去重、review queue、状态流转和排序。
- [ ] Phase 11: Scholarly Metadata Integrations - 接入 DOI、Crossref、OpenAlex、BibTeX、Zotero 等，但只进入 staging。
- [ ] Phase 12: Local Review UI - 提供本地界面审阅候选、PDF、阅读草稿、评分和 formal write 请求。
- [ ] Phase 13: Writing Support & Hardening - 做 claim-level citation check，并增强 eval、回归测试和 guardrails。
- [ ] Phase 14: Multi-Agent Orchestration - 可选延后；仅在前面 guardrails 稳定后开启。

</details>

## 下一步

当前执行目标：**Phase 7: Authorized Acquisition**。

Phase 6 已完成本地资产和来源记录基础：

1. `01_literature/sources/P###.yaml`：记录授权来源、原始路径、本地副本、授权方式和 license note。
2. `01_literature/assets/P###/manifest.yaml`：记录截图、图表、结果图等本地资产 manifest。
3. `rsa source ...` 和 `rsa asset ...`：提供 CLI 添加、校验和查看状态。
4. 保持 PDF 和真实图片文件 local-only；只跟踪可审计 metadata/manifest。

Phase 7 将在此基础上实现受控的 open access / 用户授权全文发现与下载。

## 进度

| Milestone | Phases | Plans Complete | 状态 | 完成时间 |
|-----------|--------|----------------|------|----------|
| v1.0 Local Harness | 1-5 | 14/14 | 已发布 | 2026-05-13 |
| v2.0 Scaled Literature Workstation | 6-13 core, 14 optional | 2/2 | Phase 6 完成 | - |

---

*Roadmap updated after Phase 6 Asset & Source Foundation: 2026-05-13*
