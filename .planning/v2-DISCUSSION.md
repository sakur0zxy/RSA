# v2 Discussion: What Should Come Next

**Created:** 2026-05-13  
**Status:** Discussion draft, not locked requirements

## Recommended v2 Theme

v2 should turn the v1 local harness into a more scalable literature-review workstation while preserving the same evidence hierarchy:

candidate evidence -> verified metadata -> reading notes -> formal map/research notes -> synthesis guidance.

## Candidate Workstreams

### 1. Large-Scale Literature Review

**Goal:** Support larger batches without losing auditability.

Possible features:
- `rsa campaign create` for multi-round review campaigns.
- Batch candidate import from CSV/BibTeX/RIS.
- Deduplication by DOI, title and official URL.
- Review queue states: `new`, `needs_verification`, `verified`, `rejected`, `uncertain`, `deferred`.
- Progress reports by topic profile and priority question.

Why it matters: this matches the user's stated need for large-scale literature research while keeping v1's staged admission model.

### 2. Source File And Screenshot Asset Management

**Goal:** Make local PDFs, screenshots and important figure/result captures easier to preserve.

Possible features:
- `rsa asset add P001 --file <path> --kind figure|table|result|screenshot`.
- Asset manifest under `assets/P###/manifest.yaml`.
- Screenshot metadata: source paper, page, figure/table number, capture reason, thesis use.
- Checks that formal notes reference assets through stable local paths.

Why it matters: the user explicitly wants PDF sources and important-result screenshots retained for later writing.

### 3. Scholarly API And Citation Manager Integrations

**Goal:** Reduce manual metadata entry while preserving verification gates.

Possible features:
- DOI lookup adapter with source labels.
- Crossref/Semantic Scholar/OpenAlex/arXiv adapters.
- Zotero/EndNote/BibTeX export or sync.
- API result staging, never direct formal writes.

Why it matters: metadata collection is a bottleneck at scale, but API data still needs review.

### 4. Review UI

**Goal:** Make candidate review and formal approval less CLI-heavy.

Possible features:
- Local Web UI for candidate verification.
- Conflict review screen for formal writes.
- Literature map and gap report visualization.
- Reading note approval workflow.

Why it matters: v1 CLI is precise, but long review sessions need lower-friction scanning and comparison.

### 5. Claim-Level Citation Checks

**Goal:** Help later writing by checking that claims are backed by approved sources.

Possible features:
- Draft claim extraction into a staging file.
- Link each claim to metadata, reading-note claim or map row.
- Detect unsupported, weakly supported or overgeneralized claims.
- Keep output as review guidance, not final academic prose.

Why it matters: this directly supports article/thesis writing without letting the agent invent conclusions.

### 6. Smarter Evaluation

**Goal:** Extend v1 deterministic evals with research-quality checks.

Possible features:
- Golden fixture sets for candidate review.
- Regression checks for source attribution quality.
- Optional LLM-judged evals with locked rubrics.
- Scorecards for hallucination risk, source quality and schema drift.

Why it matters: v1 catches harness regressions; v2 should also catch quality regressions in research behavior.

### 7. Optional Agent Runtime Orchestration

**Goal:** Add multi-agent workflows only after the harness is stable.

Possible features:
- Explicit roles for search, verification, mapping, reading and eval.
- Per-role permissions and output schemas.
- Checkpointed human approval between roles.
- No direct formal writes from search or reading agents.

Why it matters: multi-agent execution can speed work, but only if v1 guardrails remain enforceable.

## My Recommended v2 Order

1. Asset management for PDFs/screenshots.
2. Batch candidate import and campaign review queues.
3. Scholarly API lookup into staging.
4. Review UI for verification and approvals.
5. Claim-level citation checks.
6. Smarter evals.
7. Optional multi-agent orchestration.

## Open Decisions For v2 Planning

- Should v2 stay CLI-first with generated reports, or introduce a local Web UI early?
- Which citation source should be first: DOI/Crossref, Zotero, BibTeX import, or OpenAlex?
- Should PDFs remain purely manually provided, or should v2 support controlled download only from user-authorized URLs?
- How much screenshot metadata is enough without becoming annoying?
- Should v2 introduce a database, or continue with Markdown/YAML plus indexes?
