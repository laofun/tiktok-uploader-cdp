#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

VIDEO_PATH="${VIDEO_PATH:-${ROOT}/tmp/finance-20260402-0602/finance_20260402_0546_f558b267-3a6e-47e9-a296-81ca9be3293a_audio_published_video.mp4}"
COVER_PATH="${COVER_PATH:-${ROOT}/tmp/finance-20260402-0602/finance_20260402_0546_e32b107e-5620-4778-a96f-ca64848763bb_cover.jpg}"
CDP_URL="${CDP_URL:-http://127.0.0.1:9222}"
REQUEST_ID="${REQUEST_ID:-publish-example}"
SCREENSHOT_DIR="${SCREENSHOT_DIR:-${ROOT}/tmp/screenshots}"
SCHEDULE_UTC="${SCHEDULE_UTC:-}"

cd "$ROOT"

CMD=(
  uv run tiktok-uploader-cdp
  --cdp-url "$CDP_URL"
  --video "$VIDEO_PATH"
  --description "#daily @example finance update"
  --visibility everyone
  --comment
  --duet
  --stitch
  --cover "$COVER_PATH"
  --request-id "$REQUEST_ID"
  --screenshot-dir "$SCREENSHOT_DIR"
)

if [[ -n "$SCHEDULE_UTC" ]]; then
  CMD+=(--schedule "$SCHEDULE_UTC")
fi

"${CMD[@]}"
