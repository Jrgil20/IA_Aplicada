#!/usr/bin/env bash
# ==============================================================================
# Git Pre-commit Hook — Bloqueo Universal de Fuga de Secretos
# Aplica a cualquier agente (OpenCode, Claude Code, Cursor, Antigravity) y usuarios.
# ==============================================================================

FORBIDDEN_PATTERNS=(".env" "secretos/" "clave" "ERP_API_KEY")

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if git diff --cached --name-only | grep -E "$pattern" >/dev/null 2>&1; then
        echo "❌ [SEGURIDAD RECHAZADA] Intento de commit con archivo prohibido: $pattern"
        echo "   La política corporativa prohíbe versionar secretos o credenciales."
        exit 1
    fi
    if git diff --cached | grep -i "ERP_API_KEY" >/dev/null 2>&1; then
        echo "❌ [SEGURIDAD RECHAZADA] Intento de commit con credenciales expuestas (ERP_API_KEY)."
        exit 1
    fi
done

exit 0
