# JSON Schema

Current response schema version: `1.1.0`

## Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `ok` | boolean | yes | Final status of request |
| `message` | string | yes | Human-readable short summary |
| `error_code` | string or null | yes | Stable machine code for failure classification |
| `recoverable` | boolean | yes | Indicates whether retry/fallback can be meaningful |
| `recommended_action` | string | yes | Suggested next action for orchestrator |
| `retry_hint` | string | yes | Retry policy hint |
| `schema_version` | string | yes | Schema compatibility marker |
| `request_id` | string or null | yes | Caller-provided job id passthrough |
| `created_at_utc` | string | yes | ISO8601 UTC timestamp |
| `steps` | array | yes | Step-level execution diagnostics |
| `artifacts` | object | yes | Generated files (screenshots, traces) |
| `metadata` | object | yes | Additional context fields |

## Step Object

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Deterministic step name |
| `ok` | boolean | yes | Step pass/fail |
| `detail` | string | yes | Step message |
| `error_code` | string or null | yes | Error code if this step failed |

## Example: Success

```json
{
  "ok": true,
  "message": "Upload completed",
  "error_code": null,
  "recoverable": false,
  "recommended_action": "none",
  "retry_hint": "none",
  "schema_version": "1.1.0",
  "request_id": "job-123",
  "created_at_utc": "2026-04-02T10:20:00+00:00",
  "steps": [
    {"name": "connect_cdp", "ok": true, "detail": "connected", "error_code": null},
    {"name": "goto_upload", "ok": true, "detail": "https://www.tiktok.com/creator-center/upload?lang=en", "error_code": null}
  ],
  "artifacts": {},
  "metadata": {"final_url": "https://www.tiktok.com/creator-center/upload?lang=en"}
}
```

## Example: Captcha Failure

```json
{
  "ok": false,
  "message": "Captcha or anti-bot challenge detected",
  "error_code": "captcha_detected",
  "recoverable": true,
  "recommended_action": "handoff_to_human_solver_and_resume",
  "retry_hint": "retry_after_human_step",
  "schema_version": "1.1.0",
  "request_id": "job-456",
  "created_at_utc": "2026-04-02T10:25:00+00:00",
  "steps": [
    {"name": "connect_cdp", "ok": true, "detail": "connected", "error_code": null},
    {"name": "failed", "ok": false, "detail": "Captcha or anti-bot challenge detected", "error_code": "captcha_detected"}
  ],
  "artifacts": {"error_screenshot": "/tmp/tiktok-uploader-cdp/error_job-456_20260402T102500Z.png"},
  "metadata": {}
}
```

## Compatibility Notes

- OpenClaw parser should branch by `schema_version`.
- Minor version bumps (e.g. `1.1.x`) can add optional fields but should not remove stable keys.
- Major version bump is required for breaking changes.
