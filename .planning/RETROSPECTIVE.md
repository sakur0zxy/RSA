# 复盘

## 里程碑: v1.0 Local Harness

**发布时间:** 2026-05-13
**Phases:** 5
**Plans:** 14
**主要技术栈:** Python 3.11+、PyYAML、argparse、Markdown/YAML files、pytest

### 做成了什么

- 一个本地优先的 literature research harness，提供稳定的 `rsa` CLI。
- Formal metadata、paper index、candidate review、literature map、gap report 和 reading-note workflows。
- Formal writes 前的人类确认与冲突检查。
- Local-only PDF/assets policy。
- Deterministic eval fixtures 和 trace summaries，用于观察回归。
- GSD phase artifacts，用于记录 context、plans、summaries 和 verification。

### 做得顺的地方

- 将 formal records 和 `agent_outputs` 分开，让系统边界更清楚。
- English schema keys + 中文解释，兼顾机器可读和用户可读。
- 小型 deterministic tests 能捕获 SAR hard-coding 和 unsafe write behavior。
- Phase-by-phase summaries 让 archive 和 README 的整理更顺畅。

### 不够高效的地方

- 早期部分 planning files 有编码痕迹，后续人工阅读不够舒服。
- Markdown table parsing 对 v1 足够简单有效，但 record 复杂后会变脆。
- 当前 runtime 里的 GSD milestone audit helper 不完整，所以归档时使用人工检查 + 测试作为证据。

### 已建立的模式

- `validate` 表示只读。
- `generate` 和 `propose` 可以生成 artifacts，但不能改 formal records。
- Formal writes 必须带 `--human-confirmed` 和 `--confirmed-by`。
- 缺失或未授权 PDF 记录为 blocked status，不生成假 note。
- Eval baselines 放在 `01_literature/synthesis/`。

### 关键经验

- Harness 应持续把 evidence admission、reading notes 和 formal synthesis 分成独立步骤。
- 在扩展大规模文献调研前，source retention 和 screenshot asset policy 应先成为一等能力。
- v2 应优先改善 batch review、citation API 和 review UI，同时保留 v1 guardrails。

## 跨里程碑趋势

| 主题 | 观察 |
|------|------|
| 安全性 | Human-confirmed formal writes 仍是核心保护。 |
| 易用性 | CLI 对 v1 足够；大批量 review 会需要更好的界面。 |
| 数据模型 | Markdown/YAML 目前够用；parser 复杂度需要持续观察。 |
| 评估 | Deterministic evals 很有价值，但不能替代语义层面的科研质量检查。 |
