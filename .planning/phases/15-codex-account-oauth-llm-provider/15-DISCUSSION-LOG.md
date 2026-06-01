# Phase 15 Discussion Log

## Scope Decision

Selected option: small optional provider, not a full LLM platform.

Reason: RSA already has reading draft, scoring, workflow, campaign, review workspace, safety and worker layers. Phase 15 should only add a local LLM credential/provider adapter that those layers can reuse later. Expanding into web automation, general ChatGPT UI control, provider marketplace, batch LLM scheduler or multi-agent orchestration would duplicate existing phase responsibilities and increase auth risk.

## Credential Decision

Selected option: import from Codex CLI auth file into RSA local-only auth store.

Rules:

- Read source from `CODEX_HOME/auth.json` or `~/.codex/auth.json`.
- Store RSA copy at `.rsa/auth/codex_oauth.yaml`.
- Never print token values.
- Never commit `.rsa/auth/**`.
- Do token presence and expiry preflight before provider calls.

## Runtime Decision

Selected option: support `codex_oauth` for `rsa note draft` first.

Reason: Phase 8 reading draft already has a provider abstraction and schema validation. It is the safest first integration point because failed LLM output is already blocked before note creation.

## Formal Boundary Decision

Selected option: no formal write impact.

All content from this provider remains staging/review. The existing formal write gates still require explicit human confirmation and conflict/schema checks.

## Extension Decision

Selected option: reserve fields but do not implement broad functionality.

Reserved future interfaces:

- token refresh command
- alternative auth store path
- provider status JSON
- response endpoint override
- future use by scoring, visual LLM analysis and safety LLM review

Current phase implements only the minimum needed to configure, inspect, import, clear and call the provider from reading draft.
