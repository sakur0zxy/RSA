---
phase: 05-evaluation-and-hardening
artifact: hardening-guidance
created: 2026-05-13
scope: eval-fixtures, trace-summaries, regression-baseline
---

# Phase 05 Hardening Guidance / 加固指南

本文档记录 v1 harness 已知失效模式、检测方式和修复方向。它用于维护科研记录系统，不是学术结论。

## How To Run / 如何运行

- `rsa eval run`: 运行本地 deterministic fixtures，并写入 `01_literature/synthesis/eval_report.md`。
- `rsa eval baseline`: 将当前 fixtures 结果保存为 `eval_baseline.yaml`。
- `rsa eval compare`: 重新运行 fixtures，并与 baseline 比较；如果原本通过的 case 现在失败，则返回非零退出码。
- `rsa round trace R###_name`: 从轮次 archive 重新生成 `trace_summary.md`，只写轮次目录，不修改正式记录。

## Failure Modes / 失效模式

| case_id | 中文说明 | 检测内容 | 修复方向 |
|---------|----------|----------|----------|
| metadata_hallucination | 未经人工确认就写入正式 metadata | 未提供 `--human-confirmed` 时不得创建 `metadata/P###.yaml` | 保持 metadata gate，候选文献只能先留在 staging 或 round archive |
| unauthorized_pdf_behavior | 没有授权全文却生成阅读笔记 | 缺失 source file 时只能记录 blocked 状态，不得创建假 note | 检查 `note create` 的 source/authorization preflight |
| formal_record_conflict | 正式记录冲突或重复写入 | 重复 map/research note 写入必须失败且不覆盖已有内容 | 保持 all-or-nothing preflight，不增加 force overwrite |
| output_format_drift | 模板或表格 schema 漂移 | 核心模板和正式 map 表保留机器可读字段 | 模板变更时同步 parser、renderer 和测试 |
| scope_creep | agent 输出越权影响正式科研记录 | 未 approved 的 reading note 不得写入 map 或 research notes | 保持 formal writer 是唯一正式写入路径 |

## Trace Summary Contract / 追踪摘要契约

每个新 research round 都包含 `trace_summary.md`。该文件应该能回答：

- `tools_used`: 本轮允许或使用过的工具。
- `decisions_made`: 候选文献或轮次内做出的可审计决定。
- `rejected_items`: 被拒绝的候选或输出。
- `uncertain_items`: 仍需人工复核的项目。
- `human_approvals`: 已发生的人类确认或待审正式写入请求。
- `formal_write_request_count`: 轮次提出的正式写入请求数量。

`trace_summary.md` 是审计索引，不是事实源。正式文献事实仍以 `metadata/P###.yaml`、`literature_map.md`、approved reading note 和人工确认记录为准。

## Maintenance Rules / 维护规则

- 修改 prompt、模板、CLI schema 或正式写入逻辑后，先运行 `rsa eval compare`。
- 新增正式写入路径时，必须补一个对应 fixture，证明缺少人工确认时不会写入。
- 新增 round artifact 时，考虑是否需要让 `rsa round trace` 提取摘要。
- 不要让 eval 依赖网络、LLM 评分或子代理；v1 baseline 必须可离线复现。
- 所有用户可读报告继续提供中文解释，字段名、YAML key、表格列和 CLI flag 保持英文稳定。
