#!/bin/bash

REPORT_FILE="reports/latest_slack_digest.txt"
CHUNK_SIZE=2500
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SEND_SCRIPT="$SCRIPT_DIR/../send_imessage.sh"

if [ ! -f "$REPORT_FILE" ]; then
  echo "Report file not found: $REPORT_FILE"
  exit 1
fi

split -b "$CHUNK_SIZE" "$REPORT_FILE" /tmp/ai_signal_chunk_

for file in /tmp/ai_signal_chunk_*; do
  "$SEND_SCRIPT" "$(cat "$file")"
  sleep 2
done

rm /tmp/ai_signal_chunk_*
