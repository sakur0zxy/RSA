# v2 讨论稿: 下一步做什么

**创建时间:** 2026-05-13
**状态:** 讨论稿，不是锁定 requirements

## 推荐 v2 主题

v2 建议把 v1 本地 harness 扩展成更适合大规模文献调研的 workstation，同时保留同一条证据链：

candidate evidence -> verified metadata -> reading notes -> formal map/research notes -> synthesis guidance。

## 候选工作流

### 1. 大规模文献调研

**目标:** 支持更大的文献批次，但不丢失可审计性。

可能功能：

- `rsa campaign create`：创建多轮 review campaign。
- 从 CSV/BibTeX/RIS 批量导入候选文献。
- 按 DOI、title、official URL 去重。
- Review queue 状态：`new`、`needs_verification`、`verified`、`rejected`、`uncertain`、`deferred`。
- 按 topic profile 和 priority question 输出进度报告。

价值：这直接对应大规模文献调研需求，同时保留 v1 的 staged admission 模型。

### 2. PDF 和截图资产管理

**目标:** 更方便地保存本地 PDF、重要截图、图表和结果图。

可能功能：

- `rsa asset add P001 --file <path> --kind figure|table|result|screenshot`。
- 在 `assets/P###/manifest.yaml` 中保存 asset manifest。
- 截图 metadata：source paper、page、figure/table number、capture reason、thesis use。
- 校验 formal notes 是否通过稳定本地路径引用 assets。

价值：这对应后续写文章时保留 PDF 源文件和重要结果截图的需求。

### 3. 学术 API 和文献管理器集成

**目标:** 降低手动录入 metadata 的成本，同时保留 verification gates。

可能功能：

- DOI lookup adapter，并标记来源。
- Crossref / Semantic Scholar / OpenAlex / arXiv adapters。
- Zotero / EndNote / BibTeX export 或 sync。
- API 结果只进入 staging，不能直接写 formal records。

价值：规模化调研中 metadata 收集是瓶颈，但 API 数据仍需要人工核验。

### 4. 本地 Review UI

**目标:** 降低候选核验和正式批准的 CLI 操作负担。

可能功能：

- 本地 Web UI，用于 candidate verification。
- Formal write conflict review screen。
- Literature map 和 gap report 可视化。
- Reading note approval workflow。

价值：v1 CLI 很精确，但长时间 review 需要更易扫描和比较的界面。

### 5. Claim-level Citation Check

**目标:** 在后续写作阶段检查 claim 是否有 approved source 支撑。

可能功能：

- 从 draft 中抽取 claim 到 staging file。
- 将每个 claim 连接到 metadata、reading-note claim 或 map row。
- 标记 unsupported、weakly supported 或 overgeneralized claim。
- 输出保持为 review guidance，不生成最终学术正文。

价值：它直接服务文章/博士论文写作，同时避免 agent 自行发明结论。

### 6. 更强的 Eval

**目标:** 在 v1 deterministic evals 基础上增加研究质量检查。

可能功能：

- Candidate review golden fixtures。
- Source attribution quality 回归检查。
- 可选 LLM-judged evals，但必须有锁定 rubrics。
- Hallucination risk、source quality、schema drift scorecards。

价值：v1 能发现 harness 回归；v2 应进一步发现 research behavior 质量回归。

### 7. 可选 Agent Runtime 编排

**目标:** 只在 harness 稳定后加入多 agent 工作流。

可能功能：

- 明确 search、verification、mapping、reading、eval 等角色。
- 每个角色有独立权限和输出 schema。
- 角色之间必须有 checkpointed human approval。
- Search 或 reading agent 不能直接写 formal records。

价值：多 agent 可以提速，但前提是 v1 guardrails 仍能强制执行。

## 我建议的 v2 顺序

1. PDF/screenshots asset management。
2. Batch candidate import 和 campaign review queue。
3. Scholarly API lookup 进入 staging。
4. Verification/approval 的本地 review UI。
5. Claim-level citation check。
6. 更强 evals。
7. 可选 multi-agent orchestration。

## v2 规划时需要决定的问题

- v2 继续 CLI-first + generated reports，还是较早引入 local Web UI？
- 第一个 citation source 选 DOI/Crossref、Zotero、BibTeX import 还是 OpenAlex？
- PDF 是否继续完全手动提供，还是支持用户授权 URL 的受控下载？
- Screenshot metadata 需要多详细，才不会变成负担？
- v2 是否引入 database，还是继续 Markdown/YAML + indexes？
