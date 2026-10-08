# Observación 02: Orquestación Multimodal y Afinación del Payload VLM

> **Contexto:** Habilitación de la visión artificial en Gemma 3 y corrección del pipeline de inferencia en `app.py` en la NVIDIA DGX Spark.

---

## 1. Problema A: Gemma 3 corriendo sin proyector multimodal (`--mmproj`)

### Síntoma
Gemma 3 respondía únicamente preguntas de texto y devolvía alucinaciones de respuestas sobre "estilo de vida" o "metas" cuando se le preguntaba qué veía en la cámara.

### Causa Raíz
El proceso `llama-server` en el puerto `8084` se había iniciado originalmente con el comando básico:
```bash
llama-server -m /home/ucab-spark1/models/gemma-3-4b-it-GGUF/gemma-3-4b-it-Q8_0.gguf -c 32768 --port 8084
```
Sin el flag `--mmproj`, el modelo opera exclusivamente como un LLM de texto puro: los embeddings visuales no existen en el grafo computacional y el modelo es "ciego" a cualquier cuadro que se le proporcione.

### Solución
Se relanzó el servidor vinculando el codificador de visión `mmproj-model-f16.gguf` (812 MB) offloadeado a la GPU Blackwell GB10:
```bash
/home/ucab-spark1/llama.cpp/build/bin/llama-server \
  -m /home/ucab-spark1/models/gemma-3-4b-it-GGUF/gemma-3-4b-it-Q8_0.gguf \
  --mmproj /home/ucab-spark1/models/gemma-3-4b-it-GGUF/mmproj-model-f16.gguf \
  --port 8084 \
  --host 0.0.0.0 \
  -ngl 99 \
  -c 4096
```
**Resultado:** Los logs de `llama-server` confirmaron la carga exitosa:
```text
load_model: loaded multimodal model, '/home/ucab-spark1/models/gemma-3-4b-it-GGUF/mmproj-model-f16.gguf'
```

---

## 2. Problema B: Serialización Cruda de Pixeles y Timeouts en `app.py`

### Síntoma
Al pulsar "Run Inference" en la interfaz web, tras 10 segundos aparecía el error:
```text
Objects Detected: {"error":"HTTPConnectionPool(host='127.0.0.1', port=8084): Read timed out. (read timeout=10)"}
```

### Causa Raíz
1. **Serialización ineficiente:** En `process_frame`, el código convertía una matriz numpy de 896x896x3 en listas anidadas de Python (`rgb_frame.tolist()`), generando más de **2.4 millones de enteros en memoria** que colapsaban la serialización JSON de `requests.post`.
2. **Falta de límite de generación (`n_predict`):** Al no especificar límite de tokens, `llama-server` intentaba predecir hasta agotar el contexto, excediendo el `timeout=10` hardcodeado en `app.py`.
3. **Payload incorrecto para el endpoint multimodal:** Para que `llama-server` procese una imagen con `--mmproj`, el formato estándar es OpenAI `/v1/chat/completions` con `image_url` en Base64 o `/completion` con `image_data`. Enviar la lista de 2.4 millones de enteros provocaba que el servidor rechazara la petición o se quedara colgado.

### Solución
Se refactorizó la función `send_to_model` en `app.py`:
```python
def send_to_model(model_url: str, frame_data: Any, prompt: str, raw_frame=None):
    try:
        if "chat/completions" in model_url or "8084" in model_url or "8080" in model_url:
            b64_img = ""
            if raw_frame is not None:
                _, buf = cv2.imencode(".jpg", raw_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                b64_img = base64.b64encode(buf).decode("utf-8")
            
            content_list = [{"type": "text", "text": prompt}]
            if b64_img:
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                })
            
            payload = {
                "messages": [{"role": "user", "content": content_list}],
                "max_tokens": 150,
                "temperature": 0.2
            }
            resp = requests.post(model_url, json=payload, timeout=60)
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"objects": [content], "content": content}
```

---

## 3. Validación Empírica Final

Se disparó una inferencia desde la webcam con el prompt:
> *"Que ves en la imagen? Describe a la persona detalladamente."*

### Telemetría Observada:
- **Latencia total end-to-end:** **3.70 segundos**.
- **Tiempo de prompt en GPU:** 25.3 ms.
- **Rendimiento de generación:** **49.84 tokens/s**.
- **Resultado cualitativo:** El modelo identificó correctamente al usuario en la cámara (hombre joven, pelo castaño oscuro, barba cuidada, camisa azul oscuro) sin que se le hubiera suministrado ninguna pista previa en el texto.
