# Edge Clean Copilot: Specialized SLM for Clean Architecture & Spec-Driven Development

**Autor:** Jesús Rodolfo Gil Farías  
**Institución:** Universidad Católica Andrés Bello (UCAB) — Caracas, Venezuela  
**Carrera:** Escuela de Ingeniería Informática  
**Articulación Académica:** Inteligencia Artificial Aplicada & Desarrollo de Software  
**Hardware de Entrenamiento:** NVIDIA DGX Spark (GB10 Grace Blackwell, 128 GB Unified Memory)  
**Entorno de Ejecución Objetivo:** Hardware de recursos limitados (Laptops estándar, CPU / iGPU, 100% Offline)  

---

## 1. Visión y Resumen del Proyecto

Los asistentes de programación basados en modelos masivos en la nube (como GitHub Copilot o ChatGPT) generan código que compila, pero frecuentemente violan la **Regla de Dependencia de Clean Architecture**, mezclan lógica de dominio con infraestructura y requieren enviar código propietario a servidores externos bajo suscripciones de pago.

A diferencia de wrappers de prompts como *Gentle-AI* o *gentle-pi* (que operan como harnesses de contexto sobre APIs de frontera como Claude), este proyecto aborda el problema a nivel de **Sistemas de Inteligencia Artificial e Inferencia en el Borde**:
1. Entrenar y adaptar un **Small Language Model (SLM)** compacto (1.5B a 3B) mediante **LoRA** para internalizar patrones formales de Clean Architecture y pruebas BDD (Arrange-Act-Assert) directamente en sus pesos.
2. Desplegar el modelo cuantizado en formato **GGUF (Q4_K_M)** para ejecución autónoma a alta velocidad (35–70 tokens/s) en laptops comerciales comunes.
3. Construir una herramienta CLI desacoplada bajo el patrón **Puertos y Adaptadores (Ports & Adapters)** que aísle la lógica del sistema del motor de inferencia.

---

## 2. Hipótesis Técnica y Metodología

### Hipótesis Central
Un modelo de lenguaje pequeño (< 3B parámetros), altamente especializado mediante LoRA en pares sintéticos canónicos de arquitectura de software y restringido por gramáticas deterministas (GBNF / esquemas de tipos), puede superar a modelos comerciales generales en la adherencia estricta a Clean Architecture en entornos locales sin conexión.

### Estrategia Operativa: "Staging en Frío, Ráfaga en Caliente"
* **Presupuesto de Cómputo:** 7 a 9 sesiones atómicas de ~2 horas semanales en la estación NVIDIA DGX Spark.
* **Pre-laboratorio (En casa):** Curación y tokenización de datasets sintéticos validados en formato JSONL; dry-run local de 1 paso en CPU.
* **Laboratorio (En DGX Spark):** Ráfaga de entrenamiento LoRA (20 a 40 minutos), fusión de adaptadores (`merge_and_unload`) y cuantización inmediata a GGUF con `llama.cpp`.
* **Post-laboratorio (En laptop modesta):** Pruebas de regresión, medición de consumo de VRAM/RAM y desarrollo de la capa de aplicación del CLI.

---

## 3. Arquitectura del Sistema (Ports & Adapters)

```
                     ┌────────────────────────────────────────┐
                     │         Capa de Dominio / CLI          │
                     │  - AST Parsing & Code Slicing          │
                     │  - Verificación de Reglas SOLID        │
                     │  - Generación de Suites de Pruebas AAA │
                     └───────────────────┬────────────────────┘
                                         │
                             [Puerto: InferenceEngine]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
      [Adaptador: LlamaCppEngine]                      [Adaptador: MockEngine]
                 │                                               │
     (Modelo GGUF Local 4-bit)                         (Pruebas Unitarias)
```

---

## 4. Cronograma de Fases del Semestre

* **Fase 1: Infraestructura y Teacher Model (Semanas 1-3):**
  * Validación del entorno local en la DGX Spark (CUDA, `llama.cpp` nativo y servidor `llama-server` con Qwen3-Coder-30B).
  * Extracción y generación del dataset sintético de Clean Architecture asistido por el modelo de 30B como maestro (*teacher model*).
* **Fase 2: Adaptación y Especialización LoRA (Semanas 4-7):**
  * Entrenamiento de adaptadores LoRA sobre SLMs base (Qwen-2.5/3-Coder 1.5B / 3B).
  * Evaluación de convergencia, pérdida y tasa de olvido catastrófico (*catastrophic forgetting*).
* **Fase 3: Optimización, Fusión y Cuantización (Semanas 8-11):**
  * Fusión de pesos y exportación multi-cuantización (`Q4_K_M`, `Q5_K_M`, `Q8_0`).
  * Benchmarking de velocidad (tokens/segundo) y huella de memoria en laptop estándar.
* **Fase 4: Desarrollo del Cliente y Publicación (Semanas 12-15):**
  * Construcción del CLI en TypeScript / Go / Python.
  * Publicación de pesos en Hugging Face, repositorio en GitHub con CI/CD automatizado y documentación técnica final.

---

## 5. Replicabilidad Democrática

El diseño del proyecto es intencionalmente independiente de hardware costoso para su uso y reproducción:
* **Inferencia diaria:** Requiere únicamente 8–16 GB de RAM en CPU comercial vía `llama.cpp` o `Ollama`.
* **Replicabilidad del entrenamiento:** Compatible con entornos gratuitos de **Google Colab (GPU T4 de 16 GB)** o GPUs domésticas de 6 GB VRAM mediante QLoRA.

---

## 6. Referencias y Documentación Asociada
* [Documento de Propuesta Técnica Formal (Google Docs)](https://docs.google.com/document/d/1fZsRbir6Os1fA-eled90wLnMfbrQe4B7YVNMrOHMmIU/edit)
