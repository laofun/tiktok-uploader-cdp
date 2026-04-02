#!/usr/bin/env bash
set -euo pipefail

CDP_URL="${1:-http://127.0.0.1:9222}"

echo "Checking CDP endpoint: ${CDP_URL}"
if curl -fsS "${CDP_URL}/json/version"; then
  echo
  echo "CDP endpoint is reachable."
else
  echo
  echo "CDP endpoint is not reachable." >&2
  exit 1
fi
