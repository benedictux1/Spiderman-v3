#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-5001}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_FILE="/tmp/kith_server.log"
DB_FILE="$ROOT_DIR/kith_platform.db"

echo "[run_server] Ensuring no process is listening on :$PORT ..."
PIDS=$(lsof -ti tcp:$PORT || true)
if [ -n "${PIDS}" ]; then
  echo "$PIDS" | xargs -I{} bash -lc 'echo "Killing PID {}"; kill -9 {} || true'
  sleep 1
fi

# Also kill any stray python serving app.py (best effort)
ps aux | grep "kith-platform/app.py" | grep -v grep | awk '{print $2}' | xargs -I{} bash -lc 'echo "Killing stale app PID {}"; kill -9 {}' 2>/dev/null || true

# Clean WAL/SHM only if no process holds the DB
if [ -f "$DB_FILE" ]; then
  if ! lsof "$DB_FILE" >/dev/null 2>&1; then
    for f in "$DB_FILE-wal" "$DB_FILE-shm"; do
      if [ -f "$f" ]; then
        echo "Removing stale $f"
        rm -f "$f"
      fi
    done
  else
    echo "DB is in use; skipping WAL/SHM cleanup"
  fi
fi

# Load env if present
if [ -f .env ]; then
  echo "[run_server] Loading .env"
  set -a
  # shellcheck disable=SC1091
  source .env || true
  set +a
fi

# Start server
echo "[run_server] Starting server on :$PORT ..."
nohup python3 "$ROOT_DIR/kith-platform/app.py" > "$LOG_FILE" 2>&1 &
PID=$!
echo "[run_server] Started PID: $PID (logs: $LOG_FILE)"
exit 0 