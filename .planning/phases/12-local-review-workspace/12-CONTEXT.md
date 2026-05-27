# Phase 12: Local Review Workspace - Context

**Gathered:** 2026-05-27
**Status:** Ready for planning
**Source:** gsd-discuss-phase 12, consolidated from `12-DISCUSSION-WIP.md`

<domain>
## Phase Boundary

Phase 12 builds the local review workspace for RSA v2. The workspace is a Chinese-first supervision surface for campaign queues, blocked/partial workflow states, reading drafts, visual evidence candidates, AI scoring packets and formal write requests.

This phase is not a web server, not a background worker and not a formal write path. It generates a local static review package plus machine-readable manifest so the user can monitor automated literature work, open supporting files and execute validated CLI commands when intervention is needed.

The product principle is:

- 自动化负责阅读、分析、评分、队列整理和 review packet 生成。
- 用户主要负责监管异常、人工纠正和 formal gate 前的最终批准。
- 所有用户可见说明、错误原因、下一步建议和操作提示必须中文优先。
- English field names, CLI flags and schema keys stay stable, but user-facing contexts must explain them in Chinese.

</domain>

<decisions>
## Implementation Decisions

### D-01: Local workspace shape

- Decision: `static_package_plus_cli`.
- Phase 12 first generates a local static review package using HTML/Markdown.
- The package centralizes review queue, workflow report, reading draft, visual evidence, AI scoring and formal write request materials.
- The static package is for viewing and navigation only; state changes still go through CLI commands.
- Keep interfaces that can later be reused by a local Web UI: `review_object`, `artifact_link`, `decision_action` and `review_workspace_manifest`.
- The static package and future Web UI must not bypass the formal write gate.

### D-02: Unified review entry

- Decision: `unified_review_entry`.
- Phase 12 provides one supervision entry that aggregates campaign queue items, blocked/partial items, reading drafts, visual evidence, scoring packets and formal write requests.
- The goal is to let the user open one place and see what needs attention.
- This entry is for supervision and navigation; `review_decision` is not formal approval.

### D-03: Urgency-first grouping

- Decision: `urgency_first_grouping`.
- Review objects are grouped by handling urgency, not by internal module or paper number first.
- Default group order:
  1. `formal_write_request`
  2. `blocked`
  3. `partial`
  4. `needs_followup`
  5. `low_confidence`
  6. `high_priority`
  7. `auto_triaged`
  8. `completed_staging`
- Grouping affects display only and must not change campaign/workflow/scoring state semantics.

### D-04: Review object display fields

- Decision: `summary_evidence_links_action`.
- Each review object displays a concise summary, evidence links and suggested next action.
- Default fields:
  - Title or object name.
  - Object type and current status.
  - Chinese reason, risk, blocked reason or repair hint.
  - AI advice, score, confidence or priority when available.
  - Evidence links such as reading note, workflow report, visual evidence, scoring packet, campaign queue, metadata request and formal write request.
  - Suggested next step and executable CLI command.
- List pages must not inline full YAML/Markdown bodies; full content is opened through links.

### D-05: Actions are shown, not executed

- Decision: `show_commands_execute_via_cli`.
- The static package shows explicit CLI commands. The user executes them in the terminal.
- Examples:
  - `rsa campaign queue review C001 --item QI001 --decision accepted --reviewer zxy`
  - `rsa score review P001 --final-decision approved --reviewer zxy --reason "..."`
  - `rsa formal apply-note --source-note P001 --human-confirmed --confirmed-by zxy`
- Do not add page-side script execution, direct file mutation or UI calls that bypass CLI validation.

### D-06: Workspace manifest

- Decision: `generate_workspace_manifest`.
- Generate a machine-readable `review_workspace_manifest.yaml` in addition to static HTML/Markdown pages.
- Manifest contents include generation time, target campaign/paper, page paths, review objects, group/status/risk flags, artifact links, suggested CLI commands and schema/version.
- The manifest supports tests, future Web UI and future refresh automation.

### D-07: Campaign and paper entrypoints

- Decision: `campaign_and_paper_entrypoints`.
- Support both:
  - `rsa review build --campaign C001`
  - `rsa review build --paper P001`
- Campaign entry aggregates batch review queue, run ledger, batch report, metadata intake and formal write request.
- Paper entry aggregates metadata, source ledger, reading note, workflow report, visual evidence, scoring packet and related formal request links.
- Phase 12 does not auto-refresh in the background; the user reruns `build` to refresh.

### D-08: Page structure

- Decision: `index_group_detail_pages`.
- Static package uses three layers:
  - `index.html`: overview, urgent items, stats, generated time and suggested actions.
  - `groups/*.html`: one page per urgency group.
  - `objects/*.html`: one page per review object.
- The same structure should map cleanly to future Web UI routes.

### D-09: Relative links and missing markers

- Decision: `relative_links_with_missing_markers`.
- Links should use project-relative or workspace-relative paths rather than absolute paths.
- Missing evidence files must be explicitly marked in Chinese, for example: `文件缺失`, `需要重新生成`, `需要补充授权 PDF`, `需要重新运行 visual extract`.
- Do not copy all PDFs/screenshots/crops into the workspace by default.

### D-10: Actions checklist

- Decision: `generate_actions_checklist`.
- Generate an actions checklist on the index page and object detail pages.
- Checklist entries include pending object, suggested action, Chinese reason, formal gate flag, suggested order and copyable CLI command.
- The checklist is advisory only; it must not execute commands or mutate state.

### D-11: Notes through CLI

- Decision: `note_via_cli_not_inline_edit`.
- Phase 12 v1 does not support inline editing inside static pages.
- User notes and reasons are recorded through existing CLI fields such as `--reason` and `--reviewer`.
- A future `rsa review note ...` command may be added, but it is not part of this phase.

### D-12: Review command group and fixed output root

- Decision: `rsa_review_build_fixed_workspace_root`.
- Add `rsa review build`.
- Output root is `01_literature/review_workspace/`.
- Future-compatible auxiliary commands:
  - `rsa review status`
  - `rsa review open`
  - `rsa review clean`
- Do not hide this under `campaign` or `workflow`, because both campaign and paper entrypoints are first-class.

### D-13: Rebuild and cleanup policy

- Decision: `overwrite_generated_keep_user_records`.
- Re-running `rsa review build` overwrites generated HTML, manifest, group pages and object pages.
- Preserve user records such as review history, user notes, manual decision records and future workspace-local audit notes.
- Generated files include `index.html`, `groups/*.html`, `objects/*.html` and generated manifest.

### D-14: Lightweight helper commands

- Decision: `include_lightweight_status_open_clean`.
- Add lightweight helpers:
  - `rsa review status`: show latest workspace target, stats and index path.
  - `rsa review open`: open latest `index.html`.
  - `rsa review clean --generated-only`: remove generated HTML/manifest while preserving user records.
- Do not add a server, auto-refresh or page-side state mutation.

### D-15: Discussion closure

- Decision: `phase12_discussion_closed`.
- No additional Phase 12 gray areas are needed before planning.
- Keep the scope deliberately small: static supervision package, manifest, CLI entrypoints and tests.

</decisions>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Current Phase

- `.planning/phases/12-local-review-workspace/12-DISCUSSION-WIP.md` - live discussion record that produced D-01 through D-14.
- `.planning/ROADMAP.md` - v2 phase order and Phase 12 goal.
- `.planning/REQUIREMENTS.md` - milestone requirement traceability.
- `.planning/LANGUAGE-POLICY.md` - Chinese-first user-facing policy.

### Existing Implementation

- `src/rsa_cli/cli.py` - argparse style, command groups and Chinese CLI output.
- `src/rsa_cli/config.py` - project root and directory properties.
- `src/rsa_cli/skeleton.py` - workspace directory creation.
- `src/rsa_cli/campaign.py` - campaign queue, run ledger, metadata intake and review queue.
- `src/rsa_cli/workflow.py` - single-paper workflow run/report/status artifacts.
- `src/rsa_cli/scoring.py` - scoring YAML, review packet and human review records.
- `src/rsa_cli/notes.py` - reading note paths and validation.
- `src/rsa_cli/visual.py` - visual evidence candidate paths and validation.
- `README.md` - public-facing command and workflow documentation.

</canonical_refs>

<specifics>
## Specific Ideas

- Prefer deterministic local Markdown/YAML/HTML generation. Do not introduce a web framework for Phase 12.
- Prefer one `review_workspace_manifest.yaml` as the machine-readable single source for generated static pages.
- Keep generated HTML utilitarian: overview, group pages, object pages and command snippets.
- Missing file markers are a feature, not a failure; they help users see what needs regeneration.
- The workspace can be rebuilt at any time and must preserve non-generated user records.

</specifics>

<deferred>
## Deferred Ideas

- Local Web UI server and live refresh.
- Inline editing in the browser.
- Workspace-level persistent note command such as `rsa review note`.
- Background worker and scheduled automation. This belongs to Phase 14.
- Complex dashboards, analytics or graph visualization.
- Any formal write path that bypasses existing `rsa formal ... --human-confirmed` commands.

</deferred>

---

*Phase: 12-local-review-workspace*
*Context gathered: 2026-05-27*
