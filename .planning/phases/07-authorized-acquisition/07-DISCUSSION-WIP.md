# Phase 7 临时讨论记录 / Discussion WIP

**Phase:** 07 Authorized Acquisition  
**用途:** 临时记录讨论中的小决策。每讨论完一个小点，先更新本文档；全部讨论完成后，再整理进正式 `07-CONTEXT.md` 和总决策文档。  
**状态:** discussing

## 记录规则

- 本文档是临时工作稿，不是最终规范。
- 已经明确的结论标记为 `已定`。
- 仍需继续讨论或后续整理的内容标记为 `待定` 或 `待整理`。
- 英文字段名、CLI 参数名、状态枚举保持英文；用户可读说明必须以中文为主。

---

## 小点 1：来源发现范围

**状态:** 已定

### 决策

Phase 7 的默认来源发现范围采用保守可信来源，但允许用户配置自定义搜索源和数据库源。

默认自动发现范围包括：

- DOI 关联的开放全文位置。
- `official_url` 指向的出版社、会议、预印本或项目官方页面。
- arXiv / 预印本平台。
- OpenAlex / Unpaywall 类开放元数据返回的 OA location。
- 机构库、作者主页或实验室论文页面中可明确识别的公开 PDF。

### 用户自定义 provider

用户可以在本地配置中添加自定义搜索网址、数据库网址、机构库、学校数据库入口或实验室 publication 页面。

自定义 provider 必须使用固定模板，建议放在 `.rsa/local.yaml`：

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

### 字段要求

必须包含：

- `provider_id`
- `enabled`
- `name_zh`
- `provider_type`
- `base_url`
- `query_mode`
- `query_template`
- `allowed_domains`
- `allowed_result_types`
- `access_mode`
- `requires_login`
- `user_access_confirmed`
- `authorization_policy`
- `usage_restriction_zh`
- `notes_zh`

### 边界

- 自定义 provider 只扩展发现能力，不降低匹配审查和授权记录要求。
- 自定义 provider 默认不直接写入正式 `source ledger`，必须先生成候选、审查、下载记录。
- 私人数据库入口、学校资源入口和本地偏好应优先放在 `.rsa/local.yaml`，避免提交到 git。

---

## 小点 2：检索依据与匹配规则

**状态:** 已定

### 决策

Phase 7 下载不是单纯按论文名字搜索；检索依据按稳定性排序。

推荐优先级：

```yaml
lookup_priority:
  - doi
  - official_url
  - arxiv_id
  - title_year_first_author
  - title_only
```

### 自动下载门槛

允许自动下载的典型情况：

- DOI 命中，并且来源符合当前下载策略。
- arXiv ID 命中。
- `official_url` 页面明确给出 PDF。
- `title + year + first_author` 匹配，且来源来自内置 provider 或用户自定义 provider。

不允许仅凭 `title_only` 自动下载。标题只能用于发现候选，不能单独作为自动下载依据。

### 匹配证据

候选来源需要记录：

```yaml
match_evidence:
  doi_match: true
  title_match_score: 0.96
  year_match: true
  author_match: true
  source_domain_allowed: true
```

---

## 小点 3：授权判定与下载边界

**状态:** 已定

### 决策

Phase 7 采用中等授权判定：允许下载直接可访问 PDF，也支持用户已授权访问的学校账号、机构订阅、个人订阅资源；但必须记录授权/访问模式和使用限制，不能把“可访问”直接等同于“正式授权结论”。

支持的访问/授权模式：

```yaml
authorization_mode:
  - open_access
  - direct_access
  - user_authorized_access
  - institutional_subscription
  - personal_subscription
  - provided
  - local
  - unknown
  - blocked
```

### 学校账号与机构订阅

支持用户通过学校账号、机构订阅、个人购买或数据库权限合法访问到的全文。

系统边界：

- 不保存账号密码。
- 不模拟登录流程。
- 不绕过验证码、SSO 或 paywall。
- 不破解访问控制。
- 可以使用用户已授权访问后的下载链接、本地文件或自定义 provider 入口。

记录示例：

```yaml
authorization_mode: user_authorized_access
access_mode: institutional_subscription
requires_login: true
user_access_confirmed: true
candidate_status: downloaded_pending_review
use_status: readable_draft_only
authorization_basis_zh: "用户确认已通过学校账号或机构订阅获得访问权限。"
usage_restriction_zh: "仅供个人科研阅读，不得公开分发 PDF。"
license_note: "机构订阅资源，保存在本地用于个人科研阅读。"
```

### 后续使用限制

下载成功后：

- PDF 可以保存在本地。
- 可以进入自动阅读草稿。
- 可以做 AI 摘要和评分草稿。
- PDF 不能提交到 git。
- 不能自动写入正式科研记录。
- 正式 map / research notes / metadata 仍需人工确认。

### 禁止项

- 不内置 Sci-Hub provider。
- 不自动搜索或下载 Sci-Hub。
- 不支持盗版镜像或未授权全文镜像。
- 不支持绕过 paywall 或破解访问控制。
- 用户自定义 provider 也不得用于配置未授权镜像或绕过访问控制。

---

## 小点 4：find / download 工作流

**状态:** 已定

### 决策

`find` 和 `download` 保持为两个概念，但默认工作流采用 `monitored_auto`：`rsa source find P001` 默认自动搜索、自动审查、自动下载通过规则的来源，并写入记录。

默认流程：

```text
rsa source find P001
        ↓
读取 metadata/P001.yaml
        ↓
自动搜索候选来源
        ↓
自动做匹配审查和授权/访问模式审查
        ↓
自动下载通过规则的来源
        ↓
写入 source_candidates、source ledger、PDF 本地路径和 acquisition report
```

### 保留手动控制

```powershell
rsa source find P001 --no-download
rsa source candidates P001
rsa source download P001 --best
rsa source download P001 --candidate SC001
rsa source download P001 --url "https://example.com/paper.pdf" --authorization-mode user_authorized_access --usage-restriction-zh "仅供个人科研阅读，不得公开分发 PDF。"
```

### 默认自动下载

```yaml
source_discovery:
  automation_mode: monitored_auto
  default_auto_download: true
```

### 直接 URL 下载

允许不用候选编号，直接传 URL 下载。

- 手动命令中，必须显式声明授权模式和使用限制。
- 自动流程中，URL 必须来自内置 provider、用户自定义 provider 或任务队列。
- 系统会自动补全候选记录、审查记录和下载记录。

---

## 小点 5：下载文件命名与重复处理

**状态:** 已定

### PDF 保存路径与命名

**决策:** 选择“每篇论文一个目录，按 `source_id` 命名”。

下载 PDF 保存到：

```text
01_literature/pdfs/P001/
  S001_unpaywall_publisher.pdf
  S002_arxiv_preprint.pdf
  S003_university_library_publisher.pdf
```

正式规则：

```text
01_literature/pdfs/P###/S###_<provider_id>_<version_label>.pdf
```

设计理由：

- 同一篇论文可以同时保存出版社版、arXiv 版、作者主页版、学校数据库版等多个来源版本。
- `S###` 与 Phase 6 的 `source ledger` 中的 `source_id` 对齐，便于审计。
- 不覆盖已有 PDF，避免丢失来源差异。
- PDF 文件本身仍然 local-only，不进入 git；git 只追踪 YAML/Markdown 记录。

### 多版本主 PDF 选择

**决策:** 自动选择主版本，但保留全部版本。

同一篇论文可以保留多个 PDF 来源版本，例如出版社版、accepted manuscript、arXiv/preprint、机构库副本、学校数据库副本。系统默认自动选择一个主版本，供 Phase 8 自动阅读优先使用；其他版本仍保留在 source ledger 中作为备选。

推荐主版本优先级：

```yaml
primary_version_priority:
  - publisher_version
  - accepted_manuscript
  - institutional_subscription
  - repository_copy
  - arxiv_preprint
  - preprint
  - unknown
```

source ledger 需要记录：

```yaml
is_primary: true
version_label: publisher_version
primary_reason_zh: "出版社正式版本优先作为自动阅读主版本。"
```

用户后续可以通过正式命令或配置调整主版本。调整主版本只改变 source ledger 中的 `is_primary` 标记，不删除任何 PDF 文件。

### 重复下载与去重

**决策:** 按文件 hash 去重，重复则跳过新增文件并记录审计信息。

下载成功后，系统计算文件 hash，例如 `sha256`。如果内容和已有 PDF 完全相同：

- 不新增重复 PDF 文件。
- 不覆盖已有文件。
- 在候选记录、下载日志或 source ledger 中记录重复关系。
- 保留本次发现来源的 URL、provider、访问模式和时间，方便审计“这个来源也指向同一份全文”。

记录示例：

```yaml
candidate_status: duplicate
duplicate_of: S001
file_hash:
  algorithm: sha256
  value: "..."
download_mode: automatic
duplicate_reason_zh: "下载内容与 S001 的本地 PDF 完全一致，未重复保存文件。"
```

如果 hash 不同，即使标题和 DOI 相同，也作为新版本保存，并分配新的 `source_id`。这样可以保留出版社版、预印本版、机构版之间的真实差异。

### 失败、冲突与部分下载

**决策:** 使用临时文件下载，成功校验后再原子落盘。

下载流程：

```text
download URL
  -> write .tmp file
  -> check response/content type
  -> verify file looks like PDF or expected source type
  -> compute sha256
  -> check duplicate
  -> move tmp file to final path
  -> write source ledger and acquisition report
```

规则：

- 下载中断、网络失败、文件类型错误或 hash 计算失败时，不生成正式 PDF 文件。
- 失败时删除 `.tmp` 临时文件。
- 失败仍写入候选记录或 acquisition report，记录 `failed` / `blocked` / `partial_failed` 状态和中文原因。
- 不覆盖已有正式 PDF 文件。
- 不保留残缺 PDF，避免 Phase 8 自动阅读误读坏文件。

记录示例：

```yaml
candidate_status: partial_failed
download_mode: automatic
error_reason_zh: "下载中断，临时文件已删除，未写入正式 PDF。"
tmp_file_removed: true
```

---

## 待整理进正式上下文的总决策

待 Phase 7 全部灰区讨论结束后，将本文档整理为：

- `.planning/phases/07-authorized-acquisition/07-CONTEXT.md`
- `.planning/phases/07-authorized-acquisition/07-DISCUSSION-LOG.md`
- 后续 `gsd-plan-phase 7` 可读取的正式决策依据。
