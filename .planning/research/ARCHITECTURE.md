# Architecture Research: RSA 科研 Agent

## Component Boundaries

| Component | Responsibility | Writes Formal Records? |
|---|---|---|
| Topic Profile | 定义研究主题、关键词、优先问题、指标、来源和排除范围 | No |
| Round Runner | 创建一轮任务目录，加载 profile，限制范围和批量大小 | No |
| Search Candidates | 生成检索式，收集候选来源，写入 staging/agent_outputs | No |
| Verification Review | 核验 DOI、标题、作者、年份、venue、官方链接和可靠性 | Only with approval |
| Map Integration | 将已核验文献映射到研究主题、章节和论文产出 | Only with approval |
| PDF Status | 记录获取状态、合法来源、本地路径和待办 | Only with approval |
| Paper Reading | 对已授权或已提供全文生成单篇阅读笔记 | Only with approval |
| Formal Record Writer | 统一执行 schema validation、冲突检查、人审状态检查和写入 | Yes |
| Eval Harness | 用固定 fixtures 评估输出格式、权限和学术可靠性 | No |

## Data Flow

```text
topic_profiles/*.yaml
  -> round config
  -> agent_outputs/Rxxx_*/search_candidates.md
  -> verification_review.md
  -> human approval
  -> metadata/Pxxx.yaml
  -> paper_index.md
  -> literature_map.md / research_tables.md
  -> notes/Pxxx.md
  -> agent_research_notes.md
```

## Formal vs Auxiliary Records

Formal records:

```text
01_literature/metadata/
01_literature/paper_index.md
01_literature/literature_map.md
01_literature/research_tables.md
01_literature/agent_research_notes.md
01_literature/notes/
```

Auxiliary records:

```text
01_literature/agent_outputs/Rxxx_short_topic_name/
```

Conflict rule: if auxiliary output conflicts with formal records, formal records win.

## Suggested Build Order

1. Directory schema, templates and topic profile schema.
2. Metadata YAML schema and validation.
3. Round runner and agent output archive.
4. Candidate search and verification workflow.
5. Formal writer with human approval gate.
6. Reading note workflow and literature map updates.
7. Eval harness and regression fixtures.

## Harness Engineering Requirements

- Every editable harness component has a file representation.
- Every formal write has an explicit source, schema validation result and approval status.
- Every research round has a manifest, final summary and rejected/uncertain items.
- Every tool that can affect formal records is gated.
- Every prompt/template/rule change can be checked by eval fixtures.

---
*Research note created: 2026-05-11*
