# RSA 科研 Agent Harness

RSA 是一个本地优先的科研 agent harness，用来管理可审计、可回滚、可人工确认的文献调研流程。v1.0 已归档，核心目标是让 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断写入正式科研记录。

## 当前状态

- 里程碑：`v1.0 Local Harness`
- 状态：已发布并归档
- 语言策略：用户可读内容和交互提示以中文为主；字段名、YAML key、表格列、CLI flag、命令名和代码标识保留英文。
- 存储方式：本地 Markdown/YAML 文件，便于 git diff、人工审阅和长期博士课题记录。

## v1.0 已完成能力

- Topic profile：定义并校验研究主题，包括关键词、优先问题、指标、来源偏好和评分规则。
- Research round：创建有边界的 `agent_outputs/R###_name` 调研轮次，包含目标、限制、最终总结和追踪摘要。
- 正式 metadata：通过人工确认门禁写入 `metadata/P###.yaml`。
- 候选文献 staging：检索候选和核验记录停留在 staging，不会自动进入正式记录。
- Paper index：校验或重建由正式 metadata 生成的 `paper_index.md`。
- Literature map 和 gap report：把已验证文献映射到 topic、章节、计划产出和研究角色，并生成研究空白报告。
- Reading note：只允许基于本地、用户提供或已授权全文创建单篇阅读笔记。
- Formal write guardrails：正式写入必须通过 schema 校验、冲突校验和显式人工确认。
- Harness evals：本地 deterministic fixtures 覆盖 metadata hallucination、未授权 PDF、正式记录冲突、输出格式漂移和 scope creep。

## 快速开始

```powershell
python -m pytest -q
python -m rsa_cli.cli --help
python -m rsa_cli.cli --root . init
```

创建并校验一个有边界的文献调研轮次：

```powershell
python -m rsa_cli.cli --root . validate-profile 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml
python -m rsa_cli.cli --root . new-round --topic 01_literature/topic_profiles/sar_noncontinuous_aperture.yaml --objective "调研间断孔径 SAR 文献" --name "gap sar starter"
python -m rsa_cli.cli --root . round validate R001_gap_sar_starter
python -m rsa_cli.cli --root . round trace R001_gap_sar_starter
```

运行 harness 回归检查：

```powershell
python -m rsa_cli.cli --root . eval run
python -m rsa_cli.cli --root . eval compare
```

## 主要 CLI 命令

| 命令 | 中文说明 |
|------|----------|
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

## 项目结构

```text
01_literature/
  metadata/                 # 正式文献 metadata: P###.yaml
  topic_profiles/           # 研究主题 profile
  agent_outputs/            # 有边界的 round archive
  notes/                    # P###_reading_note.md
  synthesis/                # gap report 和 eval report
  pdfs/                     # 本地-only PDF，git 忽略
  assets/                   # 本地-only 截图/结果图，git 忽略
  paper_index.md            # 正式 metadata 索引
  literature_map.md         # 正式文献到主题的映射
  agent_research_notes.md   # 人工确认后的辅助研究笔记
templates/                  # 用户可编辑模板
src/rsa_cli/                # CLI 和 harness 实现
tests/                      # 回归测试
.planning/                  # GSD 计划、里程碑归档和状态
```

## 安全边界

- 候选证据不会自动成为正式 metadata。
- `metadata/P###.yaml` 分配必须带有 `--human-confirmed` 和 `--confirmed-by`。
- 缺失或未授权 PDF 只会生成 blocked 状态记录，不会生成假的 reading note。
- `validate` 命令必须只读。
- `generate` 和 `propose` 可生成建议文件，但不能修改正式记录。
- 正式写入遇到 schema 错误、缺少确认、重复或冲突时必须失败。
- Eval report 和 trace summary 是审计材料，不是学术结论。

## GSD 文档入口

- 当前里程碑总结：`.planning/MILESTONES.md`
- v1 roadmap 归档：`.planning/milestones/v1.0-ROADMAP.md`
- v1 requirements 归档：`.planning/milestones/v1.0-REQUIREMENTS.md`
- v2 讨论稿：`.planning/v2-DISCUSSION.md`
- phase 执行历史：`.planning/phases/`
- 复盘：`.planning/RETROSPECTIVE.md`

## 验证方式

v1.0 归档时使用的验证基线：

```powershell
python -m pytest -q
python -m rsa_cli.cli --root . eval compare
```

归档时全量测试为 94 passed，`eval compare` 结果为 `regressions=0`。
