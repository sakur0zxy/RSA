# Pitfalls Research: RSA 科研 Agent

## Critical Pitfalls

| Pitfall | Warning Sign | Prevention Strategy | Phase |
|---|---|---|---|
| 未核验候选进入正式记录 | metadata 中出现来源不明、DOI 未查证的条目 | staging 与 formal writer 分离，正式写入必须有人审字段 | 2 |
| 文献元数据 hallucination | 作者、年份、venue 与官方页面不一致 | schema + source reliability + official URL/DOI 核验 | 2 |
| agent_outputs 膨胀成垃圾场 | 每轮保存大量原始日志和草稿 | 每轮最多保存少量关键 Markdown，必须有 final summary | 3 |
| 自动综述污染科研判断 | agent 直接生成“结论性综述段落” | v1 只生成阅读笔记、映射和待确认结论 | 4 |
| 未授权 PDF 行为 | agent 记录或使用非授权下载链接 | 只记录 pdf_status、official_url、local_pdf 和合法获取待办 | 2 |
| 多 agent 过早复杂化 | 职责不清、结果互相覆盖 | 先实现职责边界和 formal writer，再考虑 handoff | 1/3 |
| 评估缺失 | prompt 改动后行为漂移无人发现 | 固定 eval fixtures 覆盖格式、权限、冲突和可靠性 | 5 |
| SAR 主题与通用流程耦合过死 | 只能服务一个课题 | SAR 放在 topic profile，不写死在核心 harness | 1 |

## Failure Boundaries

- 如果没有官方来源或 DOI，仅能进入候选区，不能进入正式 metadata。
- 如果没有全文或合法访问，不能生成声称基于全文的阅读笔记。
- 如果用户要求自动写论文正文，系统应转为“提供结构化素材和引用证据”，不直接生成可提交正文。
- 如果一轮任务候选过多，应拆分 rounds，不在一次运行中混合太多主题。
- 如果 agent 判断与正式记录冲突，应记录冲突并请求人工处理。

## Security and Academic Integrity Notes

Safe harness 的核心是把风险控制嵌入 agent 生命周期：输入过滤、决策验证、工具权限和状态更新回滚。本项目的学术版本对应为：检索范围控制、写入前核验、正式记录权限分层、错误条目可回滚。

---
*Research note created: 2026-05-11*
