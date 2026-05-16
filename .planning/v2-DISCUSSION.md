# v2 讨论稿: 下一步做什么

**创建时间:** 2026-05-13
**状态:** 讨论稿，不是锁定 requirements

## 推荐 v2 主题

v2 建议把 v1 本地 harness 扩展成更适合大规模文献调研、授权全文获取、自动阅读和写作准备的 workstation，同时保留同一条证据链：

candidate evidence -> verified metadata -> authorized sources/assets -> reading notes -> AI-assisted scoring -> formal map/research notes -> synthesis guidance。

## 全局依赖设计原则

依赖设计是全局原则，不属于某一个 phase 的局部实现细节。普通用户基础版必须能够实现当前 agent 的核心闭环；optional extras 只服务非核心增强、未来扩展或开发测试。

基础安装 `python -m pip install -e .` 应包含当前核心功能所需 Python 依赖，包括本地 Markdown/YAML harness、授权来源获取、browser session provider、PDF 文本提取和自动阅读草稿。无法由 pip 可靠安装的外部资源，例如 Playwright Chromium，应通过 `rsa doctor` 或命令级 preflight check 自动检查，并给出中文修复命令。

后续 README 和帮助文档需要提供中文功能依赖矩阵，明确区分基础安装、一次性环境初始化、非核心 extras 和开发依赖。详见 `.planning/DEPENDENCY-POLICY.md`。

## 已收敛的 v2 总原则

- 默认自动运行，用户主要负责监管、异常审阅、人工覆盖和 formal 批准。
- 所有 AI 产物默认只进入 `staging / review packet`，不直接进入 `formal records`。
- 所有自动产物必须标记 `evidence_level`。
- 所有失败必须写状态记录，至少区分 `blocked` / `partial`，并提供中文原因和修复建议。
- 视觉证据只作为候选证据，不直接形成正式学术结论。
- `formal write gate` 不得被 orchestrator、batch、UI 或后续 agent 编排绕过。
- Phase 7.1 是 Phase 7 授权获取体系下的浏览器会话子能力，不是一套独立下载系统。

## 已收敛的 v2 主链

核心顺序收敛为：

Phase 6 -> Phase 7 -> Phase 7.1 -> Phase 8 -> Phase 8.1 -> Phase 9 -> Phase 10 -> Phase 11 -> Phase 12 -> Phase 13。

重型 scholarly metadata 深集成、高级图表智能和 multi-agent 编排不纳入 v2 主闭环。

## 候选工作流

### 1. 大规模文献调研

**目标:** 支持更大的文献批次，但不丢失可审计性。

可能功能：

- `rsa campaign create`：创建多轮 review campaign。
- 从 CSV/BibTeX/RIS 批量导入候选文献。
- 按 DOI、title、official URL 去重。
- Review queue 状态：`new`、`needs_verification`、`verified`、`rejected`、`uncertain`、`deferred`。
- 按 topic profile 和 priority question 输出进度报告。

价值：这直接对应大规模文献调研需求，同时保留 v1 的 staged admission 模型。

### 2. PDF 和截图资产管理

**目标:** 更方便地保存本地 PDF、重要截图、图表和结果图。

可能功能：

- `rsa asset add P001 --file <path> --kind figure|table|result|screenshot`。
- 在 `assets/P###/manifest.yaml` 中保存 asset manifest。
- 截图 metadata：source paper、page、figure/table number、capture reason、thesis use。
- 校验 formal notes 是否通过稳定本地路径引用 assets。

价值：这对应后续写文章时保留 PDF 源文件和重要结果截图的需求。

### 3. 授权全文获取和自动下载

**目标:** 在不绕过版权和访问控制的前提下，自动获取 open access、preprint、用户提供或用户授权的全文。

可能功能：

- `rsa source find P001`：从 DOI、official URL、arXiv、机构仓储或作者主页寻找公开全文候选。
- `rsa source download P001 --source-url <url> --authorization open_access|user_authorized|provided`。
- 下载结果写入 source ledger 和 PDF status report，不直接进入 formal records。
- 记录 `source_url`、`source_type`、`license_note`、`authorization_mode`、`local_pdf`、`downloaded_at`。
- 对未授权、找不到全文、访问失败的文献生成 blocked 状态，不生成假阅读笔记。
- Phase 7.1 的 browser session provider 属于本能力下的一种授权来源 provider；它复用用户本地登录会话，但不改变 Phase 7 的授权边界。

价值：它能减少手动下载和整理 PDF 的负担，同时保留 v1 的版权和人工确认边界。

### 4. 自动阅读草稿

**目标:** 基于本地或已授权全文生成可审阅 reading note draft，而不是直接生成正式学术结论。

可能功能：

- `rsa read draft P001`：从 PDF 或已授权全文生成结构化阅读草稿。
- 输出 title/abstract/method/experiment/dataset/key findings/limitations/uncertain points。
- 每条关键判断尽量记录页码、章节或局部证据。
- 保存 short quotes、source-grounded claims、agent summary 和 human decision 的边界。
- 生成候选 `asset_suggestions`，记录可能值得后续视觉处理的图表/表格、推荐原因、置信度和证据依据。

价值：它让自动阅读成为“有证据的初稿”，而不是不可追溯的摘要。

边界：

- `asset_suggestions` 只是候选建议，不能直接断言“这是论文重要图表”。
- Phase 8 不自动截图、不自动裁图、不做 OCR、不写 asset manifest。

### 4.1. 视觉证据候选提取 / Phase 8.1

**目标:** 在自动阅读草稿之后、AI 评分之前，处理最小必要视觉证据候选。

可能功能：

- 基于 Phase 8 `asset_suggestions`、授权 PDF 或本地资产生成裁图/裁表候选。
- 提取 figure/table caption。
- 对图题、表题、坐标轴标签、图例和表格可见文字做基础 OCR。
- 记录 `page`、`region`、`source_file`、`source_hash`、`asset_id`、`confidence` 和中文不确定性说明。
- 输出 local-only 视觉资产和可审阅 manifest/suggestions。

边界：

- 不做曲线数据自动还原。
- 不做高级表格结构理解。
- 不从图表自动生成正式 scientific conclusion。
- 不把图片 payload 或大段 OCR 原文提交进 git。
- 视觉证据在人工确认前只能作为 review/scoring 候选。

价值：它让图像能力足够早地服务 Phase 9 评分和后续 review，同时不污染 Phase 8 的正文阅读主链。

### 5. Evidence extraction / structured reading signals

**目标:** 在评分前先抽取结构化阅读信号，降低评分漂移。

可能功能：

- 标记文献类型：review、foundational、method、application、benchmark、dataset。
- 抽取 relevance signals：匹配的 topic profile、priority question、关键术语和问题重合点。
- 抽取 quality signals：是否有定量实验、baseline comparison、ablation、limitation section、reproducibility signals。
- 记录 evidence scope：`title_only`、`abstract_only`、`partial_full_text`、`full_text_read`、`manual_verified`。

价值：先抽取证据，再评分，比直接让模型读自由文本打分更稳定。

### 6. AI-assisted scoring / AI 辅助评分

**目标:** 为批量文献 review 提供可解释的辅助排序，而不是生成正式学术评价。

可能功能：

- `ai_relevance_score`：与当前 topic profile 和 priority questions 的相关性。
- `ai_quality_score`：基于 rubric 的方法、实验、比较和可复现性质量判断。
- `ai_read_priority_score`：阅读队列优先级，优先由 relevance、quality、evidence level、paper role 和人工规则合成。
- `score_confidence`：评分置信度。
- `score_evidence_level`：评分依据范围。
- `scoring_basis`：结构化中文理由，包括正向/负向信号。
- `quality_rubric`：拆分质量评分子项，例如 problem clarity、method soundness、experiment strength、comparison fairness、reproducibility signals、limitation awareness。
- `human_review`：记录人工覆盖分数、理由、reviewer 和 reviewed_at。

边界：

- AI scoring 只能用于 queue sorting、candidate screening 和 review guidance。
- 未人工确认的评分不得写入 formal records。
- 评分结果必须保留中文解释和证据范围。
- `abstract_only` 或 `title_only` 的评分应降低 confidence，并限制 priority 上限。

价值：它能帮助大规模文献调研时快速决定先读什么、哪些要人工重点复核、哪些只是低优先级材料。

建议 schema 草案：

```yaml
ai_scoring:
  score_version: "v2-rubric-001"
  score_evidence_level: "abstract_only"
  ai_relevance_score: 4
  ai_quality_score: 3
  ai_read_priority_score: 4
  score_confidence: "medium"

  relevance_rationale_zh: "文章直接讨论间断孔径造成的频域采样缺失，与当前主题 Q1 高度相关。"
  quality_rationale_zh: "实验设计有一定对比，但验证场景较单一，缺少更强的多数据集或消融支持。"

  quality_rubric:
    problem_clarity: 4
    method_soundness: 3
    experiment_strength: 3
    comparison_fairness: 2
    reproducibility_signals: 2
    limitation_awareness: 2

  scoring_basis:
    relevance_signals:
      - "直接匹配 gapped aperture / missing samples"
      - "涉及恢复方法比较"
    quality_signals_positive:
      - "包含定量实验"
      - "存在方法对比"
    quality_signals_negative:
      - "实验覆盖有限"
      - "未见明确消融"

  human_review:
    reviewed: false
    reviewer: null
    reviewed_at: null
    override_relevance_score: null
    override_quality_score: null
    override_priority_score: null
    override_reason_zh: null
```

### 7. 轻量 metadata enrichment

**目标:** 只保留主闭环真正需要的轻量补全，不在 v2 主链中过早接入重型 scholarly integrations。

可能功能：

- DOI/BibTeX 基础补全。
- title/author/year 标准化。
- dedup 辅助。
- 补全结果只进入 staging/review，不直接写 formal records。

价值：规模化调研中 metadata 收集是瓶颈，但 v2 不需要先做完整 Crossref/OpenAlex/Zotero 生态集成。

边界：

- Crossref/OpenAlex/Zotero 深集成进入 deferred。
- 轻量补全可以并入 Phase 9，为 evidence signals、scoring 和 batch review 服务。

### 8. 本地 Review Workspace

**目标:** 提供本地监管台，降低候选核验和正式批准的 CLI 操作负担。

可能功能：

- 本地 Web UI，用于 candidate verification。
- 下载状态、阅读草稿、视觉证据候选、AI scoring 和人工覆盖的 review queue。
- Formal write conflict review screen。
- Literature map 和 gap report 可视化。
- Reading note approval workflow。

价值：v1 CLI 很精确，但长时间 review 需要更易扫描和比较的界面。

边界：

- 只做监管台，不做复杂运营面板。
- 不绕过 formal write gate。

### 9. Claim-level Citation Check

**目标:** 在后续写作阶段检查 claim 是否有 approved source 支撑。

可能功能：

- 从 draft 中抽取 claim 到 staging file。
- 将每个 claim 连接到 metadata、reading-note claim 或 map row。
- 标记 unsupported、weakly supported 或 overgeneralized claim。
- 输出保持为 review guidance，不生成最终学术正文。

价值：它直接服务文章/博士论文写作，同时避免 agent 自行发明结论。

### Deferred A. Advanced Figure Intelligence

**目标:** 记录暂不纳入 v2 主闭环的高级图表能力，避免 Phase 8.1 过度膨胀。

延后能力：

- 曲线数据自动还原。
- 高级表格结构理解。
- 图表数值自动恢复。
- 图表驱动的自动结论生成。
- 复杂视觉问答或多模态 agent 推理。

边界：

- Advanced figure intelligence 只能在 Phase 8.1 最小视觉证据链稳定后重新打开。
- 即使未来实现，也不得绕过人工确认和 formal write gate。

Phase 8.1 只覆盖候选裁图/裁表、caption 提取、基础 OCR 和来源追踪。

### 10. 更强的 Eval

**目标:** 在 v1 deterministic evals 基础上增加研究质量检查。

可能功能：

- Candidate review golden fixtures。
- Source attribution quality 回归检查。
- AI scoring rubric regression fixtures。
- Evidence-level gating checks，确保 `abstract_only` 评分不会被当成 `full_text_read`。
- 可选 LLM-judged evals，但必须有锁定 rubrics。
- Hallucination risk、source quality、schema drift scorecards。

价值：v1 能发现 harness 回归；v2 应进一步发现 research behavior 质量回归。

### 11. 可选 Agent Runtime 编排

**目标:** 只在 harness 稳定后加入多 agent 工作流。

可能功能：

- 明确 search、verification、mapping、reading、eval 等角色。
- 每个角色有独立权限和输出 schema。
- 角色之间必须有 checkpointed human approval。
- Search 或 reading agent 不能直接写 formal records。

价值：多 agent 可以提速，但前提是 v1 guardrails 仍能强制执行。

## 我建议的 v2 顺序

1. Phase 6: PDF/screenshots asset management。
2. Phase 7: Authorized download / source trace。
3. Phase 7.1: Browser session provider，作为 Phase 7 的授权会话子能力。
4. Phase 8: Auto reading draft，只生成正文阅读草稿和候选 `asset_suggestions`。
5. Phase 8.1: Visual evidence extraction，做候选裁图/裁表、caption、基础 OCR 和来源追踪。
6. Phase 9: Evidence signals & AI-assisted scoring，融合正文证据和视觉证据候选，并做轻量 metadata enrichment。
7. Phase 10: Workflow orchestrator，把已有命令和 v2 子能力串成默认自动运行、可监控、可调整的流程。
8. Phase 11: Batch candidate import 和 campaign review queue。
9. Phase 12: Local review workspace，用于监管候选、PDF、阅读草稿、视觉证据、评分和 formal approval。
10. Phase 13: Writing safety & hardening，包含 claim-level citation check、更强 eval、回归测试和 guardrails。

Deferred：Scholarly metadata deep integrations、advanced figure intelligence、multi-agent orchestration。

## 已采纳的外部建议: AI scoring

结论：值得加入 v2 scope，但必须做成“有证据来源的辅助排序器”，不是“论文质量自动判定器”。

采纳项：

- 接受 `ai_relevance_score` 和 `ai_quality_score` 分离。
- 接受 `score_confidence`。
- 接受新增 `score_evidence_level`，枚举建议为 `title_only`、`abstract_only`、`partial_full_text`、`full_text_read`、`manual_verified`。
- 接受新增 `ai_read_priority_score`，但作为 review queue 排序建议，不作为正式结论。
- 接受把 `quality_score` 拆成 `quality_rubric` 子项。
- 接受结构化 `scoring_basis`，避免只有自由文本理由。
- 接受可追溯 `human_review`，记录人工覆盖、reviewer、时间和中文理由。
- 接受在 auto reading draft 和 scoring 之间增加 evidence extraction / structured reading signals。

不采纳或限制：

- 不把 AI scoring 当成正式学术评价。
- 不允许未人工确认的质量结论或推荐标签直接进入 formal records。
- 不让 `ai_read_priority_score` 完全由模型自由生成；应有规则、证据范围和中文理由。

## 已解决或收敛的问题

- v2 继续 CLI-first + generated reports；Local Review Workspace 放到 Phase 12，只做监管台。
- PDF 支持 open access、用户提供和用户授权来源的受控下载；已由 Phase 7/7.1 处理。
- v2 主闭环继续 Markdown/YAML + local-only assets，不在当前主链引入 database。
- Screenshot / visual metadata 在 Phase 8.1 只保留最小必要字段：source、page、region、caption/OCR、confidence、method、Chinese uncertainty note。
- AI scoring 采用 relevance、quality、read priority 三分离；read priority 采用 AI proposal + rule cap，不作为正式学术结论。
- Metadata enrichment 收缩为轻量 DOI/BibTeX 基础补全、title/author/year 标准化和 dedup 辅助；Crossref/OpenAlex/Zotero 深集成延后。
