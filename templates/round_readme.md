# 研究轮次 {round_id}

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
