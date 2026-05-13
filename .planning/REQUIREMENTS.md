# Requirements: v2.0 Scaled Literature Workstation

**创建时间:** 2026-05-13
**状态:** Draft for v2 planning

## 核心约束

- 用户可见内容中文优先；CLI help、成功提示、错误信息、模板说明、报告正文、README、GSD 文档和人工确认提示都必须可由中文用户直接理解。
- schema name、CLI flag、YAML key、Markdown 表格列、状态枚举和代码标识保持英文稳定；当它们出现在用户需要阅读或填写的位置时，必须提供中文解释或中文上下文。
- 不做未授权 PDF 获取，不绕过 paywall，不模拟机构账号批量下载。
- AI 生成内容、自动阅读草稿和 AI scoring 不得直接进入 formal records。
- Formal writes 仍必须经过 schema 校验、冲突检查和显式人工确认。
- 除非后续 phase 明确改用数据库，否则 v2 继续使用本地 Markdown/YAML。

## 全局语言要求

- [x] **LANG-01:** 当前项目入口文档记录中文优先语言策略，并说明英文标识保留范围。
- [x] **LANG-02:** 已实现 CLI 的主要 help、成功提示、错误信息和状态输出使用中文优先文案。
- [x] **LANG-03:** 模板和正式记录 seed 文件保留英文 key/列名，同时提供中文说明。
- [ ] **LANG-04:** 后续新增 phase 必须在计划和测试中显式覆盖中文用户可见内容。

## Phase 6: Asset & Source Foundation

- [x] **V2-SRC-01:** User can register a local/provided/authorized source file for a formal `P###` paper without modifying formal metadata.
- [x] **V2-SRC-02:** Source records preserve `source_type`, `authorization`, `license_note`, original path, local path, status and added time.
- [x] **V2-SRC-03:** Source validation is read-only and fails when a referenced local file is missing.
- [x] **V2-ASSET-01:** User can add screenshots, figures, tables, results or other local assets for a formal `P###` paper.
- [x] **V2-ASSET-02:** Asset manifests preserve `asset_id`, `kind`, label, description, page/figure metadata, original path, local path and added time.
- [x] **V2-ASSET-03:** PDF and binary assets remain local-only while source/asset manifests remain auditable text records.
- [x] **V2-ASSET-04:** CLI output and validation errors use Chinese-first user-facing text.

## Future Phase Requirements

### Phase 7: Authorized Acquisition

- [ ] **V2-DL-01:** User can discover open access or user-authorized full-text candidates from trusted metadata.
- [ ] **V2-DL-02:** Download commands must record authorization mode and fail closed for uncertain or blocked sources.

### Phase 8: Auto Reading Draft

- [ ] **V2-READ-01:** User can generate reading note drafts only from local or authorized full text.
- [ ] **V2-READ-02:** Drafts distinguish source-grounded claims, short quotes, agent summary, uncertain points and human decisions.

### Phase 9: Evidence Signals & AI Scoring

- [ ] **V2-SCORE-01:** AI scoring separates relevance, quality and read priority.
- [ ] **V2-SCORE-02:** Scoring must record evidence level, confidence, structured basis, rubric details and human review override.
- [ ] **V2-SCORE-03:** AI scoring is queue/review guidance only and cannot directly write formal records.

### Phase 10-14

- [ ] **V2-CAMPAIGN-01:** Campaigns support batch candidate import, deduplication and review queues.
- [ ] **V2-API-01:** Scholarly API results enter staging only.
- [ ] **V2-UI-01:** Local review UI supports verification, approval and scoring review.
- [ ] **V2-WRITE-01:** Claim-level citation checks produce review guidance, not final academic conclusions.
- [ ] **V2-ORCH-01:** Multi-agent orchestration remains optional and cannot bypass formal write gates.
