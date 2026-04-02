---
name: tiktok-uploader-cdp-openclaw
description: Use this skill when modifying tiktok-uploader-cdp for AI/OpenClaw orchestration. Enforces CDP-only browser control, config-driven selector/timeouts, stable machine-readable error contract, and automation-safe retry semantics.
---

# TikTok Uploader CDP for OpenClaw

Use this skill for all changes in this repository.

## Core Rules

1. CDP-only session control.
- Always connect to an existing logged-in browser via `chromium.connect_over_cdp`.
- Do not add cookie injection, sessionid auth, or username/password login automation.

2. Config-first UI behavior.
- Treat `src/tiktok_uploader_cdp/config.toml` as the first place to adapt selectors and timeouts.
- Prefer editing config over hardcoding new locators in Python.

3. OpenClaw-first outputs.
- Keep CLI output as a single JSON object.
- Preserve stable keys in `UploadResult`: `ok`, `error_code`, `message`, `recoverable`, `recommended_action`, `retry_hint`, `schema_version`, `request_id`, `steps`, `artifacts`, `metadata`.

4. Stable error semantics.
- Keep existing error codes stable.
- Add new codes instead of renaming old ones.
- Explicitly map each new error to retry semantics and action.

5. Diagnostics over silence.
- Every major phase should append a `StepResult`.
- On failures, capture screenshot when `screenshot_dir` is provided and include artifact path.

## Feature Set To Preserve

- Schedule support (UTC): min 20 minutes, max 10 days, 5-minute rounding.
- Visibility support: `everyone|friends|only_you`.
- Interactivity toggles: comment/duet/stitch.
- Cover upload support.
- Mention/hashtag dropdown-aware typing behavior.

## Editing Workflow

- Main flow: `src/tiktok_uploader_cdp/app/uploader.py`
- Request/response contract: `src/tiktok_uploader_cdp/domain/models.py`
- Error codes: `src/tiktok_uploader_cdp/domain/errors.py`
- CDP connection: `src/tiktok_uploader_cdp/infra/cdp.py`
- Runtime config loading: `src/tiktok_uploader_cdp/infra/runtime_config.py`
- Config file: `src/tiktok_uploader_cdp/config.toml`

When changing behavior, update tests in `tests/` to keep contract stable.

## Validation Commands

```bash
uv run pytest -q
```

## Guardrails

- Prefer selector updates in config before code changes.
- Do not convert structured failures into generic retries.
- For uncertain platform behavior, return structured error instead of implicit loops.
