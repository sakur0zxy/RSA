---
phase: 01
slug: harness-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-11
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_config.py tests/test_profiles.py tests/test_skeleton.py tests/test_rounds.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_config.py tests/test_profiles.py tests/test_skeleton.py tests/test_rounds.py -q`
- **After every plan wave:** Run `python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DOCS-01 | T-01-01 | Local-only files ignored | unit | `python -m pytest tests/test_skeleton.py -q` | W0 | pending |
| 01-02-01 | 02 | 2 | PROF-01 | T-02-01 | YAML uses safe_load | unit | `python -m pytest tests/test_profiles.py -q` | W0 | pending |
| 01-02-02 | 02 | 2 | PROF-02 | T-02-02 | Invalid profiles fail safely | unit | `python -m pytest tests/test_profiles.py -q` | W0 | pending |
| 01-03-01 | 03 | 3 | ROUND-01 | T-03-01 | Round limits enforced | integration | `python -m pytest tests/test_rounds.py -q` | W0 | pending |
| 01-03-02 | 03 | 3 | DOCS-01 | T-03-02 | CLI help and docs present | smoke | `python -m pytest tests/test_cli.py -q` | W0 | pending |

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — package metadata, console script, pytest configuration
- [ ] `tests/test_config.py` — config merge expectations
- [ ] `tests/test_profiles.py` — profile schema validation expectations
- [ ] `tests/test_skeleton.py` — directory and ignore-rule expectations
- [ ] `tests/test_rounds.py` — round naming and candidate cap expectations
- [ ] `tests/test_cli.py` — CLI smoke expectations

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SAR starter profile content is faithful to old plan | PROF-01 | Automated schema cannot judge research-topic completeness | Read `01_literature/topic_profiles/sar_noncontinuous_aperture.yaml` against old plan topics before Phase 1 sign-off |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
