# Guía de Ejecución Lab 1 — Mesa de Soporte (DGX Spark)

> **Entorno objetivo:** NVIDIA DGX Spark (`ucab-spark2`) vía PuTTY / SSH.  
> **Ubicación de trabajo en Spark:** `~/mesa-de-trabajo/lab1`  
> **Modelo:** `/srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`

---

## Paso 0: Preparar entorno y verificar prerequisitos

Copia y pega en PuTTY para crear la carpeta y ejecutar el script de verificación rápida:

```bash
mkdir -p ~/mesa-de-trabajo/lab1
cd ~/mesa-de-trabajo/lab1
```

Si deseas correr la verificación rápida directamente (puedes crear el script pegándolo o correr estas comprobaciones básicas):

```bash
# Verificar existencia del modelo
ls -lh /srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf

# Verificar binario llama-server
which llama-server || ls -lh ~/llama.cpp/build/bin/llama-server

# Verificar disponibilidad del puerto 8080
ss -tlnp | grep 8080
```

---

## Paso 1: Descargar los archivos del laboratorio vía `curl` o `wget`

Descarga los archivos del lab directamente desde nuestro repositorio (`Jrgil20/IA_Aplicada`) a `~/mesa-de-trabajo/lab1`:

```bash
mkdir -p ~/mesa-de-trabajo/lab1
cd ~/mesa-de-trabajo/lab1

# 1. Descargar dataset de tickets (CSV)
curl -fsSL -o tickets_tramontana.csv https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/tickets_tramontana.csv

# 2. Descargar script de verificación previa (preflight.sh)
curl -fsSL -o preflight.sh https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/preflight.sh
chmod +x preflight.sh

# 3. Descargar archivo de prompts para OpenCode
curl -fsSL -o prompts.md https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/prompts.md

# (Opcional) Si prefieres usar wget en vez de curl:
# wget -O tickets_tramontana.csv https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/tickets_tramontana.csv
# wget -O preflight.sh https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/preflight.sh && chmod +x preflight.sh
# wget -O prompts.md https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/prompts.md

# Verificar que los 85 tickets están presentes (86 líneas con header)
wc -l tickets_tramontana.csv
```

---

## Paso 2: Iniciar el servidor local (`llama-server`)

Abre una sesión / terminal de PuTTY (o usa `tmux` / `screen` / segundo terminal) para dejar el servidor de inferencia corriendo:

```bash
# Ubicar el binario de llama-server
LLAMA_BIN=$(which llama-server 2>/dev/null || echo "$HOME/llama.cpp/build/bin/llama-server")

# Iniciar servidor con descarga completa de capas a GPU
$LLAMA_BIN \
  -m /srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 8192 \
  --n-gpu-layers 99
```

> **Verificación rápida de salud del servidor (en otra terminal):**
> ```bash
> curl http://localhost:8080/health
> ```

---

## Paso 3: Configurar y verificar OpenCode CLI

En otra terminal de PuTTY en `~/mesa-de-trabajo/lab1`, configura las variables de entorno para que OpenCode interactúe con el endpoint de `llama-server`:

```bash
export OPENAI_BASE_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="no-key-required"

# Validar que opencode responda
opencode --help
```

---

## Paso 4: Generar o descargar el clasificador (`classify_tickets.py`)

Para evitar los errores típicos de modelos al generar este script:
1. **Regla de duplicados:** Las descripciones vacías o menores a 10 caracteres **NO** son duplicadas entre sí (sino se marcan 84 duplicados falsos).
2. **Strip de Markdown:** Si el modelo responde con ` ```json ... ``` `, debe limpiarse antes de hacer `json.loads`.
3. **Endpoint:** Enviar el JSON directamente a `http://localhost:8080/v1/chat/completions`.

Tienes tres opciones:

### Opción A: Descargar directamente el script afinado y probado (Recomendado)
Para asegurar que no haya fallas de sintaxis ni conteos incorrectos:

```bash
cd ~/mesa-de-trabajo/lab1
curl -fsSL -o classify_tickets.py https://raw.githubusercontent.com/Jrgil20/IA_Aplicada/main/labs/lab1/classify_tickets.py
chmod +x classify_tickets.py
```

### Opción B: Generar con OpenCode (Modo no interactivo)
```bash
cd ~/mesa-de-trabajo/lab1

opencode run "Write classify_tickets.py to classify tickets from tickets_tramontana.csv using standard library (csv, json, urllib.request) via http://localhost:8080/v1/chat/completions. IMPORTANT RULES: 1. Only non-empty descriptions with length > 10 chars can be duplicates; empty descriptions are NOT duplicates. 2. If model returns markdown codeblocks, strip them before json.loads. 3. Return JSON with categoria (facturacion/tecnico/ventas/otro), urgencia (baja/media/alta), and single-sentence resumen in Spanish. 4. Fallback to sin_clasificar on error. 5. Save output sorted by urgency into tickets_clasificados.json."
```

### Opción C: Modo interactivo en OpenCode (Prompt afinado)
Abre OpenCode en `~/mesa-de-trabajo/lab1`:
```bash
cd ~/mesa-de-trabajo/lab1
opencode
```

Pega este prompt afinado:

```markdown
Write a complete, robust Python script named `classify_tickets.py` to classify support tickets from `tickets_tramontana.csv` using a local LLM server running on `http://localhost:8080/v1/chat/completions`.

### Data Details
- Input file: `tickets_tramontana.csv`
- Columns: `Cliente`, `Asunto`, `Nº Ticket`, `Fecha de creación`, `Canal`, `Descripción del problema`, `Estado`, `Agente`.
- Edge cases in data:
  1. Missing descriptions: some rows have empty "Descripción del problema"; use the "Asunto" column as text to classify.
  2. Empty descriptions are NOT duplicates of each other! Only non-empty descriptions (> 10 chars) can be flagged as duplicates.
  3. Language: some tickets are in English.
  4. Dirty ticket IDs and varied dates.

### Functional Requirements
1. Standard libraries only (`csv`, `json`, `urllib.request`, `re`) - no external pip dependencies.
2. Read all 85 tickets from `tickets_tramontana.csv`.
3. Normalize descriptions (lowercase, strip punctuation) to detect duplicate descriptions and flag `es_duplicado: true/false`.
4. Call `http://localhost:8080/v1/chat/completions` with low temperature (0.1).
5. Strip markdown code fences (```json ... ```) from the LLM output before parsing with `json.loads`.
6. Output JSON fields:
   - "categoria": one of ["facturacion", "tecnico", "ventas", "otro"]
   - "urgencia": one of ["baja", "media", "alta"]
   - "resumen": single sentence in Spanish.
7. Graceful error handling: On network timeout or parse failure, fallback to `categoria: "sin_clasificar"` and `urgencia: "sin_clasificar"`.
8. Output: Save the full enriched list ordered with highest urgency first ("alta" > "media" > "baja" > "sin_clasificar") into `tickets_clasificados.json`.
9. Print a clean summary table to stdout with counts per category and urgency, plus duplicates detected.
```

---

## Paso 5: Ejecución del script y validación de resultados

Ejecuta el script generado:

```bash
cd ~/mesa-de-trabajo/lab1
python3 classify_tickets.py
```

### Verificación de los criterios de éxito:

```bash
# 1. Verificar total procesado (deben ser 85 tickets)
python3 -c "import json; data=json.load(open('tickets_clasificados.json')); print('Total clasificados:', len(data))"

# 2. Conteo por urgencia y detección de 'sin_clasificar'
python3 -c "
import json
from collections import Counter
data = json.load(open('tickets_clasificados.json'))
urgencias = Counter(item.get('urgencia', 'sin_clasificar') for item in data)
categorias = Counter(item.get('categoria', 'sin_clasificar') for item in data)
print('Urgencias:', dict(urgencias))
print('Categorias:', dict(categorias))
duplicados = [item for item in data if item.get('es_duplicado')]
print(f'Duplicados detectados: {len(duplicados)}')
"
```
