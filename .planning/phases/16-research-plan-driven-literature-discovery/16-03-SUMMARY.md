# Phase 16-03 Summary: CLI Documentation Verification And Release Readiness

## 完成内容

- 新增 `rsa discovery run|validate|status`。
- `run` 支持 `--plan-file`、`--objective`、`--topic-profile`、`--provider`、`--max-queries`、`--max-results`、`--no-search`、`--no-campaign` 和 campaign 导入参数。
- `validate` 和 `status` 为只读命令，输出中文状态、候选数、检索式数和文件路径。
- `rsa.yaml` 增加 discovery 默认配置。
- README、ROADMAP、REQUIREMENTS、STATE 和 Phase 16 验证记录会同步更新。

## 边界

- `rsa discovery run` 的默认路径是科研计划 -> discovery artifacts -> provider candidates -> campaign staging。
- 即使自动创建 campaign，也不会绕过后续 metadata intake、review queue 或 formal write gate。

## 验证

- `python -m pytest tests/test_discovery.py tests/test_campaign.py tests/test_cli.py tests/test_config.py tests/test_skeleton.py tests/test_templates.py -q`
- `python -m pytest -q`
- `python -m rsa_cli.cli --root . eval compare`
- `gsd-sdk query state.validate`
