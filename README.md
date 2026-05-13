# RSA Research Agent Harness

RSA 是一个本地优先的科研 agent harness，用来管理可审计、可回滚、可人工确认的文献调研流程。v1.0 已归档，核心目标是让 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断写入正式科研记录。

## Status

- Milestone: `v1.0 Local Harness`
- State: shipped and archived
- Language policy: 用户可读内容提供中文说明；字段名、YAML key、表格列和 CLI flag 保持英文稳定。
- Storage model: local Markdown/YAML files, suitable for git diff, manual review and long-term PhD research records.

## What v1.0 Delivers

- Topic profiles: define and validate research topics with keywords, priority questions, metrics, source preferences and grading rules.
- Research rounds: create bounded `agent_outputs/R###_name` archives with objectives, limits, final summaries and trace summaries.
- Formal metadata: add verified papers as `metadata/P###.yaml` only through human-confirmed gates.
- Candidate staging: keep search candidates and verification reviews outside formal records until checked.
- Paper index: validate or regenerate `paper_index.md` from formal metadata.
- Literature map and gap reports: map verified papers to topic profiles, thesis sections, planned outputs and research roles; generate topic gap reports.
- Reading notes: create single-paper notes only from local, provided or authorized source files.
- Formal write guardrails: apply map/note writes only with schema checks, conflict checks and explicit human confirmation.
- Harness evals: run deterministic local fixtures for metadata hallucination, unauthorized PDF behavior, formal conflicts, output drift and scope creep.

## Quick Start

```powershell
python -m pytest -q
python -m rsa_cli.cli --help
python -m rsa_cli.cli --root . init
```

Create and validate a bounded research round:

```powershell
python -m rsa_cli.cli --root . validate-profile 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml
python -m rsa_cli.cli --root . new-round --topic 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml --objective "调研间断孔径 SAR 文献" --name "gap sar starter"
python -m rsa_cli.cli --root . round validate R001_gap_sar_starter
python -m rsa_cli.cli --root . round trace R001_gap_sar_starter
```

Run harness regression checks:

```powershell
python -m rsa_cli.cli --root . eval run
python -m rsa_cli.cli --root . eval compare
```

## Main CLI Commands

| Command | Purpose |
|---------|---------|
| `rsa init` | 创建本地文献工作区结构和模板。 |
| `rsa validate-profile` | 校验 topic profile YAML。 |
| `rsa new-round` | 创建有边界的文献调研轮次。 |
| `rsa round validate` | 只读校验 round archive。 |
| `rsa round trace` | 生成或刷新 `trace_summary.md`。 |
| `rsa add-paper` | 通过人工确认写入正式 metadata。 |
| `rsa validate-index` / `rsa regenerate-index` | 校验或重建文献索引。 |
| `rsa map validate` / `rsa map propose` | 校验正式 map 或生成 map 建议。 |
| `rsa gap generate` / `rsa gap validate` | 生成或校验研究空白报告。 |
| `rsa note create` / `rsa note validate` / `rsa note status` | 创建、校验或查看单篇阅读笔记。 |
| `rsa formal apply-map` / `rsa formal apply-note` | 通过人工确认把建议写入正式记录。 |
| `rsa eval run` / `rsa eval baseline` / `rsa eval compare` | 运行本地 harness evals 和回归比较。 |

## Project Layout

```text
01_literature/
  metadata/                 # Formal paper metadata: P###.yaml
  topic_profiles/           # Research topic profiles
  agent_outputs/            # Bounded round archives
  notes/                    # P###_reading_note.md
  synthesis/                # Gap reports and eval reports
  pdfs/                     # Local-only PDFs, ignored by git
  assets/                   # Local-only screenshots/results, ignored by git
  paper_index.md            # Formal metadata index
  literature_map.md         # Formal paper-to-topic map
  agent_research_notes.md   # Human-approved auxiliary research notes
templates/                  # User-editable templates
src/rsa_cli/                # CLI and harness implementation
tests/                      # Regression tests
.planning/                  # GSD planning, milestone archive and state
```

## Guardrails

- Candidate evidence does not become formal metadata automatically.
- `metadata/P###.yaml` allocation requires `--human-confirmed` and `--confirmed-by`.
- Missing or unauthorized PDFs create blocked status records, not fake reading notes.
- `validate` commands are read-only.
- Generated proposals do not modify formal records.
- Formal writes fail on schema errors, missing approvals, duplicates or conflicts.
- Eval reports and trace summaries are audit artifacts, not academic conclusions.

## GSD Artifacts

- Current milestone summary: `.planning/MILESTONES.md`
- Archived roadmap: `.planning/milestones/v1.0-ROADMAP.md`
- Archived requirements: `.planning/milestones/v1.0-REQUIREMENTS.md`
- v2 discussion draft: `.planning/v2-DISCUSSION.md`
- Phase history: `.planning/phases/`
- Retrospective: `.planning/RETROSPECTIVE.md`

## Verification

The archived v1.0 verification baseline is:

```powershell
python -m pytest -q
python -m rsa_cli.cli --root . eval compare
```

At archive time, the full suite passed with 94 tests and `eval compare` reported `regressions=0`.
