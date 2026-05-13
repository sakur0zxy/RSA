# RSA Research Agent Harness

## What This Is

RSA 是一个面向博士科研工作的本地优先 research agent harness。它不负责自动写论文，也不把 agent 输出当作事实源；它负责把文献检索、候选核验、正式 metadata、阅读笔记、文献映射、研究空白和 eval 回归检查放进可审计、可回滚、可人工确认的工作流。

v1.0 已经作为 `Local Harness` 归档。当前项目可以作为 SAR 间断孔径 / 分布式 SAR 文献工作的起点，也可以复用到其他科研主题，只要新增 topic profile。

## Core Value

让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

## Current State

- Shipped milestone: `v1.0 Local Harness`
- Archive: `.planning/milestones/v1.0-ROADMAP.md`
- Requirements archive: `.planning/milestones/v1.0-REQUIREMENTS.md`
- Runtime: Python CLI, Markdown/YAML files, pytest regression suite
- Current verification: 94 tests passing and `rsa eval compare` reports `regressions=0`

## Requirements

### Validated

- Topic profile driven research entry - v1.0
- Bounded research rounds with archive and trace summaries - v1.0
- Metadata-first formal paper records - v1.0
- Candidate staging and verification reviews - v1.0
- Paper index consistency checks - v1.0
- Literature map and topic gap reports - v1.0
- Authorized reading notes - v1.0
- Human-confirmed formal write guardrails - v1.0
- Local deterministic eval fixtures - v1.0
- Project-level agent guidance through `AGENTS.md` - v1.0

### Active For Next Milestone

- Decide v2 scope from `.planning/v2-DISCUSSION.md`.
- Define fresh v2 requirements before implementation.
- Preserve v1 guardrails while adding scale, integrations or UI.

### Out of Scope Unless Reopened

- Automatic thesis or paper prose generation.
- Treating unverified candidates or agent summaries as formal facts.
- Unauthorized PDF download or bypassing publisher access controls.
- Direct SAR imaging algorithm implementation.
- Multi-agent orchestration that can bypass formal write gates.

## Context

The project now has a usable local harness:

- `01_literature/metadata/` stores formal paper metadata.
- `01_literature/agent_outputs/` stores bounded research round archives.
- `01_literature/notes/` stores structured reading notes.
- `01_literature/literature_map.md` connects verified papers to topic questions and planned outputs.
- `01_literature/synthesis/` stores gap reports and eval reports.
- `.planning/` stores GSD context, archives, retrospectives and v2 discussion.

The most important v1 boundary remains: formal records outrank generated artifacts. Agent outputs can suggest, summarize or propose, but only human-confirmed commands write formal records.

## Constraints

- Storage: keep v1 data in local Markdown/YAML unless v2 explicitly chooses a database.
- Authority: formal records outrank `agent_outputs`.
- Copyright: no unauthorized PDF acquisition.
- Human review: formal writes require explicit confirmation.
- Evaluation: prompt, template, parser or formal-write changes should run `rsa eval compare`.
- Language: user-facing text should provide Chinese explanation; schema names and CLI flags stay English.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local Markdown/YAML harness | Easy to audit, diff, archive and migrate | Validated in v1.0 |
| Metadata-first formal records | Prevents scattered unverified paper facts | Validated in v1.0 |
| `agent_outputs` as lightweight archives | Keeps traceability without treating generated notes as formal facts | Validated in v1.0 |
| Human-confirmed formal writes | Reduces hallucination and academic-integrity risk | Validated in v1.0 |
| SAR starter profile, generic harness | Serves current PhD topic without hard-coding SAR into Python source | Validated in v1.0 |
| Deterministic evals before orchestration | Harness reliability should precede larger agent systems | Validated in v1.0 |

## Next Milestone Goals

v2 should focus on scaling the literature workflow without weakening v1 safety:

1. Asset management for PDFs, screenshots and important result captures.
2. Batch candidate import and campaign review queues.
3. Scholarly API or citation manager integration into staging.
4. Local review UI for verification and formal approvals.
5. Claim-level citation checks for later writing.

See `.planning/v2-DISCUSSION.md` for details.

---

*Last updated: 2026-05-13 after v1.0 milestone archive*
