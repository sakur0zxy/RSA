# Phase 16: Research Plan Driven Literature Discovery - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning
**Source:** gsd-discuss-phase 16, completed inline without subagents; user delegated decisions to the agent

<domain>
## Phase Boundary

Phase 16 adds the missing front door of RSA: it turns a user-provided research plan into auditable search queries and candidate literature campaigns.

This phase delivers plan-to-campaign discovery:

- read a Markdown/text research plan, plain objective or existing topic profile;
- derive research questions, keywords and query bundles;
- search legal/auditable scholarly or user-configured sources;
- normalize discovered papers into staging/campaign candidates;
- preserve Chinese-first reasons, confidence and failure records;
- hand off to existing Phase 7-15 acquisition, reading, scoring, workflow, worker and review paths.

It is not a formal metadata writer, not a thesis conclusion generator, not a full scholarly metadata platform and not a paywall bypass. Discovered papers remain candidates until the existing metadata intake and formal write gates approve them.

</domain>

<decisions>
## Implementation Decisions

### D-01: Phase shape

- Decision: `research_plan_to_campaign_discovery`.
- Phase 16 sits before existing campaign automation.
- It creates discovery artifacts and campaign candidates, then reuses Phase 7-15.
- It must not create `metadata/P###.yaml`, update `paper_index.md`, or write formal map/note/research records directly.

### D-02: Input sources

- Decision: `md_txt_objective_topic_profile_v1`.
- v1 supports:
  - Markdown or plain text research plan file;
  - plain text objective;
  - optional existing `topic_profile`.
- The plan source must be recorded as `plan_source` with path, type, status and Chinese explanation.
- Future interface reserved for `docx`, Zotero collections, BibTeX libraries and Web UI uploads, but these are not required in v1.

### D-03: Discovery profile and query bundle

- Decision: `auditable_query_bundle`.
- RSA must write a machine-readable discovery profile and query bundle under `01_literature/discovery/`.
- Stable fields include:
  - `discovery_id`
  - `plan_source`
  - `research_questions`
  - `keywords`
  - `query_bundle`
  - `source_provider`
  - `search_run_id`
  - `candidate_id`
  - `evidence_level`
  - `status`
  - `reason_zh`
  - `repair_hint_zh`
- Each query should include Chinese rationale, English search terms, inclusion/exclusion hints, confidence and source trace.

### D-04: Search providers

- Decision: `legal_auditable_provider_registry`.
- Default providers should be legal/auditable scholarly indexes or local/user-configured providers.
- Provider records must preserve source name, URL, query, response status, rate-limit/error information and Chinese reason text.
- User custom provider support should reuse the existing local-first configuration style.
- Phase 16 must not use Sci-Hub, unauthorized mirrors, saved passwords, silent cookie extraction or access-control bypass.

### D-05: Candidate staging

- Decision: `discovery_candidates_feed_campaign`.
- Discovered papers become staging candidates with title, authors, year, DOI/URL, abstract/snippet, source provider, match evidence, dedup key, triage status and Chinese rationale.
- Export/import must integrate with existing `01_literature/campaigns/C###.yaml`.
- If a candidate already matches formal metadata, it may be marked as linked by existing campaign logic.
- Metadata intake can propose formal writes later, but discovery itself cannot write formal records.

### D-06: Automation and supervision

- Decision: `automatic_discovery_with_review_controls`.
- Default workflow can automatically parse plan, generate queries, run provider search, deduplicate and create a campaign.
- Users supervise through discovery status, campaign queue, review workspace and existing formal requests.
- Low-confidence, provider failure, unreadable plan, empty query, rate limit or ambiguous identity must produce `blocked` or `needs_review` status rather than fake results.

### D-07: Chinese-first user experience

- Decision: `zh_first_discovery_outputs`.
- CLI help, errors, success messages, generated Markdown reports, discovery status and README text must be readable by Chinese users.
- Schema keys, command names, provider ids and YAML keys remain English and stable, with Chinese explanations where users read or fill them.

### D-08: Extension interfaces

- Decision: `reserve_without_expanding`.
- Reserve interfaces for:
  - `llm_query_generation`
  - `iterative_query_refinement`
  - `provider_plugins`
  - `scholarly_metadata_enrichment`
  - `discovery_eval`
  - `web_review_ui`
  - `manual_override_history`
- Current implementation should keep these as explicit `not_run` or `not_enabled` fields unless needed for the v1 closed loop.

### the agent's Discretion

- Implementation can choose conservative heuristic query generation first, with optional LLM hooks behind existing provider/preflight boundaries.
- Implementation can choose file names and command names, as long as they are Chinese-first for users and integrate with existing campaign/discovery roots.
- Implementation can keep provider search minimal and testable, using deterministic fixtures/mocks for tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope And Requirements

- `.planning/ROADMAP.md` — Phase 16 goal, boundary and dependency on Phase 15.
- `.planning/REQUIREMENTS.md` — `V2-DISCOVERY-01` through `V2-DISCOVERY-08`.
- `.planning/STATE.md` — active phase state and non-bypass decisions.
- `.planning/PROJECT.md` — project value, Chinese-first policy, local Markdown/YAML harness and formal record boundaries.

### Existing Reuse Points

- `src/rsa_cli/campaign.py` — campaign create/import/dedup/review queue primitives to reuse for discovered candidates.
- `src/rsa_cli/acquisition.py` — source discovery/provider safety rules and custom provider validation patterns.
- `src/rsa_cli/config.py` — local config merge, existing `source_discovery` and future discovery config shape.
- `src/rsa_cli/cli.py` — argparse command-group style and Chinese-first output pattern.
- `src/rsa_cli/templates.py` and `templates/search_candidates.md` — candidate staging language and formal metadata boundary wording.
- `tests/test_campaign.py`, `tests/test_acquisition.py`, `tests/test_cli.py`, `tests/test_templates.py` — regression patterns for command behavior, provider validation and Chinese template checks.

### Prior Phase Context

- `.planning/phases/07-authorized-acquisition/07-CONTEXT.md` — authorized source discovery/download boundaries and custom provider schema.
- `.planning/phases/08.2-campaign-foundation/08.2-VERIFICATION.md` — campaign foundation behavior and non-formal-write boundary.
- `.planning/phases/11-campaign-batch-review/11-CONTEXT.md` — campaign queue, metadata intake, review decision and formal gate semantics.
- `.planning/phases/15-codex-account-oauth-llm-provider/15-CONTEXT.md` — optional LLM provider boundary, local-only credentials and fail-closed behavior.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `ProjectConfig` already exposes `campaigns_root`, `topic_profiles_root`, `source_discovery`, `custom_source_providers` and merged `.rsa/local.yaml`.
- `campaign.create_campaign()` and `campaign.import_campaign_items()` already provide campaign creation, CSV/TSV/YAML import, dedup and formal metadata linking.
- `acquisition.validate_custom_providers()` already defines strict local provider safety checks and forbidden provider text handling.
- Existing CLI command groups use `_run_<domain>_command()` functions and Chinese-first `print()` messages.
- Existing tests use `tmp_path`, YAML fixtures and direct function imports for deterministic local validation.

### Established Patterns

- Store machine-readable state in YAML and user-readable reports in Markdown.
- Keep binary or sensitive artifacts local-only and git-ignored.
- Use `blocked`, `needs_review`, `partial`, `ready_for_review` or equivalent staging status instead of fabricating success.
- Let automation create staging/review artifacts, while formal writes require explicit human confirmation.
- Keep English keys stable and add Chinese explanations where users interact with files or CLI output.

### Integration Points

- Add `discovery_root` or equivalent config accessor under `01_literature/discovery/`.
- Add a `rsa discovery` or `rsa discover` command group in `cli.py`.
- Feed discovered candidates into existing campaign import/create logic instead of creating a parallel queue.
- Add README/docs/tests alongside command implementation.

</code_context>

<specifics>
## Specific Ideas

- Primary user scenario: a Chinese user has a research plan file and wants RSA to automatically find related papers, then let the existing RSA workflow download/read/score/review them.
- The default output should explain why each query and candidate was produced in Chinese.
- Candidate discovery should be automatic by default, but user can inspect, rerun or disable provider search.

</specifics>

<deferred>
## Deferred Ideas

- Full Crossref/OpenAlex/Zotero deep sync and citation graph construction.
- Advanced semantic search, embeddings and vector database.
- Complex Web UI editing and interactive query refinement.
- Multi-agent discovery/review orchestration.
- Full `.docx` parsing unless the implementation can reuse existing document tooling without making it a core dependency.

</deferred>

---

*Phase: 16-Research Plan Driven Literature Discovery*
*Context gathered: 2026-05-31*

