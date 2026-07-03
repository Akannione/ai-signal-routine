#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/config/local.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

token="${GITHUB_TOKEN:-}"
token="${token//\"/}"
token="${token//\'/}"
if [[ -z "$token" ]]; then
  echo "github_token_status=missing"
  echo "Set GITHUB_TOKEN in config/local.env, then rerun this script."
  exit 2
fi

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT

if ! http_status="$(
  curl --silent --show-error \
    --connect-timeout 10 \
    --max-time 20 \
    --output "$response_file" \
    --write-out '%{http_code}' \
    --header 'Accept: application/vnd.github+json' \
    --header "Authorization: Bearer $token" \
    --header 'User-Agent: ai-signal-routine-token-check' \
    https://api.github.com/rate_limit
)"; then
  echo "github_token_status=network_error"
  exit 3
fi

if [[ "$http_status" == "401" ]]; then
  echo "github_token_status=invalid"
  echo "Replace GITHUB_TOKEN with a fresh token. Do not include quotes, spaces, or a Bearer prefix."
  exit 1
fi

python3 - "$http_status" "$response_file" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


status = int(sys.argv[1])
body = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
try:
    payload = json.loads(body)
except json.JSONDecodeError:
    print("github_token_status=invalid_response")
    sys.exit(1)

if status == 200:
    core = payload.get("resources", {}).get("core", {})
    search = payload.get("resources", {}).get("search", {})
    print("github_token_status=valid")
    print(f"core_limit={core.get('limit')} core_remaining={core.get('remaining')}")
    print(f"search_limit={search.get('limit')} search_remaining={search.get('remaining')}")
    sys.exit(0)

print(f"github_token_status=unexpected_http_{status}")
message = str(payload.get("message", ""))
if message:
    print(message[:500])
sys.exit(1)
PY
