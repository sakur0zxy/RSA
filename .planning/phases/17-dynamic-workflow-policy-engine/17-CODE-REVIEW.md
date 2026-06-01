# Phase 17 Code Review

## Findings

No blocking findings.

## Review Notes

- `dynamic_workflow.py` 写入的 `formal_write_allowed` 强制为 `false`，符合 formal gate 约束。
- invalid policy 会在写入 DW 决策前失败，避免产生伪决策。
- `override` 只更新 `human_override` 和监管状态，不会修改正式记录。
- CLI 输出中文优先，且 `validate`/`status` 为只读路径。
- README 明确说明 `selected_action` 只是建议，不是已执行动作。

## Residual Risk

- 默认策略仍是规则匹配，不是完整 workflow DSL；后续如果策略复杂化，需要保持 schema migration 和回归测试。
- `rsa dynamic evaluate` 当前只生成建议，不自动调用 worker 或 workflow；这是 Phase 17 的安全边界，不是缺陷。

