from __future__ import annotations


TEMPLATE_FILES: dict[str, str] = {
    "topic_profile.yaml": """topic_id: example_topic
topic_name: Example research topic
core_keywords:
  - keyword
priority_questions:
  - What should this research round answer?
important_metrics:
  - evidence quality
preferred_sources:
  - peer-reviewed papers
exclude_scope:
  - unverified claims
grade_rules:
  A:
    description: High-priority candidate
    criteria:
      - Directly answers a priority question
      - Reliable source with reusable evidence
  B:
    description: Useful supporting candidate
    criteria:
      - Related to the topic boundary
      - May support background or comparison
  C:
    description: Low-priority candidate
    criteria:
      - Peripheral or weakly connected
  Reject:
    description: Out of scope or unreliable
    criteria:
      - Not source-grounded
      - Outside the exclude_scope boundary
required_outputs:
  - search_candidates.md
  - final_round_summary.md
""",
    "paper_metadata.yaml": """paper_id: P000
title:
authors: []
year:
venue:
doi:
official_url:
source_reliability:
verification_status: unverified
pdf_status: not_acquired
local_pdf:
assets: []
used_for: []
last_checked:
human_confirmed: false
""",
    "paper_note.md": """# Paper Note: P000

## Source

- Metadata record:
- Local PDF:
- Authorization status:

## Claims and Evidence

## Agent Summary

## Human Decisions
""",
    "round_readme.md": """# Research Round {round_id}

## Objective

{objective}

## Topic

- Profile: `{topic_profile}`
- Max candidates: {max_candidates}
- Allowed tools: {allowed_tools}
- Output policy: {output_policy}
- Approval mode: {approval_mode}
- Campaign ID: {campaign_id}

## Formal Write Policy

This round may stage candidates and notes in `agent_outputs/`, but formal metadata,
maps, notes, and research records require schema validation and human confirmation.

## Local Assets

PDFs belong under the configured `pdfs/` directory. Important screenshots and
result images belong under `assets/P###/` and should be referenced from metadata.
""",
    "final_round_summary.md": """# Final Round Summary: {round_id}

## Status

draft

## Key Findings

## Candidate Decisions

## Formal Record Updates Requested

## Human Confirmation

- Confirmed by:
- Date:
""",
    "search_candidates.md": """# Search Candidates

| Candidate | Source | Why relevant | Status |
|-----------|--------|--------------|--------|
""",
    "verification_review.md": """# Verification Review

| Candidate | DOI/title checked | Official URL | Decision | Reason |
|-----------|-------------------|--------------|----------|--------|
""",
    "map_integration.md": """# Map Integration

| Paper | Priority question | Role | Notes |
|-------|-------------------|------|-------|
""",
    "pdf_acquisition_report.md": """# PDF Acquisition Report

| Paper | PDF status | Local path | Source/authorization | Notes |
|-------|------------|------------|----------------------|-------|
""",
    "reading_batch_report.md": """# Reading Batch Report

| Paper | Reading note | Status | Human approval |
|-------|--------------|--------|----------------|
""",
}


FORMAL_RECORD_FILES: dict[str, str] = {
    "paper_index.md": """# Paper Index

Formal paper records appear here only after metadata validation and human confirmation.
""",
    "literature_map.md": """# Literature Map

Verified papers can be mapped to topic questions, thesis chapters, and research roles here.
""",
    "research_tables.md": """# Research Tables

Use this file for human-reviewed comparison tables and evidence summaries.
""",
    "agent_research_notes.md": """# Agent Research Notes

Agent-generated research notes remain auxiliary until reviewed and promoted by a human.
""",
}
