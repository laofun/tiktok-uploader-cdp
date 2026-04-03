# Step Detail - Post and Content Restriction Modal

## A) Post click base path

### Selector key

- `post_button`

### Click strategy

1. Resolve visible post button.
2. Try `scroll_into_view_if_needed`.
3. Try normal click.
4. Fallback click with `force=True`.
5. If still failed -> `post_failed`.

### Optional post-now modal

- Selector key: `post_now_modal`
- If found and visible, click and emit `click_post_now_modal`.

## B) Content restriction modal remediation

### Trigger detection

- Selector key: `content_modal`
- Plus text marker fallback via `has_content_rejection(page)`

### Goal

Attempt best-effort remediation before declaring hard content rejection.

### Selector keys

- `content_modal_view_details`
- `content_modal_continue`
- `content_modal_close`
- `content_check_lite_toggle`
- `copyright_check_toggle`

### Detailed sequence

1. Click `View details` if present.
2. Decide toggle actions from request values:
- if `content_check_lite=False`, attempt disable toggle
- if `copyright_check=False`, attempt disable toggle
3. Emit step `toggle_content_check` with detail:
- `content_check_lite=off,copyright_check=off` or
- `no_toggle_change`
4. Try click Continue button.
5. If Continue absent, click Close button.
6. Emit step `continue_content_modal` with detail:
- `continue_clicked` or `modal_closed`
7. Sleep 1s and re-check modal presence.
8. If still present -> throw `content_rejected`.
9. If cleared -> signal caller to retry post.
10. Caller clicks post again and emits `retry_post_after_content_modal`.

## C) Publish confirmation

### Selector key

- `publish_confirm`

### Behavior

1. Wait confirmation locator until `timeout_seconds`.
2. Read text (presence check).
3. Emit `wait_publish_confirmation`.
4. Return success payload.

### Timeout branch

- If confirmation not reached before timeout -> `upload_timeout`.
