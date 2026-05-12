# Phase 4 Discussion Log

**Phase:** 04 - Reading Note Workflow
**Date:** 2026-05-12
**Mode:** agent-decided, no subagents

## Areas Considered

| Area | Decision | Result |
|------|----------|--------|
| Authorized input | Require formal metadata plus existing local/user-provided/authorized source file. | Adopted |
| Missing source behavior | Record status in `pdf_acquisition_report.md`; do not create a note. | Adopted |
| Note schema | Separate source-grounded claims, short quotes, agent summary and human decision. | Adopted |
| Approval boundary | `approved` requires human confirmation fields. | Adopted |
| Formal influence | Use `rsa formal apply-note` with confirmation; no automatic formal writes. | Adopted |

## Deferred

- Automatic PDF parsing and summarization.
- Batch reading-note generation.
- Web UI review surface.
