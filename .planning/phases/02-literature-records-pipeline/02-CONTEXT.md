# Phase 2: Literature Records Pipeline - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 建立正式文献记录流水线：定义 `metadata/P###.yaml` 的正式 schema，提供候选文献 review/staging 格式，生成和校验 `paper_index.md`，并确保候选文献在人工确认前不会进入正式 metadata。

本阶段交付的是文献记录和一致性规则，不交付真实联网搜索、自动 PDF 获取、全文阅读笔记、topic mapping、正式 research map 写入、LLM agent 编排或大规模 campaign orchestration。

</domain>

<decisions>
## Implementation Decisions

### User-Facing Language
- **D-01:** 所有需要用户阅读的内容都必须提供中文，包括 Markdown 模板、正式记录说明、review 表头、`paper_index.md` 展示内容、CLI 成功/错误提示、CLI help 文案和后续报告。
- **D-02:** 结构化 YAML 字段名和 CLI 参数名保留英文，便于工具稳定、测试和后续集成。
- **D-03:** 当英文 YAML 字段名或 CLI 参数名出现在用户可见内容中时，必须同时提供中文翻译或解释，例如字段说明表、模板注释、help 文案或文档说明。

### Formal Metadata Admission
- **D-04:** 正式 `metadata/P###.yaml` 只能在文献达到 `verified` 且显式 `human_confirmed` 后生成。
- **D-05:** `verified` 表示身份和来源核验通过，不要求已经拿到合法 PDF。
- **D-06:** 身份和来源核验至少需要核对 `title`、`authors`、`year`、`venue`，以及 `doi` 或 `official_url`，并记录 `source_reliability` 和 `last_checked`。
- **D-07:** 正式 metadata 写入必须要求显式人工确认参数，例如 `--human-confirmed` 和 `--confirmed-by`。没有人工确认时只能留在 staging/review。
- **D-08:** `rejected` 和 `uncertain` 候选保留在 round 的 `verification_review.md` 或 staging 文件中，不分配正式 `P###`。

### Formal Metadata Schema
- **D-09:** Phase 2 的正式 metadata 使用标准字段集，覆盖身份、来源核验、收录决策、PDF/资产、课题用途和人工确认。
- **D-10:** 标准字段集包括：`paper_id`、`title`、`authors`、`year`、`venue`、`doi`、`official_url`、`source_reliability`、`verification_status`、`decision`、`decision_reason`、`last_checked`、`pdf_status`、`local_pdf`、`assets`、`topic_profile`、`priority_questions`、`used_for`、`research_roles`、`notes`、`human_confirmed`、`confirmed_by`、`confirmed_at`。
- **D-11:** `assets` 引用 `01_literature/assets/P###/` 下的本地截图、图表或结果图路径；PDF 引用 `local_pdf`，不把 PDF 或截图 payload 放进 agent round archive。

### Paper ID and File Rules
- **D-12:** 正式 paper id 使用简单递增编号：`P001`、`P002`、`P003`。
- **D-13:** `P###` 只有在正式 metadata 写入成功时才占用。候选、`uncertain`、`rejected` 不占正式编号。
- **D-14:** 正式 metadata 文件名只使用 ID，例如 `metadata/P001.yaml`。
- **D-15:** 每篇文献的本地截图和结果资产目录跟随同一个 ID，例如 `assets/P001/`。

### Candidate Review Records
- **D-16:** 候选文献 staging/review 的主记录使用每轮的 Markdown 文件 `verification_review.md`。
- **D-17:** Phase 2 暂时不引入 `C001` candidate id、每候选一个 YAML 文件或单独 candidate schema。
- **D-18:** 候选状态枚举只使用 `verified`、`rejected`、`uncertain`。
- **D-19:** `verified` 只表示来源核验通过和可以建议入库，不会自动写入正式 metadata。
- **D-20:** `verification_review.md` 使用轻量证据字段：`candidate_title`、`source`、`doi_or_url`、`decision`、`reason`、`last_checked`。用户可见模板必须解释这些英文名的中文含义。

### Paper Index
- **D-21:** `paper_index.md` 是人类可读索引，但正式事实源仍然是 `metadata/P###.yaml`。
- **D-22:** `paper_index.md` 默认展示精简列：`paper_id`、`year`、`title`、`venue`、`decision`、`used_for`、`pdf_status`。
- **D-23:** `paper_index.md` 按 `paper_id` 升序排列。
- **D-24:** `paper_index.md` 不建议手动维护，应由 CLI 根据 metadata 生成和校验。
- **D-25:** 如果 metadata 和 `paper_index.md` 不一致，CLI 校验应报错并提供可操作的不一致信息。重建 index 必须通过显式 regenerate 命令，不在 validate 时自动改文件。

### Phase 1 Localization Cleanup
- **D-26:** Phase 1 已经生成、且后续用户会阅读或编辑的英文模板和正式记录种子，也必须在 Phase 2 执行时补中文说明；这属于用户可见性修正，不改变 Phase 1 的功能边界。
- **D-27:** 需要补中文说明的 Phase 1 遗留对象由执行者判断，但至少包括：`templates/topic_profile.yaml`、`templates/round_readme.md`、`templates/final_round_summary.md`、`templates/paper_note.md`、`templates/map_integration.md`、`templates/pdf_acquisition_report.md`、`templates/reading_batch_report.md`、`01_literature/literature_map.md`、`01_literature/research_tables.md`、`01_literature/agent_research_notes.md`。`templates/paper_metadata.yaml`、`templates/search_candidates.md`、`templates/verification_review.md` 和 `01_literature/paper_index.md` 已由 Phase 2 的 metadata/review/index 计划覆盖，但同样必须遵守 D-01 至 D-03。

### the agent's Discretion
- 具体 CLI 子命令名称可以由 planner 决定，但必须体现人工确认门槛和显式 regenerate 行为。
- 具体 YAML 校验实现、日期格式校验和 Markdown 表格生成方式可以由 planner 决定，只要保持本地文件、可测试、可 diff。
- 模板中文措辞可以在实现阶段微调，但不能去掉英文 key 的中文解释。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` - Project identity, evidence hierarchy, local-first constraints, human-review principle.
- `.planning/REQUIREMENTS.md` - Phase 2 requirements: `META-01`, `META-02`, `META-03`, `SRCH-01`, `SRCH-02`.
- `.planning/ROADMAP.md` - Phase 2 goal, success criteria, and plan outline.
- `.planning/STATE.md` - Current project state and next phase position.
- `.planning/phases/01-harness-foundation/01-CONTEXT.md` - Prior decisions on directory skeleton, bounded rounds, local PDFs/assets, and formal-write policy.
- `AGENTS.md` - Project-local agent instructions, evidence hierarchy, GSD workflow, and local-only asset policy.

### Existing Harness Code
- `rsa.yaml` - Current config defaults for literature root, round limits, approval mode, and campaign id.
- `src/rsa_cli/config.py` - Project config loading and path accessors.
- `src/rsa_cli/cli.py` - Existing `rsa` CLI entry point and error handling pattern.
- `src/rsa_cli/rounds.py` - Existing bounded round creation and formal-write guardrail wording.
- `src/rsa_cli/templates.py` - Existing root templates and formal record seed files.
- `templates/paper_metadata.yaml` - Current minimal metadata template to expand.
- `templates/verification_review.md` - Current minimal candidate review template to localize and expand.
- `templates/search_candidates.md` - Candidate staging template related to Phase 2 review flow.
- `templates/topic_profile.yaml` - Phase 1 topic profile template that needs Chinese field explanations.
- `templates/round_readme.md` - Round archive README template that needs Chinese user-facing labels.
- `templates/final_round_summary.md` - Round summary template that needs Chinese section names.
- `templates/paper_note.md` - Reading-note template seed that needs Chinese explanations without implementing Phase 4 reading behavior.
- `templates/map_integration.md` - Map-integration template seed that needs Chinese explanations without implementing Phase 3 mapping behavior.
- `templates/pdf_acquisition_report.md` - PDF status template seed that needs Chinese explanations without enabling unauthorized PDF acquisition.
- `templates/reading_batch_report.md` - Reading batch template seed that needs Chinese explanations without implementing reading-note generation.
- `01_literature/literature_map.md` - Formal map seed that needs Chinese guidance while remaining a placeholder until Phase 3.
- `01_literature/research_tables.md` - Formal research-table seed that needs Chinese guidance.
- `01_literature/agent_research_notes.md` - Agent note seed that needs Chinese guidance preserving auxiliary status.

### Prior Literature Workflow Reference
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/agent_literature_workflow_plan.md` - Old literature agent workflow, metadata fields, verification review responsibilities, and staging boundaries.
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/phase_0_literature_research_plan.md` - SAR research priorities and output expectations.
- `E:/博士文件/工作整理/PhD_DistributedSAR_NoncontinuousAperture/00_plan/research_question_boundary.md` - SAR topic boundary and failure conditions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProjectConfig` already resolves `literature_root`, `templates_root`, `topic_profiles_root`, and `agent_outputs_root`; Phase 2 should add metadata/index paths through the same config style.
- The CLI already uses `argparse`, returns concise stderr errors, and catches known exception types instead of dumping tracebacks.
- `TEMPLATE_FILES` and root `templates/` already provide the template override pattern.
- Existing tests cover config merge, CLI smoke behavior, skeleton creation, topic profiles, and round creation.

### Established Patterns
- Local-first Markdown/YAML records are the default.
- Formal records outrank `agent_outputs/`.
- Agent outputs can stage suggestions, but formal writes require validation and human confirmation.
- PDFs and screenshots are local-only and referenced by paths.
- Core data keys use English; user-facing explanation should now be Chinese.

### Integration Points
- New Phase 2 code should connect through `rsa` CLI subcommands.
- Metadata files belong under the configured literature root, defaulting to `01_literature/metadata/`.
- Index generation and validation connect to `01_literature/paper_index.md`.
- Candidate review templates connect to round archives under `01_literature/agent_outputs/R###_.../`.

</code_context>

<specifics>
## Specific Ideas

- `metadata/P###.yaml` is a formal fact card for one verified and human-confirmed paper, not a reading note and not an agent summary.
- `human_confirmed` means the user or designated human has approved the record for formal storage; it does not mean the full paper has already been deeply read.
- `paper_index.md` should be quick to scan in Chinese, while still showing stable English field names where useful.
- Phase 1's English-only placeholders should be localized as a cleanup inside Phase 2 so the project does not carry mixed-language user-facing templates into later phases.
- Large-scale literature review remains possible later through multiple bounded rounds and campaign metadata, not by weakening Phase 2's formal admission gate.

</specifics>

<deferred>
## Deferred Ideas

- Per-candidate YAML files and `C001` candidate IDs are deferred until there is evidence that Markdown review tables are insufficient.
- Automatic formal metadata creation from `verified` candidates is rejected for v1.
- Rich topic mapping, thesis chapter grouping, planned paper outputs, coverage gaps, and formal map updates belong to Phase 3.
- Real search adapters, large campaign orchestration, PDF acquisition automation, reading notes, and LLM agent execution remain later-phase or v2 work.

</deferred>

---

*Phase: 02-literature-records-pipeline*
*Context gathered: 2026-05-11*
