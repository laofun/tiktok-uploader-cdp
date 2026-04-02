---
name: tiktok-uploader-cdp-openclaw
description: Use this skill when modifying tiktok-uploader-cdp for AI/OpenClaw orchestration. Enforces CDP-only authenticated browser control, stable machine-readable error contract, captcha/UI-change detection, and automation-safe retry semantics.
---

# TikTok Uploader CDP for OpenClaw

Use this skill for all changes in this repository.

## Core Rules

1. CDP-only session control.
- Always connect to an existing logged-in browser via `chromium.connect_over_cdp`.
- Do not add cookie injection, sessionid auth, or username/password login automation.

2. OpenClaw-first outputs.
- Keep CLI output as a single JSON object.
- Preserve stable keys in `UploadResult`: `ok`, `error_code`, `message`, `recoverable`, `recommended_action`, `retry_hint`, `schema_version`, `request_id`, `steps`, `artifacts`, `metadata`.

3. Stable error semantics.
- `captcha_detected`: recoverable, requires human/captcha handoff.
- `ui_changed`: non-recoverable retry loop breaker until selector update.
- `not_logged_in`: recoverable after user login.
- `cdp_connect_failed`: recoverable after environment fix.

4. Diagnostics over silence.
- Every major phase should append a `StepResult`.
- On failures, capture screenshot when `screenshot_dir` is provided and include path in `artifacts`.

## Editing Workflow

- Main flow: `src/tiktok_uploader_cdp/app/uploader.py`
- Error codes: `src/tiktok_uploader_cdp/domain/errors.py`
- Output contract: `src/tiktok_uploader_cdp/domain/models.py`
- CDP connection: `src/tiktok_uploader_cdp/infra/cdp.py`
- Captcha/login detection: `src/tiktok_uploader_cdp/infra/detectors.py`
- Selector fallback set: `src/tiktok_uploader_cdp/infra/selectors.py`

When changing behavior, update tests in `tests/` to keep error contract stable.

## Validation Commands

```bash
uv run pytest -q
```

Before merge, verify at least:

```bash
uv run pytest -q
```

## Guardrails

- Prefer adding selector fallbacks before declaring `ui_changed`.
- Keep `error_code` values stable; add new codes instead of renaming existing ones.
- If a behavior is uncertain for automation (e.g. new TikTok interstitial), surface it as structured failure rather than implicit retry loops.
