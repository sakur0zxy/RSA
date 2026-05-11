# Stack Research: RSA 科研 Agent

## Recommendation

v1 推荐采用本地优先的 Python + Markdown/YAML + CLI harness，而不是直接建设 Web 平台或复杂数据库。

## Stack

| Layer | v1 Choice | Rationale | Confidence |
|---|---|---|---|
| Runtime | Python CLI | 科研脚本、YAML、PDF/文本处理和评估脚本生态成熟 | High |
| Storage | Markdown + YAML in git | 可审阅、可 diff、可回滚，符合科研记录透明性 | High |
| Config | `topic_profiles/*.yaml` | 不同研究主题复用同一 workflow | High |
| Records | `metadata/`, `paper_index.md`, `literature_map.md`, `notes/` | metadata-first，正式记录和辅助输出分离 | High |
| Agent outputs | `agent_outputs/Rxxx_*` | 每轮轻量归档，保留 final summary 和关键中间结果 | High |
| Guardrails | Schema validation + write gates + human confirmation flags | 防止未核验内容进入正式记录 | High |
| Evals | Fixture-based local evals | 用固定案例测 hallucination、格式漂移、权限违规和冲突处理 | High |
| Observability | Per-round manifest + trace summary | 记录工具、输入、输出、拒绝原因和人工确认 | Medium |
| Optional SDK | OpenAI Agents SDK or equivalent later | 当需要状态、handoff、tool guardrails 和 traces 时再接入 | Medium |

## Harness Implications

Harness 的重点不是“让模型更会说”，而是约束模型如何看见任务、调用工具、记录状态、申请写入正式记录和接受评估。OpenAI Agents SDK 文档把 code-first agent app 的重点放在 orchestration、tool execution、state 和 approvals 上；这与本项目的本地 harness 方向一致。

## Non-Goals for v1

- 不引入复杂数据库。
- 不做自动 PDF 下载器。
- 不做 Web UI。
- 不做通用 multi-agent 平台。
- 不把模型 trace 全量永久保存为正式科研记录。

## Source Notes

- OpenAI Agents SDK emphasizes code-owned orchestration, tools, state and approvals: https://developers.openai.com/api/docs/guides/agents
- OpenAI guardrails distinguish input, output and tool guardrails, useful for tool-level write control: https://openai.github.io/openai-agents-python/guardrails/
- OpenAI trace grading and agent eval docs support trace-based debugging before repeatable eval datasets: https://developers.openai.com/api/docs/guides/trace-grading and https://developers.openai.com/api/docs/guides/agent-evals
- Recent harness-engineering papers frame harnesses as tool/context/state/observability systems, but they are emerging research rather than settled standards: https://arxiv.org/abs/2604.25850 and https://arxiv.org/abs/2604.13630

---
*Research note created: 2026-05-11*
