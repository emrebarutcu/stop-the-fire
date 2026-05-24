#!/usr/bin/env bash
#
# run.sh — start the Firefighter Web Suite (backend + frontend).
#
# Usage:
#   ./run.sh           # auto-setup if needed, then start both servers
#   ./run.sh --help    # this message
#
# First run will create backend/.venv + pip install + npm install (~1–2 min).
# Subsequent runs start in a few seconds. Ctrl+C stops everything.
#
set -euo pipefail

# ---------- config ----------
BACKEND_PORT=${BACKEND_PORT:-8765}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/.run-logs"
mkdir -p "$LOG_DIR"

# ---------- output helpers ----------
RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
BLUE=$'\033[34m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; NC=$'\033[0m'
say()  { printf "%s[run]%s %s\n" "$BLUE" "$NC" "$1"; }
ok()   { printf "%s[ok]%s  %s\n" "$GREEN" "$NC" "$1"; }
warn() { printf "%s[!]%s   %s\n" "$YELLOW" "$NC" "$1"; }
die()  { printf "%s[x]%s   %s\n" "$RED" "$NC" "$1" >&2; exit 1; }

case "${1:-}" in
  -h|--help)
    sed -n '2,12p' "$0"; exit 0 ;;
esac

# ---------- 1. detect Python ----------
choose_python() {
  for v in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$v" >/dev/null 2>&1; then
      if "$v" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
        echo "$v"; return
      fi
    fi
  done
  return 1
}

# ---------- 2. backend setup ----------
if [[ ! -d "$BACKEND/.venv" ]]; then
  PY=$(choose_python) || die "Python 3.10+ bulunamadı (brew install python@3.13 dene)"
  say "Backend venv kuruluyor ($PY)..."
  "$PY" -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install -q --upgrade pip
  "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"
  ok "Backend deps kuruldu"
fi

# ---------- 3. frontend setup ----------
command -v node >/dev/null 2>&1 || die "Node.js bulunamadı (brew install node)"
command -v npm  >/dev/null 2>&1 || die "npm bulunamadı"
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  say "Frontend deps kuruluyor (npm install)..."
  (cd "$FRONTEND" && npm install --silent --no-audit --no-fund) \
    || die "npm install başarısız"
  ok "Frontend deps kuruldu"
fi

# ---------- 4. port checks ----------
port_pid() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | awk 'NR>1 {print $2; exit}'
}

if pid=$(port_pid "$BACKEND_PORT") && [[ -n "$pid" ]]; then
  die "Backend portu $BACKEND_PORT meşgul (PID $pid). Önce: kill $pid"
fi
if pid=$(port_pid "$FRONTEND_PORT") && [[ -n "$pid" ]]; then
  warn "Frontend portu $FRONTEND_PORT meşgul (PID $pid); Vite alternatif port deneyecek."
fi

# ---------- 5. cleanup trap ----------
BACKEND_PID=""
FRONTEND_PID=""
_CLEANED=0

cleanup() {
  [[ "$_CLEANED" -eq 1 ]] && return
  _CLEANED=1
  printf "\n%s[run]%s durduruluyor...\n" "$BLUE" "$NC"
  if [[ -n "$BACKEND_PID" ]]; then
    pkill -P "$BACKEND_PID" 2>/dev/null || true
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$FRONTEND_PID" ]]; then
    pkill -P "$FRONTEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  ok "çıkıldı"
}
trap cleanup EXIT INT TERM

# ---------- 6. start backend ----------
say "Backend başlatılıyor (port $BACKEND_PORT)..."
(
  cd "$BACKEND"
  exec .venv/bin/uvicorn main:app \
    --host 127.0.0.1 --port "$BACKEND_PORT" \
    --log-level warning
) > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# wait for /api/health to respond
for _ in $(seq 1 60); do
  if curl -s "http://127.0.0.1:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
    ok "Backend hazır (PID $BACKEND_PID)"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo
    tail -n 30 "$LOG_DIR/backend.log" >&2
    die "Backend başlatılamadı (full log: $LOG_DIR/backend.log)"
  fi
  sleep 0.5
done
if ! curl -s "http://127.0.0.1:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
  die "Backend 30 sn'de health check'e cevap vermedi"
fi

# ---------- 7. start frontend ----------
say "Frontend başlatılıyor (port $FRONTEND_PORT)..."
(
  cd "$FRONTEND"
  exec npx vite --host 127.0.0.1 --port "$FRONTEND_PORT"
) > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# wait for Vite "ready in"
for _ in $(seq 1 40); do
  if grep -q "ready in" "$LOG_DIR/frontend.log" 2>/dev/null; then break; fi
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo
    tail -n 30 "$LOG_DIR/frontend.log" >&2
    die "Frontend başlatılamadı (full log: $LOG_DIR/frontend.log)"
  fi
  sleep 0.3
done

# Vite may have fallen back to a different port; discover the actual URL.
ACTUAL_URL=$(grep -oE "Local: *http://[^ ]+" "$LOG_DIR/frontend.log" \
              | tail -1 | awk '{print $2}')
ACTUAL_URL="${ACTUAL_URL:-http://localhost:$FRONTEND_PORT/}"
ACTUAL_URL="${ACTUAL_URL%[[:space:]]*}"  # trim trailing whitespace/ANSI

ok "Frontend hazır (PID $FRONTEND_PID)"
printf "\n"
printf "  %s🔥 Firefighter Web Suite%s\n" "$BOLD" "$NC"
printf "  ──────────────────────────────────────\n"
printf "  Frontend:  %s%s%s\n" "$GREEN" "$ACTUAL_URL" "$NC"
printf "  Backend:   %shttp://127.0.0.1:%s%s  (docs: /docs)\n" "$DIM" "$BACKEND_PORT" "$NC"
printf "  Logs:      %s%s/{backend,frontend}.log%s\n" "$DIM" "$LOG_DIR" "$NC"
printf "  ──────────────────────────────────────\n"
printf "  %sCtrl+C ile durdur%s\n\n" "$DIM" "$NC"

# wait for the first child to exit, then trigger cleanup
wait -n 2>/dev/null || wait
