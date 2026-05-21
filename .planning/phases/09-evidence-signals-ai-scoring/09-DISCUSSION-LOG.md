# Phase 09: Evidence Signals & AI Scoring - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.  
> Decisions are captured in `09-CONTEXT.md`; this log preserves alternatives considered.

**Date:** 2026-05-21T10:32:54+08:00  
**Phase:** 09-Evidence Signals & AI Scoring  
**Areas discussed:** Scoring Object And Entry Point, Scoring Output Location, Evidence Signals Schema, Scoring Rubric, Visual Evidence Use, Human Review Override, CLI And Outputs

---

## Scoring Object And Entry Point

| Option | Description | Selected |
|--------|-------------|----------|
| Single paper + campaign item | Support both, with `P###` single-paper scoring as the core implementation path. | ✓ |
| Single paper only | Simpler but does not connect Phase 8.2 campaign queue. | |
| Campaign only | Too coarse and hard to test/debug. | |
| Human score only | Avoids AI scoring but misses Phase 9 purpose. | |

**User's choice:** 1  
**Notes:** Single-paper scoring is the core unit; campaign scoring reuses it.

---

## Scoring Output Location

| Option | Description | Selected |
|--------|-------------|----------|
| Independent scoring files | Store `P###_scoring.yaml`, `P###_review_packet.md`, and campaign scoring summary separately. | ✓ |
| Write back to reading note | Mixes Phase 8 readiness score with Phase 9 paper scoring. | |
| Write into campaign queue | Bloats queue items and makes batch state harder to audit. | |
| Write directly to formal records | Violates formal write gate. | |

**User's choice:** 1  
**Notes:** Scoring outputs are staging/review artifacts, not formal records.

---

## Evidence Signals Schema

| Option | Description | Selected |
|--------|-------------|----------|
| Base signals + rubric-ready signals + provenance links | Preserve enough structure for scoring, audit, batch comparison, and regression tests. | ✓ |
| Final scores and rationale only | Simple but weak traceability. | |
| Complete claims / visual interpretation | Too heavy; overlaps Phase 13 and advanced visual intelligence. | |
| Reuse upstream artifacts only | Avoids duplication but makes scoring hard to debug. | |

**User's choice:** 1  
**Notes:** Signals include text, visual, topic, provenance, and uncertainty signals.

---

## Scoring Rubric

| Option | Description | Selected |
|--------|-------------|----------|
| 10-point three-score rubric | Separate relevance, quality, and read priority; quality uses rubric subitems. | ✓ |
| 1-5 score rubric | Simpler but too coarse for batch sorting. | |
| Single composite score | Mixes different concepts and can mislead. | |
| Freeform LLM score | Flexible but not auditable. | |

**User's choice:** 1  
**Notes:** Six points and above means AI initial recommendation to pass into supervision queue, not formal approval.

---

## Visual Evidence Use

| Option | Description | Selected |
|--------|-------------|----------|
| Weighted but degradable signal | Visual candidates can affect scoring, but low-confidence or conflicting evidence must degrade/route to review. | ✓ |
| Display only | Safe but underuses Phase 8.1 outputs. | |
| Strong automatic visual judgment | Too aggressive and could amplify OCR or visual-analysis errors. | |
| Human-confirmed visual evidence only | Too low automation for Phase 9. | |

**User's choice:** 1  
**Notes:** Visual evidence can strengthen quality and read-priority signals but remains staging/review material.

---

## Human Review Override

| Option | Description | Selected |
|--------|-------------|----------|
| AI automatic judgment + user supervision/traceability + later correction | AI can judge at staging/review layer; humans supervise key items and can correct later with history. | ✓ |
| Everything requires human confirmation | Safest but too manual for the desired automation level. | |
| AI score threshold auto-approves | Too risky and could bypass formal gates. | |
| AI score only, no human override | Not suitable for research supervision. | |

**User's choice:** Enhanced option 1  
**Notes:** User clarified that AI should be able to judge automatically, while humans can supervise, trace, and later change scores/decisions if a paper is found problematic.

---

## CLI And Outputs

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal loop commands + scoring/review packet outputs | Implement `rsa score ...`, read-only validate/status, campaign summary, and review/correction command. | ✓ |
| Single-paper only | Safer but leaves Phase 8.2 unconnected. | |
| Full batch review workspace | Too large; belongs in Phase 11/12. | |
| YAML only | Machine-friendly but weak Chinese user review experience. | |

**User's choice:** 1  
**Notes:** Required outputs are `P###_scoring.yaml`, `P###_review_packet.md`, and `C###_scoring_summary.yaml`.

---

## Agent Discretion

- Exact internal module split, dataclass names, helper functions, and scoring-formula details can be decided during planning.
- The implementation must preserve Chinese-first user-facing content, local Markdown/YAML storage, fail-closed behavior, and formal write gates.

## Deferred Ideas

- Workflow orchestrator remains Phase 10.
- Complete campaign and batch review remains Phase 11.
- Local review workspace remains Phase 12.
- Claim-level citation hardening remains Phase 13.
- Advanced figure intelligence remains deferred.
