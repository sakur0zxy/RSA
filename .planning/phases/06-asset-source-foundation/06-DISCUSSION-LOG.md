# Phase 6 Discussion Log: Asset & Source Foundation

**Date:** 2026-05-13
**Mode:** `gsd-discuss-phase` inline, no subagents
**User instruction:** Agent decides; no intermediate prompts.

## Decisions Made

- Phase 6 starts v2 by building source and asset foundations before automatic download or reading.
- Source records use `01_literature/sources/P###.yaml`.
- Asset manifests use `01_literature/assets/P###/manifest.yaml`.
- Binary PDFs and image/result assets remain local-only and gitignored.
- Source/asset manifests are text records and may be tracked.
- Source and asset registration must not update formal metadata automatically.
- CLI commands are `rsa source add|validate|status` and `rsa asset add|validate|status`.

## Deferred

- Automatic source discovery/download moves to Phase 7.
- Auto reading draft moves to Phase 8.
- Evidence extraction and AI scoring move to Phase 9.
- Batch review queue moves to Phase 10.
- Local review UI moves to Phase 12.
