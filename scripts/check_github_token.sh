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

python3 - <<'PY'
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


token = os.environ.get("GITHUB_TOKEN", "").strip().strip("\"").strip("'")
if not token:
    print("github_token_status=missing")
    print("Set GITHUB_TOKEN in config/local.env, then rerun this script.")
    sys.exit(2)

request = Request(
    "https://api.github.com/rate_limit",
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "ai-signal-routine-token-check",
    },
)

try:
    with urlopen(request, timeout=20) as response:
        status = response.status
        body = response.read().decode("utf-8", errors="replace")
except HTTPError as exc:
    status = exc.code
    body = exc.read().decode("utf-8", errors="replace")
except URLError as exc:
    print("github_token_status=network_error")
    print(str(exc.reason))
    sys.exit(3)
except OSError as exc:
    print("github_token_status=network_error")
    print(str(exc))
    sys.exit(3)

if status == 200:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        print("github_token_status=invalid_response")
        sys.exit(1)
    core = payload.get("resources", {}).get("core", {})
    search = payload.get("resources", {}).get("search", {})
    print("github_token_status=valid")
    print(f"core_limit={core.get('limit')} core_remaining={core.get('remaining')}")
    print(f"search_limit={search.get('limit')} search_remaining={search.get('remaining')}")
    sys.exit(0)

if status == 401:
    print("github_token_status=invalid")
    print("Replace GITHUB_TOKEN with a fresh token. Do not include quotes, spaces, or a Bearer prefix.")
    sys.exit(1)

print(f"github_token_status=unexpected_http_{status}")
try:
    message = json.loads(body).get("message", "")
except json.JSONDecodeError:
    message = ""
if message:
    print(message[:500])
sys.exit(1)
PY
