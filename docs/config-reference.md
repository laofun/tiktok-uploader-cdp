# Config Reference

Default file: `src/tiktok_uploader_cdp/config.toml`

## Sections

- `[timeouts]`: wait settings in seconds
- `[limits]`: schedule constraints
- `[file_types]`: accepted cover image extensions
- `[selectors]`: all DOM selectors used by uploader flow

## Schedule Constraints

- `schedule_min_minutes`: minimum future window
- `schedule_max_days`: maximum future window
- `schedule_minute_multiple`: minute slot multiple

Current logic enforces:
- schedule must be UTC
- schedule window must be within min/max
- minute is rounded up to nearest `schedule_minute_multiple`

## Selector Strategy

Each selector key is a list for fallback matching where possible.

High-impact keys:
- `upload_input`
- `description`
- `post_button`
- `publish_confirm`
- `visibility_dropdown`
- `comment_toggle` / `duet_toggle` / `stitch_toggle`
- `schedule_*`
- `cover_*`
- `mention_box` / `mention_user_id`

When TikTok UI changes, update `config.toml` first before changing code paths.
