# Phase 16-01 Summary: Discovery Profile And Query Bundle Foundation

## 完成内容

- 新增 `ProjectConfig.discovery_root` 和 `DEFAULT_CONFIG["discovery"]`，配置 `default_provider`、`default_max_queries`、`default_max_results`、`allowed_providers` 和 `automation_mode`。
- `rsa init`/skeleton 会创建 `01_literature/discovery/`，用于保存科研计划驱动发现的 staging 产物。
- 新增 `src/rsa_cli/discovery.py` 的基础能力：`DR###` 编号、科研计划 `.md/.txt` 或 `--objective` 输入、topic profile 辅助关键词、`DR###_profile.yaml`、`DR###_queries.yaml`、只读 `validate_discovery()` 和 `discovery_status()`。
- 用户可读字段包含中文解释，稳定字段名保持英文，例如 `plan_source`、`research_questions`、`query_bundle`、`evidence_level`、`status`。

## 边界

- Phase 16-01 只创建 discovery staging 记录，不搜索 provider，不创建 campaign，也不写 `metadata/P###.yaml`。
- `.docx`、BibTeX、Zotero、LLM query refinement 和 Web UI 作为后续接口保留，不进入 v1 实现。

## 验证

- `python -m pytest tests/test_discovery.py tests/test_config.py tests/test_skeleton.py -q`
