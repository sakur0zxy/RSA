# Phase 8 Auto Reading Draft - Discussion WIP

**状态:** 讨论中  
**创建时间:** 2026-05-16  
**用途:** 临时记录 Phase 8 讨论结果；每完成一个小点立即更新，最后整理进 `08-CONTEXT.md` 和正式 discussion log。

## Phase 边界

Phase 8 负责基于本地、用户提供或已授权全文生成可审阅 reading note draft。

本阶段不负责自动下载 PDF、批量 campaign、AI 评分、正式学术结论、正式 map/research note 写入，也不绕过 Phase 4/7/7.1 已锁定的授权和 formal write 门禁。

## 已继承决定

- 用户可见内容中文优先；字段名、YAML key、CLI flag、状态枚举保持英文，并提供中文解释。
- 自动阅读草稿只能来自本地、用户提供或已授权全文。
- Browser session 下载得到的 PDF 只是本地授权阅读材料，不能自动进入 formal records。
- Reading note 必须区分 `source_grounded_claims`、`short_quotes`、`agent_summary`、`human_decision`。
- `approved` 和任何正式写入仍必须人工确认。

## 待讨论灰区

1. 草稿生成入口与自动化边界。
2. 全文解析与失败降级策略。
3. 草稿证据结构与引用定位。
4. 审阅状态、正式边界和后续 Phase 9 连接。

## 已完成讨论点

### 1. 草稿生成入口

- **决策:** Phase 8 新增 `rsa note draft P###` 作为自动阅读草稿主入口。
- **说明:** `rsa note draft P###` 默认从 `source ledger` 或已下载 PDF 中选择可用授权全文生成可审阅草稿；`rsa note create` 保持为人工创建空白 reading note 的低层命令。
- **边界:** 下载、来源发现仍属于 Phase 7/7.1；Phase 8 不把下载和阅读强耦合。
- **失败处理:** 找不到本地、用户提供或已授权全文时，命令写入 blocked/status 记录，不生成假草稿。
- **中文要求:** 用户可见提示、错误、模板说明使用中文；命令名、flag、YAML key 保持英文。

### 2. 默认全文来源选择

- **决策:** `rsa note draft P###` 默认读取 `sources/P###.yaml`，优先选择 `is_primary: true`、`status: available` 且类型为 PDF 的授权全文。
- **备选规则:** 如果没有 primary PDF，则按 Phase 7 版本优先级选择可用 PDF，例如 `publisher_version` 优先于 `accepted_manuscript`、`repository_copy`、`arxiv_preprint` 等。
- **人工覆盖:** 命令允许 `--source-file <path>` 覆盖默认选择，用于用户想临时指定某个全文版本的场景。
- **不采用:** 不默认选最新下载 PDF；不为所有 PDF 同时生成多份 draft，多版本比较留到后续增强。

### 3. 自动草稿状态

- **修正决策:** Phase 8 允许 AI 做初审；当全文解析、LLM 输出、schema 校验和自动审查清单全部通过时，`rsa note draft P###` 可以自动设置 `note_status: ready_for_review`。
- **默认状态:** 生成过程中的中间产物仍是 `draft`；只有完整通过自动初审的草稿才能进入 `ready_for_review`。
- **不得自动批准:** `approved` 仍必须由用户人工确认，并满足 Phase 4 的 `human_confirmed: true`、`confirmed_by`、`confirmed_at`。
- **AI 初审含义:** `ready_for_review` 表示“AI 已完成结构化初审，等待用户最终监管”，不是正式学术结论，也不允许直接写入 formal records。
- **失败或不完整:** 解析不完整、LLM 输出不稳定、claim 证据不足、schema 不合格或存在高风险不确定项时，保持 `draft`、`partial`/`blocked` 状态记录或直接 fail closed。
- **不采用:** 不允许自动生成 `approved`；不允许 `ready_for_review` 绕过人工 formal write gate。

### 4. 已有 reading note 时的覆盖策略

- **决策:** `rsa note draft P###` 默认不覆盖已有 `01_literature/notes/P###_reading_note.md`。
- **允许覆盖条件:** 只有显式传入 `--overwrite-draft`，且已有 note 的 `note_status: draft` 时，才允许覆盖。
- **禁止覆盖:** 已有 note 为 `ready_for_review`、`approved` 或包含人工确认字段时，不允许自动覆盖。
- **原因:** 保护用户人工编辑过的阅读笔记，避免自动草稿覆盖正式审阅痕迹。

### 5. PDF 文本提取能力

- **决策:** Phase 8 引入本地 PDF 文本提取能力，作为 `rsa note draft P###` 自动阅读草稿的基础。
- **范围:** 只做本地 parser，从授权 PDF 中抽取文本和页码/片段信息；不调用云端服务直接阅读 PDF。
- **降级:** PDF 无法解析、文本过少、加密或损坏时，写入 blocked/partial 状态和中文原因，不生成伪阅读结论。
- **测试要求:** parser 需要有 deterministic fixture，覆盖成功、空文本、损坏 PDF、缺失文件等路径。

### 6. 功能依赖与安装选择

- **修正决策:** 普通用户基础版必须能够实现当前 agent 的所有核心功能，而不是只提供一个弱化版 harness。
- **基础安装:** `python -m pip install -e .` 是普通用户默认安装，应包含当前核心功能所需依赖，支持 metadata、round、map、source ledger、授权来源获取、browser session provider、PDF 文本提取和 `rsa note draft P###` 自动阅读草稿。
- **核心依赖方向:** `PyYAML`、PDF parser 依赖和 browser session 所需 Python 依赖都应进入基础运行依赖；浏览器二进制安装如果仍需要额外 setup command，README 必须用中文明确说明这是一次性环境初始化，不是可选核心功能。
- **可选依赖定位:** optional extras 只用于非核心增强、未来扩展或开发测试，例如 `.[dev]`、未来的 `.[llm]`、`.[ui]`、`.[cloud]` 等。
- **用户选择:** 用户可以选择基础版即可获得核心功能；也可以选择额外 extras 开启非核心增强；“全不选”表示不安装任何非核心 extras，不影响核心闭环。
- **文档要求:** README/帮助文档需要提供中文功能依赖矩阵，但矩阵必须明确标注“核心功能已包含在基础安装中”，避免用户误以为自动阅读或授权会话下载不是基础能力。
- **缺环境处理:** 当基础依赖已安装但外部环境缺少一次性资源，例如 Playwright Chromium 未安装时，命令必须 fail closed，给出中文解释和修复命令，不生成伪结果。
- **安装/运行自检:** 安装该 agent 后需要提供自动环境检查。Python 包依赖由基础安装声明并由 pip 自动安装；无法由 pip 可靠内置安装的外部资源，例如 Playwright Chromium、本地浏览器运行资源或未来模型/工具资源，需要通过 RSA 自检提示用户补齐。
- **自检入口:** 计划阶段应加入 `rsa doctor` 或等价命令，用中文列出核心功能状态、缺失项、影响范围和一键修复命令。需要相关资源的命令在运行前也必须做 preflight check。
- **提示原则:** 缺依赖或缺环境资源时，提示必须说明“缺什么、影响哪个功能、怎么安装/修复”，不得只输出 Python traceback。
- **全局化处理:** 该依赖原则已提升到 `.planning/DEPENDENCY-POLICY.md`、`.planning/PROJECT.md`、`.planning/REQUIREMENTS.md` 和 `.planning/v2-DISCUSSION.md`，后续 Phase 8 plan/execute 必须按全局设计落地。
- **外部建议采纳:** 采纳“核心闭环命令契约”“四层依赖 taxonomy”“doctor 契约”“doctor/preflight 边界”“fail closed 定义”“功能-依赖矩阵”“pyproject 分层草案”和“测试防漂移”建议；不采纳把 browser/PDF 核心能力重新降级为 optional-only 的理解。

### 7. PDF 解析缓存位置

- **决策:** PDF 文本提取结果保存为 local-only 解析缓存，不进入 git。
- **建议位置:** `01_literature/extracted/P###/` 或实现阶段选定的等价目录。
- **缓存内容:** 可保存抽取文本、页码、片段索引、parser 版本、source PDF hash 和提取状态，便于复用、调试和复现。
- **Reading note 边界:** `P###_reading_note.md` 只保留必要短引用、页码、证据片段摘要和 source reference，不写入大段全文。
- **不采用:** 不把全文解析文本写进 reading note；不把大段全文写进可提交 YAML/Markdown manifest。

### 8. PDF 解析失败状态

- **决策:** PDF 解析失败状态区分 `blocked` 和 `partial`。
- **`blocked`:** PDF 缺失、未授权、损坏、加密不可读、parser 不可用或没有可提取文本时使用；不得生成阅读草稿。
- **`partial`:** 能提取部分文本，但页码/章节/证据覆盖不足，或正文过短不足以支撑完整草稿时使用；可以生成带明显限制说明的 partial draft。
- **记录要求:** 两种状态都必须写中文原因、影响范围和修复建议，并保留 source PDF、hash、parser 信息。
- **不采用:** 不把所有失败都记为 `blocked`；不在证据不足时生成看似完整的 draft。

### 9. LLM-assisted reading draft 边界

- **修正决策:** Phase 8 需要 LLM-assisted reading draft。纯 PDF parser 只负责抽取文本、页码、章节候选和片段位置，不能可靠完成研究问题、方法、实验、结果、限制和课题关系的语义整理。
- **流程:** 授权 PDF -> 本地 parser 抽取文本和片段 -> LLM 基于片段生成结构化 reading draft -> 用户人工审阅。
- **边界:** LLM 只能生成 `note_status: draft` 的可审阅草稿，不得生成 `approved`，不得写 formal records，不得生成质量/相关性/阅读优先级评分。
- **证据要求:** LLM 输出的关键 claim 必须尽量带 `page`、`section`、`source_chunk_id` 或 evidence snippet；证据不足时进入 `uncertain_points_zh`。
- **后置能力:** AI scoring、read priority、正式评价和 claim-level citation check 留给 Phase 9/后续 phase。

### 10. Reading draft schema

- **决策:** Phase 8 必须固定 reading draft schema，避免 LLM 自由发挥。
- **frontmatter 元信息:** `paper_id`、`note_status: draft`、`source_file`、`source_id`、`source_hash`、`extraction_status`、`evidence_level`、`llm_model`、`draft_created_at`。
- **结构化阅读草稿:** `research_problem_zh`、`method_summary_zh`、`experiment_summary_zh`、`dataset_or_scene_zh`、`metrics_zh`、`main_findings_zh`、`limitations_zh`、`topic_relevance_zh`、`uncertain_points_zh`。
- **来源支撑 claims:** 每条 claim 至少包含 `claim_zh`、`evidence_page`、`evidence_section`、`source_chunk_id`、`evidence_snippet`、`needs_human_check`。
- **短引用:** 每条 short quote 包含 `quote`、`page`、`section`、`reason_zh`；短引用必须保持必要且短，不能复制长段原文。
- **候选视觉资产建议:** 可包含 `asset_request_type`、`page`、`figure_or_table`、`reason_zh`、`confidence`、`evidence_basis`，用于提醒用户后续保存或识别可能有价值的图表/表格；这只是候选建议，不是重要性定论。
- **人工审阅区:** 保留 `human_decision`、`human_confirmed: false`、`confirmed_by: null`、`confirmed_at: null`、`note_integration_requests: []`。
- **不包含:** `ai_quality_score`、`ai_relevance_score`、`ai_read_priority_score`、正式论文结论、自动 map 写入、长段原文、自动 approved。
- **中文用户要求:** 英文字段名保持稳定，但模板、字段说明、CLI 输出、校验错误和审阅提示必须提供中文解释。所有 `*_zh` 字段应以中文生成，方便中文用户直接审阅。

### 11. Claim 证据定位

- **决策:** `source_grounded_claims` 中每条 claim 采用 `chunk + page + section` 三级定位。
- **必备字段:** `source_chunk_id`、`evidence_page`、`evidence_section`、`evidence_snippet`、`needs_human_check`。
- **用途:** 支撑人工复核、后续截图保存、Phase 9 evidence signals / scoring 和 future citation check。
- **限制:** `evidence_snippet` 只保留必要短证据，不保存长段全文；完整解析文本保留在 local-only cache。

### 12. Short quotes 规则

- **决策:** 保留 `short_quotes`，但必须严格限制为短引用。
- **必备字段:** `quote`、`page`、`section`、`reason_zh`。
- **用途:** 仅用于核验关键术语、定义、方法表述或结果句，不作为论文正文材料。
- **限制:** 不允许保存长段原文；模板和校验错误必须用中文说明短引用的用途和限制。

### 13. Uncertain points 安全出口

- **决策:** `uncertain_points_zh` 是 LLM 不确定、证据不足或解析不完整时的强制安全出口。
- **规则:** 凡是没有足够证据定位的内容，不得写入 `source_grounded_claims`，必须进入 `uncertain_points_zh`。
- **适用情况:** PDF 解析不完整、章节无法定位、文本片段冲突、LLM 只能推测、缺少实验细节、缺少限制说明等。
- **中文要求:** 每条 uncertain point 用中文说明“不确定什么、为什么不确定、建议用户检查哪里”。

### 14. 图像/图表智能能力归属

- **修正方向:** 用户希望图像能力放到 **Phase 8.1**，作为 Phase 8 reading draft 之后的相邻增强，避免拖到太后面。
- **采纳外部建议:** 明确 Phase 7.1 是 Phase 7 的授权会话子能力；明确 Phase 8 的 `asset_suggestions` 是候选建议，不是“重要图表”定论。
- **建议边界:** Phase 8.1 只做最小必要视觉证据处理，不做高级图表智能。
- **Phase 8 范围:** Phase 8 只生成候选 `asset_suggestions`，例如“第几页哪张图/表可能值得保存或后续识别”，并记录 `reason_zh`、`confidence` 和 `evidence_basis`；不自动截图、不自动裁图、不写 asset manifest，也不直接断言某图表已经具有正式学术重要性。
- **Phase 8.1 范围草案:** 基于 Phase 8 的 `asset_suggestions`，对授权 PDF 或本地资产做候选裁图、caption 提取、基础 OCR、page/region/source trace，并保存为 local-only 可审阅资产建议。
- **延后范围:** 曲线数据提取、高级表格结构理解、图表数值自动还原、图表驱动的自动结论生成继续延后为 Advanced Figure Intelligence。
- **中文用户要求:** 图像识别输出、OCR 结果、低置信度原因、人工审阅提示都必须中文可读；字段名和参数名保留英文并提供中文解释。

### 15. v2 收缩版 Roadmap 对齐

- **决策:** v2 主链收敛为 Phase 6 -> Phase 7 -> Phase 7.1 -> Phase 8 -> Phase 8.1 -> Phase 9 -> Phase 10 -> Phase 11 -> Phase 12 -> Phase 13。
- **已完成 Phase:** Phase 6、7、7.1 的 completed 状态不重开；本次只澄清 Phase 7.1 的关系，并调整 Phase 8 之后的未来边界。
- **Phase 9 调整:** Phase 9 负责融合正文证据和 Phase 8.1 视觉证据候选后进行 AI-assisted scoring；缺少视觉证据时应降级运行。
- **Phase 12 调整:** Local Review Workspace / 本地监管台不做复杂运营面板。
- **延后项:** Crossref/OpenAlex/Zotero 深集成、高级图表智能和 multi-agent 编排不纳入 v2 主闭环。

### 16. LLM 调用方式

- **决策:** `rsa note draft P###` 默认从本地设置读取 LLM 配置并自动调用 LLM 生成阅读草稿。
- **配置来源:** 优先读取 `.rsa/local.yaml` 中的本机私有配置；可由 `rsa.yaml` 提供非敏感默认项，例如 provider、model、超时、chunk 限制和输出语言。
- **密钥原则:** 不在 `rsa.yaml`、`.planning/`、模板或 git tracked 文件中保存 API key；配置中只能引用环境变量名或本地-only secret 路径。
- **失败语义:** 缺少 provider/model/API key/env var、LLM provider 不可用、返回内容无法解析或 schema 不合格时，命令必须 fail closed，写入 `blocked` 或 `partial` 状态和中文修复建议，不生成看似完整的假草稿。
- **自动化边界:** 默认自动运行，适配后续 orchestrator；AI 可做初审并把完整草稿推进到 `ready_for_review`，但不得自动 `approved` 或 formal write。
- **中文用户要求:** 生成内容默认中文；字段名保持英文；错误、修复建议、配置说明必须中文可读。

### 17. LLM 配置内容边界

- **决策:** 配置文件只允许保存非敏感 LLM 配置和环境变量引用，不保存 API key 本体。
- **允许字段:** `provider`、`model`、`api_key_env`、`base_url`、`timeout_seconds`、`max_chunks`、`max_input_tokens`、`temperature`、`language: zh`、`prompt_profile`。
- **推荐位置:** `rsa.yaml` 可保存项目级非敏感默认值；`.rsa/local.yaml` 可覆盖本机 provider/model/api_key_env/base_url 等私有设置，并保持 local-only。
- **禁止内容:** API key、refresh token、cookie、账号密码、机构登录凭据不得写入 tracked 配置、模板、`.planning/` 或 reading note。
- **复现要求:** reading note frontmatter 记录 `llm_provider`、`llm_model`、`prompt_version`、`draft_created_at`，但不记录密钥或完整请求正文。
- **中文用户要求:** README、doctor 和配置错误必须说明“字段名是什么意思、缺什么、怎么设置环境变量”。

### 18. LLM 输出校验失败处理

- **决策:** LLM 返回内容如果不能通过 reading draft schema 校验，`rsa note draft P###` 必须 fail closed，不生成正常 reading note。
- **状态记录:** 根据失败程度写入 `blocked` 或 `partial` 状态报告，并记录中文原因、影响范围和修复建议。
- **保留内容:** 只保存简短失败诊断、provider/model、prompt_version、source hash、parser 状态和 schema error 摘要；不保存 API key、完整 prompt、完整响应或大段全文。
- **重试边界:** v1 Phase 8 不默认无限重试；最多允许实现阶段设计一次安全重试或 `--retry` 显式重试，但重试结果仍必须通过 schema 校验。
- **禁止行为:** 不允许生成字段大量留空但外观看似完成的 reading note；不允许把无法解析的 LLM 自由文本当作 `agent_summary` 写入正式 note。
- **中文用户要求:** 错误提示必须明确说明“模型输出格式不合格、未生成正常阅读草稿、用户可以检查配置/降低 chunk 数/重新运行”。

### 19. Prompt packet 保存策略

- **决策:** Phase 8 保存脱敏、local-only 的 prompt packet，方便复现、调试和后续 eval，但不保存敏感内容。
- **建议位置:** `01_literature/extracted/P###/prompt_packet.yaml` 或实现阶段选定的等价 local-only 目录；该目录不得进入 git。
- **允许内容:** `paper_id`、`source_id`、`source_hash`、`chunk_ids`、`chunk_count`、`prompt_version`、`schema_version`、`llm_provider`、`llm_model`、`language: zh`、`created_at`、`input_token_estimate`、`status`、简短中文诊断。
- **禁止内容:** API key、完整 PDF 全文、完整 prompt、完整 LLM 响应、cookie、账号密码、机构登录凭据、大段版权文本。
- **Reading note 关系:** reading note frontmatter 可引用 prompt packet 的相对路径或 packet id，但不能把 prompt packet 内容复制进 note。
- **失败处理:** 如果 prompt packet 无法写入，不应继续伪造阅读草稿；命令应 fail closed，并用中文说明 local-only 诊断文件无法保存。
- **中文用户要求:** 文档必须解释 prompt packet 是“调试和复现用的脱敏摘要”，不是论文全文缓存，也不是正式科研记录。

### 20. AI 初审与 `ready_for_review`

- **决策:** Phase 8 的自动化目标不是只生成原始草稿，而是尽量自动完成 AI 初审；通过初审的 note 可自动进入 `ready_for_review`。
- **进入条件:** 必须满足授权全文有效、PDF 解析结果可用、LLM 输出通过 schema 校验、关键 claim 有证据定位、short quotes 合规、`uncertain_points_zh` 已记录不确定内容、自动审查清单通过。
- **建议新增字段:** `agent_review_status`、`agent_reviewed_at`、`agent_review_summary_zh`、`agent_review_warnings`、`needs_human_review: true`。
- **状态含义:** `ready_for_review` 表示 AI 已完成初步结构化审查，用户只需要重点监管高风险项、低置信度项、`uncertain_points_zh` 和 formal write requests。
- **人工边界:** `human_confirmed` 必须保持 `false`，直到用户手动确认；`approved`、`formal apply-note` 和任何正式记录写入仍必须由用户执行。
- **失败降级:** 如果自动初审没有通过，note 保持 `draft` 或命令写入 `partial/blocked` 状态，并给出中文原因和修复建议。

### 21. AI 初审检查范围

- **决策:** Phase 8 的 AI 初审只做结构、证据和风险三项检查，不做正式论文质量评价。
- **结构检查:** frontmatter 和正文结构完整；必填字段存在；`note_status`、`evidence_level`、`extraction_status`、`source_file`、`source_hash`、`llm_provider/model` 等元信息可用。
- **证据检查:** `source_grounded_claims` 中关键 claim 必须带 `evidence_page`、`evidence_section`、`source_chunk_id` 或短 `evidence_snippet`；证据不足的内容进入 `uncertain_points_zh`。
- **风险检查:** 检查 PDF 解析是否 `partial`、章节定位是否缺失、LLM 输出是否低置信度、short quotes 是否过长、是否存在过度概括或无法定位依据的说法。
- **不做内容:** 不给 `ai_quality_score`、`ai_relevance_score`、`ai_read_priority_score`；不判断论文好坏；不生成正式学术评价；不替代 Phase 9 scoring 或后续 claim-level citation check。
- **通过条件:** 结构完整、关键 claim 有证据定位、风险项已明确记录、无 schema error、无高风险伪结论时，可自动进入 `ready_for_review`。
- **中文用户要求:** `agent_review_summary_zh` 必须用中文告诉用户“AI 初审通过了什么、还需要人工重点看什么”。

### 22. Review packet 与链接

- **决策:** Phase 8 生成紧凑中文 review packet，作为用户最终监管入口。
- **必要性:** 有必要提供链接。用户不应该只看孤立摘要；review packet 必须能快速跳回相关文档记录，方便核验来源、状态和证据链。
- **建议位置:** `01_literature/notes/P###_review_packet.md` 或实现阶段选定的等价位置；它是可审阅衍生产物，不是 formal record。
- **必须链接:** `metadata/P###.yaml`、`notes/P###_reading_note.md`、`sources/P###.yaml`、PDF status/source candidate record、local-only extracted cache、prompt packet、候选 `asset_suggestions`、后续 Phase 8.1 visual evidence 输出位置。
- **内容范围:** AI 初审结论、需要人工重点看的 claims、`uncertain_points_zh`、short quotes、候选图表/表格、解析/LLM 风险、是否建议人工推进到 `approved` 的检查清单。
- **链接规则:** tracked Markdown 中只写相对路径或 stable id；local-only PDF/cache/image 路径可以在用户本机可读，但不得把二进制内容或大段全文写入 git。
- **边界:** review packet 不做正式学术评价，不替代 `approved`，不写 formal map/research note；它只是监管和人工确认入口。
- **中文用户要求:** packet 正文以中文为主；字段名和文件名保持英文，旁边给中文解释。

### 23. Review packet 10 分初审分

- **决策:** Phase 8 review packet 增加 `agent_review_score_10`，满分 10 分，用于表示 reading note 的 AI 初审通过度。
- **分数含义:** 该分数只评价“阅读草稿是否足够完整、可追溯、适合交给用户监管”，不是 `ai_quality_score`、不是 `ai_relevance_score`，也不是论文质量或学术价值判断。
- **建议阈值:** 6 分及以上可标记为“建议进入人工通过检查”；8 分及以上可标记为“低风险 ready_for_review”；低于 6 分保持 `draft` 或要求修复。
- **不得自动批准:** 即使分数高于 6，也不能自动设置 `approved`，不能自动 `human_confirmed: true`，不能自动 formal write。
- **建议 rubric:** 结构完整性 2 分；证据定位与 claim grounding 3 分；不确定性和风险披露 2 分；short quotes 合规 1 分；来源/授权/缓存/packet 链接完整 1 分；中文可读性和监管清单清晰 1 分。
- **输出字段:** `agent_review_score_10`、`agent_review_grade`、`agent_review_rationale_zh`、`score_breakdown`、`recommended_human_action_zh`。
- **中文用户要求:** 分数旁必须用中文解释“为什么是这个分、扣分点是什么、用户重点看哪里”。
