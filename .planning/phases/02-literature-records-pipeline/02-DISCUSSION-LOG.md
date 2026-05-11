# Phase 2: Literature Records Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md`; this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 02-literature-records-pipeline
**Areas discussed:** Formal metadata admission threshold, Paper ID and filename rules, Candidate review record format, paper_index.md visible fields, Formal metadata field depth

---

## Cross-Cutting User-Facing Language

**User's choice:** 所有需要用户看的内容都需要提供中文。字段名和参数名保留英文，但要留有相关翻译或解释。

**Notes:** 这条规则适用于 Phase 2 以及后续面向用户的模板、CLI 文案、报告和正式记录说明。YAML key 和 CLI 参数名保持英文，用户可见解释使用中文。

---

## Phase 1 Localization Cleanup

**User's choice:** 对 Phase 1 中没有进行中文注释和解释的地方添加对应中文，具体哪些地方由执行者判断。

**Notes:** 纳入 Phase 2 执行范围的遗留用户可见对象包括 `templates/topic_profile.yaml`、`templates/round_readme.md`、`templates/final_round_summary.md`、`templates/paper_note.md`、`templates/map_integration.md`、`templates/pdf_acquisition_report.md`、`templates/reading_batch_report.md`、`01_literature/literature_map.md`、`01_literature/research_tables.md`、`01_literature/agent_research_notes.md`。这只是补中文说明，不提前实现 Phase 3/4 的 map、PDF 获取或阅读笔记功能。

---

## Formal Metadata Admission Threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Only verified + human-confirmed | 正式 `metadata/P###.yaml` 只在核验通过且显式人工确认后生成。 | yes |
| Generate metadata for all reviewed candidates | 所有 review 后的候选都进 metadata，用 status 区分。 | |
| Keep uncertain draft YAML elsewhere | verified 进入正式 metadata，uncertain 放非正式 draft/staging YAML。 | |

**User's choice:** Only verified + human-confirmed.

**Notes:** `verified` 的标准是身份与来源核验通过，不要求已经拿到 PDF。人工确认必须通过显式参数触发。没有入库的候选保留在 `verification_review.md` 或 staging 文件中。

---

## Paper ID and Filename Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Sequential P001/P002 IDs | 按正式入库成功顺序递增，ID 不承载年份或主题语义。 | yes |
| Year-based IDs | 例如 `P2024-001`，肉眼能看年份但补录和版本年份会麻烦。 | |
| Topic-prefixed IDs | 例如 `SAR-P001`，多主题时可读但 v1 复杂度更高。 | |

**User's choice:** Sequential `P001`, `P002`, ...

**Notes:** `P###` 只有正式 metadata 写入成功时才占用。文件名只用 `P001.yaml`。资产目录跟随同一 ID，例如 `assets/P001/`。

---

## Candidate Review Record Format

| Option | Description | Selected |
|--------|-------------|----------|
| Per-round Markdown table | 用 `verification_review.md` 作为候选 review 主记录。 | yes |
| One YAML per candidate | 每个候选一个 `C001.yaml`，结构化更强但多一套 schema。 | |
| Both Markdown and YAML | 人看 Markdown，工具读 YAML，但字段会重复。 | |

**User's choice:** Per-round Markdown table.

**Notes:** 状态枚举只使用 `verified`、`rejected`、`uncertain`。review 表字段为 `candidate_title`、`source`、`doi_or_url`、`decision`、`reason`、`last_checked`。`verified` 不自动入 formal metadata，只生成可入库建议。

---

## paper_index.md Visible Fields

| Option | Description | Selected |
|--------|-------------|----------|
| Concise index columns | `paper_id`, `year`, `title`, `venue`, `decision`, `used_for`, `pdf_status`。 | yes |
| Full index columns | 额外显示 authors、doi_or_url、source_reliability、last_checked。 | |
| Minimal index columns | 只显示 paper_id、title、decision。 | |

**User's choice:** Concise index columns.

**Notes:** `paper_index.md` 按 `paper_id` 升序排列，不建议手动维护。CLI 根据 metadata 生成和校验 index；不一致时报错，重建必须使用显式 regenerate 命令。

---

## Formal Metadata Field Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Standard field set | 身份、来源核验、决策、PDF/资产、课题用途、人工确认。 | yes |
| Lighter schema | 只保留身份、来源、PDF、确认字段。 | |
| Fuller schema | Phase 2 就加入章节、论文产出、图表用途等 mapping 字段。 | |

**User's choice:** Standard field set.

**Notes:** 字段包括 `paper_id`, `title`, `authors`, `year`, `venue`, `doi`, `official_url`, `source_reliability`, `verification_status`, `decision`, `decision_reason`, `last_checked`, `pdf_status`, `local_pdf`, `assets`, `topic_profile`, `priority_questions`, `used_for`, `research_roles`, `notes`, `human_confirmed`, `confirmed_by`, `confirmed_at`。

---

## the agent's Discretion

- 具体 CLI 子命令名称。
- 具体 YAML 校验实现和 Markdown 表格生成方式。
- 中文模板措辞细节。

## Deferred Ideas

- Per-candidate YAML files and `C001` candidate IDs.
- Automatic formal metadata creation from `verified` candidates.
- Phase 3 mapping, coverage gap analysis, formal map updates.
- Real search adapters, PDF acquisition automation, reading notes, LLM agent execution, large campaign orchestration.
