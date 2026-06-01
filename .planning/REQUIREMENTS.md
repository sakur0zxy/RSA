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

- [x] **DEP-01:** 基础安装 `python -m pip install -e .` 包含当前核心 agent 功能所需 Python 依赖。
- [x] **DEP-02:** optional extras 只用于非核心增强、未来扩展或开发测试；不得把当前核心闭环拆成用户必须手动选择的 extras。
- [x] **DEP-03:** README/帮助文档提供中文功能依赖矩阵，明确区分基础安装、一次性环境初始化、非核心 extras 和开发依赖。
- [x] **DEP-04:** 提供 `rsa doctor` 或等价环境自检，检查核心功能依赖、外部运行资源和修复命令。
- [x] **DEP-05:** 依赖或外部资源缺失时，相关命令必须 fail closed，输出中文原因和修复命令，不得生成伪结果或 traceback-only 错误。
- [x] **DEP-06:** `.planning/DEPENDENCY-POLICY.md` 维护命令级核心闭环契约和功能-依赖矩阵，后续 README、`pyproject.toml`、doctor 和 preflight 必须与其一致。
- [x] **DEP-07:** `rsa doctor` 输出统一使用 `OK`、`WARN`、`BLOCKED` 状态，并列出受影响命令和中文修复命令。
- [x] **DEP-08:** 命令级 preflight 与 `rsa doctor` 共享依赖检查逻辑，避免同一缺失项给出不一致结论。
- [x] **DEP-09:** 测试覆盖 base runtime 下核心命令可启动、缺外部资源时 fail closed、doctor 输出与命令 gating 一致。

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

- [x] **V2-READ-01:** User can generate reading note drafts only from local or authorized full text.
- [x] **V2-READ-02:** Drafts distinguish source-grounded claims, short quotes, agent summary, uncertain points and human decisions.
- [x] **V2-READ-03:** Drafts may output candidate `asset_suggestions`, but each suggestion must include Chinese reason text, confidence, and evidence basis; it must not assert that the figure/table is academically important.
- [x] **V2-READ-04:** Phase 8 must not crop images, run OCR, extract chart data, write asset manifests, approve notes, score papers, or write formal records.

### Phase 8.1: Visual Evidence Extraction

- [x] **V2-VIS-01:** User can generate visual evidence candidates from Phase 8 `asset_suggestions`, local PDFs, or authorized assets without writing formal records.
- [x] **V2-VIS-02:** Cropped figure/table candidates and extracted visual assets remain local-only; auditable manifests/suggestions keep stable English keys with Chinese explanations.
- [x] **V2-VIS-03:** Caption extraction and basic OCR/region-text outputs are marked as draft/review-needed and include source page, region, confidence, extraction method, and Chinese uncertainty notes.
- [x] **V2-VIS-04:** Visual extraction must fail closed on unreadable PDFs/images, low confidence, ambiguous regions, unsupported chart types, or missing trace information; it must not invent numeric data.
- [x] **V2-VIS-05:** Phase 8.1 must not perform curve data restoration, advanced table reconstruction, chart-driven formal conclusions, or direct formal writes; those remain deferred advanced figure intelligence.

### Phase 8.2: Campaign Foundation

- [x] **V2-CAMP-FND-01:** User can create a campaign queue record under `01_literature/campaigns/C###.yaml` with Chinese name, objective, status and automation boundary.
- [x] **V2-CAMP-FND-02:** User can import batch candidates from CSV/TSV/YAML into a campaign without requiring Phase 9 scoring or Phase 10 workflow orchestration.
- [x] **V2-CAMP-FND-03:** Campaign import performs lightweight dedup using DOI, URL, or title/year/first_author and marks duplicates without deleting source rows.
- [x] **V2-CAMP-FND-04:** Campaign import can link items to existing formal `metadata/P###.yaml`, while keeping `linked` distinct from reading/scoring/formal approval.
- [x] **V2-CAMP-FND-05:** Campaign validate/status commands are read-only, Chinese-first, and report queued, linked, duplicate, needs_review and blocked counts.

### Phase 9: Evidence Signals & AI Scoring

- [x] **V2-SCORE-01:** AI scoring separates relevance, quality and read priority.
- [x] **V2-SCORE-02:** Scoring must record evidence level, confidence, structured basis, rubric details and human review override.
- [x] **V2-SCORE-03:** AI scoring is queue/review guidance only and cannot directly write formal records.
- [x] **V2-SCORE-04:** Scoring may consume text evidence and Phase 8.1 visual evidence candidates, but must degrade gracefully when visual evidence is missing or low confidence.
- [x] **V2-SCORE-05:** Any metadata enrichment in Phase 9 must stay lightweight and serve the scoring/review loop only: DOI/BibTeX basics, title/author/year normalization, and dedup assistance.

### Phase 10: Workflow Orchestrator

- [x] **V2-WORKFLOW-01:** User can run one monitored workflow command that chains existing v1/v2 steps and advances automatically until review is needed.
- [x] **V2-WORKFLOW-02:** Workflow runs must be resumable: interrupted runs record current step, completed outputs, pending review items and next action.
- [x] **V2-WORKFLOW-03:** Workflow automation must stop before formal writes and produce a review packet for metadata, map, reading note or research-note approvals.
- [x] **V2-WORKFLOW-04:** User can monitor and adjust workflow execution through status commands, local config, step-level toggles and explicit rerun/resume commands.
- [x] **V2-WORKFLOW-05:** Phase 10 orchestrates a single-paper sequential chain: acquisition -> reading draft -> visual extraction -> scoring -> review packet.
- [x] **V2-WORKFLOW-06:** Phase 10 run state must preserve batch-ready fields such as `run_id`, `paper_id`, `campaign_id`, `step_id`, `step_status`, `artifacts`, `retry_policy` and Chinese blocked/partial reasons, but must not implement campaign worker queues or uncontrolled parallelism.

### Phase 11-14

- [x] **V2-CAMPAIGN-01:** Campaigns integrate Phase 8.2 queues with Phase 9 scoring, Phase 10 workflow runs, ranking/filtering and batch review automation.
- [x] **V2-CAMPAIGN-02:** Campaign processing uses controlled pipeline parallelism across papers while preserving sequential dependencies inside each paper workflow.
- [x] **V2-CAMPAIGN-03:** Campaign-level concurrency must be configurable and conservative by default, with separate limits for acquisition, reading draft, visual extraction and scoring.
- [x] **V2-CAMPAIGN-04:** Batch failures must support `continue_on_error`, `pause_on_auth_error` and `pause_on_formal_request` semantics, with Chinese status reports and no automatic formal writes.
- [x] **V2-CAMPAIGN-05:** `queued` campaign items generate metadata intake requests with `auto_triaged` machine triage by default, but must not create formal `paper_id` records or write `metadata/P###.yaml` directly.
- [x] **V2-CAMPAIGN-06:** Metadata intake requests and formal write requests must be designed as migratable independent objects with stable ids, source campaign/item links, status, candidate data and Chinese rationale.
- [x] **V2-CAMPAIGN-07:** Campaign review queues must group items by status, sort within groups by read priority/risk/confidence, preserve artifact links, and support `accepted | deferred | rejected | needs_followup` review decisions without treating them as formal approvals.
- [x] **V2-CAMPAIGN-08:** Campaign run state and batch reports must be stored beside the campaign in local YAML/Markdown, use Chinese-first supervision text, avoid sensitive/full-log content, and keep `C###.yaml` as a lightweight queue index.
- [x] **V2-CAMPAIGN-09:** Campaign CLI must extend `rsa campaign` with `run`, `resume`, `pause`, `queue` and `report`; normal run must not rerun completed staging items, and `--dry-run`, `--items` and `--status` filters must be supported.
- [x] **V2-WORKSPACE-01:** Local review workspace supports verification, approval, reading draft review, visual evidence review and scoring review.
- [x] **V2-WRITE-01:** Claim-level citation checks produce review guidance, not final academic conclusions.
- [x] **V2-WRITE-02:** Phase 13 hardening/eval must monitor campaign failure scenarios including authorization errors, blocked/partial aggregation, review queue ordering regression, formal request non-execution, metadata intake not writing formal metadata, completed-item non-rerun, low-confidence/high-priority queue admission, and campaign error-policy semantics.
- [x] **V2-WORKER-01:** Phase 14 adds Background Worker & Scheduled Automation only after the synchronous Phase 11 campaign path, Phase 12 supervision workspace and Phase 13 hardening have a stable contract.
- [x] **V2-WORKER-02:** Worker mode must reuse Phase 10 workflow primitives and Phase 11 campaign scheduling state instead of rewriting their core logic.
- [x] **V2-WORKER-03:** Worker mode may add background workers, async task execution, long-task recovery, status monitoring, scheduled campaign runs and worker log summaries.
- [x] **V2-WORKER-04:** Worker mode must not bypass formal write gates, implement multi-agent orchestration, or require complex cloud services for the local-first core workflow.

### Phase 15: Codex Account OAuth LLM Provider

- [x] **V2-CODEX-01:** RSA can define an optional `codex_oauth` or equivalent LLM provider that uses a user-authorized Codex/ChatGPT account session for AI tasks without replacing existing API-key and OpenAI-compatible providers.
- [x] **V2-CODEX-02:** Provider authentication must use an explicit user authorization flow or import path; it must not automate the ChatGPT web UI, scrape browser cookies, store account passwords, or bypass OpenAI/Codex access controls.
- [x] **V2-CODEX-03:** OAuth/session material must be stored local-only, ignored by git, refreshable when supported, and cleared through an explicit CLI command.
- [x] **V2-CODEX-04:** `rsa doctor` and command-level preflight must report provider availability, missing login, expired tokens, quota/rate limits, unsupported models and recovery actions in Chinese-first text.
- [x] **V2-CODEX-05:** Codex-account LLM calls must fail closed when credentials, entitlement, model support or backend compatibility is uncertain; no fake reading draft, scoring or review packet may be generated.
- [x] **V2-CODEX-06:** Outputs produced through this provider remain staging/review artifacts and cannot write formal records or bypass existing human-confirmed formal write gates.

### Phase 16: Research Plan Driven Literature Discovery

- [x] **V2-DISCOVERY-01:** User can provide a research plan file, plain-text objective or existing topic profile, and RSA can derive a discovery profile without modifying formal records.
- [x] **V2-DISCOVERY-02:** Discovery profiles must preserve stable English keys such as `plan_source`, `research_questions`, `query_bundle`, `source_provider`, `search_run_id`, `candidate_id`, `evidence_level` and `status`, while providing Chinese explanations for user-facing fields.
- [x] **V2-DISCOVERY-03:** RSA can generate auditable search query bundles from the research plan, including Chinese rationale, English search terms, inclusion/exclusion hints, topic links and confidence.
- [x] **V2-DISCOVERY-04:** Discovery search providers must be legal, configurable and auditable; default providers should be open scholarly indexes or user-configured custom sources, and must not bypass paywalls or use unauthorized mirrors.
- [x] **V2-DISCOVERY-05:** Discovered papers enter staging/campaign records with source links, match evidence, dedup keys, triage status and Chinese rationale; discovery must not directly create `metadata/P###.yaml` or write `paper_index.md`.
- [x] **V2-DISCOVERY-06:** Discovery results must integrate with existing Phase 8.2/11 campaign queues, metadata intake requests, review decisions and controlled automation instead of creating a parallel literature queue.
- [x] **V2-DISCOVERY-07:** Discovery commands must fail closed when the plan is unreadable, query generation is unsupported, providers are unavailable, rate limits occur or evidence is insufficient; failures must write Chinese status/recovery guidance.
- [x] **V2-DISCOVERY-08:** Phase 16 should reserve extension interfaces for iterative query refinement, richer scholarly metadata integrations, discovery evals and Web review UI, but keep the first implementation focused on research-plan-to-campaign discovery.

### Phase 17: Dynamic Workflow Policy Engine

- [ ] **V2-DYNAMIC-01:** RSA can evaluate a local workflow policy against current artifacts, evidence levels, dependency state, confidence, failures and user configuration to produce auditable `next_actions`.
- [ ] **V2-DYNAMIC-02:** Dynamic workflow remains bounded: it reuses Phase 10 single-paper workflow, Phase 11 campaign scheduling, Phase 12 review workspace, Phase 13 safety checks and Phase 14 worker queue instead of replacing them.
- [ ] **V2-DYNAMIC-03:** Policy decisions must be stored as local YAML/Markdown audit records with stable English keys and Chinese explanations, including `decision_id`, `trigger`, `inputs`, `selected_action`, `reason_zh`, `confidence`, `evidence_level`, `blocked_reason_zh` and `repair_hint_zh`.
- [ ] **V2-DYNAMIC-04:** Policy rules must support conservative conditions such as `run_if`, `skip_if`, `retry_if`, `block_if`, `route_to_review_if` and `stop_before_formal_write`.
- [ ] **V2-DYNAMIC-05:** Users can inspect, validate and override dynamic workflow decisions through Chinese-first CLI commands without editing formal records directly.
- [ ] **V2-DYNAMIC-06:** AI or LLM assistance may suggest policy actions only as staging/review guidance; it must record evidence and confidence and must not directly execute formal writes.
- [ ] **V2-DYNAMIC-07:** Dynamic workflow must fail closed on invalid policy files, missing required artifacts, conflicting actions, unsupported steps, dependency blocks or low confidence.
- [ ] **V2-DYNAMIC-08:** Phase 17 reserves extension interfaces for policy plugins, LLM policy suggestions, Web UI policy editing and learned heuristics, but the first implementation must stay local-first, deterministic where possible and conservative by default.

### Deferred

- [ ] **V2-DEFER-01:** Crossref/OpenAlex/Zotero deep integrations remain deferred unless the core loop later proves they are necessary.
- [ ] **V2-DEFER-02:** Advanced figure intelligence, including curve data restoration and advanced table structure understanding, remains deferred beyond Phase 8.1.
- [ ] **V2-DEFER-03:** Multi-agent orchestration remains optional and cannot bypass formal write gates.
