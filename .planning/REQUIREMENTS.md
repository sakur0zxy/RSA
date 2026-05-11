# Requirements: RSA 科研 Agent

**Defined:** 2026-05-11
**Core Value:** 让科研 agent 的每一步输出都能追溯到来源、状态和人工确认，避免把未核验的模型判断混入正式科研记录。

## v1 Requirements

### Profiles

- [x] **PROF-01**: User can define a research topic profile in YAML with topic id, name, keywords, priority questions, metrics, preferred sources, excluded scope, grading rules and required outputs.
- [x] **PROF-02**: User can validate a topic profile and receive actionable errors for missing required fields or invalid values.

### Rounds

- [ ] **ROUND-01**: User can start a bounded research round with topic profile, objective, max paper count, allowed tools, output policy and human approval mode.
- [ ] **ROUND-02**: User can inspect each completed research round through a lightweight archive containing `README.md`, `final_round_summary.md` and only task-relevant optional files.

### Literature Records

- [ ] **META-01**: User can store each verified paper as one metadata YAML file with required identity, source, status, PDF and research-use fields.
- [ ] **META-02**: User can maintain `paper_index.md` as a human-readable index consistent with metadata YAML records.
- [ ] **META-03**: User can track DOI, official URL, source reliability, PDF status, local PDF path, decision and `last_checked` for each paper.

### Candidate Search

- [ ] **SRCH-01**: User can collect candidate papers into a staging area without writing them into formal metadata.
- [ ] **SRCH-02**: User can review candidate papers as verified, rejected or uncertain with reasons and source evidence.

### Topic Mapping

- [ ] **MAP-01**: User can map verified papers to topic profiles, priority questions, thesis chapters, planned paper outputs and baseline/theory roles.
- [ ] **MAP-02**: User can see research gaps by comparing verified literature coverage against topic profile priority questions.

### Reading Notes

- [ ] **NOTE-01**: User can generate a single-paper reading note only from provided, local or otherwise authorized full text.
- [ ] **NOTE-02**: User can require human approval before reading notes, literature maps or research notes become formal records.

### Guardrails

- [ ] **GUARD-01**: User can rely on a formal record writer that validates schema, checks conflicts, verifies approval status and blocks unsafe writes.

### Evaluation

- [ ] **EVAL-01**: User can run local eval fixtures covering metadata hallucination, unauthorized PDF behavior, formal-record conflicts, output format drift and scope creep.
- [ ] **EVAL-02**: User can inspect a trace summary for each round, including tools used, decisions made, rejected items, uncertain items and human approvals.

### Project Guidance

- [x] **DOCS-01**: Future agents can read project-root `AGENTS.md` and understand the evidence hierarchy, harness rules, coding workflow and GSD entry points.

## v2 Requirements

Deferred to future releases.

### Integrations

- **INTG-01**: User can sync selected metadata with Zotero, EndNote or another citation manager.
- **INTG-02**: User can query scholarly APIs through dedicated adapters with rate limits and source labels.
- **INTG-03**: User can optionally use OpenAI Agents SDK or another agent runtime for stateful orchestration and tool guardrails.

### Interface

- **UI-01**: User can review candidate papers, approvals and conflicts in a local Web UI.
- **UI-02**: User can visualize topic coverage and research gaps.

### Advanced Research Support

- **ADV-01**: User can compare versions of literature maps across rounds.
- **ADV-02**: User can run claim-level citation checks for longer synthesis drafts.
- **ADV-03**: User can batch-process larger literature sets with checkpointed human review.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic thesis or review writing | v1 should produce auditable research materials, not final academic prose |
| Unauthorized PDF download | Copyright and academic integrity risk |
| Complex database backend | Local files are enough for v1 validation and easier to review |
| Full multi-agent platform | Harness reliability should come before orchestration complexity |
| Direct SAR imaging algorithm implementation | This project builds the research agent harness, not the SAR algorithm codebase |
| Large one-shot literature ingestion | Small bounded rounds are easier to audit and correct |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROF-01 | Phase 1 | Complete |
| PROF-02 | Phase 1 | Complete |
| ROUND-01 | Phase 1 | Pending |
| DOCS-01 | Phase 1 | Complete |
| META-01 | Phase 2 | Pending |
| META-02 | Phase 2 | Pending |
| META-03 | Phase 2 | Pending |
| SRCH-01 | Phase 2 | Pending |
| SRCH-02 | Phase 2 | Pending |
| ROUND-02 | Phase 3 | Pending |
| MAP-01 | Phase 3 | Pending |
| MAP-02 | Phase 3 | Pending |
| GUARD-01 | Phase 3 | Pending |
| NOTE-01 | Phase 4 | Pending |
| NOTE-02 | Phase 4 | Pending |
| EVAL-01 | Phase 5 | Pending |
| EVAL-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-05-11*
*Last updated: 2026-05-11 after initial definition*
