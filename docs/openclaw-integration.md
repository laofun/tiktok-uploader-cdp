# OpenClaw Integration Guide

This guide describes how OpenClaw should orchestrate `tiktok-uploader-cdp` safely.

For a full phase-by-phase internals walkthrough, read `docs/full-system/00-index.md`.
For visual flowcharts, read `docs/full-system/11-mermaid-flows.md`.

## Preconditions

1. Browser is launched with CDP enabled (example endpoint `http://127.0.0.1:9222`).
2. Target TikTok account is already logged in by user.
3. Upload file exists at an absolute path.
4. OpenClaw passes a unique `request_id` per job.

## Recommended Invocation

```bash
uv run tiktok-uploader-cdp \
  --cdp-url http://127.0.0.1:9222 \
  --video /abs/path/video.mp4 \
  --description "caption" \
  --visibility friends \
  --comment \
  --duet \
  --stitch \
  --cover /abs/path/cover.jpg \
  --request-id job-123 \
  --screenshot-dir /tmp/tiktok-uploader-cdp
```

Use `--dry-run` for preflight checks before real publish.
Use `--schedule "YYYY-MM-DD HH:MM"` (UTC) only when a delayed post is needed.
Use `--config /abs/path/config.toml` when you maintain selectors externally.

## Decision State Machine

1. Parse JSON output.
2. If `ok=true`, mark job success.
3. If `ok=false`, branch by `error_code`:
- `captcha_detected`: set job state `WAIT_HUMAN_CHALLENGE`, notify operator, retry only after manual completion.
- `rate_limited`: set state `WAIT_BACKOFF`, retry using delayed exponential backoff.
- `network_error`: set state `WAIT_BACKOFF`, verify connectivity, retry with backoff.
- `not_logged_in`: set state `WAIT_USER_LOGIN`, notify operator to re-login in the same browser profile.
- `content_rejected`: set state `NEEDS_CONTENT_REVISION`, do not auto-retry without content change.
- `ui_changed`: set state `NEEDS_MAINTENANCE`, create engineering alert with screenshot and step trace.
- `cdp_connect_failed` or `no_browser_context`: set state `ENV_FIX_REQUIRED`, restart browser or repair CDP launch options.
- `processing_stuck`: allow one delayed retry; if repeated, escalate for platform-side investigation.
- `upload_timeout` or `post_failed`: allow one automatic retry, then escalate to human review.
- `unknown_error`: direct escalate to human review.
- `invalid_schedule`: mark as input validation failure; do not retry without schedule correction.

## Logging Requirements

Store at least:

- `request_id`
- `error_code`
- `recommended_action`
- `retry_hint`
- `steps`
- `artifacts.error_screenshot` (if present)

For restriction scenarios, inspect step names:
- `toggle_content_check`
- `continue_content_modal`
- `retry_post_after_content_modal`

## Operational Guardrails

- Do not auto-retry infinite loops.
- Do not override `ui_changed` into generic retry.
- Keep parser tolerant to extra fields but strict on stable keys.
- Keep fallback policy declarative and driven by `error_code` + `retry_hint`.
