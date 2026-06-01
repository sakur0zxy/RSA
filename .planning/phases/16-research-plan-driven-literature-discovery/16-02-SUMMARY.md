# Phase 16-02 Summary: Provider Search And Campaign Export

## 完成内容

- `search_discovery()` 支持 `openalex`、`crossref` 和 `offline` provider。实现使用 Python 标准库 HTTP，不新增核心依赖。
- provider 响应会规范化为 discovery candidate：`candidate_id`、`source_provider`、`source_query_id`、`title`、`doi`、`official_url`、`year`、`first_author`、`evidence_level`、`reason_zh`。
- `DR###_results.yaml` 和 `DR###_report.md` 记录候选、失败、中文修复建议和预留接口。
- `export_discovery_to_campaign()` 会把候选导入既有 `campaign` 队列，复用 Phase 8.2/11 的去重、链接、metadata intake 和 formal gate 边界。

## 边界

- provider 失败、无结果或 unsupported provider 会 fail closed，不生成伪候选。
- discovery 导出只进入 `campaign` staging，仍不会直接创建 `P###.yaml` 或写 `paper_index.md`。
- 未实现未授权镜像、paywall 绕过、复杂 provider 插件或自动正式写入。

## 验证

- `python -m pytest tests/test_discovery.py tests/test_campaign.py -q`
