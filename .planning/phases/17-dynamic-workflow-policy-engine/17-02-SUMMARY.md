# 17-02 Summary

已完成 `rsa dynamic` CLI：

- `rsa dynamic evaluate TARGET_ID`
- `rsa dynamic validate [DW###]`
- `rsa dynamic status [DW###]`
- `rsa dynamic override DW### --decision accepted|deferred|rejected|needs_followup --reviewer ... --reason ...`

CLI 输出中文优先；字段名和状态枚举保持英文稳定。`override` 只记录监管覆盖，不会允许 formal write。

