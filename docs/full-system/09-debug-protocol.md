# Debug Protocol

## Objective

Create reproducible evidence for fast root-cause isolation with minimum reruns.

## Standard triage sequence

1. Verify CDP endpoint health (`scripts/check_cdp.sh`).
2. Run same payload with `--dry-run` first.
3. Keep stable `--request-id` for correlation.
4. Enable `--screenshot-dir`.
5. Save full stdout JSON (not partial snippets).

## Step-based diagnosis map

- Fail before `connect_cdp`: process/environment issue.
- Fail at `connect_cdp`: CDP port/profile/context issue.
- Fail at `goto_upload`: URL/navigation/auth surface issue.
- Fail at `attach_video`: upload selector/input/iframe issue.
- Fail at `set_cover`: cover modal selector/visibility/confirm issue.
- Fail at `set_schedule`: calendar/time picker drift.
- Fail at `click_post`: post button interaction issue.
- Fail after `click_post` with `content_rejected`: policy modal unresolved.
- Fail at `wait_publish_confirmation`: async publish timeout.

## DOM capture checklist for UI drift

Capture at failure point:

1. `page.url`
2. all frame URLs (`page.frames`)
3. count and HTML of `input[type=file]`
4. target modal root HTML (`status-result`, `cover-container`, etc.)
5. selector hit matrix (which selector matched / not matched)

## Minimal reproducibility package

1. run command used
2. full JSON output
3. screenshot(s)
4. active config file snapshot
5. TikTok UI language and upload URL used

## Decision tree

1. If `ui_changed` and selector mismatch is clear:
- patch `config.toml` first
2. If selectors look valid but action still fails:
- add click/attach fallback in code
3. If policy modal persists after remediation:
- treat as content issue, not selector issue
