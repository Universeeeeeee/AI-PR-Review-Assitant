#!/usr/bin/env bash
set -euo pipefail

SKIP_INSTALL=0
SETUP_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --skip-install)
      SKIP_INSTALL=1
      ;;
    --setup-only)
      SETUP_ONLY=1
      ;;
    -h|--help)
      cat <<'HELP'
Usage: ./scripts/start-dev.sh [--skip-install] [--setup-only]

Starts the AI PR Review Assistant local development environment.

Options:
  --skip-install  Do not run pip install or npm install.
  --setup-only    Prepare env files and dependencies, but do not start servers.
HELP
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"
BACKEND_LOG="$BACKEND_DIR/.start-dev-uvicorn.log"
BACKEND_ERR="$BACKEND_DIR/.start-dev-uvicorn.err.log"
FRONTEND_LOG="$FRONTEND_DIR/.start-dev-vite.log"
FRONTEND_ERR="$FRONTEND_DIR/.start-dev-vite.err.log"
PID_FILE="$ROOT_DIR/.start-dev-pids"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Missing Python. Install Python 3.11+ and make sure it is on PATH." >&2
  exit 1
fi

for cmd in node npm; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing command '$cmd'. Install Node.js 20+ with npm." >&2
    exit 1
  fi
done

ensure_env_file() {
  local directory="$1"
  if [[ ! -f "$directory/.env" ]]; then
    cp "$directory/.env.example" "$directory/.env"
    echo "Created $directory/.env from .env.example"
  fi
}

port_in_use() {
  local port="$1"
  "$PYTHON_CMD" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sys.exit(0)
sys.exit(1)
PY
}

wait_http_ok() {
  local url="$1"
  local timeout="${2:-30}"
  "$PYTHON_CMD" - "$url" "$timeout" <<'PY'
import sys
import time
from urllib.request import urlopen

url = sys.argv[1]
deadline = time.time() + int(sys.argv[2])
while time.time() < deadline:
    try:
        with urlopen(url, timeout=3) as response:
            if 200 <= response.status < 500:
                sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(1)
PY
}

echo "AI PR Review Assistant local dev startup"
echo "Root: $ROOT_DIR"

ensure_env_file "$BACKEND_DIR"
ensure_env_file "$FRONTEND_DIR"

if [[ ! -x "$BACKEND_PYTHON" ]]; then
  echo "Creating backend virtual environment..."
  (cd "$BACKEND_DIR" && "$PYTHON_CMD" -m venv .venv)
fi

if [[ "$SKIP_INSTALL" -eq 0 ]]; then
  echo "Installing backend dependencies..."
  (cd "$BACKEND_DIR" && "$BACKEND_PYTHON" -m pip install -r requirements.txt)

  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

if [[ "$SETUP_ONLY" -eq 1 ]]; then
  echo "Setup complete. Servers were not started because --setup-only was used."
  exit 0
fi

rm -f "$PID_FILE"

if port_in_use 8000; then
  echo "Port 8000 is already in use. Backend was not started."
else
  echo "Starting backend on http://localhost:8000 ..."
  (
    cd "$BACKEND_DIR"
    "$BACKEND_PYTHON" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 >"$BACKEND_LOG" 2>"$BACKEND_ERR" &
    echo "backend=$!" >> "$PID_FILE"
  )
fi

if port_in_use 5173; then
  echo "Port 5173 is already in use. Frontend was not started."
else
  echo "Starting frontend on http://localhost:5173 ..."
  (
    cd "$FRONTEND_DIR"
    npm run dev -- --host 127.0.0.1 --port 5173 >"$FRONTEND_LOG" 2>"$FRONTEND_ERR" &
    echo "frontend=$!" >> "$PID_FILE"
  )
fi

backend_ready=0
frontend_ready=0
if wait_http_ok "http://localhost:8000/health" 30; then
  backend_ready=1
fi
if wait_http_ok "http://localhost:5173" 30; then
  frontend_ready=1
fi

cat <<EOF

Local URLs:
  Frontend: http://localhost:5173
  Backend:  http://localhost:8000/health

Logs:
  Backend stdout: $BACKEND_LOG
  Backend stderr: $BACKEND_ERR
  Frontend stdout: $FRONTEND_LOG
  Frontend stderr: $FRONTEND_ERR
  PID file:        $PID_FILE

Stop servers:
  ./scripts/stop-dev.sh
EOF

if [[ "$backend_ready" -ne 1 || "$frontend_ready" -ne 1 ]]; then
  echo ""
  echo "One or more services did not respond before the timeout."
  echo "Check the log files above for details."
  exit 1
fi

echo ""
echo "Development environment is ready."
