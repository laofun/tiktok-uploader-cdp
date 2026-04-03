# Error Handling and Retry Semantics

## Response Contract Summary

Every run returns one JSON object containing:

- `ok`
- `message`
- `error_code`
- `recoverable`
- `recommended_action`
- `retry_hint`
- `steps[]`
- `artifacts{}`

## Error Origin Buckets

### Bucket 1 - Environment bootstrap

- `cdp_connect_failed`
- `no_browser_context`
- `not_logged_in`

Policy:

- Usually recoverable after environment fix.
- Orchestrator should not hot-loop retries.

### Bucket 2 - Platform defense / temporary platform state

- `captcha_detected`
- `rate_limited`
- `network_error`

Policy:

- Require human handoff or backoff retry policy.

### Bucket 3 - Input correctness

- `file_not_found`
- `invalid_schedule`

Policy:

- Non-retry until input corrected.

### Bucket 4 - UI drift / selector staleness

- `ui_changed`

Policy:

- Disable auto-retry.
- Collect DOM evidence.
- Update config selectors first.

### Bucket 5 - Publish path instability

- `processing_stuck`
- `upload_timeout`
- `post_failed`

Policy:

- Retry once (or bounded retries) then escalate.

### Bucket 6 - Policy hard block

- `content_rejected`

Policy:

- No blind retry.
- Content/caption/media adjustment required.

## Retry Hint Mapping (effective contract)

- `retry_after_human_step`: captcha/login gate.
- `retry_after_environment_fix`: CDP/login bootstrap issues.
- `retry_with_backoff`: rate/network transient issues.
- `retry_once`: timeout/stuck/post-click transient branch.
- `do_not_retry_without_input_change`: invalid schedule or missing file.
- `do_not_retry_until_selector_update`: UI drift branch.
- `do_not_retry_without_content_change`: policy rejection.
- `do_not_retry_without_human_review`: unknown terminal branch.

## Step-level Failure Marker

On any failure, final step includes:

- `name=failed`
- `ok=false`
- `detail=<exception text>`
- `error_code=<stable code>`

This allows OpenClaw to map both stage and code.
