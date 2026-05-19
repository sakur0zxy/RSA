# Requirements: v2.0 Scaled Literature Workstation

**创建时间:** 2026-05-13
**状态:** Draft for v2 planning

## 核心约束

- 用户可见内容中文优先；CLI help、成功提示、错误信息、模板说明、报告正文、README、GSD 文档和人工确认提示都必须可由中文用户直接理解。
- schema name、CLI flag、YAML key、Markdown 表格列、状态枚举和代码标识保持英文稳定；当它们出现在用户需要阅读或填写的位置时，必须提供中文解释或中文上下文。
- 不做未授权 PDF 获取，不绕过 paywall，不模拟机构账号批量下载。
- AI 生成内容、自动阅读草稿和 AI scoring 不得直接进入 formal records。
- Formal writes 仍必须经过 schema 校验、冲突检查和显式人工确认。
- 默认自动运行，用户主要负责监管、异常审阅、人工覆盖和 formal 批准。
- 所有自动产物必须标记 `evidence_level`；失败必须写状态记录，至少区分 `blocked` / `partial`。
- 视觉证据只作为候选证据，不直接形成正式学术结论。
- `formal write gate` 不得被 orchestrator、batch、UI 或后续 agent 编排绕过。
- 除非后续 phase 明确改用数据库，否则 v2 继续使用本地 Markdown/YAML。
- 普通用户基础版必须覆盖当前核心 agent 闭环；当前核心功能所需 Python 依赖应进入基础安装，optional extras 只用于非核心增强、未来扩展或开发测试。
- 缺少无法由 pip 可靠安装的外部资源时，必须通过 `rsa doctor` 或命令级 preflight check 给出中文修复提示，并 fail closed，不得生成伪结果。

## 全局语言要求

- [x] **LANG-01:** 当前项目入口文档记录中文优先语言策略，并说明英文标识保留范围。
- [x] **LANG-02:** 已实现 CLI 的主要 help、成功提示、错误信息和状态输出使用中文优先文案。
- [x] **LANG-03:** 模板和正式记录 seed 文件保留英文 key/列名，同时提供中文说明。
- [x] **LANG-04:** 后续新增 phase 必须在计划和测试中显式覆盖中文用户可见内容。

## 全局依赖要求

- [ ] **DEP-01:** 基础安装 `python -m pip install -e .` 包含当前核心 agent 功能所需 Python 依赖。
- [ ] **DEP-02:** optional extras 只用于非核心增强、未来扩展或开发测试；不得把当前核心闭环拆成用户必须手动选择的 extras。
- [ ] **DEP-03:** README/帮助文档提供中文功能依赖矩阵，明确区分基础安装、一次性环境初始化、非核心 extras 和开发依赖。
- [ ] **DEP-04:** 提供 `rsa doctor` 或等价环境自检，检查核心功能依赖、外部运行资源和修复命令。
- [ ] **DEP-05:** 依赖或外部资源缺失时，相关命令必须 fail closed，输出中文原因和修复命令，不得生成伪结果或 traceback-only 错误。
- [ ] **DEP-06:** `.planning/DEPENDENCY-POLICY.md` 维护命令级核心闭环契约和功能-依赖矩阵，后续 README、`pyproject.toml`、doctor 和 preflight 必须与其一致。
- [ ] **DEP-07:** `rsa doctor` 输出统一使用 `OK`、`WARN`、`BLOCKED` 状态，并列出受影响命令和中文修复命令。
- [ ] **DEP-08:** 命令级 preflight 与 `rsa doctor` 共享依赖检查逻辑，避免同一缺失项给出不一致结论。
- [ ] **DEP-09:** 测试覆盖 base runtime 下核心命令可启动、缺外部资源时 fail closed、doctor 输出与命令 gating 一致。

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

- [x] **V2-DL-01:** User can discover open access or user-authorized full-text candidates from trusted metadata.
- [x] **V2-DL-02:** Download commands must record authorization mode and fail closed for uncertain or blocked sources.
- [x] **V2-DL-03:** `rsa source find P###` defaults to monitored automation: it searches, reviews and downloads rule-approved sources without requiring step-by-step user intervention.
- [x] **V2-DL-04:** User can monitor and adjust automatic acquisition through candidate records, status/report commands, provider configuration, `--no-download`, and explicit manual download commands.
- [x] **V2-DL-05:** Automatic acquisition must remain auditable: every downloaded, skipped, blocked, failed or duplicate source records match evidence, authorization/access mode, Chinese reason text and local file handling status.

### Phase 7.1: Browser Session Provider

- [x] **V2-BROWSER-00:** Phase 7.1 is a browser-session provider under Phase 7 authorized acquisition, not a separate acquisition policy.
- [x] **V2-BROWSER-01:** User can define a `browser_session` custom provider with `login_url`, `allowed_domains`, local-only `session_storage`, query rules and Chinese usage restrictions.
- [x] **V2-BROWSER-02:** User can run `rsa source login <provider_id>` to open the provider login page, complete login manually, and store browser session state under `.rsa/sessions/` without saving passwords.
- [x] **V2-BROWSER-03:** RSA can reuse a user-authorized browser session to search and download papers the user has access to, while preserving Phase 7 candidate/source ledger audit records for every paper.
- [x] **V2-BROWSER-04:** User can inspect and clear provider sessions through Chinese-first CLI commands such as `rsa source session status <provider_id>` and `rsa source session clear <provider_id>`.
- [x] **V2-BROWSER-05:** Browser session providers must fail closed: no password storage, no silent extraction from existing browsers, no captcha/SSO/paywall bypass, no unauthorized mirrors, and all session files remain local-only and ignored by git.

### Phase 8: Auto Reading Draft

- [ ] **V2-READ-01:** User can generate reading note drafts only from local or authorized full text.
- [ ] **V2-READ-02:** Drafts distinguish source-grounded claims, short quotes, agent summary, uncertain points and human decisions.
- [ ] **V2-READ-03:** Drafts may output candidate `asset_suggestions`, but each suggestion must include Chinese reason text, confidence, and evidence basis; it must not assert that the figure/table is academically important.
- [ ] **V2-READ-04:** Phase 8 must not crop images, run OCR, extract chart data, write asset manifests, approve notes, score papers, or write formal records.

### Phase 8.1: Visual Evidence Extraction

- [x] **V2-VIS-01:** User can generate visual evidence candidates from Phase 8 `asset_suggestions`, local PDFs, or authorized assets without writing formal records.
- [x] **V2-VIS-02:** Cropped figure/table candidates and extracted visual assets remain local-only; auditable manifests/suggestions keep stable English keys with Chinese explanations.
- [x] **V2-VIS-03:** Caption extraction and basic OCR/region-text outputs are marked as draft/review-needed and include source page, region, confidence, extraction method, and Chinese uncertainty notes.
- [x] **V2-VIS-04:** Visual extraction must fail closed on unreadable PDFs/images, low confidence, ambiguous regions, unsupported chart types, or missing trace information; it must not invent numeric data.
- [x] **V2-VIS-05:** Phase 8.1 must not perform curve data restoration, advanced table reconstruction, chart-driven formal conclusions, or direct formal writes; those remain deferred advanced figure intelligence.

### Phase 9: Evidence Signals & AI Scoring

- [ ] **V2-SCORE-01:** AI scoring separates relevance, quality and read priority.
- [ ] **V2-SCORE-02:** Scoring must record evidence level, confidence, structured basis, rubric details and human review override.
- [ ] **V2-SCORE-03:** AI scoring is queue/review guidance only and cannot directly write formal records.
- [ ] **V2-SCORE-04:** Scoring may consume text evidence and Phase 8.1 visual evidence candidates, but must degrade gracefully when visual evidence is missing or low confidence.
- [ ] **V2-SCORE-05:** Any metadata enrichment in Phase 9 must stay lightweight and serve the scoring/review loop only: DOI/BibTeX basics, title/author/year normalization, and dedup assistance.

### Phase 10: Workflow Orchestrator

- [ ] **V2-WORKFLOW-01:** User can run one monitored workflow command that chains existing v1/v2 steps and advances automatically until review is needed.
- [ ] **V2-WORKFLOW-02:** Workflow runs must be resumable: interrupted runs record current step, completed outputs, pending review items and next action.
- [ ] **V2-WORKFLOW-03:** Workflow automation must stop before formal writes and produce a review packet for metadata, map, reading note or research-note approvals.
- [ ] **V2-WORKFLOW-04:** User can monitor and adjust workflow execution through status commands, local config, step-level toggles and explicit rerun/resume commands.

### Phase 11-13

- [ ] **V2-CAMPAIGN-01:** Campaigns support batch candidate import, deduplication and review queues.
- [ ] **V2-WORKSPACE-01:** Local review workspace supports verification, approval, reading draft review, visual evidence review and scoring review.
- [ ] **V2-WRITE-01:** Claim-level citation checks produce review guidance, not final academic conclusions.

### Deferred

- [ ] **V2-DEFER-01:** Crossref/OpenAlex/Zotero deep integrations remain deferred unless the core loop later proves they are necessary.
- [ ] **V2-DEFER-02:** Advanced figure intelligence, including curve data restoration and advanced table structure understanding, remains deferred beyond Phase 8.1.
- [ ] **V2-DEFER-03:** Multi-agent orchestration remains optional and cannot bypass formal write gates.
