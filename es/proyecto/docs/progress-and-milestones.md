# Progreso e Hitos Verificados: Edge Clean Copilot

> **Proyecto:** Edge Clean Copilot — SLM Especializado para Clean Architecture  
> **Asignatura:** Inteligencia Artificial Aplicada (UCAB)  
> **Autor:** Jesús Rodolfo Gil Farías  
> **Progreso Global del Proyecto:** **57%**  
> **Última Verificación:** 22 de Octubre de 2026  

---

## 1. Tablero Ejecutivo de Estado

| Fase | Descripción | Ventana Planificada | Completitud | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Fase 1** | Infraestructura, Redes y Dataset del Modelo Teacher | Semanas 1–3 | **100%** | **COMPLETA** |
| **Fase 2** | Adaptación LoRA y Especialización del SLM Estudiante | Semanas 4–7 | **80%** (Runtime listo) | **ACTIVA / LISTA PARA DISPARAR** |
| **Fase 3** | Consolidación de Pesos, Cuantización y Exportación GGUF | Semanas 8–11 | **0%** | PENDIENTE |
| **Fase 4** | CLI Hexagonal, Inferencia Edge Offline y Publicación | Semanas 12–15 | **50%** (Arquitectura lista) | EN PROGRESO |

---

## 2. Hitos de la Fase 1 (Completados y Verificados)

- [x] **Topología de Red Directa (Auto-MDIX):**
  - Conexión cableada par a par entre laptop (`192.168.6.44/26`) y NVIDIA DGX Spark (`192.168.6.35/26`).
  - Autenticación sin contraseña Ed25519 configurada en `~/.ssh/config`.
  - Subred `/26` (`255.255.255.192`) validada y documentada.

- [x] **Servidor del Teacher Model (`llama-server`):**
  - Modelo Teacher `Qwen3-Coder-30B` descargado 99 capas en GPU Blackwell GB10.
  - Instancia dedicada en puerto `8085` sin interferencia con la práctica en puerto `8080`.
  - Velocidad de generación validada en **~91.6 tokens/s** con latencia sub-15ms.

- [x] **Curaduría del Dataset Semilla de Clean Architecture:**
  - 8 pares canónicos de alta calidad extraídos de ArrowMaze.
  - Entidades de dominio con invariantes en constructores fábrica.
  - Objetos de valor inmutables.
  - Casos de uso con `Result<T, DomainError>`.
  - Interfaces de puertos y adaptadores con inversión de dependencias.
  - Tests unitarios AAA con repositorios mock.

- [x] **Generador Automatizado con Modelo Maestro:**
  - Implementado [`dataset/generate_with_teacher.py`](../../proyecto/dataset/generate_with_teacher.py) con soporte ChatML y flag defensivo `--max-time-minutes`.
  - Generados **160 ejemplos sintéticos** (~186.212 tokens) en [`dataset/generated_examples.jsonl`](../../proyecto/dataset/generated_examples.jsonl).

- [x] **Suite de Validación del Dataset:**
  - Implementado [`dataset/validate_dataset.py`](../../proyecto/dataset/validate_dataset.py) validando roles (`system`, `user`, `assistant`), contenido y conteo de tokens.

---

## 3. Hitos de la Fase 2 (En Progreso / 80% Completada)

- [x] **Pipeline de Fine-Tuning Nativo en PyTorch:**
  - Implementado [`training/train_lora.py`](../../proyecto/training/train_lora.py) con PyTorch y `peft`.
  - Modos `--dry-run` y entrenamiento completo.
  - Módulos objetivo: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
  - Hiperparámetros base: $r=16$, $\alpha=32$, optimizador AdamW con bfloat16.
  - Flag `--merge` para consolidación automática de pesos.

- [x] **Configuración del Entorno Grace Blackwell (GB10):**
  - Creado virtualenv `/home/ucab-spark1/lora_venv` en Spark 1 con PyTorch 2.14.1 (CUDA 13.0) y bfloat16 nativo.

- [x] **Descarga de Pesos Base (73% completada):**
  - 2.26 GB de 3.09 GB descargados de `Qwen/Qwen2.5-Coder-1.5B-Instruct` en caché NVMe.

- [ ] **Primera Ráfaga de Fine-Tuning (Pendiente):**
  - Completar los ~800 MB restantes.
  - Ejecutar ráfaga de 10-15 minutos en GPU sobre los 160 pares.
  - Evaluar convergencia de la curva de pérdida.

---

## 4. Hitos de la Fase 4 (CLI Cliente — 50% Completada)

- [x] **Implementación de Arquitectura Hexagonal:**
  - Código TypeScript estructurado bajo [`proyecto/cli/`](../../proyecto/cli/):
    - **Dominio:** Entidad `SourceFile.ts` con invariantes de extensión y tamaño (<50k caracteres).
    - **Aplicación:** Caso de uso `RefactorCodeUseCase.ts` orquestando la inferencia y retornando `Result<T, E>`.
    - **Puertos:** `IInferenceEngine.ts` definiendo el contrato abstracto de inferencia.
    - **Adaptadores:** `MockInferenceAdapter.ts` para tests deterministas offline y `LlamaServerAdapter.ts` para HTTP.

- [ ] **Inferencia Offline en el Edge con SLM Entrenado (Pendiente Fase 3):**
  - Integración del binario `.gguf` cuantizado vía motor local en laptops comerciales.
