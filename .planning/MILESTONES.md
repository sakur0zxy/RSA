# 里程碑记录

## v1.0 Local Harness

**状态:** 已发布
**发布时间:** 2026-05-13
**分支:** `v1phase3`
**Tag:** `v1.0`  
**Phases:** 5  
**Plans:** 14  
**归档前 commits:** 49
**时间线:** 2026-05-11 到 2026-05-13
**Open artifact audit:** 当前本地 GSD 安装不支持 `gsd-sdk query audit-open`；文件扫描未发现 open audit artifacts。

### 交付内容

v1.0 交付了一个本地优先的科研 agent harness，用于可审计文献工作流：formal metadata gates、bounded research rounds、candidate staging、literature maps、reading notes、formal write guardrails、trace summaries 和 deterministic eval fixtures。

### 关键成果

1. 创建可复用的项目骨架、topic profile 系统和 CLI 入口。
2. 建立 metadata-first 文献记录和 `paper_index.md` 一致性检查。
3. 增加 candidate verification staging，防止候选内容直接进入正式记录。
4. 将 research rounds 连接到 literature maps、gap reports 和 formal write requests。
5. 增加 authorized reading notes 和 formal note-derived write gates。
6. 增加 local eval fixtures、baselines 和 trace summaries，用于 harness hardening。

### 归档文件

- Roadmap 归档: `.planning/milestones/v1.0-ROADMAP.md`
- Requirements 归档: `.planning/milestones/v1.0-REQUIREMENTS.md`
- 复盘: `.planning/RETROSPECTIVE.md`
- v2 讨论稿: `.planning/v2-DISCUSSION.md`

### 归档时接受的已知缺口

- 归档前没有生成独立 milestone audit 文件。
- v1 evals 是 deterministic harness checks，不是 semantic LLM grading。
- v1 不包含 Web UI、scholarly API integration、citation manager sync 或 large-scale batch processing。
