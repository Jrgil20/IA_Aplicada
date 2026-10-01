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

## Paso 4: Generar el clasificador con OpenCode

Tienes dos formas de ejecutar OpenCode para generar `classify_tickets.py`:

### Opción A: Modo no interactivo (un solo comando directo)
Ejecuta OpenCode pasándole directamente el prompt desde la terminal o leyendo el archivo `prompts.md`:

```bash
cd ~/mesa-de-trabajo/lab1

opencode run "Write a complete, robust Python script named classify_tickets.py to classify support tickets from tickets_tramontana.csv using standard libraries only (csv, json, urllib.request). Connect to http://localhost:8080/v1/chat/completions. Read all 85 tickets, handle missing descriptions and English text, detect duplicate descriptions by flagging es_duplicado: true/false. For each ticket output JSON with categoria (facturacion/tecnico/ventas/otro), urgencia (baja/media/alta), and a one-sentence resumen. If an error occurs, fallback to sin_clasificar. Save output ordered by urgency (alta first) into tickets_clasificados.json and print summary counts."
```

### Opción B: Modo interactivo
Abre la consola de OpenCode dentro del directorio:

```bash
cd ~/mesa-de-trabajo/lab1
opencode
```
Y dentro de la sesión interactiva, pega el contenido del prompt de [`prompts.md`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab1/prompts.md).

Al finalizar, verifica que `classify_tickets.py` fue creado:
```bash
ls -lh classify_tickets.py
head -n 20 classify_tickets.py
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
