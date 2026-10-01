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

## Paso 1: Descargar los datos del problema vía `curl` o `wget`

Descarga directa del dataset de tickets desde GitHub al directorio de trabajo en la Spark:

```bash
cd ~/mesa-de-trabajo/lab1

# Con wget:
wget -O tickets_tramontana.csv https://raw.githubusercontent.com/rsanchezsoutec/tramontana-datos-ficticios/main/01_mesa_de_soporte/tickets_tramontana.csv

# O con curl (si wget no está disponible):
# curl -fsSL -o tickets_tramontana.csv https://raw.githubusercontent.com/rsanchezsoutec/tramontana-datos-ficticios/main/01_mesa_de_soporte/tickets_tramontana.csv

# Confirmar 86 líneas (header + 85 tickets)
wc -l tickets_tramontana.csv
head -n 5 tickets_tramontana.csv
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

En otra terminal de PuTTY en `~/mesa-de-trabajo/lab1`, verifica OpenCode y asegúrate de que apunte a `http://localhost:8080/v1`:

```bash
# Validar versión y ayuda
opencode --help

# Si OpenCode usa un archivo de configuración local o variables de entorno:
export OPENAI_BASE_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="no-key-required"
```

---

## Paso 4: Generar el clasificador con OpenCode

Abre OpenCode en la carpeta `~/mesa-de-trabajo/lab1` pasándole el prompt detallado de [prompts.md](file:///home/jr_g/Develop/IA_Aplicada/labs/lab1/prompts.md) para que genere `classify_tickets.py`.

El script generado procesará `tickets_tramontana.csv`, se comunicará con `http://localhost:8080/v1/chat/completions` y guardará los resultados en `tickets_clasificados.json`.

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
