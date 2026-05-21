# Phase 09 Research: Evidence Signals & AI Scoring

**Research date:** 2026-05-21  
**Mode:** Inline local research, no subagents  
**Scope:** Phase 9 planning only; no implementation performed in this research pass

## Research Question

How should RSA add AI-assisted relevance, quality and read-priority scoring while preserving the project's Chinese-first UX, staging/formal boundary, local Markdown/YAML persistence, and traceable evidence chain from Phase 8, Phase 8.1 and Phase 8.2?

## Local Code Findings

### Existing Inputs

- `src/rsa_cli/reading_draft.py` already produces `P###_reading_note.md`, source-grounded claims, short quotes, uncertain points, asset suggestions, source cache links, prompt packets and Chinese review packets.
- Phase 8 `agent_review_score_10` is explicitly a reading-draft readiness score. It must not be reused as paper relevance, quality or reading priority.
- `src/rsa_cli/visual.py` already writes `01_literature/assets/P###/visual_evidence_candidates.yaml`, local-only crops, local-only visual context packets, page/region/source trace, candidate statuses, confidence levels and evidence levels.
- `src/rsa_cli/campaign.py` already writes `01_literature/campaigns/C###.yaml` with imported candidate rows, lightweight deduplication and optional formal metadata links.
- `src/rsa_cli/cli.py` already uses grouped argparse subcommands, Chinese-first help text, and read-only `validate` / `status` command patterns.
- `src/rsa_cli/config.py` has no `scores_root` yet.
- `src/rsa_cli/skeleton.py` creates core literature directories but has no `01_literature/scores/` yet.

### Existing Persistence Pattern

RSA uses local text artifacts for reviewable state:

- machine-readable YAML for structured state;
- Markdown packets for Chinese user supervision;
- local-only binary or large artifacts under ignored directories;
- formal writes isolated behind explicit formal commands and human confirmation.

Phase 9 should follow the same pattern:

- scoring source of truth: `01_literature/scores/P###_scoring.yaml`;
- human-facing review aid: `01_literature/scores/P###_review_packet.md`;
- campaign summary: `01_literature/campaigns/C###_scoring_summary.yaml`;
- no automatic writes to `metadata/`, `paper_index.md`, `literature_map.md`, `agent_research_notes.md` or reading note frontmatter.

## Design Conclusions

### 1. Add a Dedicated Scoring Module

Create `src/rsa_cli/scoring.py` instead of mixing scoring into `reading_draft.py`, `visual.py` or `campaign.py`.

Rationale:

- keeps Phase 8 readiness review separate from Phase 9 paper scoring;
- gives Phase 10 workflow and Phase 11 campaign review a stable callable interface;
- keeps formal write boundaries easier to audit;
- allows schema tests and deterministic scoring tests without needing actual LLM calls.

### 2. Build Evidence Signals Before Scores

The scoring pipeline should first build `evidence_signals`, then derive scores and decisions.

Minimum signal groups:

- text signals from reading note: `problem_signal`, `method_signal`, `experiment_signal`, `dataset_signal`, `metric_signal`, `finding_signal`, `limitation_signal`;
- visual signals from visual candidates: `visual_candidate_ids`, `visual_type`, `evidence_level`, `confidence`, `degraded_reason_zh`;
- topic signals: `topic_profile`, `priority_question`, Chinese explanation;
- provenance links: metadata, reading note, source chunks, source ledger, visual candidates, visual context packets and campaign item when relevant;
- uncertainty signals: abstract-only evidence, missing full text, low-confidence visual evidence, OCR partial success, and text/visual conflicts.

This makes scoring auditable and gives later regression tests a stable substrate.

### 3. Use Separate 0-10 Scores

Keep three scores:

- `ai_relevance_score_10`: fit to topic profile, priority question and research scenario;
- `ai_quality_score_10`: rubric-backed paper quality;
- `ai_read_priority_score_10`: practical reading priority for queue sorting.

Quality must use rubric subitems rather than a freeform single number:

- `method_clarity`;
- `experiment_strength`;
- `comparison_fairness`;
- `reproducibility_signals`;
- `limitation_awareness`.

Thresholds are staging semantics only:

- `>= 8`: priority reading / key review;
- `6-7`: recommend pass into supervision queue;
- `< 6`: defer or low priority.

### 4. Make Visual Evidence Weighted And Degradable

Visual evidence should strengthen score confidence only when it is traceable and high-confidence.

Rules:

- missing visual candidates do not block scoring;
- low-confidence or partial OCR visual candidates lower `score_confidence` and add Chinese limitation notes;
- text/visual conflicts produce `ai_review_decision: needs_review`;
- unconfirmed OCR or LLM visual interpretation never enters formal records.

### 5. Human Review Is Supervision, Not Formal Approval

Phase 9 should support automatic staging decisions while preserving review history:

- `ai_review_decision`: `recommend_pass`, `recommend_defer`, `needs_review`, `blocked`;
- `human_review`: current human supervision state;
- `review_history`: append-only trace of manual corrections and score overrides.

`recommend_pass` must not mean `approved`. Formal approval remains out of Phase 9.

### 6. Campaign Scoring Reuses Single-Paper Logic

`rsa score campaign C001` should iterate over linked formal metadata items and call the same scoring logic used by `rsa score P001`.

Campaign scoring may write a summary under the campaign directory, but Phase 9 must not become Phase 11's full batch review system.

## Implementation Risks

### Risk: Scoring Appears To Be A Formal Academic Judgment

Mitigation:

- use `ai_review_decision` staging labels;
- write clear Chinese review packet wording;
- do not add formal write commands;
- do not write Phase 9 outputs into formal records.

### Risk: Visual Evidence Overweights Weak OCR Or Unconfirmed LLM Analysis

Mitigation:

- score confidence must degrade for weak/partial visual evidence;
- visual signal records must include candidate id, evidence level, confidence and Chinese limitation;
- text/visual conflicts force `needs_review`.

### Risk: LLM Dependency Blocks Deterministic Tests

Mitigation:

- implement deterministic schema extraction and scoring heuristics first;
- keep any future LLM scoring behind config/preflight and fail-closed behavior;
- use local fixture YAML/Markdown tests for Phase 9 acceptance.

### Risk: Campaign Scoring Duplicates Future Phase 11

Mitigation:

- Phase 9 campaign command only loops through linked papers and writes a summary;
- no queue UI, no full batch operations, no workflow orchestration, no formal writes.

## Recommended Plan Split

1. **09-01 Scoring Schema, Config And Skeleton**
   - Add `scores_root`, skeleton directory, scoring schema helpers and validation primitives.
2. **09-02 Single-Paper Evidence Signals And Scoring**
   - Implement `rsa score P001`, evidence signal construction, score calculation, review packet and human correction history.
3. **09-03 CLI And Campaign Scoring Integration**
   - Wire CLI group, campaign scoring summary, Chinese docs and regression coverage.

## Verification Strategy

Minimum tests:

- scoring YAML schema validation;
- missing metadata / missing reading note fail closed with Chinese errors;
- missing visual candidates degrade but do not block;
- low-confidence visual candidates degrade score confidence;
- text/visual conflicts set `needs_review`;
- `validate` and `status` are read-only;
- `review` updates `human_review` and appends `review_history` without formal writes;
- campaign scoring reuses single-paper outputs and writes `C###_scoring_summary.yaml`;
- CLI help/output remains Chinese-first.

Final commands:

- `python -m pytest tests/test_scoring.py tests/test_cli.py tests/test_campaign.py tests/test_skeleton.py -q`
- `python -m pytest -q`

