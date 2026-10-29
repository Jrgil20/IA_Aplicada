# INFORME FINAL DE EJECUCIÓN · WORKSHOP AGENTES DE CÓDIGO
## Especialización en IA Aplicada · Soutec / UCAB
### Plataforma de Cómputo: NVIDIA DGX Spark (`ucab-spark2`) · Octubre 2026

---

## 1. Ficha Técnica y Entorno de Ejecución

| Parámetro | Detalle Técnico |
| :--- | :--- |
| **Estación de Trabajo** | NVIDIA DGX Spark (`ucab-spark2`, IP `192.168.6.34`) |
| **Arquitectura de Cómputo** | NVIDIA GB10 Superchip, 128 GB Memoria Unificada |
| **Modelo Servido** | `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` (`/srv/models/`) |
| **Motor de Inferencia** | `llama-server` (puerto `127.0.0.1:8080`, `-ngl 99`, contexto 393k tokens) |
| **Consumo de Memoria VRAM/RSS** | **~8,03 GB** (`8.029.400 KB`, 6,3% de los 128 GB disponibles) |
| **Herramientas de Agente** | OpenCode CLI 1.18.35 + Skills de Claude Code + Bash Pipeline |
| **Directorio de Trabajo en Spark** | `/home/ucab-spark2/mesa-de-trabajo-equipo-1/lab3/` |
| **Servidor HTTP Local** | Activo en background en `http://192.168.6.34:8000/` |

---

## 2. Resumen Ejecutivo de los 5 Problemas Resueltos

### Problema 1: La Reunión con Proveedores
- **Criterio de Falla Consensuado:** Criterio Mixto Ponderado con Prioridad Financiera ($60\%$ Monto en Mora, $25\%$ Días Máximos de Retraso, $15\%$ Entregas Tardías Históricas).
- **Decisión Ejecutiva:** Iniciar la reunión con **P04 (Importadora Margarita)** por concentrar **$44.978,06 USD** (el 43,2% de la mora de toda la empresa), 100% de pedidos pendientes vencidos (hasta 38 días de mora) y 14 entregas históricas fuera de plazo.
- **Entregables:** `salidas/criterio-problema-1.md` y `salidas/1-reunion-proveedores.html`.

### Problema 2: El Informe de los Lunes
- **Comando Unificado:** Script ejecutable `./informe-lunes.sh` que corre en un solo paso independientemente de la herramienta usada (OpenCode, Claude Code o terminal directa).
- **Proveedores Críticos Notificados (> 10 días de mora):**
  - **P04 (Importadora Margarita):** 4 pedidos, $44.978,06 USD.
  - **P06 (Tecnología Zulia):** 4 pedidos (3 saneados), $20.214,17 USD.
  - **P01 (Distribuidora Andina):** 3 pedidos, $2.309,40 USD (atraso máximo de 50 días).
  - **P02 (Logística del Ávila):** 2 pedidos, $1.858,50 USD.
- **Garantía de Seguridad:** Redacción de 4 borradores de reclamo en Markdown. Cumplimiento estricto de la directiva de compras: **cero auto-envío de correos**.
- **Entregables:** `informe-lunes.sh`, `.claude/skills/informe-lunes/SKILL.md` y `salidas/2-lunes/`.

### Problema 3: La Auditoría de TI
- **Cumplimiento de las 3 Exigencias:**
  1. *Confinamiento de Claves y Contratos:* Blindaje de `.env` y `secretos/` mediante permisos de sistema operativo `chmod 0600` / `0700` y reglas declarativas en `opencode.json`.
  2. *Prohibición de Compartir Sesiones:* Directiva `"share": "disabled"` en la raíz del proyecto.
  3. *Configuración que viaja con el Repo:* Todo persistido en `opencode.json`, `AGENTS.md` y hook de Git.
- **Matriz de Red-Teaming (6 Vectores Probados):**
  - Lectura por herramienta y comando shell directo (`cat .env`): **BLOQUEADOS**.
  - Evasión por base64: **MITIGADA** por permisos POSIX `0600`.
  - Evasión por Python inline: **DIAGNÓSTICO HONESTO** para la auditora: los filtros regex de un agente no bastan frente a intérpretes completos si comparten el UID; se requiere containerización / Vault para producción.
  - Exfiltración Git: **BLOQUEADA** por pre-commit hook `.git/hooks/pre-commit`.
- **Entregables:** `scripts/test_universal_red_team.py`, `scripts/pre-commit-hook.sh` y `salidas/3-auditoria.html`.

### Problema 4: Finanzas no se fía (Calidad de Datos)
- **7 Filas Anómalas Reales Aisladas ($28.431,45 USD en juego):**
  1. Fila 73 (`PO-1072`, P02): Cantidad negativa `-703` (-$1.117,77).
  2. Fila 116 (`PO-1115`, P01): Precio unitario $0.00 (122 unidades sin cotizar).
  3. Fila 153 (`PO-1152`, P03): Paradoja temporal (entregado antes de pedirse).
  4. Fila 280 (`PO-1279`, P09): Proveedor huérfano inexistente en catálogo.
  5. Fila 305 (`PO-1303`, P06): Clon duplicado idéntico a la fila 304 ($67,05).
  6. Fila 312 (`PO-1310`, P06): Estado Entregado con fecha de entrega vacía.
  7. Fila 328 (`PO-1326`, P05): Estado Pendiente sin fecha comprometida ($18.701,28).
- **Marco Permanente de Gobernanza (5 Reglas):**
  1. Unicidad y deduplicación por PO-ID (`AGENTS.md` + pipeline).
  2. Rango físico estricto (cantidades y precios > 0).
  3. Integridad referencial contra catálogo de proveedores.
  4. Causalidad temporal y completitud de estados de entrega.
  5. Inmutabilidad de `pedidos.csv` y conciliación en doble columna (Bruto vs Cuarentena).
- **Entregables:** `scripts/validar_calidad_datos.py` y `salidas/4-calidad-datos.html`.

### Problema 5: El Tablero del Gerente General
- **Orquestación de Subagentes:** 4 subagentes especializados analíticos operando dentro del límite de consumo (< 56%).
- **Métricas C-Level Consolidadas:**
  - Presupuesto Total Saneado: **$1.173.427,95 USD** (Pareto Top 3 concentra 81,1%).
  - Confiabilidad Operativa Global (OTD %): **80,5%** (251 pedidos a tiempo de 312).
  - Capital en Mora Activa Total: **$103.220,11 USD**.
- **Posicionamiento en Matriz de Kraljic:**
  - **P04 (Margarita):** Estratégico Crítico -> Congelar pagos nuevos y exigir penalización.
  - **P01 (Andina):** Cuello de Botella -> Licitar proveedor alternativo por mora de 50 días.
  - **P05 (Llanos) y P06 (Zulia):** Apalancados -> Negociar descuentos por volumen y plazo a 60 días.
  - **P02 (Ávila) y P03 (Caroní):** Rutinarios -> Mantener operación automatizada.
- **Entregables:** `salidas/5-tablero-gerente.md` y `salidas/5-tablero-gerente.html`.

---

## 3. Portal Maestro Unificado en Spark

Todos los entregables anteriores quedaron consolidados en una interfaz SPA interactiva:
- **Archivo:** `/home/ucab-spark2/mesa-de-trabajo-equipo-1/lab3/salidas/index.html`
- **URL de Acceso en Red Local:** `http://192.168.6.34:8000/`

---
*Informe generado automáticamente y persistido en la estación DGX Spark.*
