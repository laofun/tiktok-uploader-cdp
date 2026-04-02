# Runbook

Operator runbook for high-frequency failure modes.

## 1) captcha_detected

Symptoms:
- `error_code=captcha_detected`
- screenshot shows challenge widget or anti-bot gate

Actions:
1. Open the controlled browser profile.
2. Solve captcha manually.
3. Confirm TikTok upload page is normal.
4. Re-run the same job with same `request_id` suffix policy (or linked retry id).

Do not:
- spam retries before manual solve.

## 2) ui_changed

Symptoms:
- `error_code=ui_changed`
- step failure indicates no selector matched

Actions:
1. Open screenshot from `artifacts.error_screenshot`.
2. Compare current TikTok DOM with selector lists in `src/tiktok_uploader_cdp/infra/selectors.py`.
3. Add fallback selectors first; avoid replacing all selectors blindly.
4. Run `uv run pytest -q`.
5. Run a dry-run job to verify pre-post flow.

Do not:
- auto-retry production jobs while selectors are stale.

## 3) not_logged_in

Symptoms:
- redirected to login/signup flow

Actions:
1. Ask user to log in using the exact browser profile exposed via CDP.
2. Confirm navigation to upload page works.
3. Retry job.

## 4) cdp_connect_failed / no_browser_context

Symptoms:
- cannot connect, or browser has no usable context

Actions:
1. Ensure browser launched with debug port enabled.
2. Verify CDP endpoint is reachable.
3. Open at least one normal tab in that browser instance.
4. Retry job.

## 5) upload_timeout

Actions:
1. Retry once automatically.
2. If still failing, escalate with screenshot and step trace.
3. Check network stability, TikTok status, and page responsiveness.

## 6) unknown_error

Actions:
1. Escalate to maintainer.
2. Attach raw JSON output and screenshot artifact.
3. Reproduce with `--dry-run` first, then full run if dry-run passes.

## 7) rate_limited

Symptoms:
- `error_code=rate_limited`
- page text indicates throttling/temporary block

Actions:
1. Pause immediate retries.
2. Retry with backoff window (for example 5m, 15m, 30m).
3. If repeated rate limits occur, reduce upload concurrency and rotate schedule windows.

## 8) content_rejected

Symptoms:
- `error_code=content_rejected`
- page indicates policy/community/restriction rejection

Actions:
1. First inspect step trace for:
`toggle_content_check`, `continue_content_modal`, `retry_post_after_content_modal`.
2. If those steps are missing, update selectors in config for modal/toggles.
3. If those steps executed but still rejected, stop auto-retry and route to content revision flow.
4. Submit a new upload job after content changes.

## 9) network_error

Symptoms:
- `error_code=network_error`
- page text indicates connectivity failure

Actions:
1. Check runner network and upstream connectivity.
2. Retry with backoff (do not hammer immediate retries).
3. If persistent, route job to a healthy runner/environment.

## 10) processing_stuck

Symptoms:
- `error_code=processing_stuck`
- upload attached, but post-ready state never appears

Actions:
1. Wait short cooldown and retry once.
2. If repeated, escalate with screenshot + steps.
3. Check file codec/size and TikTok processing health.

## 11) invalid_schedule

Symptoms:
- `error_code=invalid_schedule`
- schedule outside allowed window

Actions:
1. Ensure schedule is UTC.
2. Set schedule between 20 minutes and 10 days in the future.
3. Re-submit job with corrected schedule.

## 12) selector drift under new features

Symptoms:
- failures while setting visibility/interactivity/schedule/cover/mentions
- often appears as `ui_changed` or `post_failed`

Actions:
1. Update selectors in `src/tiktok_uploader_cdp/config.toml`.
2. Prefer selector updates before changing code.
3. Re-run dry-run script and inspect step trace.
