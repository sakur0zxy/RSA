# Phase 15: Codex Account OAuth LLM Provider - Context

## Phase Goal

为 RSA 增加一个可选的 `codex_oauth` LLM provider，让本地已登录的 Codex/ChatGPT 账号会话可以用于 RSA 的 AI 辅助任务，优先接入 `rsa note draft` 的 reading draft 生成链路。

这个阶段只做最小可用闭环：本地凭据发现、导入、状态检查、命令级 preflight、LLM 调用适配和中文诊断。它不是默认 provider，也不替代现有 `mock`、`openai` 或 `openai_compatible`。

## Decisions

1. Provider id 固定为 `codex_oauth`。
2. 默认凭据来源是 Codex CLI 的 `auth.json`，位置按 `CODEX_HOME/auth.json` 或 `~/.codex/auth.json` 查找。
3. RSA 自己只保存本地副本到 `.rsa/auth/codex_oauth.yaml`，并要求 `.rsa/auth/**` 不进入 git。
4. 当前阶段不实现网页登录、不抓浏览器 cookies、不保存账号密码、不模拟 SSO、不绕过 OpenAI/Codex 访问控制。
5. 当前阶段不自动刷新 token。保留 `refresh_command`、`token_source`、`auth_store`、`base_url`、`response_endpoint` 等扩展字段，但默认只做 status/import/clear 和 fail-closed preflight。
6. `rsa note draft` 可以使用 `reading_draft.llm.provider: codex_oauth` 调用该 provider。后续 scoring、visual LLM 和 safety LLM 可复用同一 provider 接口，但不在本阶段扩大实现。
7. 所有用户可见信息中文优先；字段名、provider id、YAML key、CLI flag 保持英文稳定。
8. 通过 `codex_oauth` 生成的内容仍是 staging/review artifact，不能进入 formal records，也不能绕过 `rsa formal ... --human-confirmed`。

## Boundaries

Phase 15 MUST NOT:

- automate ChatGPT web UI;
- scrape browser cookies;
- store account passwords;
- bypass Codex/OpenAI auth or access control;
- make `codex_oauth` the default provider;
- turn AI output into formal metadata, map rows, research notes or thesis text without human confirmation;
- add multi-agent routing, cloud worker, web UI, or batch LLM scheduling.

## Extension Interfaces

The implementation should preserve these future extension points without implementing them fully:

- `reading_draft.llm.codex_oauth.auth_store`
- `reading_draft.llm.codex_oauth.codex_home`
- `reading_draft.llm.codex_oauth.token_source`
- `reading_draft.llm.codex_oauth.refresh_command`
- `reading_draft.llm.codex_oauth.base_url`
- `reading_draft.llm.codex_oauth.response_endpoint`
- provider status fields for `refresh_supported`, `future_interfaces`, and token source diagnostics

## User-Facing Workflow

1. User logs in with Codex CLI or already has a local Codex auth file.
2. User runs `rsa llm codex status` to inspect whether RSA can see usable credentials.
3. User runs `rsa llm codex import` to copy usable local Codex auth material into RSA local-only auth storage.
4. User configures `.rsa/local.yaml`:

```yaml
reading_draft:
  llm:
    provider: codex_oauth
    model: gpt-5
```

5. User runs `rsa note draft P001`.
6. If credentials are missing, expired, malformed, or the provider call fails, RSA fails closed and writes status/prompt diagnostics instead of creating a fake reading note.

## Chinese-First Requirement

CLI help, success messages, failure messages, repair hints, README, phase docs and generated status files must be understandable by Chinese users. Stable identifiers remain English, but every user-facing place must include Chinese context.
