# Team Upload Update - 2026-04-03

## Branch scope

- Repo: `tiktok-uploader-cdp`
- Date: 2026-04-03
- Focus:
1. Remove inactive/dead artifacts and stale module usage.
2. Improve runtime flow around `wait_processing_ready`.
3. Expand and link visual Mermaid documentation.

## What changed

### 1) Cleanup inactive code/files

- Removed file: `src/tiktok_uploader_cdp/infra/selectors.py`
- Reason: module was only used as a constant holder for detector checks; upload-related selector constants inside it were stale and not used by runtime.
- Action taken:
1. Moved required captcha/login constants directly into `src/tiktok_uploader_cdp/infra/detectors.py`.
2. Updated docs references from deleted file to active sources (`config.toml` + `infra/detectors.py`).

Runtime behavior after cleanup: unchanged for detection semantics.

### 2) Runtime flow optimization (processing wait position)

- Updated `src/tiktok_uploader_cdp/app/uploader.py` execution order:
1. `attach_video`
2. metadata steps (`set_interactivity`, `set_visibility`, `set_description`, `set_cover`, `set_schedule`)
3. `wait_processing_ready`
4. `guard_before_post` and `click_post`

Why:

- Previous order waited immediately after upload attach and could idle for long timeout windows.
- New order uses upload-processing time to complete metadata first, reducing wasted wait and improving end-to-end throughput.

Step contract impact:

- `wait_processing_ready` step still exists with same name.
- Its position in `steps[]` moved to just before post.

### 3) Documentation and flow visualization

- Added detailed docs set under `docs/full-system/`.
- Added Mermaid visual flows in `docs/full-system/11-mermaid-flows.md`, including:
1. End-to-end runtime flow.
2. Content restriction modal remediation.
3. OpenClaw retry/fallback state map.
4. Dedicated `wait_processing_ready` loop flow.

## Validation

- Test suite: `uv run pytest -q`
- Result: `15 passed`

## Integration notes for Team Upload

1. If parser depends on strict step order, update expectation for `wait_processing_ready` position (now after metadata steps).
2. No error code changes and no top-level JSON schema changes.
3. Detection behavior for captcha/login remains equivalent after module cleanup.
