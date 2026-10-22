# Observaciones y Análisis Técnico — Lab 02: VLM Interactivo con Webcam

Este directorio contiene los reportes de post-mortem, análisis de causas raíz y optimizaciones implementadas durante la sesión práctica en vivo de **Lab 02** conectando la webcam de la laptop local con los modelos de visión desplegados en la **NVIDIA DGX Spark** (`ucab-spark1`).

---

## Índice de Documentos

| Documento | Enfoque | Estado |
| :--- | :--- | :--- |
| [**01. Subnetting y Resolución de Firewall**](./01-network-subnetting-and-firewall-resolution.md) | Diagnóstico de Capa 1 a 3: resolución de máscara `/26`, aislamiento ARP y reglas de UFW en la laptop. | **Resuelto** |
| [**02. Orquestación Multimodal y Payload VLM**](./02-vlm-multimodal-orchestration-and-vision-payload.md) | Activación de proyector `--mmproj`, corrección de serialización JSON en `app.py` y validación empírica en GPU Blackwell. | **Resuelto** |
| [**03. Despliegue Dual y Orquestación**](./03-dual-model-orchestration-and-qwen-coder.md) | Concurrencia de Gemma 3 4B VLM y Qwen 3 Coder 30B, corrección de payload para modelos no-VLM y script `iniciar_lab2.sh`. | **Resuelto** |
| [**04. Desbordamiento de Contexto en OpenCode y Aislamiento**](./04-opencode-agent-context-overflow-analysis.md) | Análisis de prefill inicial de agentes (~8k tokens), aumento de contexto a 32k y clarificación de aislamiento vs duplicación de procesos. | **Resuelto** |

---

## Resumen Ejecutivo de la Sesión

1. **Conectividad:** Se logró enlace físico y enrutamiento directo punto a punto entre la laptop del estudiante (`192.168.6.50/26`) y la Spark (`192.168.6.42/26`) con latencia `< 1 ms`.
2. **Video Streaming:** Se implementó `stream_camera.py` en la laptop exponiendo un feed MJPEG en `http://192.168.6.50:8080/video`.
3. **Inferencia de Visión:** Se levantó `llama-server` con `gemma-3-4b-it-Q8_0.gguf` y `mmproj-model-f16.gguf` en el puerto `8084`, alcanzando **49.84 tokens/s** y una latencia final de **3.7 segundos** por consulta visual.
