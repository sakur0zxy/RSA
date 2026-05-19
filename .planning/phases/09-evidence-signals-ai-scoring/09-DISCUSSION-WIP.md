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

- 用户触发：`$gsd-discuss-phase 9`
- 本地 SDK 结果：`gsd-sdk query init.phase-op 9` 未识别 Phase 9。
- Fallback 原因：ROADMAP 中确实存在 `Phase 9: Evidence Signals & AI Scoring`，但本地 `validate.health` 也已显示当前 ROADMAP 格式/中文内容会导致 phase 识别 warning。
- 处理方式：按 GSD fallback 建立 `.planning/phases/09-evidence-signals-ai-scoring/`，继续执行 discuss-phase 的上下文收集与决策记录。

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

- 待用户选择第一个讨论灰区。
