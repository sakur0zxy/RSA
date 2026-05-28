# Phase 13 Discussion Log

## Completed Decisions

1. Phase 13 focuses on writing safety and hardening, not automatic paper writing.
2. Claim-level citation checks are applied to staging/review artifacts and produce review guidance only.
3. Safety audit files live under `01_literature/safety/`.
4. Safety status values are `passed | needs_review | blocked | missing`.
5. Campaign failure monitoring covers the Phase 11 failure modes listed in `V2-WRITE-02`.
6. Drift checks stay deterministic in v1 and reserve interfaces for later LLM-based evaluation.
7. Formal write gate remains the only path into formal records.
8. All user-visible content is Chinese-first; English field names stay stable.

## Reserved Interfaces

- `llm_claim_review`
- `citation_graph`
- `advanced_figure_claim_binding`
- `paragraph_id`
- `sentence_id`
- `figure_id`
- `table_id`
- future `confidence` and reviewer override fields

## Deferred

- Full thesis prose generation.
- LLM-based claim truth adjudication.
- Advanced figure intelligence and curve/table reconstruction.
- Background worker and scheduled automation, which remain Phase 14.
