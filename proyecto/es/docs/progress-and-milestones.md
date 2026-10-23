# Progreso e Hitos Verificados: Edge Clean Copilot

> **Proyecto:** Edge Clean Copilot — SLM Especializado para Clean Architecture  
> **Asignatura:** Inteligencia Artificial Aplicada (UCAB)  
> **Autor:** Jesús Rodolfo Gil Farías  
> **Progreso Global del Proyecto:** **70%**  
> **Última Verificación:** 22 de Octubre de 2026 (Consolidación y Cierre de Sesión)  

---

## 1. Tablero Ejecutivo de Estado

| Fase | Descripción | Ventana Planificada | Completitud | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Fase 1** | Infraestructura, Redes y Dataset del Modelo Teacher | Semanas 1–3 | **100%** | **COMPLETA Y VERIFICADA** |
| **Fase 2** | Adaptación LoRA y Especialización del SLM Estudiante | Semanas 4–7 | **85%** (Runtime listo, 73% pesos en NVMe) | **ACTIVA / LISTA PARA RÁFAGA** |
| **Fase 3** | Consolidación de Pesos, Cuantización y Exportación GGUF | Semanas 8–11 | **50%** (Script automatizado y probado) | EN ESPERA |
| **Fase 4** | CLI Hexagonal, Tests Unitarios y Benchmark Automatizado| Semanas 12–15 | **70%** (28/28 tests en verde, benchmark listo)| EN PROGRESO |

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
  - Entidades de dominio con invariantes, objetos de valor puros, casos de uso con `Result<T, DomainError>`, interfaces de puertos y tests unitarios AAA.

- [x] **Generador Automatizado con Modelo Maestro:**
  - Implementado [`dataset/generate_with_teacher.py`](../../../proyecto/dataset/generate_with_teacher.py) con soporte ChatML y flag defensivo `--max-time-minutes`.
  - Generados **160 ejemplos sintéticos** (~186k tokens) en [`dataset/generated_examples.jsonl`](../../../proyecto/dataset/generated_examples.jsonl).

- [x] **Partición Estratificada del Dataset (Cero Data Leakage):**
  - Implementado [`dataset/split_dataset.py`](../../../proyecto/dataset/split_dataset.py) con semilla determinista (`seed=42`).
  - Creado [`dataset/train.jsonl`](../../../proyecto/dataset/train.jsonl) (**138 muestras**, ~156k tokens, 82.1%).
  - Creado [`dataset/eval_holdout.jsonl`](../../../proyecto/dataset/eval_holdout.jsonl) (**30 muestras**, ~35k tokens, 17.9%) aislado para evaluación.
  - Sintaxis validada vía [`dataset/validate_dataset.py`](../../../proyecto/dataset/validate_dataset.py).

---

## 3. Hitos de la Fase 2 (En Progreso / 85% Completada)

- [x] **Pipeline de Fine-Tuning Nativo en PyTorch:**
  - Implementado [`training/train_lora.py`](../../../proyecto/training/train_lora.py) con optimizador AdamW, dynamic batch padding, `--max-time-minutes` y `--merge`.
  - Hiperparámetros base: $r=16$, $\alpha=32$, apuntando por defecto a `../dataset/train.jsonl`.

- [x] **Configuración del Entorno Grace Blackwell (GB10):**
  - Virtualenv `/home/ucab-spark1/lora_venv` en Spark 1 con PyTorch 2.14.1 (CUDA 13.0) y bfloat16 nativo verificado.

- [x] **Descarga de Pesos Base (73% completada):**
  - 2.26 GB de 3.09 GB descargados de `Qwen/Qwen2.5-Coder-1.5B-Instruct` en caché NVMe.

- [ ] **Primera Ráfaga de Fine-Tuning (Pendiente Próxima Sesión Spark):**
  - Reanudar los ~800 MB restantes (~3 min).
  - Ejecutar ráfaga de 10-15 minutos en GPU sobre `train.jsonl` con `--merge`.

---

## 4. Hitos de la Fase 3 (En Espera / 50% Completada)

- [x] **Script Automatizado One-Click de Cuantización a GGUF:**
  - Implementado [`training/convert_to_gguf.sh`](../../../proyecto/training/convert_to_gguf.sh) con autodetección de `llama.cpp` y `lora_venv`.
  - Manejo de errores defensivo ante carpetas inexistentes o binarios sin compilar.
  - Genera `Q4_K_M` (default) y matriz multi-cuantización (`Q4_K_M`, `Q5_K_M`, `Q8_0`) con `--clean-f16`.

- [ ] **Ejecución Física de Cuantización:**
  - A la espera de los pesos consolidados de la ráfaga de la Fase 2 en la Spark.

---

## 5. Hitos de la Fase 4 (CLI Cliente y Benchmark — 70% Completada)

- [x] **Implementación de Arquitectura Hexagonal:**
  - Código TypeScript estructurado bajo [`proyecto/cli/`](../../../proyecto/cli/) separando Dominio, Aplicación, Puertos e Infraestructura.
  - Normalización defensiva de endpoints en [`LlamaServerAdapter.ts`](../../../proyecto/cli/src/infrastructure/ai/LlamaServerAdapter.ts) tolerando `/`, `/v1` y `/v1/chat/completions`.

- [x] **Suite Integral de Tests Unitarios con Vitest:**
  - **28 tests pasando en 278 ms (100% en verde)** a lo largo de las 5 suites:
    - `SourceFile.test.ts` (10 tests)
    - `RefactorCodeUseCase.test.ts` (5 tests)
    - `Result.test.ts` (4 tests)
    - `LlamaServerAdapter.test.ts` (7 tests)
    - `FileDiskReader.test.ts` (2 tests)

- [x] **Arnés de Evaluación Automatizado:**
  - Implementado [`evaluation/eval_benchmark.py`](../../../proyecto/evaluation/eval_benchmark.py) en Python 3 puro (0 dependencias).
  - Fórmula CAS (0–100 pts) evaluando Frontera de Dominio (30%), Invariantes (25%), Puertos (25%) y Tipado Seguro (20%).
  - Calibrado contra los 10 casos de control en [`evaluation/test_benchmark_cases.jsonl`](../../../proyecto/evaluation/test_benchmark_cases.jsonl).
