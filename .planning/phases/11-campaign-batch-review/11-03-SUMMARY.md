# 11-03 Summary: Review Queue, Batch Report, CLI And Docs

## 完成内容

- 新增 `generate_review_queue`，按 blocked、partial、needs_review、auto_triaged、low_confidence、high_priority、completed_staging、skipped 分组生成监管队列。
- review queue 保留 artifact links、risk flags、score signal、中文监管说明和 review decision 扩展说明。
- 新增 `review_campaign_queue_item`，支持 `accepted | deferred | rejected | needs_followup`，并写入 review history。
- 新增 `write_batch_report`，生成中文批量报告，说明自动化状态、监管队列和正式写入边界。
- 扩展 CLI：
  - `rsa campaign run`
  - `rsa campaign resume`
  - `rsa campaign pause`
  - `rsa campaign queue`
  - `rsa campaign queue review`
  - `rsa campaign report`
- 更新 README 和 GSD 要求/路线图，补充 Phase 11 工作流说明。

## 用户可见边界

- 用户看到的 CLI help、成功提示、错误提示、batch report、README 均以中文为主。
- 英文字段名、状态名、CLI flag 保持稳定，并提供中文解释。
- review queue 决策不等于 formal approval。

## 验证

- `python -m pytest tests/test_campaign.py -q`
- `python -m pytest tests/test_cli.py -q`
- `python -m pytest tests/test_templates.py -q`
- `python -m pytest -q`
