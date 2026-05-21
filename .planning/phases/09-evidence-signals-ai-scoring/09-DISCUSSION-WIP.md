---
phase: "09"
title: Evidence Signals & AI Scoring
status: in_progress
created_at: "2026-05-19"
discussion_mode: "gsd-discuss-phase fallback"
---

# Phase 09 Discussion WIP

> 临时讨论记录。每完成一个小点就更新这里；全部讨论完成后整理进 `09-CONTEXT.md` 和 `09-DISCUSSION-LOG.md`。

## GSD 初始化状态

- 用户触发：`$gsd-discuss-phase 9`，随后再次触发 `$gsd-discuss-phase` 继续讨论。
- 本地 SDK 当前结果：`gsd-sdk query init.phase-op 9` 已正常识别 Phase 9。
- 永久修复：已在 `ROADMAP.md` 增加 GSD 解析索引，并创建 Phase 10-13 占位目录；`gsd-sdk query validate.health` 已恢复 healthy。
- 处理方式：继续执行 Phase 9 的 discuss-phase 上下文收集与决策记录。

## Phase 边界草案

Phase 9 负责把 Phase 8 的正文阅读证据、Phase 8.1 的视觉证据候选、Phase 8.2 的 campaign queue 连接起来，生成 AI-assisted evidence signals 和辅助评分。

## 已锁定的上游边界

- 所有 AI 产物默认进入 staging / review packet，不直接进入 formal records。
- 评分必须区分 relevance、quality、read priority。
- 评分必须记录 evidence level、confidence、structured basis、rubric details 和 human review override。
- 评分只能用于排序、筛选和 review guidance，不能直接成为正式学术结论。
- Phase 9 可以消费正文证据与视觉证据候选；视觉证据缺失或低置信时必须降级。
- Phase 9 的 metadata enrichment 只能轻量服务主闭环：DOI/BibTeX basics、title/author/year normalization、dedup assistance。
- 用户可见内容继续中文优先；字段名、YAML key、CLI flag 和代码标识保持英文稳定。

## 候选灰区

1. Scoring Object And Entry Point：评分对象是单篇 `P###`、campaign item，还是两者都支持。
2. Evidence Signals Schema：评分前需要抽取哪些结构化 evidence signals。
3. Scoring Rubric：relevance、quality、read priority 如何拆分、计分、合成。
4. Visual Evidence Use：Phase 8.1 的图表/表格候选如何参与评分，低置信或缺失时如何降级。
5. Human Review Override：人工覆盖、review 状态和不写入 formal records 的门禁如何表达。
6. CLI And Outputs：需要哪些命令、输出文件和中文 review packet。

## 当前讨论进度

- 已完成 CLI And Outputs 的第 1-7 个决策。
- Phase 9 discuss-phase 决策收集完成，整理进 `09-CONTEXT.md` 和 `09-DISCUSSION-LOG.md`。

## 已完成讨论点

### 1. Scoring Object And Entry Point：评分对象与入口

**决策：** 选择“单篇 + campaign item 都支持，单篇为核心入口”。

**含义：**

- Phase 9 必须提供单篇评分入口，例如 `rsa score P001`。
- Campaign 评分入口复用单篇评分逻辑，例如后续可设计为 `rsa score campaign C001`。
- 单篇评分是最小可验证能力，便于测试、调试、人工复核和 Phase 10 编排。
- Campaign 批量评分只负责遍历、汇总和记录队列状态，不重新实现评分逻辑。

**边界：**

- Phase 9 不做完整 campaign review UI。
- Phase 9 不做 workflow orchestration。
- Phase 9 不把评分结果写入 formal records。

### 2. Scoring Output Location：评分结果保存位置

**决策：** 选择“独立 scoring 文件”。

**含义：**

- 单篇评分结果写入 `01_literature/scores/P###_scoring.yaml`。
- Campaign 评分汇总写入 `01_literature/campaigns/C###_scoring_summary.yaml`。
- Reading note 继续保存阅读草稿就绪度评分，例如 `agent_review_score_10`；Phase 9 的论文相关性/质量/阅读优先级评分不写回 reading note frontmatter。
- Campaign queue YAML 继续保持轻量候选队列职责；批量评分结果通过 summary 文件关联，不直接把大量 AI 判断塞进 queue item。

**边界：**

- Scoring YAML 属于 staging/review 机器可读产物，不是 formal record。
- Scoring Markdown review packet 可作为人类审阅入口，但不能替代机器可读 YAML。
- Formal records 不得直接引用未人工确认的 AI scoring 作为学术结论。

### 3. Evidence Signals Schema：评分前结构化证据信号

**决策：** 选择“基础 signals + rubric-ready signals + provenance links”。

**含义：**

- Phase 9 在正式打分前生成结构化 `evidence_signals`，用于支撑评分、审计、批量排序和后续回归测试。
- 正文信号至少覆盖：`problem_signal`、`method_signal`、`experiment_signal`、`dataset_signal`、`metric_signal`、`finding_signal`、`limitation_signal`。
- 视觉信号至少覆盖：`visual_candidate_ids`、`visual_type`、`evidence_level`、`confidence`、`degraded_reason_zh`。
- 主题信号记录与 `topic_profile`、`priority_question` 的匹配点，并保留中文解释，方便中文用户审阅。
- 来源链路必须能回到 reading note、source chunk、page/region、visual candidate id 或相关 artifact。
- 不确定性信号必须显式记录，例如只看摘要、全文缺失、视觉证据低置信、OCR 部分成功、正文和视觉证据冲突。

**边界：**

- Evidence signals 是评分前的 staging 层，不是 formal record。
- Phase 9 不做完整 claim-level citation check；该能力属于 Phase 13。
- Phase 9 不把图像理解扩张为高级视觉问答或曲线数据自动还原。
- 如果 evidence signals 不足，评分必须降级并写明中文原因，不能伪装成完整评分。

### 4. Scoring Rubric：评分规则

**决策：** 选择“10 分制三类主分 + 子项 rubric + 规则合成阅读优先级”。

**含义：**

- Phase 9 使用 `0-10` 分制，保留足够区分度，方便批量排序、阈值过滤和人工监管。
- 主分必须区分：
  - `ai_relevance_score_10`：论文与当前课题、研究问题、应用场景的相关性。
  - `ai_quality_score_10`：论文质量，由方法清晰度、实验强度、对比公平性、可复现性信号、局限性意识等子项支持。
  - `ai_read_priority_score_10`：阅读优先级，由相关性、质量、证据等级、论文角色和用户课题优先级合成。
- 阈值采用中文可解释规则：
  - `>= 8`：优先阅读 / 重点复核。
  - `6-7`：AI 初审建议通过，进入用户监管队列。
  - `< 6`：低优先级或暂缓阅读。
- `ai_read_priority_score_10` 不完全等于相关性或质量；综述、经典基础论文、高度贴近当前任务但质量中等的论文可以通过规则获得更高阅读优先级。

**边界：**

- `6 分以上建议通过` 只表示 AI 初审建议通过，不表示学术结论已成立。
- 评分不得绕过 human review，也不得直接写入 formal records。
- LLM 不能自由拍脑袋打分；必须输出 rubric 子项、证据范围、中文理由和不确定性说明。
- 低证据等级评分必须限制置信度，并在中文说明里明确“依据不足”。

### 5. Visual Evidence Use：视觉证据如何参与评分

**决策：** 选择“视觉证据作为加权信号参与评分，但必须可降级”。

**含义：**

- Phase 8.1 产生的图表、表格、caption、OCR、LLM 图像分析候选可以进入 Phase 9 的 `evidence_signals`。
- 高置信视觉证据可以增强 `ai_quality_score_10` 的实验强度、方法对比、结果支撑、可复现性信号等子项。
- 高置信视觉证据也可以影响 `ai_read_priority_score_10`，例如论文包含与当前 priority question 直接相关的关键图表或对比实验。
- 低置信视觉证据只能作为弱信号，必须写入 `degraded_reason_zh`，并降低 `score_confidence`。
- 缺失视觉证据不阻塞评分，但评分必须说明证据范围不足，不能假装完成了完整图表审查。
- 正文证据与视觉证据冲突时，评分状态进入 `needs_review`，交给用户监管。

**边界：**

- 视觉证据只参与 AI 初审和排序，不直接成为 formal scientific claim。
- 未人工确认的 OCR 或 LLM 图像解释不得写入 formal records。
- Phase 9 不做曲线数据自动还原、高级表格结构理解或复杂视觉问答；这些属于后续扩展。
- 视觉证据必须保留 `visual_candidate_id`、page/region/source link，便于用户回源核查。

### 6. Human Review Override：人工监管与覆盖

**决策：** 选择“AI 自动判断 + 用户监管追溯 + 事后可修正”的增强版。

**含义：**

- Phase 9 默认自动完成评分、初审建议、中文理由、风险标记和 review packet 生成。
- AI 可以自动作出 staging/review 层判断，用于自动排序、筛选、推进 review queue 和生成候选结论说明。
- AI 可以自动写入 `ai_review_decision`：
  - `recommend_pass`：AI 初审建议通过，进入用户监管队列。
  - `recommend_defer`：低优先级或暂缓阅读。
  - `needs_review`：证据冲突、低置信、高风险、关键字段缺失或接近阈值。
  - `blocked`：缺少必要来源、缺少 reading note、无有效证据或依赖条件不满足。
- 自动化默认尽量往前推进到 staging/review 层：能评分就评分，能排序就排序，能生成 review packet 就生成 packet。
- 用户不需要逐篇确认所有 AI 初审项，只重点监管：
  - `needs_review` / `blocked` 项。
  - `score_confidence` 低的项。
  - `ai_read_priority_score_10 >= 8` 的高优先级项。
  - AI 建议进入 formal write 的项。
  - 正文证据与视觉证据冲突的项。
- 如果后续发现某篇文献存在问题，用户可以事后更改评分、判断或最终处理结果；更改必须留下可追溯记录，而不是静默覆盖旧判断。
- 人工监管与事后修正必须记录到 `human_review` 和 `review_history`：
  - `reviewed`
  - `reviewer`
  - `reviewed_at`
  - `final_decision`
  - `override_relevance_score_10`
  - `override_quality_score_10`
  - `override_priority_score_10`
  - `override_reason_zh`
  - `revision_id`
  - `changed_at`
  - `changed_by`
  - `previous_decision`
  - `new_decision`
  - `change_reason_zh`
- Review packet 必须提供可点击或可追溯链接，指向 scoring YAML、reading note、PDF/source cache、visual candidates、campaign item 和相关规划文档。

**边界：**

- AI 可以自动完成初审、排序和 staging 判断，但不能自动完成 formal approval。
- `recommend_pass` 不是 `approved`；前者是 AI staging 建议，后者必须来自人工监管或正式写入门禁。
- `formal write gate` 继续要求 human confirmation，不允许被 scoring、campaign、orchestrator 或 UI 绕过。
- 自动化程度提高只作用于 review 前的 staging 层，不改变 formal records 的人工确认原则。
- 事后人工修正可以改变当前有效判断，但必须保留历史记录，方便追溯“AI 当时怎么判断、用户后来为什么改”。

### 7. CLI And Outputs：命令与输出文件

**决策：** 选择“最小闭环命令 + scoring/review packet 双输出”。

**含义：**

- Phase 9 先实现够用、可测试、可接 Phase 10 的评分命令，不提前做完整 batch review workspace。
- 单篇命令：
  - `rsa score P001`：对单篇论文生成 scoring YAML 和中文 review packet。
  - `rsa score validate P001`：只读校验评分文件。
  - `rsa score status P001`：查看评分状态、AI 判断、人工监管状态。
  - `rsa score review P001 --final-decision approved|rejected|deferred --reviewer zxy --reason "中文原因"`：人工监督、覆盖或事后修正。
- Campaign 命令：
  - `rsa score campaign C001`：复用单篇评分逻辑，批量生成 campaign scoring summary。
- 输出文件：
  - `01_literature/scores/P###_scoring.yaml`
  - `01_literature/scores/P###_review_packet.md`
  - `01_literature/campaigns/C###_scoring_summary.yaml`

**边界：**

- Phase 9 不做完整 Phase 11 batch review workspace。
- Phase 9 不做 Phase 10 orchestrator；campaign scoring 只批量调用/汇总单篇评分逻辑。
- Markdown review packet 是中文用户审阅入口，但机器可读真相仍以 scoring YAML 为准。
- 所有命令输出必须中文优先，英文 key/flag/status 保持稳定并给出中文上下文。
