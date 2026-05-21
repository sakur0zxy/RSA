# RSA 科研 Agent Harness

## What This Is

兼容 GSD health 的英文标题别名；正式中文说明见下方 `## 项目定位`。

## 项目定位

RSA 是一个面向博士科研工作的本地优先 research agent harness。它不负责自动写论文，也不把 agent 输出当作事实源；它负责把文献检索、候选核验、正式 metadata、阅读笔记、文献映射、研究空白和 eval 回归检查放进可审计、可回滚、可人工确认的工作流。

v1.0 已作为 `Local Harness` 归档。当前项目可以作为 SAR 间断孔径 / 分布式 SAR 文献工作的起点，也可以复用到其他科研主题，只要新增 topic profile。

## Core Value

兼容 GSD health 的英文标题别名；正式中文说明见下方 `## 核心价值`。

## 核心价值

让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

## 语言策略

RSA 当前主要面向中文用户。所有用户可见内容必须中文优先，包括 CLI help、成功提示、错误信息、模板说明、报告正文、README、GSD 文档和人工确认提示。

字段名、YAML key、Markdown 表格列、CLI flag、命令名、状态枚举和代码标识保持英文稳定；当这些英文标识出现在用户需要阅读或填写的位置时，必须提供中文解释或中文上下文。详见 `.planning/LANGUAGE-POLICY.md`。

## 依赖策略

RSA 的普通用户基础版必须能实现当前 agent 的核心闭环。`python -m pip install -e .` 应安装当前核心功能所需的 Python 依赖；optional extras 只用于非核心增强、未来扩展或开发测试。

当前核心能力包括本地 Markdown/YAML harness、metadata/round/map/gap、source ledger、授权来源获取、browser session provider、PDF 文本提取和自动阅读草稿。不能把这些核心能力拆成用户必须手动猜测的 optional extras。

无法由 pip 可靠安装的外部资源，例如 Playwright Chromium、本地浏览器运行资源或未来模型/工具资源，应通过 `rsa doctor` 或命令级 preflight check 自动检查。缺失时必须用中文说明缺什么、影响哪个功能、如何修复，并且不得生成伪结果。

依赖策略必须维护命令级核心闭环契约、功能-依赖矩阵、`OK`/`WARN`/`BLOCKED` 自检状态、doctor 与命令 preflight 的边界，以及 fail closed 的统一定义。

详见 `.planning/DEPENDENCY-POLICY.md`。

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
- Browser session provider 作为授权获取子能力 - v2 Phase 7.1

### 下一阶段

- Phase 7/7.1 已完成授权全文获取和浏览器会话复用能力，下一步推进 Phase 8 Auto Reading Draft。
- Phase 8 只生成阅读草稿和候选 `asset_suggestions`；Phase 8.1 再处理最小必要视觉证据候选。
- 增加自动阅读、视觉证据、评分、批量 campaign 或 review workspace 能力时，必须保留 v1 formal write guardrails 和 Phase 7 授权边界。

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
- 依赖：普通用户基础版必须覆盖当前核心 agent 闭环；optional extras 只用于非核心增强、未来扩展或开发测试。

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
| Phase 7.1 是 Phase 7 的子能力 | 浏览器会话复用只是授权获取的一种 provider，不是独立下载政策 | v2 Phase 7.1 已验证 |
| Phase 8 `asset_suggestions` 只做候选建议 | 正文阅读可提示可能值得处理的图表，但不能直接断言图表重要性 | v2 Phase 8 设计约束 |
| 图像能力放入 Phase 8.1 | 让视觉证据在 Phase 9 评分前进入证据链，同时不扩大 Phase 8 正文阅读主流程 | v2 Roadmap 已调整 |
| 自动化采用分层并行 | 单篇论文内部必须按依赖顺序跑；多篇论文可在 campaign 层受控并行，避免 Phase 10 膨胀成批量调度系统 | v2 Phase 10/11 设计约束 |
| 基础版覆盖核心 agent 功能 | 普通用户不应为了当前核心闭环手动猜 optional extras；缺外部资源由自检给中文修复路径 | 全局设计已锁定，待 Phase 8/后续实现落地 |

## 下一里程碑目标

v2 应重点扩展文献工作规模，同时不削弱 v1 安全边界：

1. PDF、截图和重要结果图的 asset management。
2. Authorized download / source trace，只允许 open access、用户提供或用户授权来源。已在 Phase 7/7.1 完成。
3. Auto reading draft，基于本地或已授权全文生成可审阅阅读草稿。下一步。
4. Visual evidence extraction，把 Phase 8 的候选 `asset_suggestions` 转成可审阅裁图、caption、基础 OCR 和来源追踪。
5. Evidence extraction / structured reading signals，在评分前抽取正文证据和视觉证据候选。
6. AI-assisted scoring rubric，区分 relevance、quality 和 read priority，且不直接进入 formal records。
7. Workflow orchestrator，串联已有命令，把单篇论文按依赖顺序自动跑到 review packet，同时允许用户监控关键环节和调整流程。
8. Campaign controlled parallelism 和 batch review queue：多篇论文之间允许小规模流水线并行，但每篇论文内部仍复用 Phase 10 的顺序 workflow primitive。
9. Local review workspace，用于监管候选、PDF、阅读草稿、视觉证据、评分和 formal approval。
10. 面向后续写作的 claim-level citation check。

重型 Crossref/OpenAlex/Zotero 深集成、高级图表智能和 multi-agent 编排不纳入 v2 主闭环；只有 DOI/BibTeX 基础补全、title/author/year 标准化和 dedup 辅助可以按 Phase 9 主闭环需要收窄实现。

详见 `.planning/v2-DISCUSSION.md`。

---

*Last updated: 2026-05-16 after Phase 8/8.1 roadmap alignment*
