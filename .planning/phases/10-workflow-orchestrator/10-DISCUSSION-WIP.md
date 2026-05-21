# Phase 10 Workflow Orchestrator - Discussion WIP

**Started:** 2026-05-21  
**Status:** discussing  
**Source:** `$gsd-discuss-phase` inline discussion, no subagents

## Phase Boundary

Phase 10 负责把已经实现的 v1/v2 命令串联成一个可监控、可恢复、可调整的自动工作流。它默认自动运行到 review packet 或需要人工监管的位置，但不得绕过 formal write gate。

Phase 10 不负责完整 batch review UI，不负责 Local Review Workspace，不负责 claim-level citation hardening，也不直接执行 formal writes。

## Carry-Forward Decisions

- 用户可见内容中文优先；英文 key、flag、status enum 和代码标识保持稳定。
- AI 产物默认进入 staging / review packet，不直接进入 formal records。
- `formal write gate` 不得被 orchestrator、batch、UI 或后续 agent 编排绕过。
- Phase 7 acquisition、Phase 8 reading draft、Phase 8.1 visual extraction、Phase 9 scoring 已有可调用 CLI。
- Phase 8.2 campaign foundation 已有队列基础，但完整 Campaign & Batch Review 仍属于 Phase 11。
- 用户希望系统自动化程度高：AI/自动流程可以自行推进普通步骤，用户主要监管关键环节、异常项和 formal approval。

## Candidate Gray Areas

1. **Workflow entry point and default unit**  
   决定 Phase 10 的最小运行对象是单篇 `P###`、campaign item，还是两者都支持但以单篇为核心。

2. **Automatic chain and stop gates**  
   决定 workflow 默认串联哪些步骤、什么情况下继续、什么情况下停止到 review。

3. **Run state and resume model**  
   决定 workflow run 的状态文件、step 记录、artifact link、resume/rerun/rollback 语义。

4. **Monitoring and user controls**  
   决定用户如何查看进度、调整步骤、禁用某些阶段、处理 blocked/partial/needs_review。

5. **Project-wide parallelism placement**  
   已安排到整体项目：Phase 10 做单篇顺序 workflow primitive，Phase 11 做 campaign 级受控并行。该分工已同步到 `.planning/PROJECT.md`、`.planning/ROADMAP.md` 和 `.planning/REQUIREMENTS.md`。

## Clarifications

### Campaign Role In Phase 10

- 在 Phase 10 中，`campaign_id` 的作用是“上下文和来源标记”，不是批量调度入口。
- Phase 10 可以读取 campaign item 中的 `topic_profile`、`priority_question`、候选来源、导入批次和用户目标，用来影响单篇 workflow 的 scoring/review packet 上下文。
- Phase 10 的主运行单位仍是单篇 `paper_id`，例如 `rsa workflow run P001 --campaign-id C001`。
- Phase 10 不负责遍历整个 `C001`、不做多篇并发、不做 campaign 排序、不做批量异常聚合；这些属于 Phase 11。
- Phase 10 的 run state 应记录 `campaign_id` 和 `campaign_item_id`，让 Phase 11 后续可以把单篇运行结果汇总回 campaign review queue。

## Decisions Captured

### Area 1: Automatic Chain And Stop Gates

- **Selected first:** 自动链路与停止点。
- **Reason:** Phase 10 的核心价值是自动把已有 v1/v2 命令串起来，并在需要人工监管的位置停住；先锁定默认链路可以约束后续入口、状态恢复和监控设计。
- **Accepted recommendation:** 采用“单篇内部顺序链 + campaign 级受控并行留给 Phase 11”的边界。
- **Phase 10 decision:** 单篇论文内部按依赖顺序推进：acquisition -> reading draft -> visual extraction -> scoring -> review packet。默认自动跑到 review packet 或需要人工监管的位置。
- **Phase 10 boundary:** Phase 10 不实现多篇 worker queue、不做阶段并发限流、不做 campaign 排序运营；但 run state 和 step schema 要为 Phase 11 的受控并行调度保留字段，例如 `run_id`、`paper_id`、`campaign_id`、`step_id`、`step_status`、`artifacts`、`blocked_reason_zh`、`retry_policy`。
- **Phase 11 handoff:** 多篇论文之间可流水线式小并行；每篇内部仍顺序推进。并发控制建议由 Phase 11 处理，例如 acquisition 2-3、reading draft 2、visual extraction 1-2、scoring 2-3。
- **Stop gate decision:** formal write 一律不并行自动推进；遇到 formal request、授权错误、text/visual conflict、低置信度关键项、blocked/partial 状态时，Phase 10 停到 review packet 或 status report。
- **Re-evaluation:** 重新判断后仍确认该分工。Phase 10 的核心是把单篇链路变成可靠、可恢复、可监控的 workflow primitive；Phase 11 才适合在这些 primitive 之上做 campaign 级队列、并发、排序和批量异常聚合。这样既保留自动化扩展空间，又避免 Phase 10 同时承担 orchestrator 和 batch scheduler 两个职责。
- **Project-level placement:** 该想法不作为新 phase，不放 deferred；它成为 v2 的全局自动化调度原则，并分别落到 Phase 10 requirements 和 Phase 11 campaign requirements。
- **Partial handling:** 默认选择“可用 partial 继续跑到 review packet”。当来源、schema 和核心上游产物仍可用时，Phase 10 不因普通 `partial` 立刻停止；它应继续后续步骤，并在 run state、step report 和 review packet 中显式记录 `partial_reason_zh`、`evidence_level`、受影响步骤、后续人工监管建议。`partial` 不能被当作正常成功，也不能绕过 formal write gate。
- **Blocked handling:** 默认选择“blocked 立刻停止当前论文链路”。当出现无授权全文、PDF 不可读、metadata 不存在、schema 破坏、LLM 输出无效或其它无法可信继续的问题时，Phase 10 必须 fail closed：停止当前 `paper_id` 的 workflow，写入 run state、step report、中文失败原因和修复建议，不生成正常完成态 review packet。后续 Phase 11 可以继续处理其它论文，但不能把该 blocked 项当作成功项。
- **Needs-review handling:** 默认选择“继续跑到 review packet，然后停给用户监管”。当出现低置信度视觉证据、text/visual conflict、评分不稳定、来源疑点或其它需要人工判断的问题时，Phase 10 应继续聚合可用材料，并在最终 review packet、run state 和 status 输出中突出 `needs_review`，列出原因、证据链接和建议动作；不得自动降级为 defer，也不得视为 formal approval。
- **Visual extraction clarification:** 之前 Phase 8.1 已实现的是保守的视觉证据候选提取：裁图/裁表候选、caption/region text、基础 OCR-like 文本、page/region/source trace、`visual_context_packet` 和 `llm_visual_analysis: not_run` 占位。它没有实现高级图表智能，也没有真实调用 LLM 进行图像理解；`curve_extraction`、`table_structure`、`multimodal_interpretation` 均默认 `not_run`。因此 Phase 10 默认运行 `visual extraction` 时，只表示运行现有保守视觉候选提取，不表示默认执行 LLM 图像理解或高级图表分析。
- **Advanced figure intelligence interface:** 保留高级图表智能接口，但 Phase 10 不执行该能力。Workflow run state、step artifacts 和 review packet link schema 应能引用未来的 `llm_visual_analysis`、`advanced_analysis.curve_extraction`、`advanced_analysis.table_structure`、`advanced_analysis.multimodal_interpretation` 结果；当前默认值保持 `not_run`，并用中文说明“接口已保留，功能未执行”。后续如新增高级图表智能 phase，不需要破坏 Phase 10 run schema。
- **Visual step default:** 默认选择运行保守 visual extraction，即 Phase 10 默认调用现有 `rsa visual extract P###`；但 `llm_visual_analysis` 和高级图表智能字段保持 `not_run`。这让 scoring/review packet 获得图表/表格候选证据，同时不扩大 Phase 10 scope。

### Area 2: Workflow Entry Point And Default Unit

- **Entry point decision:** 默认选择“以单篇 `P###` 为核心入口，campaign 只作为可选上下文”。
- **CLI shape:** 主命令应类似 `rsa workflow run P001`；可选支持 `--campaign-id C001` 和 `--campaign-item-id CI001` 记录来源上下文。
- **Campaign boundary:** Phase 10 不接受 `rsa workflow run C001` 作为批量调度入口；campaign 级遍历、并行、排序和异常聚合属于 Phase 11。
- **Context usage:** 当提供 campaign 上下文时，Phase 10 可读取 `topic_profile`、`priority_question`、campaign objective、导入来源和 dedup/linking 信息，用于 scoring/review packet 和 run state。

### Area 3: Run State And Resume Model

- **Run state location:** 默认选择每篇论文单独一个 workflow run 文件，例如 `01_literature/workflows/P001/RUN-001.yaml`。
- **Reason:** 单篇独立 run state 更适合 Phase 10 的 single-paper workflow primitive，也便于 Phase 11 后续按 campaign 汇总多个 `P###` 的运行结果。
- **Rejected alternatives:** 不采用全局 `runs.yaml`，避免写入冲突和并发恢复混乱；不只写 review packet，因为缺少独立 run state 会削弱 resume/rerun/status 能力。
- **Step ledger detail:** 默认保存完整 step ledger。每个 step 至少记录 `step_id`、`command`、`status`、`started_at`、`finished_at`、输入摘要、输出 artifact 链接、`error_zh`、`repair_hint_zh`、`retryable` 和 `needs_user_action`。
- **Log boundary:** 主 run YAML 不保存完整 stdout/stderr，避免日志噪声、敏感信息和版权内容进入可跟踪记录；只保存必要中文摘要和 artifact path。
- **Resume default:** `rsa workflow resume P###` 默认从最后一个未完成、失败或可重试 step 恢复；已完成且 artifact 校验有效的 step 不重跑。
- **Manual resume override:** 保留 `--from-step <step_id>` 给高级用户手动指定恢复点，但必须在中文提示中说明可能重用或覆盖哪些 artifact。
- **Artifact reuse validation:** resume 时对已完成 step 做轻量 artifact 校验：检查 artifact 文件存在、schema 有效、`paper_id`/`run_id` 或相关来源匹配、状态允许复用。校验通过则跳过该 step；校验失败则从该 step 重跑或停到 repair，不能只相信 run state 中的 `completed`。

### Area 4: Monitoring And User Controls

- **Command surface decision:** 默认选择完整控制命令集：`run`、`resume`、`status`、`report`、`stop`、`rerun`。
- **Required CLI shape:**
  - `rsa workflow run P001`
  - `rsa workflow resume P001`
  - `rsa workflow status P001`
  - `rsa workflow report P001`
  - `rsa workflow stop P001`
  - `rsa workflow rerun P001 --from-step visual_extraction`
- **Stop semantics:** `stop` 标记当前 workflow run 为用户暂停或停止，并写入中文原因；如果当前实现是同步 CLI，`stop` 至少要能阻止后续 `resume` 自动继续，后台/异步 worker 的实时中断可留给后续增强。
- **Rerun semantics:** `rerun` 用于明确重跑一个 step 或从某 step 重新执行，并必须提示会复用、覆盖或重新生成哪些 artifacts。`resume --from-step` 偏向断点恢复，`rerun --from-step` 偏向用户主动重算。
- **User control principle:** 用户必须能通过 status/report 监控关键环节，通过 stop/rerun/resume 调整流程；但这些控制命令仍不得绕过 formal write gate。
- **Step toggles:** 允许通过本地配置和命令 flag 跳过 workflow step。默认配置可保存在 `.rsa/local.yaml` 或项目配置中，命令行 flag 优先级更高。典型用途包括跳过 acquisition 使用已有 PDF、跳过 visual extraction 加快流程、只重跑 scoring/report。所有跳过行为必须写入 run state 和 report，说明 `skipped_reason_zh`，不能让缺失步骤看起来像成功完成。

## Deferred Ideas

- Campaign 级受控并行、阶段 worker queue、campaign ranking/filtering 和总体 review queue 放入 Phase 11。
- 高级图表智能的真实执行仍延后：包括 LLM 图像理解、曲线/坐标轴/图例/数值提取、高级表格结构理解、图表证据与 claim 绑定、以及多模态图像结论生成。
