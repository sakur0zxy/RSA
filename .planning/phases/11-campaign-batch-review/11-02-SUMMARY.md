# 11-02 Summary: Pipeline Runner, Concurrency And Resume

## 完成内容

- 新增 `run_campaign`，把 campaign 队列接入 Phase 10 单篇 workflow primitive。
- `linked` item 会自动进入单篇 workflow；`queued` item 会进入 metadata intake request。
- run ledger 记录 `pipeline.strategy: stage_queue_limited_sync`、阶段顺序、worker limits、filters、每个 item 的中文状态和 artifact link。
- 新增 `resume_campaign_run`，恢复时不会重复执行已完成 staging 项。
- 新增 `pause_campaign_run`，支持中文暂停原因。
- 支持 `--dry-run`、`--item/--items`、`--status` 和阶段并发覆盖参数。

## 自动化策略

- 多篇论文之间采用受控流水线并行契约，v2 CLI 先以同步执行方式落地并记录 worker limits。
- 单篇论文内部仍按 acquisition -> reading_draft -> visual_extraction -> scoring -> review_packet 顺序执行。
- 单篇失败时记录 `failed/blocked/partial` 并继续处理其他 item，不让单篇失败拖垮整个 campaign。

## 验证

- `python -m pytest tests/test_campaign.py -q`
- `python -m pytest tests/test_cli.py -q`
- `python -m pytest -q`
