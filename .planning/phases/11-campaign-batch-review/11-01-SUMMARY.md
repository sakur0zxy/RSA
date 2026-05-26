# 11-01 Summary: Campaign Run State And Metadata Intake

## 完成内容

- 在全局配置中加入 `campaign.concurrency`，默认值为 acquisition=2、reading_draft=2、visual_extraction=1、scoring=2。
- 新增 campaign run 相关本地文件约定：
  - `01_literature/campaigns/C###_run.yaml`
  - `01_literature/campaigns/C###_metadata_requests.yaml`
- 为 `queued` campaign item 生成独立的 metadata intake request，默认状态为 `auto_triaged`。
- metadata intake request 保留 `request_id`、`source_campaign_id`、`queued_item_id`、`candidate_metadata`、`triage_reason_zh` 和 `formal_write_allowed: false`。
- 对 `accepted` metadata request 只生成 `formal_write_request`，状态为 `pending_human_approval`，不创建 `metadata/P###.yaml`。

## 边界

- `auto_triaged` 只表示机器已初步分诊，不表示人工批准。
- `accepted` 只表示监管队列项进入后续流程，不等于 formal approval。
- Phase 11 不执行 formal write；正式写入仍必须通过 formal gate 和人工确认命令。

## 验证

- `python -m pytest tests/test_campaign.py -q`
- `python -m pytest -q`
