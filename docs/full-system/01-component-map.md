# Component Map

## Layered Architecture

### Entry Layer

- File: `src/tiktok_uploader_cdp/cli.py`
- Responsibility:
1. Parse CLI arguments.
2. Parse optional `--schedule` into UTC datetime.
3. Build `UploadRequest`.
4. Run `TikTokCDPUploader.upload()`.
5. Print exactly one JSON object.

### Application Layer

- File: `src/tiktok_uploader_cdp/app/uploader.py`
- Responsibility:
1. Orchestrate complete upload flow.
2. Emit structured `steps[]`.
3. Convert exceptions into `UploadResult` contract.
4. Apply fallback paths for unstable UI interactions.

### Domain Layer

- File: `src/tiktok_uploader_cdp/domain/models.py`
- Objects:
1. `UploadRequest`: run input payload.
2. `StepResult`: per-phase diagnostic signal.
3. `UploadResult`: final machine-readable response.

- File: `src/tiktok_uploader_cdp/domain/errors.py`
- Objects:
1. `ErrorCode`: stable cross-system codes.
2. `UploadError`: explicit error with `recoverable` and `recommended_action`.

### Infrastructure Layer

- `infra/cdp.py`: CDP connect/close, context/page acquisition.
- `infra/runtime_config.py`: parse `config.toml`, provide selector/timeouts access.
- `infra/page_ops.py`: selector candidate matching utility (`find_first_visible`).
- `infra/detectors.py`: login/captcha/rate-limit/network/content checks.
- `infra/detectors.py`: detector constants and checks for login/captcha/rate/network/content states.

## Runtime Data Flow

1. CLI input -> `UploadRequest`
2. `UploadRequest` + `config.toml` -> runtime decisions
3. Page actions -> `StepResult[]`
4. Exceptions -> mapped `UploadResult` with stable error semantics

## Config-driven Surface

`config.toml` controls:

- timeouts (`implicit_wait_seconds`, `processing_ready_timeout_seconds`, ...)
- schedule limits (`schedule_min_minutes`, `schedule_max_days`, ...)
- allowed cover extensions
- selector fallback chains for each UI block

## Core Invariant

TUC never logs in for user and never injects cookies.

- Browser auth state must already exist in the CDP-controlled profile.
