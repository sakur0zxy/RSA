# Phase 7: Authorized Acquisition - Context

**Gathered:** 2026-05-14  
**Status:** Ready for planning  
**Mode:** `gsd-discuss-phase` inline, no subagents, user-guided decisions

<domain>

## Phase Boundary

Phase 7 在 Phase 6 的 source ledger、PDF local-only、asset manifest 基础上，实现受控的全文来源发现与下载。

本阶段负责：

- 根据正式 `metadata/P###.yaml` 自动发现可下载全文来源。
- 支持 open access、direct access、用户已授权访问、学校账号/机构订阅、个人订阅、本地/用户提供来源。
- 支持用户配置自定义搜索源和数据库源。
- 默认自动搜索、自动审查、自动下载通过规则的来源。
- 写入 `source_candidates`、`sources/P###.yaml`、本地 PDF 路径和 `pdf_acquisition_report.md`。

本阶段不负责：

- 自动阅读全文总结或阅读笔记，这属于 Phase 8。
- AI 质量评分、相关性评分或阅读优先级评分，这属于 Phase 9。
- Review UI、批量 campaign 或 citation check。
- 绕过 paywall、破解访问控制、保存账号密码、模拟验证码/SSO 登录。
- 内置或自动化 Sci-Hub、盗版镜像、未授权全文镜像。

</domain>

<decisions>

## Implementation Decisions

### 来源发现范围

- **D-01:** 默认发现范围采用保守可信来源，包括 DOI 关联全文、`official_url`、arXiv/预印本、OpenAlex/Unpaywall 类 OA metadata、机构库、作者主页和实验室论文页面中可明确识别的 PDF。
- **D-02:** 支持用户自定义搜索源、数据库源、学校数据库入口、机构库或实验室 publication 页面。
- **D-03:** 用户自定义 provider 必须使用固定 YAML 模板，建议放在本地 `.rsa/local.yaml`，避免把私人数据库入口或学校资源路径提交到 git。
- **D-04:** 自定义 provider 只扩展发现能力，不降低匹配审查、授权记录和下载边界要求。

### 自定义 provider schema

- **D-05:** `source_discovery.custom_providers` 每项至少包含 `provider_id`、`enabled`、`name_zh`、`provider_type`、`base_url`、`query_mode`、`query_template`、`allowed_domains`、`allowed_result_types`、`access_mode`、`requires_login`、`user_access_confirmed`、`authorization_policy`、`usage_restriction_zh`、`notes_zh`。
- **D-06:** v1 实现优先支持 `query_mode: url_template`，占位符包括 `{doi}`、`{title}`、`{year}`、`{first_author}`、`{paper_id}`。
- **D-07:** 用户可配置 `access_mode: institutional_subscription` 或 `personal_subscription`，但系统不得保存密码或自动处理登录流程。

示例：

```yaml
source_discovery:
  custom_providers:
    - provider_id: university_library
      enabled: true
      name_zh: "学校图书馆数据库"
      provider_type: database_search
      base_url: "https://library.example.edu"
      query_mode: url_template
      query_template: "https://library.example.edu/search?q={title}"
      allowed_domains:
        - "library.example.edu"
      allowed_result_types:
        - database_record
        - publisher_page
        - pdf
      access_mode: institutional_subscription
      requires_login: true
      user_access_confirmed: true
      authorization_policy: user_authorized_access
      usage_restriction_zh: "仅供个人科研阅读，不得公开分发 PDF。"
      max_results: 5
      timeout_seconds: 20
      rate_limit_seconds: 3
      notes_zh: "用户通过学校账号或机构订阅访问；RSA 不保存账号密码，不模拟登录，只使用用户已授权访问后的结果。"
```

### 检索依据与匹配规则

- **D-08:** 下载不是单纯按标题搜索。检索优先级固定为 `doi`、`official_url`、`arxiv_id`、`title_year_first_author`、`title_only`。
- **D-09:** `title_only` 只能生成候选，不得单独触发自动下载。
- **D-10:** 每个候选来源必须记录匹配证据，例如 `doi_match`、`title_match_score`、`year_match`、`author_match`、`source_domain_allowed`。
- **D-11:** 允许自动下载的典型情况包括 DOI 命中、arXiv ID 命中、`official_url` 明确给出 PDF、`title + year + first_author` 匹配且来源属于内置或用户配置 provider。

### 授权判定与下载边界

- **D-12:** 采用中等授权判定。允许下载直接可访问 PDF，也支持用户已授权访问的学校账号、机构订阅、个人订阅资源。
- **D-13:** “可访问”不等同于“正式授权结论”。下载后必须记录 `authorization_mode`、`access_mode`、`authorization_basis_zh`、`usage_restriction_zh` 或 `license_note`。
- **D-14:** 支持的授权/访问模式包括 `open_access`、`direct_access`、`user_authorized_access`、`institutional_subscription`、`personal_subscription`、`provided`、`local`、`unknown`、`blocked`。
- **D-15:** 对学校账号、机构订阅、个人订阅等来源，系统可以使用用户已授权访问后的下载链接、本地文件或自定义 provider 入口，但不得保存账号密码、模拟登录、绕过验证码/SSO/paywall 或破解访问控制。
- **D-16:** 非 OA 或授权待确认来源下载后可以进入自动阅读草稿，但必须标记为 draft/pending，不得自动写入正式 `literature_map.md`、`agent_research_notes.md`、`metadata` 或论文结论。
- **D-17:** 不内置、不推荐、不自动化 Sci-Hub 或任何未授权镜像源。用户自定义 provider 也不得用于配置未授权镜像或绕过访问控制。

### find/download 工作流

- **D-18:** `find` 和 `download` 保持为两个概念，但默认运行模式是 `monitored_auto`。
- **D-19:** 默认 `rsa source find P001` 会自动搜索、自动审查、自动下载通过规则的来源，并写入候选、source ledger、本地 PDF 路径和 acquisition report。
- **D-20:** 必须保留人工监控和调试入口，例如 `--no-download`、`rsa source candidates P001`、`rsa source download P001 --best`、`rsa source download P001 --candidate SC001`。
- **D-21:** 允许直接 URL 下载。手动命令必须显式声明授权模式和使用限制；自动流程中的 URL 必须来自内置 provider、用户自定义 provider 或任务队列，并自动补全候选、审查和下载记录。

默认配置方向：

```yaml
source_discovery:
  automation_mode: monitored_auto
  default_auto_download: true
```

### 文件命名、多版本与去重

- **D-22:** PDF 保存路径使用每篇论文一个目录，按 `source_id` 命名：`01_literature/pdfs/P###/S###_<provider_id>_<version_label>.pdf`。
- **D-23:** 同一篇论文可以保留多个 PDF 版本，系统自动选择主版本，但保留全部版本。
- **D-24:** 主版本优先级为 `publisher_version`、`accepted_manuscript`、`institutional_subscription`、`repository_copy`、`arxiv_preprint`、`preprint`、`unknown`。
- **D-25:** source ledger 需要记录 `is_primary`、`version_label`、`primary_reason_zh`。用户后续可以调整主版本标记，但不删除任何 PDF。
- **D-26:** 重复下载按 `sha256` hash 去重。内容相同则不新增 PDF，不覆盖已有文件，并记录 `duplicate_of` 和中文原因。
- **D-27:** hash 不同即使 DOI/标题相同，也作为新版本保存，分配新的 `source_id`。
- **D-28:** 下载必须先写 `.tmp` 临时文件，校验文件类型、hash 和去重后再原子落盘。失败时删除临时文件，只写 `failed`、`blocked` 或 `partial_failed` 状态和中文原因。

### 中文用户优先

- **D-29:** 所有用户可见 CLI help、成功提示、错误信息、状态报告、模板说明和 GSD 文档必须中文优先。
- **D-30:** 英文字段名、CLI flag、YAML key、Markdown 表格列名和状态枚举保持英文稳定，但在用户需要阅读或填写的位置必须提供中文解释。

### Agent Discretion

- 实现时可以决定内部 helper 名称、文件拆分、具体下载库和错误类型，只要符合现有 argparse/YAML/Markdown 风格。
- v1 可以先实现 `url_template` provider，复杂浏览器自动化、数据库 API 专用 connector 和登录会话复用可延后。
- 自动审查的标题相似度算法、provider 默认列表和 status 输出格式由 planner/implementation 决定，但必须可测试、可解释、中文可读。

</decisions>

<specifics>

## Specific Ideas

- 用户希望系统核心特征是“能够在用户不干预的情况下自动进行，用户可以监控重要环节并进行调整”。
- 因此 Phase 7 默认自动下载，但保留 `--no-download`、候选查看和手动下载命令作为监控/调整入口。
- 用户明确需要支持学校账号、机构订阅、个人订阅等已授权访问资源，记录用途为“仅供个人科研阅读，不得公开分发 PDF”。
- 每个 GSD 讨论阶段需要维护临时 `DISCUSSION-WIP.md`，每完成一个小点立即更新，最后再整理进正式 context 和总决策。

</specifics>

<canonical_refs>

## Canonical References

### Project scope and requirements

- `.planning/ROADMAP.md` - Phase 7 在 v2 roadmap 中的边界：授权全文获取，不绕过 paywall。
- `.planning/REQUIREMENTS.md` - `V2-DL-01`、`V2-DL-02` 和 `LANG-04`。
- `.planning/PROJECT.md` - 项目总原则：正式记录受保护、中文用户优先、本地 Markdown/YAML。
- `.planning/v2-DISCUSSION.md` - v2 自动下载、自动阅读、AI scoring 的阶段拆分。

### Prior phase foundations

- `.planning/phases/06-asset-source-foundation/06-CONTEXT.md` - Phase 6 source ledger、asset manifest、local-only PDF 边界。
- `.planning/phases/07-authorized-acquisition/07-DISCUSSION-WIP.md` - Phase 7 逐点讨论工作稿，保留完整讨论过程。

### Existing implementation

- `src/rsa_cli/assets.py` - Phase 6 source ledger 和 asset manifest helper。
- `src/rsa_cli/cli.py` - argparse 子命令结构和中文 CLI 输出模式。
- `src/rsa_cli/config.py` - `rsa.yaml` 与 `.rsa/local.yaml` 合并逻辑，适合承载本地 custom provider 配置。
- `src/rsa_cli/templates.py` - 模板文件与中文字段说明。
- `src/rsa_cli/notes.py` - PDF acquisition report 和 reading note 授权边界。
- `src/rsa_cli/skeleton.py` - 新目录和模板初始化入口。

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `ProjectConfig.pdfs_root`、`sources_root`、`assets_root` 已存在，可用于新增 `source_candidates_root` 或下载输出路径。
- `load_project_config` 已经合并 `.rsa/local.yaml`，适合承载 `source_discovery.custom_providers`。
- `assets.add_source_record` 已能复制本地文件并写入 `sources/P###.yaml`，Phase 7 可以在下载成功后复用或扩展该路径。
- `notes.record_pdf_status` 可继续记录 PDF 获取状态，但 Phase 7 可能需要更结构化的候选和下载状态。

### Established Patterns

- CLI 使用 argparse subcommand group，小型 `_run_*_command` 分发。
- YAML 写入使用 `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)`。
- `validate` 和 `status` 命令应只读。
- PDF 和 binary assets local-only，manifest/source YAML 可审计。
- 失败和阻塞状态需要中文错误/原因，不静默失败。

### Integration Points

- `rsa source find`、`rsa source candidates`、`rsa source download` 应扩展现有 `source` 命令组。
- 新增候选文件建议为 `01_literature/source_candidates/P###.yaml`。
- 下载成功后写入 `01_literature/pdfs/P###/` 和 `01_literature/sources/P###.yaml`。
- `skeleton.py`、`.gitignore`、templates 和 tests 需要覆盖 source candidates、custom provider 模板、PDF local-only、中文说明。

</code_context>

<deferred>

## Deferred Ideas

- 自动阅读全文、阅读笔记草稿生成：Phase 8。
- 结构化证据抽取、AI relevance/quality/read priority scoring：Phase 9。
- Workflow Orchestrator：Phase 10。
- 批量 campaign、review queue、排序和去重：Phase 11。
- Crossref/OpenAlex/Zotero/BibTeX 等更完整 scholarly metadata integration：Phase 12。
- 本地 review UI：Phase 13。
- Claim-level citation check 和最终 hardening：Phase 14。
- 多 agent orchestration：Phase 15，可选延后。

</deferred>

---

*Phase: 07-authorized-acquisition*  
*Context gathered: 2026-05-14*
