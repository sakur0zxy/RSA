# Phase 11: Campaign & Batch Review - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 在 Phase 8.2 campaign queue、Phase 9 scoring 和 Phase 10 single-paper workflow primitive 之上，交付 campaign 级批量处理、受控流水线并行、metadata intake、review queue、批量报告和中文监管入口。它的目标是让多篇论文可以默认自动推进到 staging/review packet，同时保持每篇论文内部依赖顺序，并且不绕过任何 formal write gate。

Phase 11 不做后台常驻 worker、不做 Local Review Workspace UI、不做 claim-level citation hardening、不做重型 metadata 深集成、不执行正式写入。
</domain>

<decisions>
## Implementation Decisions

### Campaign 输入与自动化边界
- **D-01:** Campaign item 分为 `linked` 和 `queued`。`linked` 表示已链接到正式 `metadata/P###.yaml`，Phase 11 可以自动调用 Phase 10 workflow。`queued` 表示仍是候选条目，Phase 11 只能自动生成 metadata intake request，不能直接创建正式 `paper_id`。
- **D-02:** `queued` 条目可以自动整理、去重、轻量补全和送入待审队列，但正式 metadata 写入仍必须经过现有 metadata gate 和人工确认。
- **D-03:** 轻量 metadata enrichment 只允许服务主闭环，例如 title/author/year/doi/BibTeX basics、标准化和 dedup 辅助。补全结果写入 `candidate_metadata`，必须保留来源、置信度和中文说明，不作为已核验 formal fact。

### Metadata Intake Request
- **D-04:** Phase 11 v1 将 metadata intake request 放在 campaign 旁边，默认文件为 `01_literature/campaigns/C001_metadata_requests.yaml`。
- **D-05:** 每条 metadata request 必须按未来可独立迁移对象设计，不依赖其在 campaign 文件中的位置。必须字段为 `request_id`、`source_campaign_id`、`queued_item_id`、`status`、`candidate_metadata`、`created_at`。
- **D-06:** Metadata request 状态集合为 `auto_triaged`、`needs_review`、`accepted`、`rejected`、`merged`。默认状态为 `auto_triaged`，表示机器已初步分诊并给出建议动作，不表示人工审阅通过。
- **D-07:** `needs_review` 只用于人工明确标记需要重点审阅，或系统发现低置信度、重复冲突、缺关键 metadata、来源不清等高风险情况。
- **D-08:** Metadata request 最小 triage 字段为 `triage_confidence`、`recommended_action`、`triage_reason_zh`、`formal_write_allowed: false`。`recommended_action` 先支持 `create_new_metadata`、`possible_duplicate`、`merge_candidate`、`insufficient_metadata`、`reject_candidate`。
- **D-09:** 后续可迁移到 `01_literature/metadata_requests/MR###.yaml` 独立待办池，campaign 侧只保留 `request_id + status` 索引。

### Formal Write Request
- **D-10:** 当 metadata intake request 被标记为 `accepted` 后，Phase 11 只生成可审阅 `formal_write_request`，不直接写入 `metadata/P###.yaml`。
- **D-11:** `formal_write_request` v1 放在 review queue 或 metadata request 旁边，并与 `C001_review_queue.yaml` / `C001_metadata_requests.yaml` 互相引用。
- **D-12:** `formal_write_request` 也必须按未来可独立迁移对象设计，保留稳定 `request_id`、来源 campaign/item、目标 formal record、状态和中文理由。后续可迁移到 `01_literature/formal_write_requests/`。
- **D-13:** `formal_write_request` 状态为 `pending_human_approval`、`approved_for_write`、`rejected`、`applied`。该状态集不复用 review queue 的 `accepted/deferred/rejected/needs_followup`，避免混淆队列处理和正式写入语义。
- **D-14:** Phase 11 不增加 formal apply 子命令，也不自动执行 `approved_for_write`。正式写入继续交给 `rsa add-paper --human-confirmed`、`rsa formal apply-map`、`rsa formal apply-note` 或后续等价 formal gate。

### Campaign 受控并行
- **D-15:** Phase 11 采用小规模流水线并行。多篇论文之间可以并行推进；每篇论文内部仍复用 Phase 10 单篇顺序链，不打乱 `acquisition -> reading_draft -> visual_extraction -> scoring -> review_packet`。
- **D-16:** 默认并发为 `acquisition: 2`、`reading_draft: 2`、`visual_extraction: 1`、`scoring: 2`。
- **D-17:** 并发参数必须可由 `.rsa/local.yaml` 的 `campaign.concurrency` 长期配置，也可由当前运行的 CLI flag 临时覆盖。
- **D-18:** CLI override flags 为 `--max-acquisition`、`--max-reading-draft`、`--max-visual`、`--max-scoring`。CLI 只覆盖本次运行，优先级高于 `.rsa/local.yaml`。
- **D-19:** 采用阶段队列流水线，每个阶段有自己的队列和并发限制。某篇论文完成 `acquisition` 后即可进入 `reading_draft` 队列，不需要等待整个 campaign 的 acquisition 全部完成。
- **D-20:** 不使用全批次阶段栅栏，也不直接并发启动多个完整 Phase 10 workflow，避免 blocked 项拖住整批或失去阶段级资源限流。
- **D-21:** 默认异常策略为 `continue_on_error` + `pause_on_auth_error` + `pause_on_formal_request`。普通单篇错误不阻塞整批；授权、登录或 provider 问题暂停相关 provider/条目；formal write request 只进入 review queue。

### Review Queue
- **D-22:** Review queue 采用状态分组加组内优先级排序。状态分组顺序为 `blocked`、`needs_review`、`partial`、`auto_triaged`、`ready_for_review`、`completed_staging`。
- **D-23:** 最小 queue item schema 为 `queue_item_id`、`source_campaign_id`、`source_item_id`、`paper_id` 或 `request_id`、`queue_group`、`priority_score`、`risk_flags`、`reason_zh`、`artifact_links`、`review_decision`、`review_decision_version`、`followup_actions`。
- **D-24:** `artifact_links` 最小集合为 `campaign_path`、`workflow_run_path`、`workflow_report_path`、`scoring_path`、`scoring_review_packet_path`、`metadata_request_path`、`batch_report_path`。缺失时允许为 `null`，但必须有中文原因。
- **D-25:** `artifact_links` 必须可扩展，后续可追加 `source_ledger_path`、`visual_candidates_path`、`reading_note_path`、`pdf_path`、`formal_write_request_path`。旧 parser 必须忽略未知链接键。
- **D-26:** 组内排序优先使用 `ai_read_priority_score_10`；同分时优先展示低置信度、高风险、疑似重复、授权异常、metadata intake 需要处理的条目。
- **D-27:** `blocked`、`needs_review`、`partial`、低置信度、高优先级、疑似重复、formal write request、metadata intake request 必须进入 review queue。
- **D-28:** 高优先级阈值为 `ai_read_priority_score_10 >= 8`。低置信度阈值为 `score_confidence != high`。
- **D-29:** 支持轻量 review 标记，例如 `rsa campaign queue review C001 --item CI001 --decision accepted|deferred|rejected --reviewer zxy --reason "..."`。该命令只更新 review queue 和 review history，不写 formal records。
- **D-30:** `review_decision` 枚举为 `accepted`、`deferred`、`rejected`、`needs_followup`。不用 `approved`，避免与 formal approval 混淆。`accepted` 只表示队列项已被处理或认可进入后续流程，不等于正式批准。
- **D-31:** 保留 `review_decision_version` 和 `followup_actions`。后续细分语义优先放入 `followup_actions`，例如 `accepted_for_metadata`、`accepted_for_reading`、`duplicate_confirmed`、`needs_source_check`、`needs_pdf_reacquisition`。

### Run State 与报告
- **D-32:** Phase 11 v1 的 run state 和报告放在 campaign 目录同级文件：`01_literature/campaigns/C001_run.yaml`、`01_literature/campaigns/C001_review_queue.yaml`、`01_literature/campaigns/C001_batch_report.md`。
- **D-33:** 如果后续需要多次运行历史，可新增 `01_literature/campaign_runs/C001/RUN-###.yaml`，campaign 旁边文件只保留当前状态或索引。
- **D-34:** `C001_batch_report.md` 必须包含 campaign 摘要、处理计数、review queue 摘要、blocked/partial/auth/formal 请求列表、metadata intake 列表、下一步建议和 artifact 链接。
- **D-35:** Batch report 面向中文监管，不做全量日志倾倒，不保存完整 stdout/stderr、PDF 正文、长摘录、账号会话或敏感信息。
- **D-36:** `C001.yaml` 只追加轻量状态索引，例如 `last_run_id`、`review_queue_path`、`metadata_requests_path`、`batch_report_path`，不写入完整运行结果。
- **D-37:** Phase 11 v1 为同步 CLI 运行，但 run state 预留 worker 接口字段，例如 `worker_mode: sync_cli`、`task_id: null`、`worker_status: not_used`。

### CLI 命令组
- **D-38:** 扩展现有 `rsa campaign` 命令组，不新增 `rsa batch` 或 `rsa campaign-run`。
- **D-39:** Phase 11 新增命令为 `rsa campaign run C001`、`rsa campaign resume C001`、`rsa campaign pause C001`、`rsa campaign queue C001`、`rsa campaign report C001`。
- **D-40:** `rsa campaign run C001` 默认只处理未完成项；已完成 workflow/scoring/review packet 的 staging 项不重复运行。
- **D-41:** 支持 `rsa campaign run C001 --dry-run`，只生成运行计划和预估队列，不实际调用 workflow。默认不是 dry-run，保持自动运行优先。
- **D-42:** 支持 `--items CI001,CI002` 和 `--status linked,queued` 等本次运行过滤。过滤不永久修改 campaign 队列本体，被排除项在 report 中记为 `skipped_by_filter`。
- **D-43:** `rsa campaign pause C001` 标记 campaign run 暂停；`rsa campaign resume C001` 从 `pending`、`failed`、`retryable` 或未完成队列继续，不重跑 `completed` 项。
- **D-44:** Phase 11 v1 不实现完整 `rsa campaign rerun C001`。预留 `workflow_run_id`、`campaign_item_status`、`last_completed_step`、`rerun_allowed`、`reset_reason_zh`，未来通过 Phase 10 `workflow rerun` 批量实现。

### 实现切分与测试
- **D-45:** Phase 11 拆成 3 个 plans：`11-01 metadata intake request + campaign run state/schema`，`11-02 pipeline runner + concurrency + pause/resume`，`11-03 review queue + batch report + CLI docs/tests`。
- **D-46:** Phase 11 v1 测试以 deterministic pytest 和文档测试为主，覆盖 metadata intake、run state、pipeline 调度、并发参数、pause/resume、review queue、batch report 和 formal write 边界。

### Agent Discretion
Agent 在计划阶段可以决定内部模块命名、辅助函数布局、具体 YAML 读写 helper、测试文件拆分和错误消息措辞，但必须保持中文用户可见内容、英文稳定 schema key、local Markdown/YAML 方案、fail-closed、formal gate 不可绕过，以及上述状态语义。
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` — 项目核心价值、中文用户优先、formal records 与 agent outputs 的边界。
- `.planning/ROADMAP.md` — v2 phase 顺序、Phase 10/11 分工、Phase 14 新增位置和 deferred 范围。
- `.planning/REQUIREMENTS.md` — v2 全局约束、中文用户可见内容、依赖原则、Phase 11-14 requirements。
- `.planning/STATE.md` — 当前 milestone 状态、已完成 phase、Phase 11 下一步。
- `.planning/phases/11-campaign-batch-review/11-DISCUSSION-WIP.md` — Phase 11 逐点讨论暂存记录。

### Prior Phase Context
- `.planning/phases/08.2-campaign-foundation/08.2-CONTEXT.md` — Campaign queue、import、dedup、formal metadata link 的现有边界。
- `.planning/phases/09-evidence-signals-ai-scoring/09-CONTEXT.md` — Scoring schema、`ai_read_priority_score_10`、confidence、campaign scoring summary 和 formal boundary。
- `.planning/phases/10-workflow-orchestrator/10-CONTEXT.md` — Single-paper workflow primitive、run state、resume/rerun/status/report 语义。

### Existing Implementation
- `src/rsa_cli/campaign.py` — Campaign 创建、导入、校验、状态、CSV/TSV/YAML 读取、dedup/link 逻辑。
- `src/rsa_cli/workflow.py` — Phase 10 单篇 workflow run/resume/status/report/stop/rerun primitive。
- `src/rsa_cli/scoring.py` — 单篇评分、campaign scoring summary、review packet 和 scoring validation。
- `src/rsa_cli/cli.py` — 现有 argparse 风格和中文 CLI 输出入口。
- `src/rsa_cli/config.py` — 项目路径和本地配置读取入口。
- `tests/test_campaign.py` — Campaign foundation 的现有回归测试。
- `tests/test_workflow.py` — Phase 10 workflow 行为测试。
- `tests/test_scoring.py` — Phase 9 scoring 和 campaign summary 行为测试。
- `tests/test_cli.py` — CLI smoke 和用户可见行为测试。
- `README.md` — GitHub 风格项目说明和中文用户入口。
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `campaign.py` 已经有 campaign YAML、本地导入、轻量 dedup、linked/queued 状态和只读 validate/status 逻辑，可以作为 Phase 11 campaign run state、metadata intake request 和 review queue 的落点。
- `workflow.py` 已经提供单篇 workflow primitive。Phase 11 应调用或封装它，不重写单篇 acquisition/reading/visual/scoring 顺序链。
- `scoring.py` 已经能输出 per-paper scoring 和 campaign summary。Phase 11 review queue 应消费 scoring summary，不重新定义 AI 评分语义。
- `cli.py` 已经使用现有 argparse 命令组风格。Phase 11 应扩展 `rsa campaign`，保持中文 help、错误和状态输出。

### Established Patterns
- 正式科研记录和 staging 输出分离。Phase 11 只能生成 metadata intake、formal write request 和 review queue，不能把候选内容直接写进 formal records。
- 本地 Markdown/YAML 是 v2 当前默认存储方案。新增 schema 应保持英文 key 稳定，并为中文用户提供说明。
- PDF、截图、资产和授权会话保持 local-only。Phase 11 report 只放链接和状态，不复制敏感内容或全文。
- 命令失败必须 fail closed，输出中文原因和修复建议，不生成伪成功产物。

### Integration Points
- `rsa campaign run` 读取 `C###.yaml`，区分 `linked` 和 `queued`，对 linked 调用 Phase 10 workflow，对 queued 生成 metadata intake request。
- `rsa campaign run --dry-run` 只生成计划、估计队列和中文报告，不实际调用 workflow。
- `rsa campaign pause/resume` 操作 `C###_run.yaml` 文件状态，Phase 11 v1 不需要后台 worker。
- `rsa campaign queue` 读取 `C###_review_queue.yaml` 并按 group/priority 输出中文监管视图。
- `rsa campaign report` 读取 run state、review queue、metadata requests、scoring summary 和 workflow artifacts，生成中文 Markdown report。
</code_context>

<specifics>
## Specific Ideas

- 核心自动化语义为：文献获取、阅读草稿、视觉候选、AI 评分和 review packet 可以自动执行；写入正式数据库、map、note 或 research records 必须人工审批。
- Campaign 的作用是批量候选的自动推进和监管聚合，不是 formal database。
- 推荐工作流为：导入 campaign 候选 -> linked 项自动跑 Phase 10 -> queued 项生成 metadata intake request -> 生成 review queue -> 用户在 queue/report/workspace 中监管 -> formal write request 经人工批准后再由正式 gate 执行。
- Phase 11 的文档、CLI 输出、batch report、错误提示、状态解释必须面向中文用户；schema key、CLI flag 和状态枚举保持英文。
</specifics>

<deferred>
## Deferred Ideas

- Phase 13 负责 campaign failure monitoring / hardening，包括授权错误、blocked/partial 聚合、review queue 排序回归、formal request 不自动执行、metadata intake 不直接写 formal metadata、completed 项不被普通 run 重跑、低置信度/高优先级监管准入，以及 `continue_on_error` / `pause_on_auth_error` / `pause_on_formal_request` 语义。
- Phase 14 负责 `Background Worker & Scheduled Automation`，中文定位为“运行形态升级”。范围包括后台 worker、异步任务执行、长任务恢复、status 监控、定时 campaign run 和 worker 日志摘要。
- Phase 14 不重写 Phase 10 workflow，不重写 Phase 11 campaign 调度逻辑，不绕过 formal write gate，不做 multi-agent，不做复杂云服务。
- Future metadata request pool 可迁移到 `01_literature/metadata_requests/MR###.yaml`。
- Future formal write request pool 可迁移到 `01_literature/formal_write_requests/`。
- Future campaign run history 可迁移到 `01_literature/campaign_runs/C001/RUN-###.yaml`。
- Future campaign rerun 可以新增 `rsa campaign rerun C001`、`--from-step scoring`、`--item CI001` 或 `reset-item`，实现上应批量调用 Phase 10 `workflow rerun`。
- Crossref/OpenAlex/Zotero 深集成、高级图表智能、复杂 multi-agent 编排继续 deferred。
</deferred>

---

*Phase: 11-Campaign & Batch Review*
*Context gathered: 2026-05-26*
