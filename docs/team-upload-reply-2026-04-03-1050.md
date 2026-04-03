# Reply to Team Upload (report `tuc_ttu_report_20260403_1050.zip`)

## Findings from latest artifacts

1. The reported failure is `ui_changed` at `attach_video` with no matching `input[type='file']` selectors.
2. Screenshot `tuc_error_ui_changed_latest.png` shows upload page already in an active upload state (file name visible, progress ~73%).
3. In this state, file input may no longer be available in DOM, so strict input lookup can produce a false `ui_changed`.
4. `upload_dom.png` shows a login page from a separate capture script context; useful for environment checks but not sufficient to represent the exact failing page state.

## Fix plan (now implemented on TUC side)

1. Add fallback in `attach_video`:
- If upload input selectors fail, detect whether target video is already attached/uploading (filename present + metadata region visible).
- If true, continue flow instead of failing `ui_changed`.
2. Keep existing selector-based attach path first; fallback only applies when selector path fails.
3. Keep error contract unchanged (`ui_changed` still returned when neither input nor attached-state signals are found).
4. Add CLI version support (`--version`) so every run can report exact binary version.

## Implemented changes

- `src/tiktok_uploader_cdp/app/uploader.py`
- `src/tiktok_uploader_cdp/cli.py`
- tests/docs updated accordingly.

Validation:

- `uv run pytest -q` -> `16 passed`
- `uv run tiktok-uploader-cdp --version` -> `tiktok-uploader-cdp 0.1.0`

## Request to team upload for rerun

Please rerun the same manifest (`finance-20260402-0602`) on the updated TUC commit and attach:

1. Full stdout JSON
2. Screenshot artifact if any
3. Final `steps[]` sequence

Expected improvement:

- Runs that previously failed at `attach_video` due to missing file input while upload already in progress should now proceed to metadata/post stages.
