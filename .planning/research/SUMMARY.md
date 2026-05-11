# Research Summary: RSA 科研 Agent

## Stack

v1 采用本地优先的 Python CLI + Markdown/YAML + git harness。这个选择比 Web/数据库平台更适合当前阶段，因为科研记录需要可审阅、可 diff、可回滚，并且能快速形成真实工作流闭环。

## Table Stakes

- Topic profile 驱动。
- metadata-first 正式记录。
- 候选文献 staging 与正式记录分离。
- 元数据核验和来源可靠性标注。
- PDF 状态管理，不做未授权下载。
- 文献地图、研究表、阅读笔记和 agent_research_notes。
- 人审写入门槛。
- 固定 eval fixtures。

## Watch Out For

- 不要把 agent_outputs 当事实源。
- 不要让未核验候选自动写入 metadata。
- 不要把 SAR topic 写死进通用 harness。
- 不要过早建设复杂 multi-agent 平台。
- 不要让“阅读笔记”变成未经核验的综述正文。

## Architecture

推荐组件：Topic Profile、Round Runner、Search Candidates、Verification Review、Map Integration、PDF Status、Paper Reading、Formal Record Writer、Eval Harness。正式写入集中由 Formal Record Writer 控制，所有 agent 角色默认只产出候选和待审材料。

## Requirements Implications

v1 的需求应围绕可靠科研记录闭环，而不是围绕“模型能力展示”。验收标准应能回答：

- 是否能区分候选、待审和正式记录？
- 是否能追溯每条正式记录的来源和确认状态？
- 是否能阻止未授权 PDF 和未核验结论？
- 是否能用 eval fixtures 检查 prompt/模板/规则改动后的行为？
- 是否能用 SAR 非连续孔径 topic profile 跑通一轮小样本调研？

---
*Research synthesized: 2026-05-11*
