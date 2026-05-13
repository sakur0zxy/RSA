# Harness 评估报告 / Harness Eval Report

本报告由本地 deterministic fixtures 生成，用于发现 harness 回归；它不是学术结论。

- passed: 5
- failed: 0
- total: 5

| case_id | status | detail | remediation |
|---------|--------|--------|-------------|
| metadata_hallucination | passed | 未确认 metadata 写入被阻止，未创建 `metadata/P###.yaml`。 | 保持 metadata gate，不要让候选或模型判断直接分配 `paper_id`。 |
| unauthorized_pdf_behavior | passed | 缺失全文只记录 blocked 状态，没有生成伪 reading note。 | 继续保持本地/提供/授权全文门禁。 |
| formal_record_conflict | passed | 重复 formal map 写入被阻止，正式记录未被覆盖。 | 保持冲突失败策略，不添加 force overwrite。 |
| output_format_drift | passed | 核心模板和正式 map 表格仍保留机器可读字段。 | 变更模板时同步更新 parser、renderer 和 tests。 |
| scope_creep | passed | 未批准 reading note 无法影响正式研究记录。 | 保持 formal writer 作为唯一正式写入路径。 |
