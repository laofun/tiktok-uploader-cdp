# Step Detail - Attach Video

## Objective

Bind local video file path to the correct TikTok upload `<input type=file>` reliably despite markup drift.

## Preconditions

- `req.video_path` exists on local filesystem.
- Page already on upload screen.
- Pre-guard passed (`not_logged_in/captcha/rate/network` absent).

## Selector source

- `selectors.upload_input` in `config.toml`
- Current baseline candidates:
1. `input[type='file'][accept*='video']`
2. `input[type='file']`
3. XPath variants

## Runtime strategy (exact)

### Stage A - main page attached search

1. For each selector candidate:
1. Build locator `.first`.
2. Wait state `attached` (not `visible`).
3. If found, attempt `set_input_files(video_path)`.

### Stage B - retry on same locator

- `_try_set_input_files` retries up to 2 attempts with `0.8s` sleep.

### Stage C - iframe sweep fallback

1. Iterate all `page.frames`.
2. Repeat Stage A + B per frame.

### Stage D - fail if no success

1. If input selectors fail, check whether the target video filename is already present in page body text and description area is visible.
2. If yes, treat as existing attached/uploading state and continue (`attach_video` detail includes `already_attached`).
3. If not, throw `ui_changed` with message containing selector candidate list.

## Why `attached` is used instead of `visible`

TikTok often keeps file inputs hidden while the visible button is a wrapper element.
Using visible-only waits caused false negatives in previous runs.

## Frequent failure patterns

1. Wrong file input selected (cover input instead of video input).
2. Upload input inside iframe after TikTok UI rollout.
3. Overlay race: input attached but not ready for set_input_files.
4. Selector candidate chain too generic or outdated.

## Evidence to collect when failing

1. HTML snippet of all `input[type=file]`.
2. `accept` attributes for each input.
3. Frame tree and frame URLs.
4. JSON output `steps[]` and `error_code`.
5. Screenshot at failure.

## Recovery playbook

1. Update `selectors.upload_input` in config first.
2. Keep old selectors as fallback during migration window.
3. Validate with `--dry-run` before real post.

## Runtime ordering note

After `attach_video`, TUC now continues with metadata steps first (`set_interactivity`, `set_visibility`, `set_description`, `set_cover`, `set_schedule`) and only waits for processing readiness right before post.
This reduces idle waiting and uses upload-processing time for useful setup actions.
