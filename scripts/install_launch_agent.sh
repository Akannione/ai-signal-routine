#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  install_launch_agent.sh [--hour HH] [--minute MM] [--start-now]
  install_launch_agent.sh --print-only
  install_launch_agent.sh --uninstall

Options:
  --env-file <path>  Load schedule and delivery settings from this file.
  --hour <0-23>      Override DAILY_RUN_HOUR.
  --minute <0-59>    Override DAILY_RUN_MINUTE.
  --label <name>     Override LAUNCHD_LABEL.
  --start-now        Trigger one immediate run after installing.
  --print-only       Print the LaunchAgent plist instead of installing it.
  --uninstall        Remove the installed LaunchAgent and plist.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/config/local.env}"
RUNTIME_DIR="${RUNTIME_DIR:-$HOME/.ai-signal-routine-runtime}"

for (( index=1; index<=$#; index++ )); do
  current="${!index}"
  if [[ "$current" == "--env-file" ]]; then
    next_index=$((index + 1))
    if (( next_index > $# )); then
      echo "Missing value for --env-file" >&2
      exit 1
    fi
    ENV_FILE="${!next_index}"
    break
  fi
done

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

HOUR="${DAILY_RUN_HOUR:-8}"
MINUTE="${DAILY_RUN_MINUTE:-0}"
LAUNCHD_LABEL="${LAUNCHD_LABEL:-com.akannione.ai-signal-routine.daily}"
LAUNCH_AGENTS_DIR="${LAUNCH_AGENTS_DIR:-$HOME/Library/LaunchAgents}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
RUN_SCRIPT="${RUN_SCRIPT:-$ROOT_DIR/scripts/run_daily.sh}"
LOG_DIR="${LOG_DIR:-$ROOT_DIR/logs}"
PRINT_ONLY=0
START_NOW=0
UNINSTALL=0

is_protected_root() {
  local path="$1"
  case "$path" in
    "$HOME/Documents" | "$HOME/Documents"/* | \
    "$HOME/Desktop" | "$HOME/Desktop"/* | \
    "$HOME/Downloads" | "$HOME/Downloads"/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

remap_source_path() {
  local value="$1"
  local source_root="$2"
  local runtime_root="$3"
  case "$value" in
    "$source_root")
      printf '%s\n' "$runtime_root"
      ;;
    "$source_root"/*)
      printf '%s%s\n' "$runtime_root" "${value#$source_root}"
      ;;
    *)
      printf '%s\n' "$value"
      ;;
  esac
}

stage_runtime_copy() {
  local source_root="$1"
  local runtime_root="$2"
  local tracked_files
  local tracked_top_levels

  mkdir -p "$runtime_root"

  if git -C "$source_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    tracked_files="$(mktemp)"
    git -C "$source_root" ls-files -z -- . \
      ':(exclude)data/**' \
      ':(exclude)reports/**' >"$tracked_files"

    if command -v rsync >/dev/null 2>&1; then
      rsync -a --from0 --files-from="$tracked_files" "$source_root/" "$runtime_root/"
    else
      git -C "$source_root" archive --format=tar HEAD | tar -xf - -C "$runtime_root"
    fi

    rm -f "$tracked_files"
    tracked_top_levels="$(
      {
        git -C "$source_root" ls-files | awk -F/ '{print $1}'
        printf '%s\n' data reports
      } | sort -u
    )"
  else
    tracked_top_levels=$'.gitignore\nREADME.md\nassets\nbenchmarks\nconfig\ndashboard.py\ndata\ndocs\nmain.py\nreports\nrequirements.txt\nsample_data\nscripts\nsrc\ntests'
    for path in $tracked_top_levels; do
      if [[ -e "$source_root/$path" ]]; then
        ditto "$source_root/$path" "$runtime_root/$path"
      fi
    done
  fi

  if [[ -f "$source_root/config/local.env" ]]; then
    mkdir -p "$runtime_root/config"
    install -m 600 "$source_root/config/local.env" "$runtime_root/config/local.env"
  fi

  if [[ ! -d "$runtime_root/data" && -d "$source_root/data" ]]; then
    ditto "$source_root/data" "$runtime_root/data"
  fi
  if [[ ! -d "$runtime_root/reports" && -d "$source_root/reports" ]]; then
    ditto "$source_root/reports" "$runtime_root/reports"
  fi
  if [[ ! -x "$runtime_root/.venv/bin/python" && -d "$source_root/.venv" ]]; then
    ditto "$source_root/.venv" "$runtime_root/.venv"
  fi

  while IFS= read -r -d '' entry; do
    name="$(basename "$entry")"
    if [[ "$name" == ".venv" || "$name" == "logs" ]]; then
      continue
    fi
    if [[ $'\n'"$tracked_top_levels"$'\n' == *$'\n'"$name"$'\n'* ]]; then
      continue
    fi
    rm -rf "$entry"
  done < <(find "$runtime_root" -mindepth 1 -maxdepth 1 -print0)
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --hour)
      HOUR="${2:-}"
      shift 2
      ;;
    --minute)
      MINUTE="${2:-}"
      shift 2
      ;;
    --label)
      LAUNCHD_LABEL="${2:-}"
      shift 2
      ;;
    --print-only)
      PRINT_ONLY=1
      shift
      ;;
    --start-now)
      START_NOW=1
      shift
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_int() {
  local value="$1"
  local label="$2"
  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    echo "$label must be an integer. Got: $value" >&2
    exit 1
  fi
}

require_range() {
  local value="$1"
  local min="$2"
  local max="$3"
  local label="$4"
  if (( value < min || value > max )); then
    echo "$label must be between $min and $max. Got: $value" >&2
    exit 1
  fi
}

render_plist() {
  cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUN_SCRIPT}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ENV_FILE</key>
    <string>${ENV_FILE}</string>
    <key>PYTHON_BIN</key>
    <string>${PYTHON_BIN}</string>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>RunAtLoad</key>
  <false/>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>${HOUR}</integer>
    <key>Minute</key>
    <integer>${MINUTE}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/launchd.err.log</string>
</dict>
</plist>
EOF
}

require_int "$HOUR" "Hour"
require_int "$MINUTE" "Minute"
require_range "$HOUR" 0 23 "Hour"
require_range "$MINUTE" 0 59 "Minute"

ACTIVE_ROOT="$ROOT_DIR"
ACTIVE_ENV_FILE="$ENV_FILE"
ACTIVE_PYTHON_BIN="$PYTHON_BIN"
ACTIVE_RUN_SCRIPT="$RUN_SCRIPT"
ACTIVE_LOG_DIR="$LOG_DIR"
STAGED_RUNTIME=0

if is_protected_root "$ROOT_DIR"; then
  ACTIVE_ROOT="$RUNTIME_DIR"
  ACTIVE_ENV_FILE="$(remap_source_path "$ENV_FILE" "$ROOT_DIR" "$RUNTIME_DIR")"
  ACTIVE_PYTHON_BIN="$(remap_source_path "$PYTHON_BIN" "$ROOT_DIR" "$RUNTIME_DIR")"
  ACTIVE_RUN_SCRIPT="$(remap_source_path "$RUN_SCRIPT" "$ROOT_DIR" "$RUNTIME_DIR")"
  ACTIVE_LOG_DIR="$(remap_source_path "$LOG_DIR" "$ROOT_DIR" "$RUNTIME_DIR")"
  STAGED_RUNTIME=1
fi

if (( STAGED_RUNTIME == 1 && UNINSTALL == 0 )); then
  stage_runtime_copy "$ROOT_DIR" "$RUNTIME_DIR"
fi

if [[ ! -f "$ACTIVE_RUN_SCRIPT" ]]; then
  echo "Run script not found at $ACTIVE_RUN_SCRIPT" >&2
  exit 1
fi

PLIST_PATH="${LAUNCH_AGENTS_DIR}/${LAUNCHD_LABEL}.plist"

if (( UNINSTALL == 1 )); then
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
  rm -f "$PLIST_PATH"
  echo "Removed LaunchAgent ${LAUNCHD_LABEL}"
  exit 0
fi

if (( PRINT_ONLY == 1 )); then
  ROOT_DIR="$ACTIVE_ROOT"
  ENV_FILE="$ACTIVE_ENV_FILE"
  PYTHON_BIN="$ACTIVE_PYTHON_BIN"
  RUN_SCRIPT="$ACTIVE_RUN_SCRIPT"
  LOG_DIR="$ACTIVE_LOG_DIR"
  render_plist
  exit 0
fi

ROOT_DIR="$ACTIVE_ROOT"
ENV_FILE="$ACTIVE_ENV_FILE"
PYTHON_BIN="$ACTIVE_PYTHON_BIN"
RUN_SCRIPT="$ACTIVE_RUN_SCRIPT"
LOG_DIR="$ACTIVE_LOG_DIR"

mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR"
render_plist >"$PLIST_PATH"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/${LAUNCHD_LABEL}" >/dev/null 2>&1 || true

if (( START_NOW == 1 )); then
  launchctl kickstart -k "gui/$(id -u)/${LAUNCHD_LABEL}"
fi

printf 'Installed %s\n' "$PLIST_PATH"
printf 'Scheduled daily run at %02d:%02d local time.\n' "$HOUR" "$MINUTE"
printf 'Logs: %s and %s\n' "$LOG_DIR/launchd.out.log" "$LOG_DIR/launchd.err.log"
if (( STAGED_RUNTIME == 1 )); then
  printf 'Staged runtime copy at %s because macOS blocks background jobs from protected folders like Documents.\n' "$ROOT_DIR"
fi
