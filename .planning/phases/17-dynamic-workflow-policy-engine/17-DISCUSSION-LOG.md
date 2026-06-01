# Phase 17 Discussion Log

## 执行方式

本轮按用户要求不启动子代理或子 agent。`gsd-discuss-phase` 的问题由当前会话内联决策，原则是“不扩大化并留好接口”。

## 已完成讨论点

1. 动态工作流定位
   - 选择：做本地策略引擎，不做自由 LLM planner。
   - 理由：RSA 的安全边界依赖 formal write gate，动态决策只能在 staging/review 层建议下一步。

2. 策略存储格式
   - 选择：YAML。
   - 理由：和项目当前 Markdown/YAML harness 一致，便于 git diff、人工审阅和未来迁移。

3. 规则粒度
   - 选择：收敛为 `run_if`、`skip_if`、`retry_if`、`block_if`、`route_to_review_if`、`stop_before_formal_write`。
   - 理由：覆盖当前核心场景，避免一开始做复杂 workflow DSL。

4. 决策审计
   - 选择：每次 evaluate 生成一个 `DW###.yaml` 和中文 report。
   - 理由：动态工作流最容易产生“为什么自动做了这个判断”的疑问，必须可追溯。

5. 人工覆盖
   - 选择：保留 `override` 命令，枚举为 `accepted | deferred | rejected | needs_followup`。
   - 理由：延续 Phase 11 监管语义，不混淆 formal approval。

6. 扩展接口
   - 选择：保留 LLM 建议、学习型策略、Web 编辑和高级信号接口，但当前只标记 reserved。
   - 理由：给后续 v2/v3 留空间，不把 Phase 17 首版扩大成复杂智能调度系统。

