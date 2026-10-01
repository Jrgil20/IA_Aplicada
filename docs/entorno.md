# Especificaciones de Entorno

Detalle de hardware y entornos de ejecución contemplados en la cátedra.

---

## 1. Estación de Entrenamiento: NVIDIA DGX Spark

- **Arquitectura:** NVIDIA Grace Blackwell (GB10)
- **Memoria Unificada:** 128 GB Unified Memory
- **Propósito:** Ráfagas de entrenamiento LoRA (20–40 min), generación sintética con teacher model (Qwen-30B) y conversión directa a GGUF.
- **Guía Completa:** Consultar la [Guía de Referencia NVIDIA DGX Spark](./dgx/README.md).

---

## 2. Entorno Target de Inferencia (Edge / Laptops)

- **Arquitectura:** CPU comercial x86_64 / ARM / iGPU
- **Memoria RAM:** 8 GB – 16 GB
- **Objetivo:** Ejecución 100% offline sin dependencias de GPU dedicada, con un throughput objetivo de 35–70 tokens/s vía `llama.cpp` o `Ollama`.
