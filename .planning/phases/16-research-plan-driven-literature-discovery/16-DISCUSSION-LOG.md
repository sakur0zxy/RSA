# Phase 16: Research Plan Driven Literature Discovery - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `16-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-05-31
**Phase:** 16-research-plan-driven-literature-discovery
**Areas discussed:** Phase scope, input sources, query generation, providers, campaign integration, automation boundary, extension interfaces

---

## Phase Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Plan-to-campaign discovery | Convert research plan into search queries and campaign candidates; reuse existing RSA pipeline. | ✓ |
| Full scholarly platform | Build broad metadata/database/search platform. | |
| Formal metadata writer | Let discovery directly create `metadata/P###.yaml`. | |

**User's choice:** Agent selected conservative plan-to-campaign discovery.
**Notes:** This keeps Phase 16 useful without weakening formal record boundaries.

---

## Input Sources

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown/text/objective/topic profile | Support the current user files and existing RSA topic profile model. | ✓ |
| Add docx/Zotero/BibTeX now | Broaden input sources in the first implementation. | |
| Web UI upload first | Wait for a Web UI before discovery. | |

**User's choice:** Agent selected minimal current input support with extension hooks.
**Notes:** `.docx`, Zotero and BibTeX are preserved as future interfaces.

---

## Query Generation

| Option | Description | Selected |
|--------|-------------|----------|
| Auditable query bundle | Write queries with Chinese rationale, English terms, confidence and inclusion/exclusion hints. | ✓ |
| Free-text prompt only | Store only a prompt/result blob. | |
| Fully manual query entry | User writes every query manually. | |

**User's choice:** Agent selected auditable query bundle.
**Notes:** This supports traceability and later evals.

---

## Search Providers

| Option | Description | Selected |
|--------|-------------|----------|
| Legal/auditable provider registry | Use open scholarly indexes or user-configured providers, with blocked states on uncertainty. | ✓ |
| Any URL that returns a PDF | Too loose for discovery identity and authorization. | |
| Unauthorized mirror support | Out of scope and rejected by current project boundaries. | |

**User's choice:** Agent selected legal/auditable provider registry.
**Notes:** Provider search may be automatic, but authorization and formal writes remain gated.

---

## Campaign Integration

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse campaign queue | Discovered papers become campaign candidates and metadata intake requests later. | ✓ |
| New queue system | Create a separate discovery queue. | |
| Direct formal metadata | Discovery directly writes formal records. | |

**User's choice:** Agent selected reuse campaign queue.
**Notes:** This avoids duplicate state machines and preserves Phase 11 review semantics.

---

## Automation Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Automatic discovery with review controls | Automatically parse/search/import, then let user supervise low-confidence and formal write points. | ✓ |
| Manual-only discovery | Too little automation for RSA's product goal. | |
| Fully automatic formal database update | Too risky and violates formal gate. | |

**User's choice:** Agent selected automatic discovery with review controls.
**Notes:** Discovery artifacts can be generated without user intervention; formal writes cannot.

---

## the agent's Discretion

- Command names, file layout and internal helper boundaries can be chosen by the implementing agent.
- Query heuristics may start conservative and deterministic, with optional LLM hooks behind fail-closed preflight.
- Provider support may be minimal in v1 as long as the schema and tests reserve extension points.

## Deferred Ideas

- Full scholarly metadata sync.
- Embedding/vector search.
- Rich Web UI query refinement.
- Multi-agent discovery orchestration.
- Advanced `.docx` ingestion if it would enlarge base dependencies.

