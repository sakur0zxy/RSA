# Phase 12 Discussion WIP: Local Review Workspace

> 临时讨论记录。每完成一个小决策就更新；最终会整理进 `12-CONTEXT.md`。

## 已定决策

### D-01: 本地监管台入口形态

- 选择：`static_package_plus_cli`
- 中文说明：Phase 12 先生成本地静态监管包，用 HTML/Markdown 集中展示 review queue、workflow report、reading draft、visual evidence、AI scoring、formal write request 等材料。
- 操作边界：静态包主要负责查看和导航；真正改变状态仍通过 CLI 命令完成。
- 后续扩展：保留升级成本地 Web 服务的接口，后续 Web UI 可复用 review object、artifact link、decision action 和 workspace manifest。
- formal gate：静态包和未来 Web UI 都不得绕过 formal write gate。

### D-02: 默认展示对象

- 选择：`unified_review_entry`
- 中文说明：Phase 12 默认提供统一监管入口，聚合展示 campaign queue、blocked/partial 项、reading draft、visual evidence、AI scoring、formal write request 等需要用户监管的对象。
- 目标：用户打开一个入口即可看到自动化流程中哪里需要处理，而不是在多个命令或文件之间来回寻找。
- 边界：统一入口只做监管和导航，不把 review decision 当作 formal approval。

### D-03: 对象分组与排序

- 选择：`urgency_first_grouping`
- 中文说明：监管台按处理紧急度分组，而不是按内部模块或论文编号优先展示。
- 默认分组顺序：
  1. `formal_write_request`
  2. `blocked`
  3. `partial`
  4. `needs_followup`
  5. `low_confidence`
  6. `high_priority`
  7. `auto_triaged`
  8. `completed_staging`
- 目标：用户优先看到会影响正式记录、自动化中断、证据不足或需要补材料的项目。
- 边界：分组和排序只影响监管展示，不改变底层 campaign/workflow/scoring 状态语义。

### D-04: 单个监管对象展示信息

- 选择：`summary_evidence_links_action`
- 中文说明：每个监管对象以摘要为主，配套证据链接和建议动作。
- 默认展示字段：
  - 标题或对象名。
  - 对象类型与当前状态。
  - 中文原因、风险说明或阻塞原因。
  - AI 建议、评分、置信度或优先级。
  - 关键证据链接：reading note、workflow report、visual evidence、scoring packet、campaign queue、metadata request、formal write request 等。
- 建议下一步和可执行 CLI 命令。
- 边界：不在列表页直接塞入完整 YAML/Markdown 内容；完整内容通过链接打开。

### D-05: 静态监管包中的操作方式

- 选择：`show_commands_execute_via_cli`
- 中文说明：静态监管包只展示明确的 CLI 命令，由用户在终端执行。
- 示例命令：
  - `rsa campaign queue review C001 --item QI001 --decision accepted --reviewer zxy`
  - `rsa score review P001 --final-decision approved --reviewer zxy --reason "..."`
  - `rsa formal apply-note --source-note P001 --human-confirmed --confirmed-by zxy`
- 不采用：自动执行脚本、静态页面直接修改文件、页面绕过 CLI 调用底层函数。
- 目标：降低误触风险，保持所有状态变更都经过已有 CLI 校验和 formal gate。

### D-06: 全局 workspace manifest

- 选择：`generate_workspace_manifest`
- 中文说明：Phase 12 除了生成 HTML/Markdown 监管页面，还要生成机器可读的 `review_workspace_manifest.yaml` 或 JSON 等价物。
- manifest 内容：
  - workspace 生成时间、源 campaign/paper 范围。
  - 页面路径和对象路径。
  - review object 列表、分组、状态、风险标记。
  - artifact links：reading note、workflow report、visual candidates、scoring packet、metadata request、formal write request 等。
  - 建议 CLI 命令与中文说明。
  - schema/version 字段，方便后续 Web UI 和测试复用。
- 目标：静态包服务当前用户查看；manifest 服务后续 Web UI、测试和自动刷新扩展。

### D-07: 监管台生成范围

- 选择：`campaign_and_paper_entrypoints`
- 中文说明：Phase 12 同时支持 campaign 级监管包和 paper 级监管包。
- 目标命令：
  - `rsa review build --campaign C001`
  - `rsa review build --paper P001`
- campaign 入口：聚合批量 review queue、run ledger、batch report、metadata intake 和 formal write request。
- paper 入口：聚合单篇 metadata、source ledger、reading note、workflow report、visual evidence、scoring packet 和相关 formal request。
- 边界：Phase 12 不做后台自动刷新；刷新由用户重新运行 build 命令完成。

### D-08: 静态监管包页面结构

- 选择：`index_group_detail_pages`
- 中文说明：静态包采用首页、分组页、对象详情页三层结构。
- 页面结构：
  - `index.html`：总览、紧急项、统计、最近生成信息和下一步建议。
  - `groups/*.html`：按 formal write request、blocked、partial、low confidence、high priority 等分组查看。
  - `objects/*.html`：单个 paper、campaign item、metadata request、formal write request 或 review object 的详情页。
- 目标：既能快速监管全局，又能点进对象查看证据链和建议命令。
- 后续扩展：该结构可映射到未来 Web UI 的 route。

### D-09: 证据链接与本地文件打开策略

- 选择：`relative_links_with_missing_markers`
- 中文说明：静态监管包优先使用相对路径链接项目内文件；证据文件缺失时必须显式标记。
- 链接对象：
  - Markdown/YAML：metadata、reading note、workflow report、scoring packet、campaign queue、review queue。
  - 本地资产：PDF、截图、visual crops、context packets。
- 缺失处理：显示中文状态，如“文件缺失”“需要重新生成”“需要补充授权 PDF”“需要重新运行 visual extract”。
- 不采用：默认复制所有 PDF/截图到 workspace；默认生成绝对路径链接。
- 目标：项目目录可迁移，且不会把 local-only 资产无意复制到新的发布目录。

### D-10: 人工审批操作清单

- 选择：`generate_actions_checklist`
- 中文说明：监管台在首页和对象详情页生成 actions checklist，列出建议处理动作和对应 CLI 命令。
- checklist 内容：
  - 待处理对象。
  - 建议动作与中文原因。
  - 是否涉及 formal gate。
  - 推荐执行顺序。
  - 可复制的 CLI 命令。
- 边界：checklist 只是建议和命令说明，不自动执行，不修改状态。
- 目标：让用户快速知道下一步该处理什么，减少在多个报告之间查找命令的成本。

### D-11: 用户备注与标注

- 选择：`note_via_cli_not_inline_edit`
- 中文说明：Phase 12 v1 不在静态页面内直接编辑备注，而是在页面中提供备注/决策命令入口。
- 备注方式：
  - 复用已有 review 命令中的 `--reason`、`--reviewer` 等字段。
  - 后续如需要，可新增 `rsa review note ...` 记录 workspace 级备注。
- 不采用：静态 HTML 直接写文件、直接生成可编辑 Markdown 并把它当作正式记录。
- 目标：保留用户监管意见，同时避免静态页面绕过 CLI 校验。

### D-12: build 命令和输出目录

- 选择：`rsa_review_build_fixed_workspace_root`
- 中文说明：Phase 12 新增 `rsa review build` 命令组，输出到固定监管台目录。
- 目标命令：
  - `rsa review build --campaign C001`
  - `rsa review build --paper P001`
- 输出目录：
  - `01_literature/review_workspace/`
- 后续可扩展命令：
  - `rsa review status`
  - `rsa review open`
  - `rsa review clean`
- 不采用：挂在 `campaign` 或 `workflow` 子命令下，避免 paper/campaign 双入口不自然。

### D-13: 重建、清理与覆盖策略

- 选择：`overwrite_generated_keep_user_records`
- 中文说明：重复运行 `rsa review build` 时，默认覆盖自动生成的 HTML、manifest、分组页和对象页，但保留用户记录类文件。
- 保留对象：
  - review history。
  - 用户备注。
  - 人工 decision 记录。
  - 后续可能新增的 workspace-local audit notes。
- 可覆盖对象：
  - `index.html`
  - `groups/*.html`
  - `objects/*.html`
  - 自动生成 manifest。
- 目标：用户可以通过重新 build 刷新监管台，同时不丢失人工监管痕迹。

### D-14: review 辅助命令

- 选择：`include_lightweight_status_open_clean`
- 中文说明：Phase 12 v1 除 `rsa review build` 外，加入轻量 `status/open/clean` 辅助命令。
- 命令范围：
  - `rsa review status`：查看最近生成的 workspace、目标对象、统计和 index 路径。
  - `rsa review open`：打开最近 workspace 的 `index.html`。
  - `rsa review clean --generated-only`：清理自动生成的 HTML/manifest，保留人工记录。
- 边界：不做后台服务、不做自动刷新、不做页面内状态修改。
- 目标：让用户更容易找到、打开和刷新本地监管台。

## 待继续讨论

- D-15: 是否还有必要讨论更多细节，或收敛生成正式 context。
