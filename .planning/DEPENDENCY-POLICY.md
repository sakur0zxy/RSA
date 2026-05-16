# RSA 全局依赖策略

**状态:** 全局设计原则  
**创建时间:** 2026-05-16  
**适用范围:** RSA 当前核心 agent 功能、后续 v2/v3 功能规划、README/安装说明、CLI 自检和 GSD phase planning。

## 设计目标

RSA 的普通用户基础版必须能实现当前 agent 的核心闭环，而不是只能运行一个弱化版 harness。用户安装基础版后，应能完成从文献记录、授权来源获取、PDF/来源管理、自动阅读草稿到人工确认门禁的主要流程。

## 核心原则

1. **基础版就是普通用户版。**
   - `python -m pip install -e .` 应安装当前核心功能所需的 Python 依赖。
   - 不把当前核心能力拆成用户必须手动猜测的 optional extras。

2. **核心功能依赖进入基础运行依赖。**
   - YAML/Markdown harness 所需依赖进入基础依赖。
   - Browser session provider 所需 Python 包属于授权获取核心能力，应进入基础依赖。
   - PDF 文本提取属于自动阅读草稿核心能力，应进入基础依赖。

3. **optional extras 只用于非核心增强。**
   - `.[dev]` 用于测试和开发。
   - 未来 `.[llm]`、`.[ui]`、`.[cloud]` 等可用于外部 LLM、本地 UI、云端服务等非基础闭环能力。
   - “全不选 extras”不能破坏当前核心 agent 闭环。

4. **外部资源用自检处理。**
   - 有些资源不能只靠 pip 完成，例如 Playwright Chromium、本地浏览器运行资源、未来模型文件或外部工具。
   - 这些资源应通过 `rsa doctor` 或命令级 preflight check 检查。
   - 缺失时必须中文说明缺什么、影响哪个功能、如何修复。

5. **用户可见安装文档必须解释依赖和功能关系。**
   - README/帮助文档需要提供中文功能依赖矩阵。
   - 矩阵应明确标注：当前核心功能已包含在基础安装中。
   - 非核心 extras、一次性环境初始化、开发依赖必须分开说明。

6. **缺依赖不得生成伪结果。**
   - 缺 PDF parser、浏览器运行资源或其他核心环境时，相关命令必须 fail closed。
   - 错误信息必须给出中文修复命令，不应只输出 Python traceback。

## 依赖分层 taxonomy

RSA 依赖必须固定分为四层，后续 `pyproject.toml`、README、`rsa doctor` 和命令级 preflight 都按这个 taxonomy 判断：

### A. Base runtime dependencies

基础运行依赖。普通用户基础安装必须包含，支撑当前核心 agent 闭环。缺失时属于 `BLOCKED`。

### B. Optional feature dependencies

非核心增强依赖。只用于未来外部 LLM、本地 UI、云端服务、特定高级 connector 等增强能力。缺失时不应破坏当前核心闭环，通常属于 `WARN`。

### C. Dev/Test dependencies

开发和测试依赖。只服务开发者、贡献者和本地验证，例如 `pytest`。普通用户不需要安装。

### D. External resources / system requirements

pip 不能可靠完成安装的外部资源，例如 Playwright Chromium、本地浏览器运行资源、未来本地模型文件或系统工具。它们必须由 `rsa doctor` 和命令级 preflight 检查，缺失时按受影响命令返回 `BLOCKED` 或 `WARN`。

## 核心闭环命令契约

当前基础版必须保证下列核心命令可启动、可做自身 preflight，并在缺输入或缺环境时给出中文可恢复错误：

| 功能/命令 | 是否核心 | Python 依赖层 | 外部资源 | 缺失时行为 |
|-----------|----------|---------------|----------|------------|
| `rsa init` | 是 | base runtime | 无 | `BLOCKED`，中文说明初始化失败原因 |
| `rsa validate-profile` | 是 | base runtime | 无 | `BLOCKED`，中文说明 profile/schema 问题 |
| `rsa new-round` | 是 | base runtime | 无 | `BLOCKED`，中文说明配置或输入问题 |
| `rsa round validate` / `rsa round trace` | 是 | base runtime | 无 | `BLOCKED`，中文说明 archive 或 trace 问题 |
| `rsa add-paper` / `rsa validate-metadata` | 是 | base runtime | 无 | `BLOCKED`，中文说明 metadata gate 问题 |
| `rsa source add` / `rsa source status` / `rsa source validate` | 是 | base runtime | 本地授权文件按需存在 | `BLOCKED`，不写伪 source ledger |
| `rsa source find` / `rsa source candidates` / `rsa source download` | 是 | base runtime | 网络或用户授权来源按命令需要 | `BLOCKED`，写入可审计失败/阻塞原因，不写伪 PDF |
| `rsa source login` / `rsa source session status` / `rsa source session clear` | 是 | base runtime | Playwright Chromium、本地 browser session | `BLOCKED`，中文提示运行浏览器资源安装或重新登录 |
| `rsa asset add` / `rsa asset validate` / `rsa asset status` | 是 | base runtime | 本地资产文件按需存在 | `BLOCKED`，不写伪 asset manifest |
| `rsa note create` / `rsa note validate` / `rsa note status` | 是 | base runtime | 本地、用户提供或已授权全文按需存在 | `BLOCKED`，记录 blocked/status，不生成假 note |
| `rsa note draft` | 是，Phase 8 落地 | base runtime | 授权 PDF、PDF parser、可提取文本 | `BLOCKED` 或 `partial`，不生成伪阅读结论 |
| `rsa map validate` / `rsa map propose` | 是 | base runtime | 无 | `BLOCKED`，不写正式 map |
| `rsa gap generate` / `rsa gap validate` | 是 | base runtime | 无 | `BLOCKED`，中文说明 map/profile 问题 |
| `rsa formal apply-map` / `rsa formal apply-note` | 是 | base runtime | 人工确认字段 | `BLOCKED`，缺确认或冲突时不写 formal records |
| `rsa eval run` / `rsa eval compare` | 是 | base runtime | 无 | `BLOCKED`，中文说明 eval/baseline 问题 |
| `rsa doctor` | 是，待实现 | base runtime | 检查所有核心外部资源 | 输出 `OK` / `WARN` / `BLOCKED` 和修复命令 |

## 功能-依赖矩阵

| 能力 | 是否核心 | Python 依赖 | 外部资源 | 文档/自检要求 |
|------|----------|-------------|----------|---------------|
| 本地 Markdown/YAML harness | 是 | `PyYAML` | 无 | README 标为基础安装内置 |
| Metadata / round / map / gap | 是 | base runtime | 无 | `rsa doctor` 检查命令入口可用 |
| Source ledger 和本地资产管理 | 是 | base runtime | 本地文件按需存在 | 缺文件中文阻塞，不生成伪记录 |
| Authorized acquisition | 是 | base runtime | 网络、授权 URL、本地文件按需存在 | 下载失败写可审计状态，不静默成功 |
| Browser session provider | 是 | base runtime 包含 Playwright Python 包 | Playwright Chromium、本地 session | `rsa doctor` 检查 Chromium；命令 preflight 阻塞缺资源 |
| PDF 文本提取 | 是，Phase 8 落地 | base runtime 包含 PDF parser | 授权 PDF | `rsa doctor` 检查 parser；解析失败不生成伪结论 |
| Auto reading draft | 是，Phase 8 落地 | base runtime | 授权 PDF、可提取文本 | 输出 `draft`，缺证据 fail closed |
| 外部 LLM 自动总结/评分 | 否，未来增强 | future `.[llm]` | API key 或本地模型 | 不得影响基础核心闭环 |
| 本地 Review UI | 否，未来增强 | future `.[ui]` | 浏览器/前端运行环境 | 不得影响 CLI 核心闭环 |
| 云端服务集成 | 否，未来增强 | future `.[cloud]` | 网络/API 凭据 | 只进入 staging，不绕过 formal gates |
| 开发测试 | 否，开发专用 | `.[dev]` | 无 | README 单独列出开发安装 |

## `rsa doctor` 契约

`rsa doctor` 是全局环境体检命令，负责告诉用户当前安装能否运行核心闭环，以及哪些资源缺失。

### 最小检查范围

- Python 版本是否满足项目要求。
- base runtime dependencies 是否可 import。
- 核心命令入口是否可加载。
- Playwright Python 包是否存在。
- Playwright Chromium 或等价浏览器运行资源是否存在。
- PDF parser 是否存在。
- 项目根目录、`rsa.yaml`、`.rsa/`、`01_literature/` 等关键路径是否可访问。
- optional feature dependencies 是否安装，以及缺失时影响哪些非核心增强功能。

### 状态语义

- `OK`: 功能可正常运行。
- `WARN`: 非核心增强或可延后资源不可用，但当前核心闭环不受影响。
- `BLOCKED`: 核心命令不可运行，必须先修复。

### 输出要求

每个检查项必须用中文说明：

- 检查对象。
- 当前状态：`OK`、`WARN` 或 `BLOCKED`。
- 影响的功能/命令。
- 修复命令或修复路径。

## Doctor 与 command preflight 的边界

- `rsa doctor` 做全局体检，可以一次性列出所有核心功能、外部资源和修复命令。
- command preflight 做命令级即时检查，只检查当前命令真正需要的依赖、输入、授权和外部资源。
- 两者应共享同一套 dependency check helper，避免同一缺失项在 doctor 和命令运行中给出不同结论。
- 用户没有运行 `rsa doctor` 时，具体命令仍必须在执行前做 preflight。

## Fail closed 定义

当缺依赖、缺外部资源、缺授权输入、缺必要解析结果、schema 无效或人工确认缺失时，RSA 必须 fail closed：

- 不生成伪输出。
- 不把失败伪装成空结果或成功结果。
- 不写入 formal records。
- 不覆盖用户已有人工记录。
- 只允许写入可审计的 blocked/failed/partial 状态记录。
- 返回明确中文错误，说明缺什么、影响哪个功能、如何修复。
- expected errors 不应表现为 traceback-only。

## `pyproject.toml` 分层映射草案

后续实现应收敛到以下方向：

- `dependencies`: 当前核心闭环所需 Python 包，例如 `PyYAML`、Playwright Python 包、PDF parser。
- `optional-dependencies.dev`: 测试和开发依赖，例如 `pytest`。
- `optional-dependencies.llm`: 未来外部 LLM 或本地模型增强。
- `optional-dependencies.ui`: 未来本地 review UI。
- `optional-dependencies.cloud`: 未来云端或远程服务集成。

兼容期可以保留旧的 `browser` extra 作为安装别名或迁移提示，但不能再把 browser session provider 的核心 Python 依赖只放在 `browser` extra 中。

## 测试要求

后续实现需要至少覆盖：

- 基础安装依赖声明包含当前核心 Python 包。
- 核心命令在 base runtime 下可启动并能做 preflight。
- 缺 Playwright Chromium 时，`rsa doctor` 和 `rsa source login` 给出一致中文修复提示。
- 缺 PDF parser 或 PDF 无法解析时，`rsa doctor` / `rsa note draft` fail closed，不生成伪 reading note。
- README 功能依赖矩阵与 `pyproject.toml` / doctor 检查项保持一致。

## 当前实现差距

Phase 8 已把 PDF parser (`pypdf`) 纳入基础依赖，并为 `rsa note draft` 增加本地文本提取、prompt packet 和 fail-closed 行为。剩余差距是 `playwright` 仍位于 `browser` optional extra，`rsa doctor` 尚未实现；后续需要继续让 README、pyproject 和自检命令收敛到本策略。

## 后续落地要求

- Phase 8 plan 应把 PDF parser 和依赖策略纳入计划。
- 需要新增或规划 `rsa doctor`，检查核心 Python 包、Playwright Chromium 等外部资源。
- README 安装章节应从“browser 是可选核心能力”改为“基础安装包含核心 Python 依赖；浏览器运行资源属于一次性环境初始化”。
- 测试需要覆盖缺依赖/缺外部资源时的中文错误提示和 fail-closed 行为。
