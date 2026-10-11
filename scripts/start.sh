#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ ! -x backend/.venv/bin/python || ! -d frontend/node_modules ]]; then
  echo "Dependencies are missing. Run 'make setup' first." >&2
  exit 1
fi

backend_pid=''
frontend_pid=''
cleanup() {
  trap - EXIT INT TERM
  [[ -z "$backend_pid" ]] || kill "$backend_pid" 2>/dev/null || true
  [[ -z "$frontend_pid" ]] || kill "$frontend_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Use the uv-managed environment and launch the service processes directly so cleanup targets the actual servers.
(cd backend && exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
backend_pid=$!
(cd frontend && exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort) &
frontend_pid=$!
echo "Backend: http://127.0.0.1:8000 | Frontend: http://127.0.0.1:5173"
echo "Press Ctrl+C to stop both services."

while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 1
done
status=0
if ! kill -0 "$backend_pid" 2>/dev/null; then
  wait "$backend_pid" || status=$?
else
  wait "$frontend_pid" || status=$?
fi
exit "$status"
