# AGENTS.md

老板的项目规则：在代码或文档任务里，先读相关文件，再做最小必要改动。回答要简洁，最后说明改了什么、为什么、风险点和验证。

<!-- GSD:project-start source:PROJECT.md -->
## Project

RSA 科研 Agent 是一个面向博士科研工作的轻量 agent harness 项目。核心目标不是自动写论文，而是让文献调研、元数据核验、主题映射、PDF 状态、阅读笔记和正式记录写入都可追溯、可审计、可回滚、可评估。

核心价值：科研 agent 的每一步输出都必须能追溯到来源、状态和人工确认，未核验的模型判断不能混入正式科研记录。
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

- v1 优先使用本地文件：Markdown、YAML、git。
- 推荐实现语言为 Python CLI，但在真正进入代码阶段前先读取当时已有代码和计划。
- topic profile、prompt、模板、规则、评估用例和状态文件都应落盘，便于 diff 和回滚。
- 后续需要复杂 orchestration 时再考虑 OpenAI Agents SDK 或其他 agent runtime。
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

- 正式记录优先级高于 agent 输出档案。
- `agent_outputs/` 只保存每轮关键结论和必要中间结果，不保存大量原始日志。
- 未核验候选文献只能进入 staging 或 agent_outputs，不能进入正式 metadata。
- 未授权 PDF 不能下载或处理，只能记录获取状态和合法待办。
- 不自动写综述正文、论文正文或最终学术判断。
- 对正式记录的写入必须经过 schema validation、冲突检查和人工确认。
- 项目主要面向中文用户；CLI 输出、错误信息、模板说明、报告、README 和 GSD 文档必须中文优先。
- 字段名、YAML key、Markdown 表格列、CLI flag、状态枚举和代码标识保持英文，但要在用户可见处提供中文解释。
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

目标组件：

- Topic Profile: 定义研究主题、关键词、优先问题、指标、来源和排除范围。
- Round Runner: 创建 bounded research round，限制目标、批量大小、工具和输出。
- Search Candidates: 收集候选文献，默认写入 staging/agent_outputs。
- Verification Review: 核验 DOI、标题、作者、年份、venue、official URL 和可靠性。
- Map Integration: 将已核验文献映射到主题、研究问题、章节和论文产出。
- PDF Status: 只记录合法获取状态、本地路径和待办。
- Paper Reading: 仅基于已提供、已本地存在或已授权全文生成阅读笔记。
- Formal Record Writer: 统一控制正式记录写入。
- Eval Harness: 用固定用例检查 hallucination、越权下载、格式漂移、冲突处理和范围蔓延。
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project-local skills yet. If this project grows repeated SAR or literature-review workflows, add them under `.codex/skills/` with a `SKILL.md`.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before file-changing work, prefer a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `$gsd-discuss-phase 1` to start Phase 1 context gathering.
- `$gsd-plan-phase 1` to create the detailed Phase 1 plan.
- `$gsd-execute-phase 1` to execute the planned work.
- `$gsd-quick` for small fixes and documentation updates.
- `$gsd-debug` for investigation and bug fixing.

Do not edit broad project structure outside the GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:rsa-cli-start source:phase-01 -->
## RSA CLI Harness

Use the project CLI for Phase 1 harness operations:

- `rsa init` creates the configured literature foundation from `rsa.yaml` and `.rsa/local.yaml`.
- `rsa validate-profile <path>` validates a topic profile YAML before it is used by later workflows.
- `rsa new-round --topic <path> --objective <text> --name <text> --max-candidates <n>` creates a bounded research round under `agent_outputs/`.

Evidence hierarchy:

- Formal records are metadata files, `paper_index.md`, `literature_map.md`, notes, and human-confirmed research records.
- `agent_outputs/` is staging only. It may contain round README files, summaries, candidates, and review packets, but it is not a formal source of truth.
- Formal metadata, maps, notes, and research records require schema validation, conflict checks, and human confirmation before writes.

Local-only asset policy:

- PDFs are local-only by default and belong under `01_literature/pdfs/`.
- Important screenshots and result assets are local-only by default and belong under `01_literature/assets/P###/`.
- Metadata may reference local PDFs and assets, but agent round archives should reference those paths rather than storing PDF or screenshot payloads directly.

Phase 7 authorized acquisition:

- `rsa source find P001` uses monitored automation by default: discover candidates, review deterministic authorization/match rules, and download only approved direct PDF sources.
- `rsa source find P001 --no-download` stops at candidate generation for monitoring and adjustment.
- `rsa source candidates P001` is read-only and shows candidate status, match basis, authorization/access modes, Chinese reason text and local path.
- `rsa source download P001 --best` or `--candidate SC001` retries approved candidates without modifying formal metadata.
- `rsa source download P001 --url ... --authorization-mode ... --access-mode ... --usage-restriction-zh ...` is the explicit path for a user-authorized URL.
- Custom providers belong in `.rsa/local.yaml` under `source_discovery.custom_providers`; keep English keys stable and include Chinese `usage_restriction_zh` / `notes_zh`.
- Do not configure or suggest Sci-Hub, unauthorized mirrors, credential bypass, stored passwords, simulated login, captcha/SSO/paywall bypass, or any source that weakens the formal authorization boundary.

Phase 7.1 browser session provider:

- `provider_type: browser_session` is for user-authorized local browser sessions, not credential automation.
- `rsa source login <provider_id>` opens the provider login page; the user logs in manually, and RSA stores only local browser storage state under `.rsa/sessions/`.
- `rsa source session status <provider_id>` is read-only; `rsa source session clear <provider_id>` deletes local session files only.
- Never print or commit cookie values. `.rsa/sessions/**` is local-only.
- Session-backed downloads still go through source candidates, source ledger, hash/deduplication, PDF acquisition report and formal write guardrails.
- A session-downloaded PDF is authorized reading material only; it must not automatically write `metadata`, `literature_map.md`, `agent_research_notes.md`, or thesis conclusions.
- v1 browser session support is limited to cookie-based direct PDF URLs. DOM search, database page clicking and JS download flows belong in a later phase.

Phase 17 dynamic workflow:

- `rsa dynamic evaluate P001` / `C001` generates a DW### decision record and Chinese report from local policy and current artifact state.
- `rsa dynamic validate [DW###]` and `rsa dynamic status [DW###]` are read-only.
- `rsa dynamic override DW### --decision accepted|deferred|rejected|needs_followup --reviewer ... --reason ...` records human supervision only; it is not formal approval.
- `templates/dynamic_workflow_policy.yaml` is the default policy source. Keep rules conservative and auditable.
- `selected_action` is a recommendation, not proof that the action ran.
- `formal_write_allowed` must remain `false`; never use dynamic workflow to write `metadata/`, `literature_map.md`, `agent_research_notes.md`, or thesis conclusions directly.
<!-- GSD:rsa-cli-end -->

<!-- GSD:profile-start -->
## Developer Profile

Profile not yet configured. Run `$gsd-profile-user` if a persistent developer profile is needed.
<!-- GSD:profile-end -->
