# RSA 科研 Agent Harness

## 项目定位

RSA 是一个面向博士科研工作的本地优先 research agent harness。它不负责自动写论文，也不把 agent 输出当作事实源；它负责把文献检索、候选核验、正式 metadata、阅读笔记、文献映射、研究空白和 eval 回归检查放进可审计、可回滚、可人工确认的工作流。

v1.0 已作为 `Local Harness` 归档。当前项目可以作为 SAR 间断孔径 / 分布式 SAR 文献工作的起点，也可以复用到其他科研主题，只要新增 topic profile。

## 核心价值

让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

## 语言策略

RSA 当前主要面向中文用户。所有用户可见内容必须中文优先，包括 CLI help、成功提示、错误信息、模板说明、报告正文、README、GSD 文档和人工确认提示。

字段名、YAML key、Markdown 表格列、CLI flag、命令名、状态枚举和代码标识保持英文稳定；当这些英文标识出现在用户需要阅读或填写的位置时，必须提供中文解释或中文上下文。详见 `.planning/LANGUAGE-POLICY.md`。

## 当前状态

- 已发布里程碑：`v1.0 Local Harness`
- Roadmap 归档：`.planning/milestones/v1.0-ROADMAP.md`
- Requirements 归档：`.planning/milestones/v1.0-REQUIREMENTS.md`
- 运行形态：Python CLI、Markdown/YAML 文件、pytest 回归测试
- 当前验证：117 个测试通过，`rsa eval compare` 报告回归数 0

## Requirements

### 已验证能力

- Topic profile 驱动的研究入口 - v1.0
- 带 archive 和 trace summary 的 bounded research round - v1.0
- Metadata-first 正式文献记录 - v1.0
- 候选文献 staging 和 verification review - v1.0
- Paper index 一致性检查 - v1.0
- Literature map 和 topic gap report - v1.0
- 已授权全文 reading note - v1.0
- 人工确认 formal write guardrails - v1.0
- 本地 deterministic eval fixtures - v1.0
- 通过 `AGENTS.md` 提供项目级 agent 指引 - v1.0
- Source ledger 和 asset manifest foundation - v2 Phase 6
- Authorized acquisition workflow - v2 Phase 7

### 下一阶段

- Phase 7 已完成授权全文获取能力，下一步推进 Phase 8 Auto Reading Draft。
- 增加自动阅读、评分、批量 campaign 或 UI 能力时，必须保留 v1 formal write guardrails 和 Phase 7 授权边界。

### 除非重新打开，否则不做

- 自动生成论文或博士论文正文。
- 把未验证候选或 agent summary 当作正式事实。
- 未授权 PDF 下载或绕过出版方访问控制。
- 直接实现 SAR 成像算法。
- 允许多 agent 编排绕过 formal write gates。

## 上下文

项目现在已有可用的本地 harness：

- `01_literature/metadata/` 存放正式文献 metadata。
- `01_literature/agent_outputs/` 存放有边界的 research round archive。
- `01_literature/notes/` 存放结构化 reading note。
- `01_literature/sources/` 存放每篇文献的 source ledger。
- `01_literature/source_candidates/` 存放授权获取候选、匹配证据、审查状态和下载结果。
- `01_literature/assets/P###/manifest.yaml` 存放截图、图表和结果图 manifest。
- `01_literature/literature_map.md` 将已验证文献连接到 topic question 和 planned output。
- `01_literature/synthesis/` 存放 gap report 和 eval report。
- `.planning/` 存放 GSD context、archive、retrospective 和 v2 discussion。

最重要的 v1 边界仍然是：formal records 的权威性高于 generated artifacts。Agent 可以建议、总结或提出正式写入请求，但只有带人工确认的命令才能写入正式记录。

## 约束

- 存储：除非 v2 明确选择数据库，否则继续使用本地 Markdown/YAML。
- 权威性：formal records 高于 `agent_outputs`。
- 版权：不做未授权 PDF 获取。
- 人工审阅：formal writes 必须显式确认。
- 评估：修改 prompt、template、parser 或 formal-write 逻辑后，应运行 `rsa eval compare`。
- 语言：用户可见内容中文优先；schema name、CLI flag、YAML key、表格列、状态枚举和代码标识保持英文，并提供中文解释。

## 关键决策

| 决策 | 原因 | 结果 |
|------|------|------|
| 本地 Markdown/YAML harness | 便于审计、diff、归档和迁移 | v1.0 已验证 |
| Metadata-first formal records | 防止未验证文献事实散落在 agent summary 中 | v1.0 已验证 |
| `agent_outputs` 只做轻量 archive | 保留可追溯性，但不当作正式事实源 | v1.0 已验证 |
| Formal writes 必须人工确认 | 降低 hallucination 和学术诚信风险 | v1.0 已验证 |
| SAR starter profile + generic harness | 服务当前博士课题，同时不把 SAR 硬编码进 Python source | v1.0 已验证 |
| 先做 deterministic evals，再考虑编排 | Harness 可靠性应先于更大的 agent system | v1.0 已验证 |
| 授权全文获取默认 monitored_auto | 用户希望系统可自动推进，同时保留监控和调整入口 | v2 Phase 7 已验证 |
| 不自动化 Sci-Hub 或绕过访问控制 | 避免让自动下载污染合法来源链和正式科研记录 | v2 Phase 7 已验证 |

## 下一里程碑目标

v2 应重点扩展文献工作规模，同时不削弱 v1 安全边界：

1. PDF、截图和重要结果图的 asset management。
2. Authorized download / source trace，只允许 open access、用户提供或用户授权来源。已在 Phase 7 完成。
3. Auto reading draft，基于本地或已授权全文生成可审阅阅读草稿。下一步。
4. Evidence extraction / structured reading signals，在评分前抽取结构化证据。
5. AI-assisted scoring rubric，区分 relevance、quality 和 read priority，且不直接进入 formal records。
6. Workflow orchestrator，串联已有命令，自动跑到 review packet，同时允许用户监控关键环节和调整流程。
7. Batch candidate import 和 campaign review queue。
8. Scholarly API 或 citation manager 集成，但只进入 staging。
9. 本地 review UI，用于 verification、formal approval 和 scoring review。
10. 面向后续写作的 claim-level citation check。

详见 `.planning/v2-DISCUSSION.md`。

---

*Last updated: 2026-05-14 after Phase 7 Authorized Acquisition execution*
