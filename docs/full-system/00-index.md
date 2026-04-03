# TUC Full System - Detailed Index

This document set describes the full runtime of `tiktok-uploader-cdp` in a machine-operator style.

## Scope

- Codebase: `src/tiktok_uploader_cdp/*`
- Runtime mode: CDP-first, already logged-in browser, no cookie injection
- Consumer: OpenClaw/CrawBot and human maintainers

## Reading Modes

### Mode A: End-to-end understanding

1. `01-component-map.md`
2. `02-runtime-sequence.md`
3. `03-step-connect-and-navigation.md`
4. `04-step-attach-video.md`
5. `05-step-interactivity-visibility-description.md`
6. `06-step-cover-schedule.md`
7. `07-step-post-and-content-modal.md`
8. `08-error-handling-and-retry.md`
9. `09-debug-protocol.md`
10. `10-maintenance-checklist.md`
11. `11-mermaid-flows.md`

### Mode B: Production incident triage

1. `02-runtime-sequence.md` (find failing phase)
2. `08-error-handling-and-retry.md` (decide retry/fallback)
3. `09-debug-protocol.md` (collect evidence)
4. `10-maintenance-checklist.md` (patch strategy)
5. `11-mermaid-flows.md` (quick visual map)

### Mode C: Selector drift / UI change work

1. `04-step-attach-video.md`
2. `06-step-cover-schedule.md`
3. `07-step-post-and-content-modal.md`
4. `10-maintenance-checklist.md`
5. `11-mermaid-flows.md`

## Artifact References

- Main config: `src/tiktok_uploader_cdp/config.toml`
- CLI contract: `docs/cli-reference.md`
- Response schema: `docs/json-schema.md`
- Error catalog: `docs/error-codes.md`
- Scenarios matrix: `docs/upload-scenarios.md`
- OpenClaw integration guide: `docs/openclaw-integration.md`
