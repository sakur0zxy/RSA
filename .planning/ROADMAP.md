# Roadmap: RSA 科研 Agent

## Overview

v1 builds a local-first research agent harness in five phases. The path starts with topic profiles, round boundaries and project instructions, then adds formal literature records, candidate search staging, topic mapping, reading notes and finally eval/observability hardening. The roadmap deliberately prioritizes evidence hierarchy, human approval and repeatable checks before any advanced multi-agent orchestration.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Harness Foundation** - Define local file schema, topic profiles, research rounds and project instructions. (completed 2026-05-11)
- [x] **Phase 2: Literature Records Pipeline** - Build metadata-first records, paper index and candidate verification staging. (completed 2026-05-11)
- [x] **Phase 3: Research Round Integration** - Connect round archives, topic mapping, gap detection and formal-write guardrails. (completed 2026-05-12)
- [x] **Phase 4: Reading Note Workflow** - Add authorized full-text reading notes and approval gates for formal research notes. (completed 2026-05-12)
- [ ] **Phase 5: Evaluation and Hardening** - Add eval fixtures, trace summaries and regression checks for harness reliability.

## Phase Details

### Phase 1: Harness Foundation
**Goal**: Establish the project structure and contracts that every later agent workflow must obey.
**Depends on**: Nothing (first phase)
**Requirements**: [PROF-01, PROF-02, ROUND-01, DOCS-01]
**Success Criteria** (what must be TRUE):
  1. User can create and validate a topic profile YAML with all required research fields.
  2. User can start a bounded research round with clear objective, limits and output policy.
  3. Project-root `AGENTS.md` tells future agents how to respect evidence hierarchy and GSD workflow.
  4. SAR noncontinuous-aperture research can be represented as a starter topic profile without hard-coding SAR into the harness.
**Plans**: 3 plans

Plans:
**Wave 1**
- [x] 01-01: Create directory schema, starter topic profile and template files.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02: Implement profile validation and research round configuration.

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-03: Finalize project guidance and smoke-test a SAR starter profile.

### Phase 2: Literature Records Pipeline
**Goal**: Make verified literature metadata the formal source of truth while keeping candidates safely staged.
**Depends on**: Phase 1
**Requirements**: [META-01, META-02, META-03, SRCH-01, SRCH-02]
**Success Criteria** (what must be TRUE):
  1. User can store verified papers as one YAML file per paper with required metadata fields.
  2. User can maintain a readable `paper_index.md` that matches metadata records.
  3. Candidate papers remain outside formal metadata until reviewed.
  4. User can mark candidates verified, rejected or uncertain with reasons and source evidence.
**Plans**: 4 plans

Plans:
**Wave 1**
- [x] 02-01: Define metadata schema, paper index format and validation checks.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02: Implement candidate staging and verification review outputs.

**Wave 3** *(blocked on Wave 1 completion)*
- [x] 02-03: Add consistency checks between metadata and paper index.

**Wave 4** *(blocked on Wave 2 and Wave 3 completion)*
- [x] 02-04: Add Chinese explanations to remaining Phase 1 user-facing templates and seed files.

### Phase 3: Research Round Integration
**Goal**: Turn a bounded round into a traceable research packet that can update maps only through safe formal writes.
**Depends on**: Phase 2
**Requirements**: [ROUND-02, MAP-01, MAP-02, GUARD-01]
**Success Criteria** (what must be TRUE):
  1. User can inspect each round archive through a concise README and final summary.
  2. Verified papers can be mapped to topic questions, thesis chapters, planned papers and baseline/theory roles.
  3. User can see uncovered priority questions for a topic profile.
  4. Formal writes are blocked when schema, conflict or approval checks fail.
**Plans**: 3 plans

Plans:
**Wave 1**
- [x] 03-01: Implement round archive creation and required summary files.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02: Implement literature map and research gap update workflow.

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 03-03: Implement formal record writer with schema, conflict and approval checks.

Cross-cutting constraints:
- User-facing templates, help text, validation errors and generated reports must provide Chinese explanations while field names, YAML keys, table columns and CLI flags remain English.
- `validate` commands must be read-only; `generate` and `propose` commands may create generated guidance, but must not modify formal records.
- Formal writes must preserve Phase 2 metadata gates, avoid new `paper_id` allocation, and fail on conflicts instead of overwriting.

### Phase 4: Reading Note Workflow
**Goal**: Support single-paper reading notes without crossing copyright or academic-integrity boundaries.
**Depends on**: Phase 3
**Requirements**: [NOTE-01, NOTE-02]
**Success Criteria** (what must be TRUE):
  1. User can generate a reading note only when the full text is local, provided or otherwise authorized.
  2. Reading notes distinguish quoted/source-grounded claims, agent summaries and human decisions.
  3. Human approval is required before notes influence formal maps or research notes.
  4. Attempting to process unavailable or unauthorized PDFs results in a status update, not a fabricated note.
**Plans**: 2 plans

Plans:
**Wave 1**
- [x] 04-01: Create paper note template and authorized-content checks.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-02: Connect approved reading notes to formal maps and research notes.

Cross-cutting constraints:
- User-facing templates, help text, validation errors and generated reports must provide Chinese explanations while field names, YAML keys, table columns and CLI flags remain English.
- Reading notes require formal metadata plus an existing local, provided or otherwise authorized source file.
- Formal note-derived writes require `--human-confirmed`, `--confirmed-by`, approved note status and conflict-free validation.

### Phase 5: Evaluation and Hardening
**Goal**: Make the harness regressions visible before future prompt, tool or workflow changes can corrupt research records.
**Depends on**: Phase 4
**Requirements**: [EVAL-01, EVAL-02]
**Success Criteria** (what must be TRUE):
  1. User can run local eval fixtures for metadata hallucination, unauthorized PDF behavior, formal-record conflicts, output format drift and scope creep.
  2. Each research round emits a trace summary with tools used, decisions, rejected items, uncertain items and approvals.
  3. Prompt, template or rule changes can be compared against baseline eval results.
  4. Known failure modes are documented with remediation guidance.
**Plans**: 2 plans

Plans:
- [ ] 05-01: Build eval fixtures and scoring rules.
- [ ] 05-02: Add trace summaries, regression report and hardening docs.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Harness Foundation | 3/3 | Complete   | 2026-05-11 |
| 2. Literature Records Pipeline | 4/4 | Complete    | 2026-05-11 |
| 3. Research Round Integration | 3/3 | Complete    | 2026-05-12 |
| 4. Reading Note Workflow | 2/2 | Complete    | 2026-05-12 |
| 5. Evaluation and Hardening | 0/2 | Not started | - |

---
*Roadmap created: 2026-05-11*
