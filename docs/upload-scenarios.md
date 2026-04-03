# Upload Scenario Simulation Matrix

This matrix records simulated upload situations, expected handling, and identified gaps.

## Simulated and Verified (Backed by Tests)

| Scenario | Simulation method | Expected output | OpenClaw handling | Status |
|---|---|---|---|---|
| Captcha appears before upload | monkeypatch `has_captcha=True` | `error_code=captcha_detected`, `recoverable=true`, `retry_hint=retry_after_human_step` | pause job, request human solve, resume | covered |
| UI selector drift | monkeypatch `find_first_visible` to raise `ui_changed` | `error_code=ui_changed`, non-recoverable | stop retry loop, maintenance alert | covered |
| Dry-run validation | run with `dry_run=True` | `ok=true`, includes `dry_run_stop` step | preflight pass, safe to schedule real run | covered |
| Not logged in | monkeypatch `is_login_required=True` | `error_code=not_logged_in` | wait user login then retry | covered |
| Rate limited by platform | monkeypatch `has_rate_limit=True` | `error_code=rate_limited`, `retry_hint=retry_with_backoff` | queue delayed retry with backoff | covered |
| Content rejected by policy | monkeypatch `has_content_rejection=True` | `error_code=content_rejected`, non-recoverable | route to content revision flow | covered |
| Network/offline issue | monkeypatch `has_network_error=True` | `error_code=network_error`, `retry_hint=retry_with_backoff` | backoff retry and infra check | covered |
| Processing never reaches ready state | monkeypatch `_wait_processing_ready` to raise | `error_code=processing_stuck`, `retry_hint=retry_once` | delayed retry once, then escalate | covered |
| Post click fails | simulated click exception on post locator | `error_code=post_failed` | one retry, then escalate | covered |
| Post now modal appears | monkeypatch `_handle_optional_post_now_modal=True` | step `click_post_now_modal` appears, flow continues | no manual intervention required | covered |
| Content restriction modal remediated | force content modal present then cleared | steps `toggle_content_check`, `continue_content_modal`, `retry_post_after_content_modal` | continue flow without immediate hard fail | covered |
| Invalid schedule input | pass schedule < 20 minutes | `error_code=invalid_schedule` | reject input and require corrected schedule | covered |
| Missing cover image | pass non-existing cover path | `error_code=file_not_found` | reject input and require corrected cover path | covered |
| Failure screenshot artifact | run error flow with `screenshot_dir` | `artifacts.error_screenshot` path present | attach to alert/ticket | covered |
| Upload input unavailable but video already attached in UI | monkeypatch `_try_find_attached_in_page=None` + `_is_video_already_attached=True` | flow continues with `attach_video` detail containing `already_attached` | continue metadata/post flow without false `ui_changed` | covered |

## Important Scenarios Not Yet Fully Covered

| Scenario | Current behavior | Gap | Suggested implementation |
|---|---|---|---|
| Session expires mid-flow | may be `not_logged_in` late | no explicit stage marker | add stage-specific failure detail (`during_attach`, `before_post`) |
| Multi-tab ambiguity on CDP connect | currently first context/page | may target wrong tab | add tab selection policy by URL match + optional `--tab-url-contains` |

## Current Coverage Source

- `tests/test_uploader_errors.py`

This file currently simulates and validates the primary OpenClaw-facing failure contract.
