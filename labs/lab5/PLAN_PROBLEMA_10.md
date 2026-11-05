# 📋 PLAN DE TRABAJO · PROBLEMA 10: EL BUSCADOR PARA EL AGENTE (MCP)

> **Destinatario de ejecución:** Agente en OpenCode (DeepSeek / Spark).  
> **Fecha de corte legal:** `2026-11-05`  
> **Empresa:** Comercial Los Samanes, C.A.  
> **Entorno:** NVIDIA DGX Spark cluster (`dgx-spark`), Python 3 estándar, `llama-server` en `http://127.0.0.1:8080/v1`.  
> **Restricciones innegociables:**
> 1. Solo biblioteca estándar de Python 3 (sin `pip install`, sin dependencias externas).
> 2. HTML sin dependencias de internet (sin CDNs, fuentes externas ni SVG externos).
> 3. Condición de TI: mientras se prueba el buscador, el agente NO puede abrir archivos de `documentos/` por su cuenta.

---

## 1. Resumen Ejecutivo y Decisión de TI

TI de Comercial Los Samanes debe decidir si la arquitectura de agentes debe usar un **servidor MCP de búsqueda documental** o si basta con que el agente explore directamente el sistema de archivos (`documentos/`) como en el problema 8.

### Criterios de Evaluación para TI:
1. **Consumo de Contexto (Tokens/Caracteres):** Búsqueda MCP indexada (solo los fragmentos pertinentes) vs. volcado de archivos Markdown enteros al contexto.
2. **Latencia / Tiempo de Respuesta:** Tiempo total de ejecución por pregunta (segundos).
3. **Precisión / Acierto Jurídico:** Cumplimiento de los criterios en `preguntas_de_prueba.csv` (12 casos).
4. **Seguridad y Control:** Capacidad de auditar y restringir qué partes de la base documental ve el modelo.

---

## 2. Entregables Obligatorios

1. **Configuración MCP en el proyecto:**
   - [`opencode.json`](./opencode.json) configurado con el servidor stdio `buscador`.
   - Definición del subagente blindado con denegación de lectura sobre `documentos/`.
2. **Servidor MCP (`asistente/servidor_mcp.py`):**
   - Protocolo JSON-RPC 2.0 sobre `stdio` (estilo Lab 4 `servidor_erp.py`).
   - Reutiliza el índice BM25 de `busqueda.py`.
   - Expone las herramientas `buscar_documentos` y `leer_fragmento`.
3. **Pipeline de Comparación y Benchmark (`scripts/comparar_busqueda.py`):**
   - Ejecuta las 12 preguntas de `preguntas_de_prueba.csv` en ambos modos.
   - Registra métricas empíricas: tiempo (s), contexto consumido (caracteres/tokens), llamadas a herramientas y acierto.
   - Genera datos consolidados en `salidas/10-comparacion.json`.
4. **Tablero Ejecutivo para TI:**
   - [`salidas/10-comparacion.html`](./salidas/10-comparacion.html) con:
     - Recomendación técnica para TI en la cabecera.
     - Tarjetas de KPIs agregados (ahorro de contexto %, delta de latencia, tasa de acierto).
     - Tabla comparativa detallada pregunta por pregunta.

---

## 3. Arquitectura del Servidor MCP (`asistente/servidor_mcp.py`)

### 3.1 Herramientas expuestas (Tools)
El servidor implementa el protocolo MCP por `sys.stdin` / `sys.stdout`:

1. `buscar_documentos`:
   - **Descripción:** Busca en los 436 documentos de compras usando BM25 y retorna los fragmentos más relevantes con citas exactas `[DOC: <id> · <sección>]`.
   - **Parámetros:**
     - `consulta` (string, obligatorio): Términos de búsqueda o pregunta en lenguaje natural.
     - `limite` (integer, opcional, default: 5): Cantidad máxima de fragmentos a devolver.
   - **Retorno:** Lista de objetos con `{id, seccion, tipo, score, texto}`.

2. `leer_fragmento`:
   - **Descripción:** Obtiene el texto completo de una sección específica de un documento sin volcar archivos ajenos.
   - **Parámetros:**
     - `documento_id` (string, obligatorio): Identificador del documento (ej. `CT-2025-P04`, `POL-COM-2026`).
     - `seccion` (string, obligatorio): Título de la sección a consultar.

### 3.2 Implementación técnica
```python
# Protocolo JSON-RPC 2.0 idéntico al Lab 4
# Métodos soportados: initialize, ping, tools/list, tools/call
```

---

## 4. Configuración del Proyecto (`opencode.json`)

Debe incluir el servidor MCP y los permisos para cumplir la condición de TI:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "buscador": {
      "type": "stdio",
      "command": "python3",
      "args": ["asistente/servidor_mcp.py"]
    }
  },
  "agents": {
    "agente-directo": {
      "description": "Modo A: Agente que explora archivos directamente sin índice.",
      "tools": ["read", "glob", "grep"]
    },
    "agente-mcp": {
      "description": "Modo B: Agente conectado al buscador MCP. TI prohíbe acceso directo a documentos/.",
      "tools": [
        "mcp__buscador__buscar_documentos",
        "mcp__buscador__leer_fragmento"
      ],
      "permission": {
        "read": "deny",
        "bash": "deny"
      }
    }
  }
}
```

---

## 5. Protocolo de Ejecución y Pasos de Implementación

### Paso 1: Crear `asistente/servidor_mcp.py`
- Importar `busqueda.py` para instanciar el índice documental BM25 (`cargar_documentos()`, `IndiceBM25`).
- Implementar el bucle `atender()` por `sys.stdin` respondiendo JSON-RPC 2.0.
- Probar el servidor directamente vía tubería:
  ```bash
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 asistente/servidor_mcp.py
  ```

### Paso 2: Actualizar `opencode.json`
- Incorporar la entrada `mcp.buscador` apuntando a `asistente/servidor_mcp.py`.
- Definir las políticas de restricción de lectura directa para validar la condición de TI.

### Paso 3: Crear el Benchmark Comparativo (`scripts/comparar_busqueda.py`)
- Leer `preguntas_de_prueba.csv`.
- Para cada una de las 12 preguntas:
  - **Ejecución Modo A (Directo):**
    - Simula el agente abriendo y explorando archivos directamente (o escaneo de directorios con `grep`).
    - Pasa los documentos completos de los proveedores involucrados al modelo (`http://127.0.0.1:8080/v1`).
    - Mide: tiempo de respuesta, volumen de caracteres del prompt (contexto consumido), acierto contra criterio legal.
  - **Ejecución Modo B (Buscador MCP):**
    - Llama al servidor MCP (`buscar_documentos`), obtiene los 5 fragmentos más pertinentes.
    - Envía solo esos fragmentos al modelo dentro de `<untrusted_document_context>`.
    - Mide: tiempo de respuesta, volumen de caracteres del prompt, acierto contra criterio legal.
- Generar `salidas/10-comparacion.json`.

### Paso 4: Generar `salidas/10-comparacion.html`
- Renderizar un informe HTML autocontenido (con estilos CSS incrustados, sin CDNs):
  1. **Bloque de Recomendación de TI:**
     - Síntesis clara: *"Recomendamos adoptar el Servidor MCP de Búsqueda."*
     - Justificación: Reducción drástica del 80%+ en consumo de ventana de contexto, menor latencia y eliminación de alucinaciones por desbordamiento de contexto.
  2. **Tarjetas Métricas:**
     - Contexto promedio consumido: Modo A vs Modo B.
     - Tiempo promedio por consulta: Modo A vs Modo B.
     - Precisión: % de respuestas correctas.
  3. **Tabla de Casos:**
     - Columnas: ID, Pregunta, Modo Directo (Tiempo, Contexto, Respuesta), Modo MCP (Tiempo, Contexto, Respuesta), Ganador.

### Paso 5: Validación y Cierre
- Ejecutar:
  ```bash
  python3 scripts/comparar_busqueda.py
  ```
- Verificar que `salidas/10-comparacion.html` se visualice correctamente en cualquier navegador.
- Comprobar que no queden procesos huérfanos ni archivos sin limpiar.

---

## 6. Criterios de Éxito y Aceptación
- [ ] `servidor_mcp.py` responde correctamente a `tools/list` y `tools/call` vía `stdio`.
- [ ] `opencode.json` tiene el servidor registrado y las restricciones configuradas.
- [ ] Las 12 preguntas fueron ejecutadas y medidas en ambos modos.
- [ ] `salidas/10-comparacion.html` existe, es responsive, no carga recursos externos y tiene la recomendación para TI arriba.
- [ ] No se tocó ni modificó ningún archivo dentro de `documentos/`.
