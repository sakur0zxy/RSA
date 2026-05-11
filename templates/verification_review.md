# 候选文献核验记录

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
