from __future__ import annotations


TEMPLATE_FILES: dict[str, str] = {
    "topic_profile.yaml": """# 字段说明
# topic_id: 稳定的英文课题编号，供脚本和索引引用。
# topic_name: 中文或英文课题名称，供人阅读。
# core_keywords: 核心检索关键词列表。
# priority_questions: 本课题优先回答的问题列表。
# important_metrics: 评估论文时重点关注的指标。
# preferred_sources: 优先使用的来源类型。
# exclude_scope: 明确排除的范围。
# grade_rules: 候选文献分级规则。
# required_outputs: 每轮调研必须产出的文件名。
topic_id: example_topic
topic_name: 示例研究课题
core_keywords:
  - keyword
priority_questions:
  - 这一轮调研需要回答什么问题？
important_metrics:
  - evidence quality
preferred_sources:
  - peer-reviewed papers
exclude_scope:
  - unverified claims
grade_rules:
  A:
    description: 高优先级候选
    criteria:
      - 直接回答 priority_questions 中的问题
      - 来源可靠，证据可以复用
  B:
    description: 有用的支撑候选
    criteria:
      - 与课题边界相关
      - 可用于背景、理论或对比
  C:
    description: 低优先级候选
    criteria:
      - 关联较弱或证据不足
  Reject:
    description: 范围外或来源不可靠
    criteria:
      - 缺少可靠来源支撑
      - 落入 exclude_scope 排除范围
required_outputs:
  - search_candidates.md
  - final_round_summary.md
""",
    "paper_metadata.yaml": """# 字段说明
# paper_id: 正式文献编号，文件名必须是 metadata/P###.yaml。
# title: 论文标题。
# authors: 作者列表。
# year: 发表年份。
# venue: 期刊、会议或预印本平台。
# doi: DOI；没有 DOI 时必须提供 official_url。
# official_url: 官方页面或可靠来源链接。
# source_reliability: 来源可靠性说明。
# verification_status: 正式记录必须为 verified。
# decision: 人工收录决策。
# decision_reason: 收录决策原因。
# last_checked: 最近一次核验时间。
# pdf_status: PDF 获取与授权状态。
# local_pdf: 本地 PDF 路径；没有合法 PDF 时留空。
# assets: 本地截图、图表或结果图路径列表。
# topic_profile: 关联的课题 profile。
# priority_questions: 该文献服务的优先问题。
# used_for: 计划用途。
# research_roles: 研究角色。
# notes: 人工备注。
# human_confirmed: 是否人工确认写入正式记录。
# confirmed_by: 确认人。
# confirmed_at: 确认时间。
paper_id: P000
title:
authors: []
year:
venue:
doi:
official_url:
source_reliability:
verification_status: unverified
decision:
decision_reason:
last_checked:
pdf_status: not_acquired
local_pdf:
assets: []
topic_profile:
priority_questions: []
used_for: []
research_roles: []
notes:
human_confirmed: false
confirmed_by:
confirmed_at:
""",
    "paper_note.md": """---
paper_id: P000
metadata: metadata/P000.yaml
note_status: draft
source_file:
authorization:
source_grounded_claims: []
short_quotes: []
agent_summary:
human_decision:
human_confirmed: false
confirmed_by:
confirmed_at:
note_integration_requests: []
---

# 文献阅读笔记: P000

## 字段说明

- `paper_id`: 正式文献编号，必须已经存在于 `metadata/P###.yaml`。
- `metadata`: 对应正式元数据文件路径。
- `note_status`: 阅读笔记状态，只能使用 `draft`、`ready_for_review`、`approved` 或 `blocked`。
- `source_file`: 本地、用户提供或已授权全文文件路径。
- `authorization`: 全文授权来源，只能使用 `provided`、`local` 或 `authorized`。
- `source_grounded_claims`: 可追溯到全文来源的事实或方法判断列表。
- `short_quotes`: 短引用摘录列表，只能保留必要短句，不能复制长段原文。
- `agent_summary`: agent 辅助摘要，不是正式学术结论。
- `human_decision`: 人工阅读判断或后续动作。
- `note_integration_requests`: 建议写入正式 map 或研究笔记的请求；必须通过 `rsa formal apply-note` 人工确认后才会生效。

## 来源与授权

- metadata 记录:
- source_file:
- authorization:
- 授权状态: 仅允许使用本地、用户提供或已授权内容；不得根据未授权来源生成全文阅读结论。

## Source-Grounded Claims / 来源支撑判断

## Short Quotes / 短引用

## Agent Summary / Agent 摘要

## Human Decision / 人工决策

- 是否可进入正式研究记录:
- 需要补充核验:
""",
    "round_readme.md": """# 研究轮次 {round_id}

## 目标

{objective}

## 课题与边界

- Profile: `{topic_profile}`
- 候选数量上限 max_candidates: {max_candidates}
- 允许工具 allowed_tools: {allowed_tools}
- 输出策略 output_policy: {output_policy}
- 人工确认模式 approval_mode: {approval_mode}
- Campaign ID: {campaign_id}

## 正式写入规则

本轮可以在 `agent_outputs/` 中暂存候选、证据和草稿；正式 metadata、文献映射、阅读笔记和研究记录都需要经过 schema 校验与人工确认。

## 本地资产

PDF 只记录本地或已授权路径，重要截图和结果图放在 `assets/P###/`，并从 metadata 中引用。
""",
    "final_round_summary.md": """---
status: draft
included_files: []
formal_write_requests: []
human_confirmed: false
confirmed_by:
confirmed_at:
---

# 研究轮次总结: {round_id}

## 状态

`status`: draft

## 关键发现

## 候选决策

如本轮包含 `verification_review.md`，每一行候选文献都必须填写：

- `decision`: 只能使用 `verified`、`rejected` 或 `uncertain`。
- `reason`: 说明核验理由和证据摘要。
- `last_checked`: 记录最近一次核验日期或时间。

## 请求写入正式记录

`formal_write_requests` 只是一组机器可读的写入请求，不会自动创建 `metadata/P###.yaml`，也不会自动更新 `literature_map.md`。

支持的 `request_type`：

- `add_metadata`: 建议后续通过 Phase 2 metadata gate 写入正式文献元数据。
- `add_map_row`: 建议后续通过 `rsa formal apply-map` 写入正式文献映射。

## 人工确认

- `draft`: 草稿，尚未准备好审阅。
- `ready_for_review`: agent 或自动校验流程可以建议的最高状态。
- `completed`: 仅在人工审阅后使用，必须提供 `human_confirmed: true`、`confirmed_by` 和 `confirmed_at`。
- `blocked`: 本轮被阻塞，需要补充来源、核验或人工判断。

- confirmed_by:
- confirmed_at:
""",
    "search_candidates.md": """# 候选文献

候选文献只进入 staging。候选必须先在 `verification_review.md` 中核验，只有 `verified + human_confirmed` 并通过正式 metadata 命令后，才可以创建 `metadata/P###.yaml`。

| candidate_title | source | doi_or_url | why_relevant | next_review_action |
|-----------------|--------|------------|--------------|--------------------|
""",
    "verification_review.md": """# 候选文献核验记录

| candidate_title | source | doi_or_url | decision | reason | last_checked |
|-----------------|--------|------------|----------|--------|--------------|

## 字段说明

- `candidate_title`: 候选文献标题。
- `source`: 候选来源，例如数据库、网页、人工提供列表。
- `doi_or_url`: DOI 或官方/可靠链接。
- `decision`: 核验结论，只能使用 `verified`、`rejected` 或 `uncertain`。
- `reason`: 核验理由和证据摘要。
- `last_checked`: 最近一次核验时间。

## 状态取值

- `verified`: 身份和来源核验通过，但正式 metadata 仍然需要显式 `human_confirmed`。
- `rejected`: 明确不进入正式记录。
- `uncertain`: 信息不足，需要后续补证。
""",
    "map_integration.md": """# 文献映射建议

本模板只记录待人工审核的映射建议，不会因为填写本模板而自动写入正式记录，也不会自动修改正式 `literature_map.md`。

正式映射表使用以下英文列名，并在人工确认后通过 `rsa formal apply-map` 写入：

| paper_id | topic_profile | priority_question | thesis_section | planned_output | research_role | evidence_note | map_status |
|----------|---------------|-------------------|----------------|----------------|---------------|---------------|------------|

## 字段说明

- `paper_id`: 已通过 metadata gate 的正式文献编号。
- `topic_profile`: 课题 profile 的 `topic_id`。
- `priority_question`: 该文献支持的优先问题。
- `thesis_section`: 计划服务的论文章节。
- `planned_output`: 计划形成的综述、实验、表格或论文输出。
- `research_role`: `baseline`、`theory`、`method`、`evaluation`、`comparison`、`background`、`risk_or_limitation`。
- `evidence_note`: 证据摘要。
- `map_status`: `proposed`、`approved`、`needs_review`、`deprecated`。
""",
    "pdf_acquisition_report.md": """# PDF 获取状态记录

不得下载未授权 PDF。本表只记录状态、来源、授权情况和本地路径；PDF 文件由用户在合法授权后放入本地目录。

| paper_id | pdf_status | local_path | source_or_authorization | notes |
|----------|------------|------------|-------------------------|-------|
""",
    "reading_batch_report.md": """# 阅读批次报告

阅读输出必须基于本地、用户提供或已授权全文材料，并在进入正式研究记录前经过人工确认。

| paper_id | reading_note | status | human_approval |
|----------|--------------|--------|----------------|
""",
}


FORMAL_RECORD_FILES: dict[str, str] = {
    "paper_index.md": """# 文献索引

正式事实源是 `metadata/P###.yaml`；本文件只作为人工阅读索引，应由 `rsa regenerate-index` 生成。

| paper_id | year | title | venue | decision | used_for | pdf_status |
|----------|------|-------|-------|----------|----------|------------|

## 字段说明

- `paper_id`: 正式文献编号。
- `year`: 发表年份。
- `title`: 论文标题。
- `venue`: 期刊、会议或预印本平台。
- `decision`: 人工收录决策。
- `used_for`: 计划用于的章节、问题、实验或对比。
- `pdf_status`: PDF 获取与授权状态。
""",
    "literature_map.md": """# 文献映射

用于人工维护 verified 文献与课题、优先问题、论文章节、计划产出和研究角色之间的关系。正式更新必须通过 `rsa formal apply-map --human-confirmed`。

| paper_id | topic_profile | priority_question | thesis_section | planned_output | research_role | evidence_note | map_status |
|----------|---------------|-------------------|----------------|----------------|---------------|---------------|------------|

## 字段说明

- `paper_id`: 已通过 metadata gate 的正式文献编号，必须存在于 `metadata/P###.yaml`。
- `topic_profile`: 课题 profile 的 `topic_id`。
- `priority_question`: 该文献支持的优先问题。
- `thesis_section`: 计划服务的论文或博士论文章节。
- `planned_output`: 计划形成的综述、实验、表格或论文输出。
- `research_role`: 研究角色，只能使用 `baseline`、`theory`、`method`、`evaluation`、`comparison`、`background`、`risk_or_limitation`。
- `evidence_note`: 人工可读的证据摘要。
- `map_status`: 映射状态，只能使用 `proposed`、`approved`、`needs_review`、`deprecated`；只有 `approved` 计入 gap coverage。

## research_role 取值说明

- `baseline`: 基线方法或对照。
- `theory`: 理论依据。
- `method`: 方法设计。
- `evaluation`: 评价指标、数据或实验评价。
- `comparison`: 对比分析。
- `background`: 背景材料。
- `risk_or_limitation`: 风险、局限或失败边界。

## map_status 取值说明

- `proposed`: 建议映射，尚未正式批准。
- `approved`: 已批准映射，可用于 gap coverage。
- `needs_review`: 需要复核。
- `deprecated`: 已弃用，不计入当前覆盖。
""",
    "research_tables.md": """# 研究表格

用于保存经过人工审核的对比表、证据表和实验设置摘要。表格中的结论必须能追溯到正式 metadata 或授权阅读材料。

| table_name | source_papers | purpose | status |
|------------|---------------|---------|--------|
""",
    "pdf_acquisition_report.md": """# PDF 获取状态记录

不得下载未授权 PDF。本表只记录状态、来源、授权情况和本地路径；PDF 文件由用户在合法授权后放入本地目录。

| paper_id | pdf_status | local_path | source_or_authorization | notes |
|----------|------------|------------|-------------------------|-------|
""",
    "agent_research_notes.md": """# Agent 辅助材料

Agent 生成的研究笔记只作为辅助材料；进入论文、正式 map 或研究表格前必须人工审核和确认。

| note_id | source | summary | human_status |
|---------|--------|---------|--------------|
""",
}
