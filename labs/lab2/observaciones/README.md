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
| [**05. Auditoría de Seguridad: Prompt Injection y Fuga de Credenciales**](./05-security-audit-prompt-injection-credential-leak.md) | Reporte formal de vulnerabilidad (OWASP LLM01/LLM06, CVSS 7.5 HIGH) exfiltrando clave operativa en bot Tramontana (puerto 7000). | **Auditado** |
| [**06. Auditoría de Seguridad: Inyección por Canal Secundario y Defacement**](./06-security-audit-secondary-channel-injection-and-defacement.md) | Explotación del campo auxiliar `nota_cliente` provocando DoS funcional ("SISTEMA COMPROMETIDO") y exfiltración sin consulta. | **Auditado** |
| [**07. Auditoría de Seguridad: Secuestro de Personalidad y Bloqueo Conductual**](./07-security-audit-persona-hijacking-behavioral-lockout.md) | Anulación de rol operativo mediante instrucción imperativa ("responde solo 'ja'"), DoS funcional y persistencia en cliente. | **Auditado** |
| [**08. Análisis Comparativo de Seguridad (Vulnerable vs. Endurecido)**](./08-comparative-security-analysis-tramontana.md) | Evaluación empírica lado a lado en el dashboard comparador (`tramontana_comparador.py` en puerto 7002): fuga de secreto, canal secundario, XSS y RCE. | **Auditado** |
| [**09. Auditoría de Seguridad: Manejo Inseguro de Salida e Inyección HTML**](./09-security-audit-insecure-output-handling-html-injection.md) | Inyección de etiquetas HTML (`<b>HOLA</b>`) evaluadas por `innerHTML` en cliente web (OWASP LLM02 / CWE-79 / CWE-116). | **Auditado** |

---

## Resumen Ejecutivo de la Sesión

1. **Conectividad:** Se logró enlace físico y enrutamiento directo punto a punto entre la laptop del estudiante (`192.168.6.50/26`) y la Spark (`192.168.6.42/26`) con latencia `< 1 ms`.
2. **Video Streaming:** Se implementó `stream_camera.py` en la laptop exponiendo un feed MJPEG en `http://192.168.6.50:8080/video`.
3. **Inferencia de Visión:** Se levantó `llama-server` con `gemma-3-4b-it-Q8_0.gguf` y `mmproj-model-f16.gguf` en el puerto `8084`, alcanzando **49.84 tokens/s** y una latencia final de **3.7 segundos** por consulta visual.
