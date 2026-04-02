# tiktok-uploader-cdp

CDP-first TikTok uploader for automation systems such as OpenClaw.

## Design Goals

- Connect to an already logged-in browser over CDP.
- Never inject cookies or auto-login.
- Return structured, machine-readable errors for orchestrators.
- Detect high-impact states early (captcha, UI drift).

## Quick Start

```bash
uv sync --all-groups
uv run playwright install
uv run tiktok-uploader-cdp \
  --cdp-url http://127.0.0.1:9222 \
  --video /abs/path/video.mp4 \
  --description "hello" \
  --request-id job-123 \
  --screenshot-dir /tmp/tiktok-uploader-cdp
```

## JSON Output Contract

CLI always prints one JSON object with fields:

- `ok`: boolean
- `error_code`: null or stable code (`captcha_detected`, `ui_changed`, ...)
- `message`: short summary
- `recoverable`: whether retry/fallback is meaningful
- `recommended_action`: next action for OpenClaw
- `retry_hint`: retry policy hint (`retry_once`, `retry_after_human_step`, ...)
- `schema_version`: response schema version for parsers
- `request_id`: passthrough id from caller
- `steps`: per-step diagnostics
- `artifacts`: generated files, e.g. failure screenshot path

## OpenClaw-Oriented Error Semantics

- `captcha_detected`: recoverable; requires human/captcha solver before retry.
- `rate_limited`: recoverable; retry with backoff instead of immediate retry.
- `network_error`: recoverable; verify connectivity, then retry with backoff.
- `content_rejected`: non-recoverable by retry; revise content/metadata first.
- `processing_stuck`: recoverable once; retry once after cooldown then escalate.
- `ui_changed`: non-recoverable automatic retry; selectors likely stale.
- `not_logged_in`: recoverable; user must re-login on the controlled browser.
- `cdp_connect_failed`: recoverable after environment fix (debug port, browser launch).

## Dry Run

Use `--dry-run` to validate CDP connection, login state, captcha state, upload input and description flow, then stop before pressing Post.

## Documentation Map

- `docs/error-codes.md`: canonical error table, retry hints, and actions.
- `docs/json-schema.md`: response schema and examples.
- `docs/openclaw-integration.md`: orchestration flow and decision policy.
- `docs/runbook.md`: operator steps for captcha/UI drift/login/CDP incidents.
- `docs/upload-scenarios.md`: simulation matrix (covered vs missing scenarios).
