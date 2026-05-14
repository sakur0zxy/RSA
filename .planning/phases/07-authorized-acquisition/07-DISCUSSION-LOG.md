# Phase 7 Discussion Log

**Phase:** 07 Authorized Acquisition  
**Date:** 2026-05-14  
**Mode:** interactive `gsd-discuss-phase`, no subagents  
**Temporary WIP:** `.planning/phases/07-authorized-acquisition/07-DISCUSSION-WIP.md`

## 讨论方式

用户要求一个一个讨论，并要求后续所有 GSD 讨论都使用临时 WIP 文件记录：每讨论完一个小点就更新 WIP，全部讨论完成后再整理到正式总决策。

## 小点 1：来源发现范围

### 问题

Phase 7 应该允许自动发现哪些全文来源。

### 选项

- 保守可信来源。
- 只查结构化 OA 来源。
- 宽松发现来源。

### 决策

选择保守可信来源，同时支持用户自定义搜索源和数据库源。用户自定义 provider 必须使用固定 YAML 模板，建议放在 `.rsa/local.yaml`。

## 小点 2：检索依据与匹配规则

### 问题

下载时依据什么搜索，标题还是 DOI。

### 决策

优先 DOI，其次 `official_url`、arXiv ID，再使用 `title + year + first_author`。`title_only` 只能生成候选，不得单独触发自动下载。

## 小点 3：授权判定与下载边界

### 问题

授权判定应该多严格，学校账号或机构订阅资源是否支持。

### 决策

采用中等授权判定。支持 open access、direct access、学校账号/机构订阅、个人订阅和用户已授权访问来源。系统不保存密码、不模拟登录、不绕过 paywall。非 OA 或授权待确认来源可以进入自动阅读草稿，但不能自动进入正式科研记录。

### Sci-Hub 边界

用户提出加入 Sci-Hub 支持。结论是不内置、不推荐、不自动化 Sci-Hub 或任何未授权镜像源。用户自定义 provider 也不得用于绕过 paywall 或破解访问控制。

## 小点 4：find / download 工作流

### 问题

自动发现和下载是否拆成两个命令，以及默认是否自动下载。

### 决策

`find` 和 `download` 保持为两个概念，但默认采用 `monitored_auto`。`rsa source find P001` 默认自动搜索、自动审查并自动下载通过规则的来源。保留 `--no-download`、`source candidates`、`source download --best`、`source download --candidate` 和直接 URL 下载能力。

## 小点 5：下载文件命名与重复处理

### 问题

PDF 保存路径、主版本选择、重复下载、失败和半截文件如何处理。

### 决策

- 每篇论文一个目录，按 `source_id` 命名：`01_literature/pdfs/P###/S###_<provider_id>_<version_label>.pdf`。
- 自动选择主版本，但保留全部版本。
- 按 `sha256` hash 去重，重复内容不新增文件，但记录 `duplicate_of`。
- 下载先写 `.tmp` 临时文件，校验通过后原子落盘；失败删除临时文件并记录中文原因。

## 整理结果

正式上下文已整理到 `.planning/phases/07-authorized-acquisition/07-CONTEXT.md`。后续 `gsd-plan-phase 7` 应以 `07-CONTEXT.md` 为主要输入，并可参考 `07-DISCUSSION-WIP.md` 查看逐点讨论细节。
