# 外部建议导入评估: v2 AI Scoring

**日期:** 2026-05-13
**来源:** 用户粘贴的另一个 AI 对 v2 自动阅读和 AI 评分设计的评审建议
**处理流程:** `$gsd-import` 思路，按项目约束做冲突检查后采纳

## Conflict Detection Report

### BLOCKERS (0)

无。

### WARNINGS (2)

[WARNING] AI 评分可能被误读为正式学术结论
  Found: 外部建议引入 `ai_quality_score`、`ai_relevance_score` 和 `ai_read_priority_score`。
  Impact: 如果未加边界，评分可能污染 formal records，违背 v1 的 human-confirmed formal write 原则。
  -> 采纳时必须明确 AI scoring 只属于 staging/review guidance；进入 formal layer 前必须人工确认。

[WARNING] `ai_read_priority_score` 可能变成不可解释排序
  Found: 外部建议新增阅读优先级分。
  Impact: 如果完全交给模型自由生成，批量阅读队列可能被不稳定判断影响。
  -> 采纳时将其定义为可解释的辅助排序字段，优先由 relevance、quality、evidence level、paper role 和人工规则合成。

### INFO (5)

[INFO] Structured scoring basis
  Note: 建议把自由文本 rationale 拆成 `scoring_basis`，有助于 UI、回归评估和人工 review。

[INFO] Quality rubric
  Note: 建议把质量评分拆成 problem clarity、method soundness、experiment strength 等子项，降低单一质量分的漂移。

[INFO] Score evidence level
  Note: 建议显式记录 `title_only`、`abstract_only`、`partial_full_text`、`full_text_read`、`manual_verified`。

[INFO] Human review trace
  Note: 建议把人工覆盖做成 reviewer、time、override score、reason 的可追溯结构。

[INFO] Evidence extraction before scoring
  Note: 建议在 AI scoring 前新增 structured reading signals，先抽取证据，再基于证据评分。

## 采纳结论

### 接受

- 相关性评分和质量评分保持分离。
- 保留 `score_confidence`。
- 新增 `score_evidence_level`。
- 新增结构化 `scoring_basis`。
- 新增 `quality_rubric` 子项。
- 新增 `ai_read_priority_score`，但作为辅助排序字段，不作为正式评价。
- 新增可追溯 `human_review` 机制。
- 在 auto reading draft 和 AI scoring 之间加入 evidence extraction / structured reading signals。
- 明确 AI scoring 只能用于 queue sorting、candidate screening 和 review guidance，不能直接写入 formal records。

### 有条件接受

- `ai_read_priority_score` 不应完全由模型自由判断。v2 设计应允许 rule-based 合成，并记录生成依据。
- 质量评分可以进入 reading note draft 或 campaign review queue，但进入正式研究笔记前需要人工确认。

### 暂不接受

- 不把 AI scoring 做成“论文质量自动判定器”。
- 不把未人工确认的“推荐/不推荐”标签写入正式记录。

## 建议 schema 草案

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
