# 17-01 Summary

已完成 dynamic workflow 基础层：

- 新增 `dynamic_workflow` 配置和 ProjectConfig 访问器。
- 新增 `01_literature/dynamic_workflows/` skeleton 目录。
- 新增 `templates/dynamic_workflow_policy.yaml` 和内置 fallback policy。
- 新增 `src/rsa_cli/dynamic_workflow.py`，覆盖 policy 加载、校验、artifact snapshot、规则匹配和 DW 决策记录写入。

边界保持：策略只生成建议，不执行 formal write。

