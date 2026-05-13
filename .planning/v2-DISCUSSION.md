# v2 讨论稿: 下一步做什么

**创建时间:** 2026-05-13
**状态:** 讨论稿，不是锁定 requirements

## 推荐 v2 主题

v2 建议把 v1 本地 harness 扩展成更适合大规模文献调研、授权全文获取、自动阅读和写作准备的 workstation，同时保留同一条证据链：

candidate evidence -> verified metadata -> authorized sources/assets -> reading notes -> AI-assisted scoring -> formal map/research notes -> synthesis guidance。

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

价值：它能减少手动下载和整理 PDF 的负担，同时保留 v1 的版权和人工确认边界。

### 4. 自动阅读草稿

**目标:** 基于本地或已授权全文生成可审阅 reading note draft，而不是直接生成正式学术结论。

可能功能：

- `rsa read draft P001`：从 PDF 或已授权全文生成结构化阅读草稿。
- 输出 title/abstract/method/experiment/dataset/key findings/limitations/uncertain points。
- 每条关键判断尽量记录页码、章节或局部证据。
- 保存 short quotes、source-grounded claims、agent summary 和 human decision 的边界。
- 生成 candidate screenshot requests，方便后续保存重要图表和结果截图。

价值：它让自动阅读成为“有证据的初稿”，而不是不可追溯的摘要。

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

### 7. 学术 API 和文献管理器集成

**目标:** 降低手动录入 metadata 的成本，同时保留 verification gates。

可能功能：

- DOI lookup adapter，并标记来源。
- Crossref / Semantic Scholar / OpenAlex / arXiv adapters。
- Zotero / EndNote / BibTeX export 或 sync。
- API 结果只进入 staging，不能直接写 formal records。

价值：规模化调研中 metadata 收集是瓶颈，但 API 数据仍需要人工核验。

### 8. 本地 Review UI

**目标:** 降低候选核验和正式批准的 CLI 操作负担。

可能功能：

- 本地 Web UI，用于 candidate verification。
- 下载状态、阅读草稿、AI scoring 和人工覆盖的 review queue。
- Formal write conflict review screen。
- Literature map 和 gap report 可视化。
- Reading note approval workflow。

价值：v1 CLI 很精确，但长时间 review 需要更易扫描和比较的界面。

### 9. Claim-level Citation Check

**目标:** 在后续写作阶段检查 claim 是否有 approved source 支撑。

可能功能：

- 从 draft 中抽取 claim 到 staging file。
- 将每个 claim 连接到 metadata、reading-note claim 或 map row。
- 标记 unsupported、weakly supported 或 overgeneralized claim。
- 输出保持为 review guidance，不生成最终学术正文。

价值：它直接服务文章/博士论文写作，同时避免 agent 自行发明结论。

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

1. PDF/screenshots asset management。
2. Authorized download / source trace。
3. Auto reading draft。
4. Evidence extraction / structured reading signals。
5. AI-assisted scoring rubric。
6. Batch candidate import 和 campaign review queue。
7. Scholarly API lookup 进入 staging。
8. Verification/approval/scoring 的本地 review UI。
9. Claim-level citation check。
10. 更强 evals。
11. 可选 multi-agent orchestration。

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

## v2 规划时需要决定的问题

- v2 继续 CLI-first + generated reports，还是较早引入 local Web UI？
- 第一个 citation source 选 DOI/Crossref、Zotero、BibTeX import 还是 OpenAlex？
- PDF 是否继续完全手动提供，还是支持用户授权 URL 的受控下载？
- Screenshot metadata 需要多详细，才不会变成负担？
- v2 是否引入 database，还是继续 Markdown/YAML + indexes？
- AI scoring 的 1-5 分制是否足够，还是需要后续支持自定义 rubric 权重？
- `ai_read_priority_score` 是完全 rule-based、AI-generated，还是 AI proposal + rule cap？
