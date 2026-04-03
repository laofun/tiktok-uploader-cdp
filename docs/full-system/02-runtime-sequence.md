# Runtime Sequence

## Full Execution Timeline

### Phase 00 - Input and config bootstrap

1. Parse CLI args.
2. Build `UploadRequest`.
3. Load runtime config from `--config` or default config path.

Possible hard-stop errors:

- `file_not_found` for missing video
- `file_not_found` for missing cover
- `invalid_schedule` for schedule outside supported window

### Phase 01 - Session acquisition

1. Connect over CDP.
2. Acquire first context and first page (or open a new page in context).
3. Emit step: `connect_cdp`.

Possible hard-stop errors:

- `cdp_connect_failed`
- `no_browser_context`

### Phase 02 - Navigation and pre-guard

1. `goto(upload_url, domcontentloaded)`.
2. Emit step: `goto_upload`.
3. Run guard checks: login, captcha, rate-limit, network.
4. Emit step: `guard_login_captcha`.

Possible hard-stop errors:

- `not_logged_in`
- `captcha_detected`
- `rate_limited`
- `network_error`

### Phase 03 - Upload attach and processing readiness

1. Resolve upload input selector (main page first, then iframes).
2. Set video file with retry.
3. Emit step: `attach_video`.

Possible hard-stop errors:

- `ui_changed`

### Phase 04 - Metadata setup

1. Set interactivity toggles.
2. Emit step: `set_interactivity`.
3. Set visibility.
4. Emit step: `set_visibility`.
5. Set description with hashtag/mention handling.
6. Emit step: `set_description` (when description is non-empty).
7. Set cover (optional).
8. Emit step: `set_cover` (when cover provided).
9. Set schedule (optional normalized UTC value).
10. Emit step: `set_schedule`.
11. Poll post button readiness (`wait_processing_ready`) after metadata is done.
12. Emit step: `wait_processing_ready`.

Possible hard-stop errors:

- `ui_changed`
- `unknown_error` (unsupported cover extension path)
- `processing_stuck`
- `upload_timeout`

### Phase 05 - Pre-post guard and dry-run short circuit

1. Run guard checks again before posting.
2. Emit step: `guard_before_post`.
3. If dry-run: emit `dry_run_stop` and return success immediately.

### Phase 06 - Publish and modal remediation

1. Click post button.
2. Emit step: `click_post`.
3. If `Post now` modal appears, click and emit `click_post_now_modal`.
4. Detect content restriction modal.
5. If modal exists:
1. emit `toggle_content_check`
2. emit `continue_content_modal`
3. retry post and emit `retry_post_after_content_modal`

Possible hard-stop errors:

- `post_failed`
- `content_rejected`

### Phase 07 - Publish confirmation

1. Wait for publish success confirmation selector.
2. Emit step: `wait_publish_confirmation`.
3. Return `ok=true`.

Possible hard-stop errors:

- `upload_timeout`

## Canonical Step Name Order

Normal full publish run:

1. `connect_cdp`
2. `goto_upload`
3. `guard_login_captcha`
4. `attach_video`
5. `set_interactivity`
6. `set_visibility`
7. `set_description` (optional)
8. `set_cover` (optional)
9. `set_schedule` (optional)
10. `wait_processing_ready`
11. `guard_before_post`
12. `click_post`
13. `click_post_now_modal` (optional)
14. `toggle_content_check` (optional)
15. `continue_content_modal` (optional)
16. `retry_post_after_content_modal` (optional)
17. `wait_publish_confirmation`

Any failure appends final step `failed`.
