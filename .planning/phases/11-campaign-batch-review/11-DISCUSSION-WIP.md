# Phase 11 Campaign & Batch Review - Discussion WIP

> 本文件用于暂存逐点讨论结果；正式讨论结束后会整理进 `11-CONTEXT.md` 和 `11-DISCUSSION-LOG.md`。

## 已确认决策

### 1. Campaign 批量运行入口与可处理对象

- **选择:** 方案 2 - `linked` 自动运行，`queued` 自动生成 metadata intake request。
- **含义:** Phase 11 对已经链接到正式 `metadata/P###.yaml` 的 campaign item 自动调用 Phase 10 workflow；对尚未链接的 `queued` 条目，只生成可审阅的 metadata intake request，不直接创建正式 `paper_id`，也不写入 formal records。
- **边界:** `queued` 条目可以被自动整理、去重、补全和送入待审队列，但正式 metadata 写入仍必须经过现有 metadata gate 和人工确认。
- **原因:** 这样比“只处理 linked”自动化程度更高，同时不会让未核验候选直接污染正式科研记录。

## 待继续讨论

- metadata intake request 的格式、位置和自动化边界。
- campaign 级并发、限流和流水线调度。
- review queue 的排序、过滤和监管策略。
- 批量异常、暂停、恢复和报告语义。

### 2. Metadata Intake Request 存放位置与升级路径

- **采纳建议:** 当前采用方案 1，即每个 campaign 旁边生成 `01_literature/campaigns/C001_metadata_requests.yaml`。
- **升级约束:** 虽然当前存放在 campaign 旁边，但每条 request 必须按“未来可独立成文件的对象”设计，不能依赖它在 campaign 文件中的位置。
- **必须字段:** `request_id`、`source_campaign_id`、`queued_item_id`、`status`、`candidate_metadata`、`created_at`。
- **状态集合:** `auto_triaged`、`needs_review`、`accepted`、`rejected`、`merged`。
- **默认状态:** 采纳收缩版 `auto_triaged`。它只表示“机器已经完成初步分诊并生成建议动作”，不表示人工审阅通过，也不允许直接写入 formal metadata。
- **最小 triage 字段:** `triage_confidence`、`recommended_action`、`triage_reason_zh`、`formal_write_allowed: false`。
- **推荐动作枚举:** `create_new_metadata`、`possible_duplicate`、`merge_candidate`、`insufficient_metadata`、`reject_candidate`。
- **needs_review 语义:** `needs_review` 不再作为所有机器生成 request 的默认状态，而用于人工明确标记需要重点审阅，或系统发现低置信度、重复冲突、缺关键 metadata、来源不清等高风险情况。
- **后续升级路径:** 当 request 数量变多或需要跨 campaign 统一审阅时，可迁移到 `01_literature/metadata_requests/MR###.yaml` 独立待办池；campaign 侧只保留 `request_id + status` 索引。
- **边界:** metadata request 是 staging/review 对象，不是 formal metadata；`accepted` 也不等于已经写入 `metadata/P###.yaml`，真正写入仍需 metadata gate 和人工确认。
- **accepted 后续动作:** 用户将 metadata intake request 标记为 `accepted` 后，Phase 11 只生成可审阅的 `formal_write_request`，不直接写入 `metadata/P###.yaml`。
- **formal gate:** 正式写入仍必须通过 `rsa add-paper --human-confirmed` 或等价 metadata gate；Phase 11 不自动调用正式写入。
- **轻量补全:** queued item 生成 metadata intake request 时可以做轻量 metadata 补全和标准化，例如 title/author/year/doi/BibTeX basics；补全结果只写入 `candidate_metadata`，不写 formal metadata。
- **补全边界:** 不做 Crossref/OpenAlex/Zotero 深集成；不把低置信补全当成已核验事实；补全来源、置信度和中文说明必须保留在 request 中。
- **formal_write_request 存放:** Phase 11 v1 将 formal write request 放在 review queue 或 metadata request 旁边，优先与 `C001_review_queue.yaml` / `C001_metadata_requests.yaml` 互相引用。
- **升级约束:** formal write request 也按可迁移独立对象设计，必须带稳定 `request_id`、来源 campaign/item、目标 formal record、状态和中文理由。后续可迁移到 `01_literature/formal_write_requests/` 全局待办池。
- **formal_write_request 状态:** `pending_human_approval`、`approved_for_write`、`rejected`、`applied`。
- **状态语义:** `pending_human_approval` 表示待人工批准；`approved_for_write` 表示人工已批准但尚未执行正式写入；`rejected` 表示拒绝写入；`applied` 表示已通过正式 gate 写入目标 formal record。
- **命名边界:** 不复用 review queue 的 `accepted/deferred/rejected/needs_followup`，避免混淆“队列项处理状态”和“正式写入请求状态”。
- **执行边界:** Phase 11 只生成和更新 formal write request，不执行 formal write。正式写入继续交给已有 `rsa add-paper --human-confirmed`、`rsa formal apply-map`、`rsa formal apply-note` 或后续等价 formal gate 命令。
- **不采用:** 不在 Phase 11 增加 apply 子命令，不自动执行 `approved_for_write`。

### 3. Campaign 受控并行与资源限流

- **选择:** 方案 1 - 小规模流水线并行。
- **含义:** 多篇论文之间可以并行推进；每篇论文内部仍复用 Phase 10 的单篇顺序链，不打乱 `acquisition -> reading_draft -> visual_extraction -> scoring -> review_packet` 依赖顺序。
- **默认并发建议:** `acquisition: 2`、`reading_draft: 2`、`visual_extraction: 1`、`scoring: 2`。
- **可调整性:** 具体参数必须可通过本地设置调整，例如 `.rsa/local.yaml`；CLI flag 可临时覆盖本次 campaign run 的并发参数。
- **配置位置:** 默认并发写入 `.rsa/local.yaml` 的 `campaign.concurrency`，例如 `acquisition`、`reading_draft`、`visual_extraction`、`scoring`。
- **覆盖优先级:** CLI flag 只覆盖当前一次运行，优先级高于 `.rsa/local.yaml`；本地配置仍是长期默认值。
- **推荐 CLI flag:** `--max-acquisition`、`--max-reading-draft`、`--max-visual`、`--max-scoring`。
- **推进策略:** 采用阶段队列流水线。每个阶段有自己的队列和并发限制；某篇论文完成 `acquisition` 后即可进入 `reading_draft` 队列，不必等待整个 campaign 的 acquisition 全部完成。
- **不采用:** 不使用“全批次阶段栅栏”，避免一个阶段的 blocked 项拖住整批；也不直接并发启动多个完整 Phase 10 workflow，避免失去阶段级资源限流。
- **异常默认行为:** 采用 `continue_on_error` + `pause_on_auth_error` + `pause_on_formal_request`。普通单篇错误不阻塞整个 campaign；授权/登录/provider 问题暂停相关 provider 或相关条目；formal write request 只进入 review queue，不自动执行。
- **原因:** 该策略能保持无人值守批量推进，同时避免授权失效、登录过期或正式写入请求被自动链路扩大成系统性污染。
- **边界:** 不采用无限并行，不让一个重步骤耗尽资源；formal write 相关动作不进入自动并行队列。

### 4. Review Queue 排序与自动初审规则

- **选择:** 方案 1 - 按状态分组 + 组内优先级排序。
- **最小 queue item schema:** `queue_item_id`、`source_campaign_id`、`source_item_id`、`paper_id` 或 `request_id`、`queue_group`、`priority_score`、`risk_flags`、`reason_zh`、`artifact_links`、`review_decision`、`review_decision_version`、`followup_actions`。
- **artifact_links 最小集合:** `campaign_path`、`workflow_run_path`、`workflow_report_path`、`scoring_path`、`scoring_review_packet_path`、`metadata_request_path`、`batch_report_path`；缺失时允许为 `null`，但需要中文说明原因。
- **artifact_links 扩展:** 后续可以在 `artifact_links` 下追加新 key，例如 `source_ledger_path`、`visual_candidates_path`、`reading_note_path`、`pdf_path`、`formal_write_request_path`，旧 parser 必须忽略未知链接键。
- **schema 原因:** review queue 需要同时服务 CLI 监管、Markdown report 和后续 Phase 12 workspace；不能只存 item_id/status/link，也不能只生成不可机器读取的 report。
- **状态分组顺序:** `blocked`、`needs_review`、`partial`、`auto_triaged`、`ready_for_review`、`completed_staging`。
- **组内排序:** 优先使用 `ai_read_priority_score_10`；同分时优先展示低置信度、高风险、疑似重复、授权异常、metadata intake 需要处理的条目。
- **监管准入:** `blocked`、`needs_review`、`partial`、低置信度、高优先级、疑似重复、formal write request、metadata intake request 必须进入 review queue。
- **高优先级阈值:** `ai_read_priority_score_10 >= 8` 的条目必须进入重点监管和优先阅读队列；该阈值与 Phase 9 评分语义保持一致。
- **低置信度阈值:** `score_confidence != high` 的条目必须进入 review queue；`medium` 和 `low` 都需要用户监管。
- **轻量 review 标记:** 支持类似 `rsa campaign queue review C001 --item CI001 --decision accepted|deferred|rejected --reviewer zxy --reason "..."` 的 CLI 标记，只更新 review queue 和 review history，不写 formal records。
- **review 标记边界:** `accepted` 只表示该队列项已被用户处理或认可进入后续流程，不等于 formal approval，也不触发 metadata/map/note 写入。
- **review decision 枚举:** `accepted`、`deferred`、`rejected`、`needs_followup`。
- **命名边界:** 不使用 `approved`，避免与 formal approval 或 human-confirmed formal write 混淆。
- **扩展接口:** review queue item 应保留 `review_decision_version` 和 `followup_actions`。v1 用四个大类 decision 表示人工处理状态；后续若需要 `accepted_for_metadata`、`accepted_for_reading`、`duplicate_confirmed`、`needs_source_check`、`needs_pdf_reacquisition` 等细分语义，优先放入 `followup_actions`，避免过早膨胀主枚举。
- **字段建议:** `review_decision`、`review_decision_version: phase11-review-v1`、`review_reason_zh`、`followup_actions[]`。
- **不采用:** 不只看异常项，避免漏掉高价值论文和 formal 请求；也不把所有 processed 项都强制塞进监管队列，避免用户监管负担过重。
- **语义:** review queue 是监管入口，不是 formal approval 列表；队列排序只帮助用户决定先看什么。

### 5. Campaign Run State 与报告文件位置

- **选择:** 方案 1 - 放在 campaign 目录同级文件。
- **文件位置:** `01_literature/campaigns/C001_run.yaml`、`01_literature/campaigns/C001_review_queue.yaml`、`01_literature/campaigns/C001_batch_report.md`。
- **原因:** Phase 11 v1 以本地 Markdown/YAML 为主，按 campaign 聚合最直观，用户也最容易找到相关状态。
- **后续升级:** 如果后续需要多次运行历史，可新增 `01_literature/campaign_runs/C001/RUN-###.yaml`，并让 campaign 旁边文件只保留当前状态或索引。
- **batch report 内容:** `C001_batch_report.md` 包含 campaign 摘要、处理计数、review queue 摘要、blocked/partial/auth/formal 请求列表、metadata intake 列表、下一步建议和 artifact 链接。
- **报告边界:** Markdown report 面向中文监管，不做全量日志倾倒，不保存完整 stdout/stderr、PDF 正文、长摘录、账号会话或敏感信息。
- **语言策略:** batch report 面向中文用户；正文、原因、下一步建议、状态解释必须中文。YAML key、CLI flag、状态枚举保持英文，并在报告中给中文解释。
- **C001.yaml 更新策略:** 只追加轻量状态索引，例如 `last_run_id`、`review_queue_path`、`metadata_requests_path`、`batch_report_path`；不把完整运行结果写回 campaign 本体。
- **原因:** 保持 `C001.yaml` 作为候选队列本体，避免文件膨胀、diff 噪音和运行结果冲突，同时让用户能从 campaign 文件找到最新状态入口。
- **worker 模式:** Phase 11 v1 采用同步 CLI 运行，但在 run state 中预留 worker 接口字段，例如 `worker_mode: sync_cli`、`task_id: null`、`worker_status: not_used`。
- **后续 Phase:** 真正后台常驻 worker、任务守护、异步派发和实时 status 监控不纳入 Phase 11 v1，安排为 Phase 14。
- **Phase 14 名称:** `Background Worker & Scheduled Automation`，中文定位为“运行形态升级”。
- **Phase 14 范围:** 后台 worker、异步任务执行、长任务恢复、status 监控、定时 campaign run、worker 日志摘要。
- **Phase 14 边界:** 不重写 Phase 10 单篇 workflow，不重写 Phase 11 campaign 调度逻辑，不绕过 formal write gate，不做 multi-agent，不做复杂云服务。
- **ROADMAP 更新时机:** 当前先记录在 Phase 11 WIP；Phase 11 context 成稿时再把 Phase 14 同步到 ROADMAP，避免讨论中途打断路线图。
- **REQUIREMENTS 更新时机:** 与 ROADMAP 一起在 Phase 11 context 成稿时同步；先在 context 中写清 Phase 14 requirement 草案，避免后续 plan/execute 缺少验收依据。
- **原因:** 这样保留自动化升级方向，同时不让 Phase 11 同时承担 campaign 调度和后台任务系统两个大目标。

### 6. Campaign CLI 命令组

- **选择:** 扩展现有 `rsa campaign` 命令组。
- **新增命令:** `rsa campaign run C001`、`rsa campaign resume C001`、`rsa campaign pause C001`、`rsa campaign queue C001`、`rsa campaign report C001`。
- **原因:** campaign 相关的创建、导入、校验、状态、运行、队列和报告都放在一个入口下，中文用户更容易理解和记住。
- **边界:** 不新增 `rsa batch` 或 `rsa campaign-run` 命令组，避免概念分裂。
- **run 默认范围:** `rsa campaign run C001` 默认只处理未完成项；已完成 workflow/scoring/review packet 的 staging 项不重复运行。
- **重跑语义:** 需要重跑时应通过显式参数或后续 `rerun` 语义触发，不能让普通 run 默默覆盖旧结果。
- **dry-run:** 提供 `rsa campaign run C001 --dry-run`，只生成运行计划和预估队列，不实际调用 workflow；默认不 dry-run，保持自动运行优先。
- **运行范围过滤:** 支持 `--items CI001,CI002` 和 `--status linked,queued` 之类的本次运行过滤，方便小批量试跑、恢复和风险控制。
- **过滤边界:** 过滤只影响本次 campaign run，不永久修改 campaign 队列本体；被过滤排除的项应在 run report 中记录为 skipped_by_filter。
- **pause/resume:** `rsa campaign pause C001` 标记 campaign run 暂停；`rsa campaign resume C001` 从 `pending`、`failed`、`retryable` 或未完成队列继续，不重跑 `completed` 项。
- **暂停边界:** Phase 11 v1 可先做文件状态层暂停；如果后续实现后台 worker，再扩展为停止派发新任务并等待正在运行项自然结束。
- **campaign rerun:** Phase 11 v1 暂不实现完整 `rsa campaign rerun C001`，避免复杂覆盖语义。
- **预留字段:** campaign run item 应保留 `workflow_run_id`、`campaign_item_status`、`last_completed_step`、`rerun_allowed`、`reset_reason_zh`，方便后续升级。
- **后续升级:** 未来可增加 `rsa campaign rerun C001`、`rsa campaign rerun C001 --from-step scoring`、`rsa campaign rerun C001 --item CI001` 或 `rsa campaign reset-item C001 CI001`；实现上应批量调用 Phase 10 `workflow rerun`，不重写单篇重跑逻辑。

### 7. Phase 11 实现范围切分

- **选择:** 拆成 3 个 plan。
- **11-01:** metadata intake request + campaign run state/schema。
- **11-02:** pipeline runner + concurrency + pause/resume。
- **11-03:** review queue + batch report + CLI docs/tests。
- **原因:** 这个切分能把 staging 数据模型、批量运行引擎和用户监管输出分开，避免单个 plan 过大，同时不增加过多 GSD 开销。

### 8. 测试与后续 Eval 扩展

- **Phase 11 v1 测试:** 以 deterministic pytest 和文档测试为主，覆盖 metadata intake、run state、pipeline 调度、并发参数、pause/resume、review queue、batch report 和 formal write 边界。
- **Phase 13 失败场景监测:** 将 campaign 授权错误、`blocked`/`partial` 聚合、review queue 排序回归、formal request 不自动执行、metadata intake 不直接写 formal metadata、completed 项不被普通 run 重跑、低置信度/高优先级监管准入、`continue_on_error`/`pause_on_auth_error`/`pause_on_formal_request` 语义加入 Phase 13 hardening/eval 范围。
- **边界:** Phase 11 不立即扩展 `rsa eval`，避免本阶段从 batch workflow 膨胀成 eval hardening 阶段；Phase 13 负责把这些高风险失败场景固化为 eval/regression。

### 9. Context 收口与项目状态同步

- **选择:** Phase 11 discuss 收口时同步 `11-CONTEXT.md`、`11-DISCUSSION-LOG.md`、`.planning/ROADMAP.md`、`.planning/REQUIREMENTS.md` 和 `.planning/STATE.md`。
- **ROADMAP 同步:** 将 Phase 14 `Background Worker & Scheduled Automation` 作为后续运行形态升级阶段加入路线图。
- **REQUIREMENTS 同步:** 增加 Phase 14 worker/scheduled automation requirement 草案，并把 Phase 13 campaign failure monitoring / hardening requirement 写入验收范围。
- **STATE 同步:** 记录 Phase 11 context 已完成，下一步进入 Phase 11 planning。
