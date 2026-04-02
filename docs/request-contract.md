# Request Contract

This document defines request inputs expected by CLI/API.

## UploadRequest Fields

- `video_path` (required): absolute path to video
- `description`: caption text; mention/hashtag flow is dropdown-aware
- `cdp_url`: CDP endpoint URL
- `upload_url`: TikTok upload page URL
- `timeout_seconds`: publish confirmation timeout
- `schedule`: optional UTC datetime (`YYYY-MM-DD HH:MM` from CLI)
- `visibility`: `everyone|friends|only_you`
- `comment`: bool
- `duet`: bool
- `stitch`: bool
- `content_check_lite`: bool (attempt disable when content restriction modal appears)
- `copyright_check`: bool (attempt disable when content restriction modal appears)
- `cover_path`: optional cover path (`png|jpg|jpeg`)
- `config_path`: optional override for config file
- `dry_run`: stop before post
- `request_id`: orchestrator correlation id
- `screenshot_dir`: optional output directory for failure screenshots

## Validation Highlights

- schedule must satisfy TikTok window constraints and 5-minute rounding policy
- cover file path must exist before browser actions start
- video file path must exist before browser actions start
- content-restriction modal flow emits `toggle_content_check` and `continue_content_modal` steps when triggered
