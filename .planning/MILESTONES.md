# Milestones

## v1.0 Local Harness

**Status:** shipped  
**Shipped:** 2026-05-13  
**Branch:** `v1phase3`  
**Tag:** `v1.0`  
**Phases:** 5  
**Plans:** 14  
**Commits before archive:** 49  
**Timeline:** 2026-05-11 to 2026-05-13  
**Open artifact audit:** `gsd-sdk query audit-open` was unavailable in this local GSD install; no open audit artifacts were found by file scan.

### Delivered

v1.0 delivered a local-first research agent harness for auditable literature workflows, with formal metadata gates, bounded research rounds, candidate staging, literature maps, reading notes, formal write guardrails, trace summaries and deterministic eval fixtures.

### Key Accomplishments

1. Created the reusable project skeleton, topic profile system and CLI entry point.
2. Built metadata-first paper records and `paper_index.md` consistency checks.
3. Added staged candidate verification before formal admission.
4. Connected research rounds to literature maps, gap reports and formal write requests.
5. Added authorized reading notes and formal note-derived write gates.
6. Added local eval fixtures, baselines and trace summaries for harness hardening.

### Archives

- Roadmap archive: `.planning/milestones/v1.0-ROADMAP.md`
- Requirements archive: `.planning/milestones/v1.0-REQUIREMENTS.md`
- Retrospective: `.planning/RETROSPECTIVE.md`
- v2 discussion draft: `.planning/v2-DISCUSSION.md`

### Known Gaps Accepted At Close

- No dedicated milestone audit file was produced before archive.
- v1 evals are deterministic harness checks, not semantic LLM grading.
- v1 does not include Web UI, scholarly API integration, citation manager sync or large-scale batch processing.
