---
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
