# 自动运行与可监控性专项审计

**日期:** 2026-05-14  
**触发原因:** 检查已计划和已实现功能是否符合核心产品原则：系统应能在用户不干预的情况下自动进行，用户可以监控重要环节并进行调整。  
**使用的 GSD 流程:** `gsd-audit-uat` 思路；同时参考 `gsd-validate-phase` 和 `gsd-verify-work` 的适用边界。

## GSD skill 结论

- `gsd-audit-uat`：适合做跨 phase 的 UAT/verification 待办审计。本次运行 `gsd-sdk query audit-uat --raw`，结果为 `total_items: 0`，说明当前没有现成 UAT 待办项可直接复用。
- `gsd-validate-phase`：适合对已经执行完成的 phase 补自动化验证。Phase 7 尚未执行，不适合作为主检查入口。
- `gsd-verify-work`：适合实现后从用户视角逐条验收。Phase 7 实现完成后应使用它生成 UAT。

## 审计范围

- 已完成实现：Phase 1-6 的 CLI、metadata、round、note、map/gap、source/asset、eval 功能。
- 已完成计划：Phase 7 `07-CONTEXT.md` 和 `07-DISCUSSION-WIP.md`。
- 约束原则：中文用户优先；字段名、CLI flag、YAML key 保持英文稳定但必须有中文解释。

## 总体结论

**结论:** 当前计划方向符合该核心原则；已实现代码提供了部分基础，但 Phase 7 的“默认自动 acquisition”能力尚未实现，属于下一步必须覆盖的核心验收项。

| 检查项 | 结论 | 证据 |
|---|---|---|
| 默认自动运行 | Phase 7 计划已覆盖，代码尚未实现 | `07-CONTEXT.md` 定义 `monitored_auto` 与 `default_auto_download: true` |
| 用户监控 | 部分已实现，Phase 7 计划补强 | 已有 `source status` / `asset status`；Phase 7 要新增 `source candidates`、acquisition report |
| 用户调整 | 计划已覆盖，代码待实现 | `.rsa/local.yaml` 已支持本地配置合并；Phase 7 需要新增 provider schema 和 `--no-download` |
| 自动过程可审计 | 基础已实现，下载链路待实现 | Phase 6 source ledger 已记录来源；Phase 7 需要记录候选、匹配证据、授权模式、失败/重复原因 |
| 不污染正式记录 | 已实现并应继续保持 | formal writes 仍需 human confirmation；自动下载/阅读不得直接写 formal records |
| 中文用户优先 | 已形成项目原则，后续需继续测试覆盖 | `LANG-04` 要求后续 phase 在计划和测试中覆盖中文可见内容 |

## 已符合的部分

### 现有代码基础

- `ProjectConfig` 已合并 `rsa.yaml` 与 `.rsa/local.yaml`，适合承载本地 provider 配置。
- Phase 6 已实现 `rsa source add|validate|status` 与 `rsa asset add|validate|status`。
- `source add` 要求 `--license-note`，记录 `authorization`、`source_url`、`local_path`、`status`、`added_at`。
- `validate/status` 是只读命令，适合作为监控入口。
- PDF 和二进制资产 local-only，manifest/source YAML 可审计。
- formal writes 仍受 `--human-confirmed` 与 `--confirmed-by` 保护。

### Phase 7 计划

Phase 7 context 已明确：

- `rsa source find P001` 默认自动搜索、自动审查、自动下载。
- 默认配置为 `automation_mode: monitored_auto` 和 `default_auto_download: true`。
- 保留 `--no-download`、候选查看、手动 download、provider 配置作为监控和调整入口。
- 每个候选必须记录匹配证据、授权/访问模式、中文原因。
- 下载使用 `.tmp` 临时文件、hash 去重、失败状态记录，避免残缺 PDF 污染后续自动阅读。

## 发现的缺口

### A1. Requirements 原先没有显式写入“默认自动运行”

原本 Phase 7 只有 `V2-DL-01` 和 `V2-DL-02`，能覆盖发现和授权记录，但不足以防止 planner 把 Phase 7 做成“手动 find + 手动 download”的工具。

**处理:** 已新增：

- `V2-DL-03`：`source find` 默认 monitored automation。
- `V2-DL-04`：用户可以通过候选、状态、报告、provider 配置、`--no-download` 和手动命令监控/调整。
- `V2-DL-05`：自动 acquisition 的每个结果都必须可审计。

### A2. 当前代码还没有实现 Phase 7 自动链路

当前 `source` 命令只有 `add|validate|status`，还没有：

- `source find`
- `source candidates`
- `source download`
- `source_candidates_root`
- provider schema validation
- 默认自动下载
- hash 去重
- `.tmp` 原子落盘
- acquisition report 的结构化下载结果

这是预期状态，因为 Phase 7 还没进入 plan/execute，但必须作为下一阶段核心任务。

### A3. 旧功能偏手动，不应误判为不合格

Phase 1-6 的目标是建立 metadata、formal gate、round archive、reading note、map/gap、source/asset 基础；它们本来不负责无人干预自动下载。旧功能符合当时目标，但不等于已经满足 v2 自动化目标。

## Phase 7 plan 必须覆盖的验收点

- `rsa source find P001` 默认执行 search -> review -> download -> record。
- `rsa source find P001 --no-download` 只生成/更新 candidates，不下载。
- `rsa source candidates P001` 能展示候选、审查结果、失败原因和下载状态。
- `rsa source download P001 --candidate SC001` 和 `--url ...` 支持人工调整路径。
- 自定义 provider 从 `.rsa/local.yaml` 读取，并校验必填字段和中文说明。
- 下载结果写入 `source_candidates/P###.yaml`、`sources/P###.yaml`、`pdf_acquisition_report.md`。
- 下载失败、blocked、duplicate、partial_failed 都有中文原因。
- 重复 PDF 按 `sha256` 去重，不覆盖已有文件。
- 临时文件失败后删除，不保留残缺 PDF。
- 所有用户可见输出中文优先，英文 key/flag 保持稳定并有中文解释。

## 建议

Phase 7 可以继续进入 `gsd-plan-phase 7`，但计划必须把 `V2-DL-03`、`V2-DL-04`、`V2-DL-05` 当作一等验收目标。实现后再运行：

```powershell
python -m pytest -q
python -m rsa_cli.cli --root . eval compare
gsd-sdk query audit-uat --raw
```

并使用 `gsd-verify-work 7` 生成用户视角 UAT。
