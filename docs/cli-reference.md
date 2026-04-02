# CLI Reference

## Command

```bash
uv run tiktok-uploader-cdp [options]
```

## Core Options

- `--cdp-url`: CDP endpoint. Default: `http://127.0.0.1:9222`
- `--video` (required): absolute video path
- `--description`: caption text
- `--upload-url`: target TikTok upload URL
- `--timeout-seconds`: max wait for publish confirmation

## Config Options

- `--config`: override config path (default: `src/tiktok_uploader_cdp/config.toml`)

## Publish Behavior Options

- `--schedule "YYYY-MM-DD HH:MM"`: UTC schedule input
- `--visibility`: `everyone|friends|only_you`
- `--comment` / `--no-comment`
- `--duet` / `--no-duet`
- `--stitch` / `--no-stitch`
- `--content-check-lite` / `--no-content-check-lite`
- `--copyright-check` / `--no-copyright-check`
- `--cover /abs/path/image.jpg`

## Automation Options

- `--dry-run`: run all pre-post steps and stop before posting
- `--request-id`: passthrough id for orchestrator correlation
- `--screenshot-dir`: save error screenshots

## Example: Dry Run

```bash
uv run tiktok-uploader-cdp \
  --cdp-url http://127.0.0.1:9222 \
  --video /abs/path/video.mp4 \
  --description "#daily @example update" \
  --visibility friends \
  --comment \
  --duet \
  --stitch \
  --no-content-check-lite \
  --no-copyright-check \
  --cover /abs/path/cover.jpg \
  --request-id job-001 \
  --screenshot-dir /tmp/tiktok-uploader-cdp \
  --dry-run
```
