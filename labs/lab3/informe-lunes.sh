#!/usr/bin/env bash
# ==============================================================================
# Procedimiento Unificado de los Lunes — Departamento de Compras
# Genera el estado de pedidos atrasados para el jefe y borradores de correos.
# Funciona igual en terminal local, OpenCode o Claude Code.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "🚀 Iniciando Procedimiento Semanal de Compras (Lunes)"
echo "=========================================================="

# 1. Auditoría de Seguridad Previa
echo "🔒 [1/4] Ejecutando verificación de seguridad y permisos..."
python3 scripts/verificar_seguridad.py

# 2. Control de Calidad de Datos y Cuarentena
echo "🧹 [2/4] Auditando calidad de datos e integridad contable..."
python3 scripts/validar_calidad_datos.py

# 3. Generación de Entregables de Negocio
echo "📊 [3/4] Procesando pedidos atrasados saneados con > 10 días de mora..."
python3 scripts/generar_informe_lunes.py

# 4. Resumen de Salidas
echo "📁 [4/4] Entregables disponibles en salidas/2-lunes/:"
ls -lh salidas/2-lunes/

echo ""
echo "✅ PROCEDIMIENTO COMPLETADO EXITOSAMENTE"
echo "   - Tablero para el jefe: salidas/2-lunes/estado-pedidos-jefe.html"
echo "   - Borradores de reclamo generados (P01, P02, P04, P06)"
echo "   - POLÍTICA DE SEGURIDAD: Ningún correo fue enviado automáticamente."
echo "   - CALIDAD DE DATOS: Registros anómalos aislados en salidas/4-calidad-datos.html"
echo "=========================================================="
