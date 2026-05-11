---
phase: 02
slug: literature-records-pipeline
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-11
---

# Phase 02 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_metadata.py tests/test_index.py tests/test_cli.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_metadata.py tests/test_index.py tests/test_cli.py -q`
- **After every plan wave:** Run `python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 02-01 | 1 | META-01, META-03 | T-02-01 / T-02-02 | Formal metadata requires verified + human confirmation and stable P### IDs | unit/cli | `python -m pytest tests/test_metadata.py tests/test_cli.py -q` | yes | pending |
| 02-02-01 | 02-02 | 2 | SRCH-01, SRCH-02 | T-02-04 | Candidate review stays in staging and explains English fields in Chinese | unit/template | `python -m pytest tests/test_templates.py tests/test_cli.py -q` | Wave 2 creates if missing | pending |
| 02-03-01 | 02-03 | 3 | META-02, META-03 | T-02-03 | paper_index.md is generated/validated from metadata and regenerate is explicit | unit/cli | `python -m pytest tests/test_index.py tests/test_cli.py -q` | Wave 3 creates if missing | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

Existing pytest infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All Phase 2 behaviors have automated verification. Human approval is represented by explicit CLI flags and metadata fields, not by a manual-only test.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
