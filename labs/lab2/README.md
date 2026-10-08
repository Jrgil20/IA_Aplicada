# Guía de Ejecución Lab 2 — VLM Interactivo con Webcam (DGX Spark)

> **Entorno objetivo:** NVIDIA DGX Spark (`ucab-spark2`, 128 GB Unified Memory) + PC Local con Webcam  
> **Modelos disponibles en Spark:** `gemma3:4b`, `gemma3:12b`, `gemma3:27b` (vía Ollama)  
> **Puerto del servicio:** `11434` (Ollama API / OpenAI-compatible endpoint)  
> **Propósito:** Guía de ejecución para el estudiante y soporte contextual dinámico para el agente de codificación (OpenCode).

---

## 🏗️ Topología del Laboratorio

No procesamos el video directo en la Spark porque no tiene cámara conectada:
1. **La PC del alumno** ejecuta la captura de video con la webcam mediante OpenCV, comprime el cuadro en JPEG y lo codifica en Base64.
2. **La PC del alumno** envía la petición HTTP (JSON con la imagen y el prompt) al endpoint de la Spark.
3. **La DGX Spark** procesa la inferencia en su GPU Blackwell / memoria unificada y devuelve la respuesta en texto.

```
[ Webcam PC ] ---> [ Script Python (OpenCV) ] ---> HTTP POST (Base64) ---> [ DGX Spark (Ollama Gemma 3) ]
                           ^                                                               |
                           |                                                               |
                     [ Muestra UI ] <---------------- Devuelve respuesta JSON <------------+
```

---

## Paso 0: Preparación en la DGX Spark (vía SSH / PuTTY)

Conéctate por terminal a la Spark y ejecuta las siguientes comprobaciones:

### 1. Verificar presencia de los modelos Gemma 3
```bash
ollama list
```
Deberías ver listados:
- `gemma3:4b`
- `gemma3:12b`
- `gemma3:27b`

Si no los ves o falta alguno, repórtalo de inmediato o descárgalo si tienes permisos:
```bash
ollama pull gemma3:4b
```

### 2. Verificar que Ollama escuche peticiones externas (0.0.0.0)
Por defecto en Linux, Ollama puede iniciar escuchando únicamente en `127.0.0.1`. Para permitir que la PC del alumno se conecte por red, el servicio debe escuchar en `0.0.0.0:11434`.

Comprueba los puertos activos:
```bash
ss -tlnp | grep 11434
```

- Si dice `0.0.0.0:11434` o `*:11434`: **¡Listo! Ya está disponible en la red.**
- Si dice `127.0.0.1:11434` o no está corriendo:
  ```bash
  # Detener servicio local si está como systemd
  sudo systemctl stop ollama 2>/dev/null || pkill ollama
  
  # Iniciar exponiendo todas las interfaces
  OLLAMA_HOST=0.0.0.0:11434 ollama serve &
  ```

---

## Paso 1: Configuración en la PC del Alumno (Local)

En la máquina física donde está conectada la webcam:

### 1. Configurar IP estática en la subred de la Spark (`192.168.6.0/26`)
> [!IMPORTANT]
> La Spark está configurada en una subred **/26** (`192.168.6.0/26`, máscara `255.255.255.192`). Tu IP asignada debe estar estrictamente dentro del rango **`192.168.6.2` a `192.168.6.62`** (ej. `192.168.6.50/26`). Si asignas una IP fuera de este rango (como `.100`), la Spark no responderá al no encontrar ruta local.
>
> Para configurar tu placa Ethernet en Linux preservando el WiFi:
> ```bash
> nmcli connection modify "Wired connection 1" \
>   ipv4.addresses 192.168.6.50/26 \
>   ipv4.method manual \
>   ipv4.never-default yes
> nmcli connection up "Wired connection 1"
> ```
> Si tienes problemas de enlace o ARP, revisa la [Guía de Troubleshooting de Red de la Spark](../../docs/dgx/network-troubleshooting.md).

### 2. Test de conectividad hacia la Spark
Abre una terminal en tu PC (PowerShell, WSL o bash) y prueba que llegas al servicio (reemplaza `<IP_SPARK>` por la IP asignada a la Spark, ej. `192.168.6.42`):

```bash
ping -c 3 192.168.6.42
curl http://192.168.6.42:11434/api/tags
```
Debe devolverte un JSON con la lista de modelos. Si da timeout o conexión rechazada, revisa la IP o el firewall del puerto 11434.

### 3. Instalar dependencias del cliente
Asegúrate de contar con Python 3 y las librerías necesarias:
```bash
pip install opencv-python requests
```

---

## Paso 2: Ejecución del Cliente de Webcam

En la carpeta del laboratorio en tu PC, ejecuta el script interactivo [`webcam_vlm.py`](./webcam_vlm.py):

```bash
# Ejemplo usando el modelo liviano (4B):
python3 webcam_vlm.py --host http://<IP_SPARK>:11434 --model gemma3:4b

# Si deseas evaluar el modelo de 12B:
python3 webcam_vlm.py --host http://<IP_SPARK>:11434 --model gemma3:12b
```

### Controles interactivos en la ventana de video:
- `BARRA ESPACIADORA`: Toma una captura instantánea (snapshot), envía el frame al VLM y muestra la respuesta en consola y sobre la imagen.
- `P`: Cambia el prompt de consulta (te pedirá ingresar una nueva pregunta por consola).
- `A`: Activa/Desactiva el modo automático continuo (muestreo cada 3 segundos con control de latencia).
- `Q` o `ESC`: Cierra la cámara y finaliza el programa.

---

## Paso 3: Soporte Dinámico para el Agente (OpenCode / Copilot)

Si estás usando un agente de codificación en clase para extender o modificar el ejercicio, puedes usar estos prompts contextuales:

### Prompt A: Agregar Bounding Boxes / Detección Visual
```text
Contexto: Estamos interactuando con Gemma 3 en una DGX Spark a través de webcam_vlm.py.
Tarea: Modifica el script para solicitarle al modelo que devuelva las coordenadas de los objetos identificados en formato JSON estructurado {"label": str, "box_2d": [ymin, xmin, ymax, xmax]} y dibuja los rectángulos correspondientes sobre el frame con OpenCV.
```

### Prompt B: Modo Asistente de Lectura (OCR y Resumen)
```text
Contexto: Script de webcam conectado a Gemma 3 multimodal.
Tarea: Agrega una función o atajo de teclado 'O' que configure un prompt de sistema especializado en OCR: extraer todo el texto visible en la captura, corregir posibles errores de lectura y devolver una transcripción limpia formateada en Markdown.
```

### Prompt C: Comparativa Automática de Rendimiento (Benchmark)
```text
Contexto: Evaluando gemma3:4b vs gemma3:12b vs gemma3:27b.
Tarea: Implementa un modo benchmark que, al pulsar 'B', envíe el mismo frame secuencialmente a los tres modelos, registre los tiempos de primera respuesta, velocidad de generación y compare la precisión de las tres respuestas en un archivo CSV o tabla en consola.
```

---

## Paso 4: Prácticas y Experimentos para la Clase

Los estudiantes deben realizar las siguientes pruebas y registrar sus observaciones:

1. **Prueba de Razonamiento Visual:** Mostrarle a la cámara un problema escrito a mano (ej. ecuación simple o circuito básico) y pedirle la solución paso a paso.
2. **Prueba de Detección de Detalles:** Colocar dos objetos similares frente a la cámara y pedirle que identifique las diferencias sutiles (color, posición relativa, texto en etiquetas).
3. **Impacto de Resolución de Imagen:** Modificar la resolución del frame capturado (320x240 vs 640x480 vs 1280x720) y registrar la variación en tiempo de respuesta del modelo.

---

## 🛠️ Resolución de Problemas Frecuentes

| Síntoma | Causa Probable | Solución |
| :--- | :--- | :--- |
| `Cannot open camera: 0` | Webcam no detectada o bloqueada por otra app (Zoom, Teams). | Cierra aplicaciones que usen la cámara o prueba con `--camera 1`. |
| `Failed to connect to <IP>:11434` | Ollama está escuchando solo en `127.0.0.1` o firewall activo. | En la Spark, ejecuta `OLLAMA_HOST=0.0.0.0:11434 ollama serve`. |
| Inferencia muy lenta (> 5s por frame) | El modelo es grande (`27b`) o el frame es innecesariamente pesado. | Usa `--model gemma3:4b` y mantén la resolución en 640x480. |
| Respuestas alucinadas o genéricas | El objeto está fuera de foco o iluminación insuficiente. | Mejora la iluminación y asegúrate de encuadrar el objeto en el centro. |
