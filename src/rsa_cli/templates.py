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


STARTER_TOPIC_PROFILE = """topic_id: sar_noncontinuous_aperture
topic_name: SAR noncontinuous aperture and distributed multi-aspect imaging
core_keywords:
  - noncontinuous aperture SAR
  - sparse aperture SAR
  - wide-angle SAR
  - wide-aperture SAR
  - multi-aspect SAR
  - subaperture imaging
  - distributed SAR
  - cross-channel coherence
  - phase-history recovery
  - ghost artifact suppression
  - physics-constrained learning
priority_questions:
  - How do noncontinuous aperture gaps affect image focus, sidelobes, and ghost artifacts?
  - Which wide-angle or wide-aperture SAR methods remain reliable with missing aperture support?
  - How do multi-aspect and subaperture formulations connect to distributed SAR collection geometry?
  - What cross-channel coherence constraints are needed for phase-history recovery?
  - Which metrics best expose ghost artifacts, failure boundaries, and reconstruction uncertainty?
  - How can physics-constrained learning support recovery without replacing source-grounded evidence?
important_metrics:
  - impulse response width
  - peak sidelobe ratio
  - integrated sidelobe ratio
  - ghost artifact energy
  - phase consistency
  - cross-channel coherence
  - reconstruction error
  - failure boundary conditions
preferred_sources:
  - IEEE Transactions on Geoscience and Remote Sensing
  - IEEE Transactions on Aerospace and Electronic Systems
  - IEEE Geoscience and Remote Sensing Letters
  - IET Radar Sonar and Navigation
  - official publisher pages
  - author preprints with publisher metadata cross-checks
exclude_scope:
  - optical aperture synthesis without SAR connection
  - unverified blog summaries
  - papers without source metadata sufficient for verification
  - final thesis prose generation
grade_rules:
  A:
    description: Core theory, baseline, or evaluation evidence
    criteria:
      - Directly addresses noncontinuous aperture, wide-angle, multi-aspect, or distributed SAR
      - Provides reusable equations, algorithms, datasets, metrics, or failure analysis
      - Source metadata can be verified from a reliable venue or official page
  B:
    description: Useful support for background or comparison
    criteria:
      - Addresses adjacent SAR imaging, sparse reconstruction, phase recovery, or coherence constraints
      - Helps define terminology, baselines, or metric choices
  C:
    description: Peripheral or low-priority background
    criteria:
      - Mentions relevant concepts but lacks direct evidence for this topic profile
  Reject:
    description: Out of scope or unsafe for formal records
    criteria:
      - Not SAR-relevant
      - Cannot be verified from reliable metadata
      - Encourages unsupported claims or unauthorized PDF handling
required_outputs:
  - search_candidates.md
  - verification_review.md
  - final_round_summary.md
  - literature_map.md
"""
