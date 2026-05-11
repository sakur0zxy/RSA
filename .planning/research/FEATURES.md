# Feature Research: RSA 科研 Agent

## Table Stakes

| Feature | Why It Matters | Complexity |
|---|---|---|
| Topic profiles | 让同一 harness 支持不同研究主题 | Low |
| Candidate search staging | 候选文献不能直接进入正式记录 | Medium |
| Metadata verification | DOI、题名、作者、年份、venue、official URL 必须可核验 | Medium |
| Source reliability flags | 区分官方页面、arXiv、数据库页面、二手网页和不可靠来源 | Low |
| PDF status tracking | 管理是否已获取、是否合法、本地路径和待办 | Low |
| Literature map | 把文献映射到主题、研究问题、章节和论文产出 | Medium |
| Single-paper reading notes | 支持稳定的精读记录模板 | Medium |
| Human approval gate | 未确认候选和推断不能写入正式记录 | Medium |
| Agent output archive | 记录每轮任务结论和关键中间产物 | Low |
| Local eval fixtures | 每次修改 prompt/模板/规则后可重复检查 | Medium |

## Differentiators

| Feature | Value | Defer? |
|---|---|---|
| Conflict-aware formal write | 写入正式记录前检查 metadata、paper_index、notes 冲突 | v1 |
| Claim-level source anchoring | 阅读笔记中的关键结论必须有页码、段落或来源提示 | v1 |
| Research gap map | 自动提示当前 topic profile 下的证据缺口 | v1/v2 |
| SAR-specific starter profile | 用非连续孔径 SAR 作为第一套真实试验主题 | v1 |
| Trace grading dashboard | 用 UI 检查多轮行为退化 | v2 |
| Citation manager sync | 和 Zotero/EndNote 同步 | v2 |

## Anti-Features

| Anti-Feature | Reason |
|---|---|
| 自动写综述正文 | 学术责任高，容易把未核验信息写成结论 |
| 未授权 PDF 下载 | 版权和合规风险 |
| 全自动正式入库 | 会污染元数据和后续研究判断 |
| 大批量一键处理 | 错误难以追踪，人工确认负担过大 |
| 黑箱多 agent 编排 | 在 harness 未稳定前会增加不可控性 |

## v1 Feature Shape

v1 应更像一个“科研记录流水线 + agent harness”，而不是聊天机器人。用户给出 topic profile 或研究问题，系统创建一轮 bounded research round，agent 只在本轮范围内搜索、核验、映射、记录候选和生成待审输出。正式记录写入必须经过 schema、冲突检查和人工确认。

---
*Research note created: 2026-05-11*
