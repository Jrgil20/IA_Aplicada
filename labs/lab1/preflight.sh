#!/usr/bin/env bash
# ==============================================================================
# Lab 1 — Pre-flight Check
# Verifies that the DGX Spark environment is ready for the lab session.
# Run this BEFORE starting any lab work.
# ==============================================================================

set -euo pipefail

# --- Colors -------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

pass()  { echo -e "  ${GREEN}✔ PASS${NC}  $1"; ((PASS++)); }
fail()  { echo -e "  ${RED}✘ FAIL${NC}  $1"; ((FAIL++)); }
warn()  { echo -e "  ${YELLOW}⚠ WARN${NC}  $1"; ((WARN++)); }
header(){ echo -e "\n${CYAN}${BOLD}── $1 ──${NC}"; }

MODEL_PATH="/srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf"
WORK_DIR="$HOME/mesa-de-trabajo/lab1"
PORT=8080

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║     Lab 1 — Pre-flight Environment Check     ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo "  User:    $(whoami)"
echo "  Home:    $HOME"
echo "  Date:    $(date)"
echo ""

# --- 1. Model File ------------------------------------------------------------
header "1. Model File"

if [ -f "$MODEL_PATH" ]; then
    SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    pass "Model found: $MODEL_PATH ($SIZE)"
else
    fail "Model NOT found at $MODEL_PATH"
    echo "       Try: find /srv /models /home -name '*.gguf' -type f 2>/dev/null"
fi

# --- 2. llama-server Binary ---------------------------------------------------
header "2. llama-server Binary"

LLAMA_BIN=""
SEARCH_PATHS=(
    "$HOME/llama.cpp/build/bin/llama-server"
    "$HOME/llama.cpp/llama-server"
    "/usr/local/bin/llama-server"
    "/usr/bin/llama-server"
)

for p in "${SEARCH_PATHS[@]}"; do
    if [ -x "$p" ]; then
        LLAMA_BIN="$p"
        break
    fi
done

if [ -z "$LLAMA_BIN" ] && command -v llama-server &>/dev/null; then
    LLAMA_BIN=$(command -v llama-server)
fi

if [ -n "$LLAMA_BIN" ]; then
    pass "llama-server found: $LLAMA_BIN"
else
    fail "llama-server NOT found in common paths"
    echo "       Try: find ~ /usr -name 'llama-server' -type f 2>/dev/null"
fi

# --- 3. Port Availability -----------------------------------------------------
header "3. Port $PORT Availability"

if ss -tlnp 2>/dev/null | grep -q ":${PORT} " || netstat -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    warn "Port $PORT is ALREADY IN USE (llama-server may already be running)"
    echo "       Check: ss -tlnp | grep $PORT"
else
    pass "Port $PORT is available"
fi

# --- 4. Python ----------------------------------------------------------------
header "4. Python Environment"

if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    pass "Python3 found: $PY_VER"
else
    fail "Python3 NOT found"
fi

# Check key modules
for mod in csv json urllib.request http.client; do
    if python3 -c "import $mod" 2>/dev/null; then
        pass "Module '$mod' available"
    else
        fail "Module '$mod' NOT available"
    fi
done

# Check 'requests' (optional but useful)
if python3 -c "import requests" 2>/dev/null; then
    pass "Module 'requests' available (optional)"
else
    warn "Module 'requests' not installed (script will use urllib instead)"
    echo "       Install: pip3 install requests"
fi

# --- 5. OpenCode --------------------------------------------------------------
header "5. OpenCode"

if command -v opencode &>/dev/null; then
    pass "opencode binary found: $(command -v opencode)"

    # Check for config
    CONFIG_LOCATIONS=(
        "$HOME/.opencode/config.json"
        "$HOME/.opencode.json"
        "$HOME/.config/opencode/config.json"
    )
    CONFIG_FOUND=""
    for cfg in "${CONFIG_LOCATIONS[@]}"; do
        if [ -f "$cfg" ]; then
            CONFIG_FOUND="$cfg"
            break
        fi
    done

    if [ -n "$CONFIG_FOUND" ]; then
        pass "Config found: $CONFIG_FOUND"
        if grep -qi "8080\|localhost\|127.0.0.1" "$CONFIG_FOUND" 2>/dev/null; then
            pass "Config references local server (port 8080)"
        else
            warn "Config does NOT reference localhost:8080 — may need reconfiguration"
            echo "       Review: cat $CONFIG_FOUND"
        fi
    else
        warn "No OpenCode config file found — needs configuration"
        echo "       Check: opencode --help"
    fi
else
    fail "opencode NOT found in PATH"
    echo "       Check: which opencode || find ~ -name 'opencode' -type f 2>/dev/null"
fi

# --- 6. Network (GitHub access for wget) --------------------------------------
header "6. Network Access"

CSV_URL="https://raw.githubusercontent.com/rsanchezsoutec/tramontana-datos-ficticios/main/01_mesa_de_soporte/tickets_tramontana.csv"

if command -v wget &>/dev/null; then
    pass "wget available"
elif command -v curl &>/dev/null; then
    pass "curl available (will use curl instead of wget)"
else
    fail "Neither wget nor curl found"
fi

if wget -q --spider "$CSV_URL" 2>/dev/null || curl -sI "$CSV_URL" 2>/dev/null | grep -q "200"; then
    pass "GitHub raw URL reachable"
else
    warn "Cannot reach GitHub — CSV must be uploaded manually"
fi

# --- 7. Working Directory -----------------------------------------------------
header "7. Working Directory"

if [ -d "$WORK_DIR" ]; then
    pass "Working directory exists: $WORK_DIR"
    FILE_COUNT=$(ls -1 "$WORK_DIR" 2>/dev/null | wc -l)
    echo "       Files present: $FILE_COUNT"
else
    warn "Working directory does not exist yet: $WORK_DIR"
    echo "       Will be created: mkdir -p $WORK_DIR"
fi

# --- 8. Disk Space ------------------------------------------------------------
header "8. Disk Space"

AVAIL=$(df -h "$HOME" | awk 'NR==2 {print $4}')
AVAIL_KB=$(df "$HOME" | awk 'NR==2 {print $4}')

if [ "$AVAIL_KB" -gt 1048576 ] 2>/dev/null; then
    pass "Disk space available: $AVAIL"
else
    warn "Low disk space: $AVAIL — may cause issues"
fi

# --- 9. GPU Status ------------------------------------------------------------
header "9. GPU / Unified Memory"

if command -v nvidia-smi &>/dev/null; then
    pass "nvidia-smi available"
    echo ""
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free \
               --format=csv,noheader,nounits 2>/dev/null | while IFS=',' read -r name total used free; do
        echo -e "       GPU:  ${BOLD}$name${NC}"
        echo "       VRAM: ${used}MiB / ${total}MiB (${free}MiB free)"
    done
else
    warn "nvidia-smi not found — cannot check GPU"
fi

# --- Summary ------------------------------------------------------------------
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                   SUMMARY                    ║${NC}"
echo -e "${BOLD}╠══════════════════════════════════════════════╣${NC}"
echo -e "║  ${GREEN}PASS: $PASS${NC}    ${YELLOW}WARN: $WARN${NC}    ${RED}FAIL: $FAIL${NC}               ║"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"

if [ "$FAIL" -gt 0 ]; then
    echo -e "\n${RED}${BOLD}  ✘ Environment NOT ready — fix FAIL items before starting.${NC}"
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo -e "\n${YELLOW}${BOLD}  ⚠ Environment mostly ready — review WARN items.${NC}"
    exit 0
else
    echo -e "\n${GREEN}${BOLD}  ✔ Environment ready — proceed with the lab!${NC}"
    exit 0
fi
