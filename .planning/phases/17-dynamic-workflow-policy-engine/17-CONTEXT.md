# Phase 17 Context: Dynamic Workflow Policy Engine

## 目标

Phase 17 为 RSA 增加一个受控的动态工作流策略层。它根据当前项目状态、已有 artifact、workflow/campaign/scoring 状态、依赖可用性和用户配置生成下一步建议，并把每次决策保存为可审计记录。

## 本次决策

- 采用本地 YAML 策略文件：`templates/dynamic_workflow_policy.yaml`。
- 决策记录写入：`01_literature/dynamic_workflows/DW###.yaml`。
- 中文监管报告写入：`01_literature/dynamic_workflows/DW###_report.md`。
- CLI 命令组为 `rsa dynamic evaluate|validate|status|override`。
- 默认自动化程度为 `monitored_auto`：机器可以自动判断下一步，但只生成建议和审计记录。
- `selected_action` 只是建议，不代表已执行。
- `formal_write_allowed` 必须为 `false`，不得绕过 formal write gate。
- 人工监管覆盖使用 `accepted | deferred | rejected | needs_followup`，不使用 `approved`，避免和 formal approval 混淆。

## 保守边界

- 不重写 Phase 10 单篇 workflow。
- 不重写 Phase 11 campaign/batch 调度。
- 不替代 Phase 12 review workspace。
- 不绕过 Phase 13 writing safety。
- 不替代 Phase 14 worker queue。
- 不做自由形式 LLM planner 直接控制执行。
- 不做后台 daemon、云服务或 multi-agent orchestration。

## 预留接口

- `llm_suggestion_adapter`: 后续允许 LLM 提供候选策略建议，但必须进入 staging/review。
- `learned_policy_adapter`: 后续允许基于历史结果调优策略。
- `web_review_adapter`: 后续允许 Web UI 编辑或批准策略。
- `advanced_signal_adapter`: 后续允许接入更复杂的 evidence/safety/quality signals。

## 中文用户原则

用户可见 CLI help、成功输出、错误输出、模板说明、报告正文和 README 必须中文优先；字段名、YAML key、CLI flag、状态枚举和代码标识保持英文稳定。

