# 文献映射

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
