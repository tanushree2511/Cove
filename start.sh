#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Cove — Linux / macOS launcher
#  Usage: ./start.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}[Cove]${RESET} $*"; }
success() { echo -e "${GREEN}[Cove]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[Cove]${RESET} $*"; }
error()   { echo -e "${RED}[Cove]${RESET} $*" >&2; }

# ── Resolve script directory (follow symlinks) ────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Virtualenv setup ───────────────────────────────────────
VENV_DIR="$SCRIPT_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    info "No .venv found — creating virtualenv and installing dependencies…"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
    # swap in the onnxruntime build that matches this machine's GPU/NPU (CUDA, DirectML, OpenVINO, ...)
    "$VENV_DIR/bin/python3" "$SCRIPT_DIR/scripts/install_runtime.py" || warn "Runtime selection skipped - using the CPU build"
    success "Virtualenv ready."
else
    info "Using existing virtualenv at .venv"
fi

PYTHON="$VENV_DIR/bin/python3"

# ── 2. Hardware ───────────────────────────────────────────────
# The app detects the hardware itself (CPU cores, container limits, NVIDIA / AMD / Intel / Apple / Qualcomm
# accelerators) and benchmarks the options on first start, keeping the fastest. Nothing to configure here;
# export COVE_FORCE_CPU=1 to disable accelerators, or run: python3 scripts/install_runtime.py
info "Hardware    : auto-detected at start-up (see http://localhost:8000/hardware)"

# ── 3. Model & data directories ───────────────────────────────
export COVE_MODEL_DIR="$SCRIPT_DIR/models"
if [[ "$(uname)" == "Darwin" ]]; then
    export COVE_USER_DATA="$HOME/Library/Application Support/Cove"
else
    export COVE_USER_DATA="${XDG_CONFIG_HOME:-$HOME/.config}/Cove"
fi
mkdir -p "$COVE_USER_DATA"
info "Model dir   : $COVE_MODEL_DIR"
info "User data   : $COVE_USER_DATA"

# ── 4. Worker count ───────────────────────────────────────────
# Worker counts (CPU threads, model replicas, batch sizes) are sized automatically from the detected hardware.
# Override with COVE_AI_WORKERS / COVE_ORT_THREADS / COVE_BATCH_SIZE if you need to.

# ── 5. Kill stale processes on required ports ─────────────────
kill_port() {
    local port="$1"
    local pids
    # lsof works on both Linux and macOS
    if command -v lsof &>/dev/null; then
        pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
    else
        pids=$(fuser "$port/tcp" 2>/dev/null | awk '{print $NF}' || true)
    fi
    if [[ -n "$pids" ]]; then
        warn "Port $port in use — killing PID(s): $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 0.3
    fi
}

kill_port 8000
kill_port 8001
kill_port 8080

# ── Log directory ─────────────────────────────────────────────
LOG_DIR="$SCRIPT_DIR/.logs"
mkdir -p "$LOG_DIR"

# ── Track background PIDs for clean shutdown ──────────────────
declare -a BG_PIDS=()

cleanup() {
    echo ""
    warn "Shutting down Cove…"
    for pid in "${BG_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    success "All services stopped. Goodbye."
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── 6. Start cove-api ─────────────────────────────────────────
info "Starting cove-api   (port 8000) …"
(
    cd "$SCRIPT_DIR/cove"
    "$PYTHON" -m uvicorn api.server:app \
        --host 0.0.0.0 --port 8000 \
        >> "$LOG_DIR/cove-api.log" 2>&1
) &
BG_PIDS+=($!)

# ── 7. Start video-api ────────────────────────────────────────
info "Starting video-api  (port 8001) …"
(
    cd "$SCRIPT_DIR/videoModules"
    "$PYTHON" -m uvicorn api:app \
        --host 0.0.0.0 --port 8001 \
        >> "$LOG_DIR/video-api.log" 2>&1
) &
BG_PIDS+=($!)

# ── 8. Start frontend dev server ──────────────────────────────
info "Starting frontend   (port 8080) …"
(
    cd "$SCRIPT_DIR/frontend"
    npm run dev -- --port 8080 \
        >> "$LOG_DIR/frontend.log" 2>&1
) &
BG_PIDS+=($!)

# ── 9. Wait for cove-api health ───────────────────────────────
info "Waiting for cove-api to become healthy…"
HEALTH_URL="http://localhost:8000/health"
MAX_WAIT=60
ELAPSED=0
HEALTHY=0

while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    if curl -sf "$HEALTH_URL" &>/dev/null; then
        HEALTHY=1
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    # Show a dot every 4 seconds so the user knows we're alive
    if (( ELAPSED % 4 == 0 )); then
        printf '.'
    fi
done
echo ""   # newline after dots

if [[ $HEALTHY -ne 1 ]]; then
    error "cove-api did not become healthy within ${MAX_WAIT}s."
    error "Check logs at: $LOG_DIR/cove-api.log"
    cleanup
fi

# ── 10. Success banner ────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║  ✅  Cove is running!               ║${RESET}"
echo -e "${GREEN}${BOLD}║                                              ║${RESET}"
echo -e "${GREEN}${BOLD}║  🌐  http://localhost:8080                   ║${RESET}"
echo -e "${GREEN}${BOLD}║                                              ║${RESET}"
echo -e "${GREEN}${BOLD}║  Logs → .logs/  |  Press Ctrl+C to stop     ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${RESET}"
echo ""

# ── 12. Keep alive until Ctrl+C ──────────────────────────────
wait
