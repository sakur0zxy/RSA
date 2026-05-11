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
<!-- GSD:rsa-cli-end -->

<!-- GSD:profile-start -->
## Developer Profile

Profile not yet configured. Run `$gsd-profile-user` if a persistent developer profile is needed.
<!-- GSD:profile-end -->
