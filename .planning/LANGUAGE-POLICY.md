# RSA 语言策略

## 目标用户

RSA 当前主要面向中文用户。项目默认假设使用者希望用中文阅读工作流说明、CLI 提示、错误信息、报告、模板和人工确认内容。

## 必须中文优先的内容

- CLI help、成功提示、失败提示、状态输出和人工确认说明。
- README、GSD planning 文档、phase context/plan/summary/verification 文档。
- Markdown/YAML 模板中的说明、注释、字段指南和状态说明。
- 生成报告正文，例如 `trace_summary.md`、`eval_report.md`、gap report、PDF/source/asset 状态记录。
- 需要用户审核、填写、复制或据此做决定的任何文本。

## 保持英文稳定的内容

这些内容属于机器接口或长期 schema，不翻译成中文：

- Python 变量名、函数名、类名、模块名和其他代码标识。
- CLI 命令名、subcommand、flag，例如 `rsa source add`、`--human-confirmed`。
- YAML key、Markdown 表格列名、frontmatter key。
- 状态枚举和 schema 值，例如 `draft`、`approved`、`blocked`、`verified`。
- 文件名和目录名，例如 `metadata/P###.yaml`、`literature_map.md`。

## 写作规则

- 英文标识可以保留，但用户可见处必须有中文解释或中文上下文。
- 面向用户的错误信息要先说明“发生了什么”和“怎么修”，英文 key 只作为定位信息。
- 新增 phase、模板、CLI 命令或报告时，计划和测试都要覆盖中文用户可见内容。
- 不为了中文化而改动 schema key、CLI flag、状态枚举或代码标识，避免破坏已有工作流和测试。

## 当前核查结论

- README、当前 PROJECT/REQUIREMENTS、v2 discussion、v1 archive、模板和正式记录 seed 已基本遵循中文优先。
- Phase 1 早期的 profile/config/round 错误信息曾有英文在前或英文-only 文案，本轮已改成中文优先，同时保留 `profile`、`rounds.default_max_candidates` 等英文定位键。
- Phase 6 source/asset 命令整体中文可读；本轮将 `total/available/blocked` 状态输出改为 `总数/可用/阻塞`。
- Eval CLI 输出已从 `passed/report/regressions` 改为 `通过/报告/回归数`；eval YAML/report 内部 schema 字段仍保留英文。
