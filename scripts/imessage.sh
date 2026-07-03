#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  imessage.sh --recipient <phone-or-email> [--file <path>]
  imessage.sh --recipient <phone-or-email> --message <text>
  echo "message" | imessage.sh --recipient <phone-or-email>

Environment:
  IMESSAGE_SEND_MODE=auto|buddy|ui
    auto  Try direct Messages send first, then GUI fallback.
    buddy Direct Messages AppleScript send only.
    ui    GUI compose-and-send fallback only.
EOF
}

recipient="${IMESSAGE_RECIPIENT:-}"
input_file=""
message=""
mode="${IMESSAGE_SEND_MODE:-auto}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --recipient)
      recipient="${2:-}"
      shift 2
      ;;
    --file)
      input_file="${2:-}"
      shift 2
      ;;
    --message)
      message="${2:-}"
      shift 2
      ;;
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$message" ]]; then
        message="$1"
      else
        message="${message} $1"
      fi
      shift
      ;;
  esac
done

if [[ -n "$input_file" ]]; then
  if [[ ! -f "$input_file" ]]; then
    echo "Input file not found: $input_file" >&2
    exit 1
  fi
  message="$(cat "$input_file")"
elif [[ -z "$message" && ! -t 0 ]]; then
  message="$(cat)"
fi

if [[ -z "$recipient" ]]; then
  echo "No recipient provided. Use --recipient or set IMESSAGE_RECIPIENT." >&2
  exit 1
fi

if [[ -z "${message//[$'\t\r\n ']}" ]]; then
  echo "No message body provided. Use --message, --file, or stdin." >&2
  exit 1
fi

send_via_buddy() {
  osascript - "$recipient" "$message" <<'APPLESCRIPT'
on run argv
    set recipientAddress to item 1 of argv
    set messageText to item 2 of argv
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy recipientAddress of targetService
        send messageText to targetBuddy
    end tell
end run
APPLESCRIPT
}

send_via_ui() {
  osascript - "$recipient" "$message" <<'APPLESCRIPT'
on run argv
    set recipientAddress to item 1 of argv
    set messageText to item 2 of argv
    set originalClipboard to the clipboard

    tell application "Messages" to activate
    delay 1

    set the clipboard to messageText
    tell application "System Events"
        tell process "Messages"
            keystroke "n" using command down
            delay 0.6
            keystroke recipientAddress
            delay 0.5
            key code 36
            delay 0.8
            keystroke "v" using command down
            delay 0.3
            key code 36
        end tell
    end tell

    delay 0.2
    set the clipboard to originalClipboard
end run
APPLESCRIPT
}

case "$mode" in
  buddy)
    send_via_buddy
    ;;
  ui)
    send_via_ui
    ;;
  auto)
    if send_via_buddy 2>/tmp/imessage_buddy.err; then
      exit 0
    fi
    if send_via_ui 2>/tmp/imessage_ui.err; then
      exit 0
    fi
    echo "iMessage send failed in both buddy and UI modes." >&2
    if [[ -s /tmp/imessage_buddy.err ]]; then
      echo "--- buddy mode ---" >&2
      cat /tmp/imessage_buddy.err >&2
    fi
    if [[ -s /tmp/imessage_ui.err ]]; then
      echo "--- ui mode ---" >&2
      cat /tmp/imessage_ui.err >&2
    fi
    exit 1
    ;;
  *)
    echo "Invalid IMESSAGE_SEND_MODE: $mode" >&2
    exit 1
    ;;
esac
