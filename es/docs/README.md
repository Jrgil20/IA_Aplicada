# Documentación Técnica — IA Aplicada

> **Base de conocimiento AI-first.** Cada módulo (`/dgx`, `/cuda`, `/qlora`) es una unidad autocontenida con su propio `README.md` como punto de entrada. Los agentes deben consultar este índice para decidir qué módulo leer según la tarea activa; no es necesario cargar toda la documentación en contexto.

---

## Playbook de IA Aplicada (empieza aquí para productos)

**[Índice del playbook](./playbook/README.md)** — la capa práctica: cuándo usar IA, qué arquitectura, qué nivel de modelo (quedarse, subir, ir más barato, ir privado), costos y ahorros, privacidad, hardening, evaluación y preparación para producción. Los módulos siguientes son el trasfondo técnico.

---

## Módulos de Documentación

### 1. [NVIDIA DGX Spark (`/dgx`)](./dgx/README.md)
Guía técnica y operativa para la estación de trabajo de supercómputo de escritorio (GB10 Grace Blackwell, 128 GB Unified Memory).
- Arquitectura de hardware y especificaciones del superchip.
- Stack de software NVIDIA DGX OS y contenedores NGC.
- Metodología "Staging en Frío, Ráfaga en Caliente".
- Enlaces a documentación oficial y playbooks.

### 2. [CUDA & GPU Acceleration (`/cuda`)](./cuda/README.md)
Conceptos de paralelismo y optimización en GPUs NVIDIA.
- Streaming Multiprocessors, Warps y jerarquía de memoria.
- Compute Capability y soporte por arquitectura (Ampere a Blackwell).
- Variables de entorno críticas y toolchain de monitoreo (`nvidia-smi`, `nvtop`).
- FlashAttention y optimización de memoria.

### 3. [LoRA & QLoRA PEFT (`/qlora`)](./qlora/README.md)
Guía de adaptación eficiente de parámetros para modelos de lenguaje.
- Fundamentos matemáticos de descomposición de bajo rango ($W = W_0 + B \cdot A$).
- Innovaciones de QLoRA: NormalFloat4 (NF4), Double Quantization y Paged Optimizers.
- Selección de `target_modules` para arquitecturas Qwen y Llama.
- Pipeline completo: entrenamiento, fusión (`merge_and_unload`) y preparación para GGUF.

---

## Guías Rápidas

- [Comandos Útiles](./comandos-utiles.md) — Cheat sheet de comandos para terminal, hardware, llama.cpp y GGUF.
- [Especificaciones de Entorno](./entorno.md) — Comparativa entre la estación DGX Spark y el entorno edge de despliegue.
- [SLMs Locales vs. LLMs en la Nube](./local-slm-vs-cloud-llm.md) — Registro de decisión arquitectónica, ROI económico y patrón híbrido.
- [Enrutamiento por Costo](./enrutamiento-por-costo.md) — Nota de diseño (no implementada): cascada de reglas, SLM local y LLM de frontera para reducir costo en consultas pequeñas.
- [Casos de Uso de IA Aplicada](./casos-de-uso-ia-aplicada.md) — Qué nivel (reglas, caché, SLM local, nube) encaja con cada tarea y cuándo escalar.
- [Escalado de Cargas de IA](./escalado-cargas-ia.md) — Escalado de modelo vs. de cómputo: laptop, DGX Spark, nube.
- [Caché de Prompts](./cache-de-prompts.md) — Caché de respuesta, semántica y de prefijo/KV: cuándo usar cada una, cifras verificadas y riesgos.
- [Servir Modelos para Apps](./servir-modelos-para-apps.md) — Runtimes (llama.cpp, vLLM, Ollama, APIs), flags, capacidad, topologías, checklist de producción.
- [Selección de Modelos](./seleccion-de-modelos.md) — Proceso y criterios para elegir y reemplazar un modelo.
