# Phase 16 Discussion WIP

本文件临时记录 Phase 16 讨论决策。完成后，正式决策以 `16-CONTEXT.md` 为准。

## 已完成小点

1. **Phase 定位**
   - 决策：Phase 16 是前置发现层，负责把科研计划转成检索式和候选文献 campaign。
   - 边界：不直接创建 `metadata/P###.yaml`，不写 `paper_index.md`，不绕过 formal write gate。

2. **输入范围**
   - 决策：v1 支持 Markdown/text 科研计划文件、纯文本目标和已有 topic profile。
   - 预留：`docx`、Zotero、BibTeX、Web UI 导入接口后续扩展。

3. **检索策略**
   - 决策：自动生成 query bundle，每条 query 保留中文理由、英文检索词、来源、置信度和 inclusion/exclusion hints。
   - 边界：query generation 可以使用规则和可选 LLM，但失败时必须 fail closed，不生成伪候选。

4. **搜索来源**
   - 决策：默认只接入开放/可审计 scholarly source provider 或用户自定义 provider。
   - 边界：不使用未授权镜像，不绕过 paywall，不把 publisher 页面当成已授权 PDF。

5. **输出与接入**
   - 决策：发现结果进入 `01_literature/discovery/` 和现有 `01_literature/campaigns/`。
   - 复用：Phase 8.2 campaign import、Phase 11 metadata intake、Phase 7 source rules、Phase 10/11 workflow。

6. **自动化与人工监管**
   - 决策：系统默认自动提取计划、生成检索式、搜索候选、导入 campaign、做初筛。
   - 人工点：用户主要监管候选队列、低置信项、重复项、formal metadata 写入请求。

7. **预留接口**
   - 决策：保留 iterative query refinement、provider plugin、LLM query generation、discovery eval、Web UI review hooks。
   - 边界：当前 phase 不做完整 scholarly metadata 平台，不做复杂知识图谱，不做 multi-agent orchestration。

