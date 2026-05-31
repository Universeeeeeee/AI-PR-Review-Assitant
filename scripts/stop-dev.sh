#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'HELP'
Usage: ./scripts/stop-dev.sh

Stops local development servers started by scripts/start-dev.sh.
HELP
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/.start-dev-pids"
PIDS=()

if [[ -f "$PID_FILE" ]]; then
  while IFS="=" read -r _name pid; do
    if [[ -n "${pid:-}" && "$pid" =~ ^[0-9]+$ ]]; then
      PIDS+=("$pid")
    fi
  done < "$PID_FILE"
fi

if command -v lsof >/dev/null 2>&1; then
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && PIDS+=("$pid")
  done < <(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null || true)
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && PIDS+=("$pid")
  done < <(lsof -tiTCP:5173 -sTCP:LISTEN 2>/dev/null || true)
fi

if [[ "${#PIDS[@]}" -eq 0 ]]; then
  echo "No local dev server processes found."
else
  UNIQUE_PIDS="$(printf "%s\n" "${PIDS[@]}" | awk '!seen[$0]++')"
  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      echo "Stopped process $pid."
    else
      echo "Process $pid is not running."
    fi
  done <<EOF
$UNIQUE_PIDS
EOF
fi

rm -f "$PID_FILE"
echo "Local dev servers stopped."
