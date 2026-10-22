#!/usr/bin/env bash
# ==============================================================================
# Iniciar Lab 2 - NVIDIA DGX Spark (Modelos + Configuración Base + App Web)
# ==============================================================================
set -e

BASE_DIR="/home/ucab-spark1/Documents/Reps/Clase4"
LLAMA_BIN="/home/ucab-spark1/llama.cpp/build/bin/llama-server"

# Rutas de Modelos
GEMMA_MODEL="/home/ucab-spark1/models/gemma-3-4b-it-GGUF/gemma-3-4b-it-Q8_0.gguf"
GEMMA_MMPROJ="/home/ucab-spark1/models/gemma-3-4b-it-GGUF/mmproj-model-f16.gguf"
GEMMA_PORT=8084
GEMMA_LOG="/home/ucab-spark1/gemma_vlm.log"

QWEN_MODEL="/srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf"
QWEN_PORT=8080
QWEN_LOG="/home/ucab-spark1/qwen_coder.log"

APP_PORT=8082
APP_LOG="$BASE_DIR/app.log"

get_pid_by_port() {
    local port=$1
    ss -tlpn 2>/dev/null | grep ":$port " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n1
}

detect_spark_ip() {
    hostname -I | tr ' ' '\n' | grep '^192.168.6\.' | head -n1 || echo "192.168.6.35"
}

detect_camera_ip() {
    if [ -n "$1" ]; then
        echo "$1"
        return
    fi
    local detected
    detected=$(ip neigh show dev eno2 2>/dev/null | grep -E '192\.168\.6\.[0-9]+' | grep -v 'FAILED' | head -n1 | awk '{print $1}')
    if [ -n "$detected" ]; then
        echo "$detected"
    else
        python3 -c "import json; print(json.load(open('$BASE_DIR/config.json'))['camera_ip'].split(':')[0])" 2>/dev/null || echo "192.168.6.44"
    fi
}

sync_config() {
    local s_ip
    s_ip=$(detect_spark_ip)
    local c_ip
    c_ip=$(detect_camera_ip "$1")

    echo "⚙️ Sincronizando configuración base en config.json..."
    python3 - "$s_ip" "$c_ip" "$APP_PORT" "$GEMMA_PORT" "$QWEN_PORT" "$BASE_DIR" << 'EOF'
import sys, json

s_ip = sys.argv[1]
c_ip = sys.argv[2]
app_port = int(sys.argv[3])
gemma_port = int(sys.argv[4])
qwen_port = int(sys.argv[5])
base_dir = sys.argv[6]

path = f"{base_dir}/config.json"
try:
    with open(path, "r") as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

cfg["spark_server_ip"] = s_ip
cfg["spark_server_port"] = app_port
cfg["camera_ip"] = f"{c_ip}:8080"
cfg["models"] = [
    {
        "name": "gemma-3-4b-it",
        "url": f"http://127.0.0.1:{gemma_port}/v1/chat/completions"
    },
    {
        "name": "qwen3-30b-coder",
        "url": f"http://127.0.0.1:{qwen_port}/v1/chat/completions"
    }
]

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)

print(f"   [✓] Spark Host: {s_ip}:{app_port}")
print(f"   [✓] Laptop Cámara: {c_ip}:8080")
print(f"   [✓] Gemma VLM: http://127.0.0.1:{gemma_port}")
print(f"   [✓] Qwen Coder: http://127.0.0.1:{qwen_port}")
EOF
}

start_models() {
    echo ""
    echo "🚀 Levantando modelos de inferencia en GPU Blackwell GB10..."

    # 1. Gemma 3 4B VLM
    local g_pid
    g_pid=$(get_pid_by_port $GEMMA_PORT)
    if [ -n "$g_pid" ]; then
        echo "   [✓] Gemma 3 4B VLM ya está corriendo (PID: $g_pid) en puerto $GEMMA_PORT."
    else
        echo "   [+] Iniciando Gemma 3 4B VLM (puerto $GEMMA_PORT)..."
        nohup "$LLAMA_BIN" \
            -m "$GEMMA_MODEL" \
            --mmproj "$GEMMA_MMPROJ" \
            --port "$GEMMA_PORT" \
            --host 0.0.0.0 \
            -ngl 99 \
            -c 4096 > "$GEMMA_LOG" 2>&1 &
        sleep 2
    fi

    # 2. Qwen 3 Coder 30B
    local q_pid
    q_pid=$(get_pid_by_port $QWEN_PORT)
    if [ -n "$q_pid" ]; then
        echo "   [✓] Qwen 3 Coder 30B ya está corriendo (PID: $q_pid) en puerto $QWEN_PORT."
    else
        echo "   [+] Iniciando Qwen 3 Coder 30B (puerto $QWEN_PORT)..."
        nohup "$LLAMA_BIN" \
            -m "$QWEN_MODEL" \
            --port "$QWEN_PORT" \
            --host 0.0.0.0 \
            -ngl 99 \
            -c 4096 > "$QWEN_LOG" 2>&1 &
        sleep 2
    fi
}

start_app() {
    echo ""
    echo "🌐 Levantando Flask Web Application (app.py)..."
    local a_pid
    a_pid=$(get_pid_by_port $APP_PORT)
    if [ -n "$a_pid" ]; then
        echo "   [✓] app.py ya está escuchando en puerto $APP_PORT (PID: $a_pid)."
    else
        echo "   [+] Iniciando app.py en segundo plano..."
        cd "$BASE_DIR"
        nohup python3 app.py > "$APP_LOG" 2>&1 &
        sleep 2
        a_pid=$(get_pid_by_port $APP_PORT)
        echo "   [✓] app.py levantado exitosamente (PID: $a_pid) en puerto $APP_PORT."
    fi
}

stop_all() {
    echo "🛑 Deteniendo todo el entorno de Lab 2..."
    local g_pid
    g_pid=$(get_pid_by_port $GEMMA_PORT)
    [ -n "$g_pid" ] && kill "$g_pid" && echo "   - Gemma 3 detenido (PID: $g_pid)"

    local q_pid
    q_pid=$(get_pid_by_port $QWEN_PORT)
    [ -n "$q_pid" ] && kill "$q_pid" && echo "   - Qwen Coder detenido (PID: $q_pid)"

    local a_pid
    a_pid=$(get_pid_by_port $APP_PORT)
    [ -n "$a_pid" ] && kill "$a_pid" && echo "   - App Web detenida (PID: $a_pid)"
    echo "Todos los servicios fueron detenidos."
}

show_status() {
    local s_ip
    s_ip=$(detect_spark_ip)
    echo ""
    echo "================================================================="
    echo "📊 ESTADO DEL SISTEMA LAB 2 EN NVIDIA DGX SPARK"
    echo "================================================================="
    local g_pid
    g_pid=$(get_pid_by_port $GEMMA_PORT)
    local q_pid
    q_pid=$(get_pid_by_port $QWEN_PORT)
    local a_pid
    a_pid=$(get_pid_by_port $APP_PORT)

    [ -n "$g_pid" ] && echo "🟢 Gemma 3 4B VLM:       ACTIVO en puerto $GEMMA_PORT (PID $g_pid)" || echo "🔴 Gemma 3 4B VLM:       INACTIVO"
    [ -n "$q_pid" ] && echo "🟢 Qwen 3 Coder 30B:     ACTIVO en puerto $QWEN_PORT (PID $q_pid)" || echo "🔴 Qwen 3 Coder 30B:     INACTIVO"
    [ -n "$a_pid" ] && echo "🟢 App Web Flask:        ACTIVO en puerto $APP_PORT (PID $a_pid)" || echo "🔴 App Web Flask:        INACTIVO"

    echo ""
    if [ -n "$a_pid" ]; then
        local cam_status
        cam_status=$(curl -s --connect-timeout 2 http://127.0.0.1:$APP_PORT/camera_status 2>/dev/null || echo '{"connected": false}')
        echo "📷 Estado de Conexión con Cámara Laptop: $cam_status"
        echo "🔗 Panel Web URL: http://$s_ip:$APP_PORT"
    fi

    echo ""
    echo "🎮 Memoria GPU Asignada (nvidia-smi):"
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null || true
    echo "================================================================="
}

case "$1" in
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    restart)
        stop_all
        sleep 2
        sync_config "$2"
        start_models
        start_app
        show_status
        ;;
    start|""|*)
        TARGET_CAM_IP=""
        if [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            TARGET_CAM_IP="$1"
        elif [ "$1" == "start" ] && [[ "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            TARGET_CAM_IP="$2"
        fi

        sync_config "$TARGET_CAM_IP"
        start_models
        start_app
        show_status
        ;;
esac
