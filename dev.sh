#!/usr/bin/env bash
# Starts the backend (FastAPI) and frontend (Vite) dev servers together.
# Run from the repo root: ./dev.sh (or `bash dev.sh`)
set -e
cd "$(dirname "$0")"

BACKEND_PORT=8000
FRONTEND_PORT=5173

# `kill "$!"` doesn't reliably work here: Git Bash's $! is an MSYS-translated
# PID, not the real Windows PID taskkill needs, and npm/uvicorn --reload both
# spawn child processes that don't die with their wrapping shell anyway.
# Killing whatever's actually bound to the port sidesteps both problems.
kill_port() {
  local port=$1
  local pid
  for pid in $(netstat -ano | grep "LISTENING" | grep ":$port " | awk '{print $NF}' | sort -u); do
    taskkill //F //T //PID "$pid" 2>/dev/null
  done
}

cleanup() {
  echo ""
  echo "Stopping servers..."
  kill_port "$BACKEND_PORT"
  kill_port "$FRONTEND_PORT"
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://localhost:$BACKEND_PORT ..."
./venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port "$BACKEND_PORT" &

echo "Starting frontend on http://localhost:$FRONTEND_PORT ..."
(cd frontend && npm run dev) &

wait
