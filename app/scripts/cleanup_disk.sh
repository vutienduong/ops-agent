#!/usr/bin/env bash
set -euo pipefail

MODE="inspect"
SANDBOX_DIR="${SANDBOX_DIR:-/tmp/ops-agent-sandbox}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

mkdir -p "$SANDBOX_DIR"
LOG_FILE="$SANDBOX_DIR/events.log"
TMP_FILE="$SANDBOX_DIR/cache.tmp"

if [[ ! -f "$LOG_FILE" ]]; then
  dd if=/dev/zero of="$LOG_FILE" bs=1024 count=400 >/dev/null 2>&1
fi
if [[ ! -f "$TMP_FILE" ]]; then
  dd if=/dev/zero of="$TMP_FILE" bs=1024 count=120 >/dev/null 2>&1
fi

if [[ "$MODE" == "inspect" ]]; then
  echo "Top files under $SANDBOX_DIR:"
  du -ah "$SANDBOX_DIR" | sort -hr | head -n 5
  exit 0
fi

if [[ "$MODE" == "cleanup" ]]; then
  : > "$LOG_FILE"
  rm -f "$TMP_FILE"
  echo "Disk cleanup complete in $SANDBOX_DIR."
  exit 0
fi

echo "Unsupported mode: $MODE"
exit 1
