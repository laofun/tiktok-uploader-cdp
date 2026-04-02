# Error Codes

This document defines stable error semantics for OpenClaw orchestration.

## Contract Rules

- `error_code` values are stable identifiers. Do not rename existing values.
- New behaviors should introduce new codes instead of overloading old ones.
- `recoverable` and `retry_hint` are orchestration hints, not guarantees.
- `recommended_action` is the default next step for OpenClaw policy.

## Code Table

| error_code | Meaning | recoverable | retry_hint | recommended_action |
|---|---|---|---|---|
| `cdp_connect_failed` | Could not connect to running Chromium-based browser via CDP URL | `true` | `retry_after_environment_fix` | `ensure_debug_port_and_retry` |
| `no_browser_context` | CDP connected, but no context/page available | `true` | `retry_after_environment_fix` | `open_a_normal_browser_tab_and_retry` |
| `not_logged_in` | Browser is on auth-required page (`/login`, `/signup`) | `true` | `retry_after_environment_fix` | `user_login_then_retry` |
| `captcha_detected` | Captcha/anti-bot challenge is visible or text markers are detected | `true` | `retry_after_human_step` | `handoff_to_human_solver_and_resume` |
| `rate_limited` | TikTok temporarily throttled or blocked this upload/session | `true` | `retry_with_backoff` | `backoff_and_retry_later` |
| `content_rejected` | TikTok rejected content due to policy/restriction | `false` | `do_not_retry_without_content_change` | `revise_content_then_retry` |
| `network_error` | Network/connectivity issue detected on page | `true` | `retry_with_backoff` | `check_connectivity_and_retry` |
| `ui_changed` | Known selector set failed, likely TikTok UI drift | `false` | `do_not_retry_until_selector_update` | `update_selectors_then_retry` |
| `file_not_found` | Input video path does not exist | `false` | `do_not_retry_without_input_change` | `fix_input_file_path` |
| `processing_stuck` | Upload was attached but processing never reached post-ready state | `true` | `retry_once` | `wait_then_retry_once_then_human_review` |
| `upload_timeout` | Upload/publish confirmation did not appear in time | `true` | `retry_once` | `retry_once_then_human_review` |
| `post_failed` | Post click or post flow failed unexpectedly | `true` | `retry_once` | `retry_once_then_human_review` |
| `unknown_error` | Unclassified runtime failure | `false` | `do_not_retry_without_human_review` | `human_review` |

## OpenClaw Policy Baseline

- Retry automatically only when `recoverable=true` and `retry_hint` allows it.
- Never loop retries for `ui_changed`.
- For `captcha_detected`, require human/captcha solver gate before retry.
- For `not_logged_in`, require explicit user re-authentication gate.
- Keep audit logs of `request_id`, `error_code`, `recommended_action`, and `artifacts.error_screenshot` when present.
