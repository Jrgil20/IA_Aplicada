#!/usr/bin/env bash
# Arranca el Asistente de Compras en el puerto del equipo (8501 por defecto).
set -euo pipefail
cd "$(dirname "$0")"
PUERTO="${1:-8501}"
exec python3 servidor.py --host 0.0.0.0 --puerto "$PUERTO"
