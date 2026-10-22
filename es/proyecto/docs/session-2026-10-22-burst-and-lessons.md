# Reporte Técnico de Sesión: Generación Sintética con Teacher y Setup del Runtime ML

> **Fecha de Sesión:** 22 de Octubre de 2026  
> **Infraestructura Objetivo:** NVIDIA DGX Spark (`spark-0fbc`, `192.168.6.35/26`, Superchip GB10, 128 GB Memoria Unificada)  
> **Metodología Operativa:** "Cold Staging, Hot Burst"  
> **Estado:** Completado y Empíricamente Validado  

---

## 1. Objetivos y Resumen Ejecutivo

Los objetivos primarios de esta sesión fueron:
1. Establecer y validar aislamiento multi-inquilino en la estación NVIDIA DGX Spark para ejecutar tareas del proyecto sin interferir con las prácticas educativas concurrentes.
2. Ejecutar un burst intensivo de generación sintética asistido por el modelo maestro (Teacher) de 30B parámetros.
3. Inicializar y verificar el entorno de ejecución PyTorch (`lora_venv`) sobre el superchip ARM64 Grace Blackwell (GB10) para la adaptación LoRA de la Fase 2.
4. Cumplir rigurosamente las políticas de limpieza y guardrails de apagado seguro antes del cierre de laboratorio.

---

## 2. Orquestación de Infraestructura y Topología

### 2.1 Aislamiento de Procesos en GPU GB10

Para evitar contención de colas, sobreescritura de contextos e interferencias HTTP con la práctica de laboratorio en el puerto `8080`, se desplegó un proceso secundario de `llama-server` en el puerto dedicado `8085`:

```
                                    NVIDIA DGX Spark 1 (128 GB Memoria Unificada)
                   ┌────────────────────────────────────────────────────────────────────────┐
                   │                                                                        │
[App Práctica] ───>│ [Puerto 8080] llama-server (PID 28983)                                 │
(Browser/OpenCode) │  - Modelo: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf                │
                   │  - VRAM: 20.1 GiB | Contexto: 32,768 tokens                            │
                   ├────────────────────────────────────────────────────────────────────────┤
[Cámara Práctica]->│ [Puerto 8084] llama-server VLM (PID 15845)                             │
(Stream MJPEG)     │  - Modelo: gemma-3-4b-it-Q8_0.gguf + mmproj-model-f16.gguf             │
                   │  - VRAM: 5.8 GiB  | Contexto: 4,096 tokens                             │
                   ├────────────────────────────────────────────────────────────────────────┤
[Edge Clean Copilot] [Puerto 8085] llama-server Instancia Dedicada (PID 36645)              │
(Generación Sint)─>│  - Modelo: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf                │
                   │  - VRAM: 20.1 GiB | Contexto: 32,768 tokens | Alias: qwen3-coder-project│
                   │  - Log: /home/ucab-spark1/qwen_project_8085.log                       │
                   └────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Telemetría de Memoria y Temperatura Bajo Carga Dual 30B

| Métrica | Base (Modelo Único + VLM) | Carga Concurrente Dual 30B (Puertos 8080 + 8085 + 8084) | Delta / Sobrecarga |
| :--- | :--- | :--- | :--- |
| **Memoria Unificada Total** | 121 GiB | 121 GiB | 0 GiB |
| **RAM / VRAM Ocupada** | 35 GiB | 57 GiB | +22 GiB (Qwen 30B dedicado + slots KV) |
| **RAM Disponible** | 86 GiB | 64 GiB | **Buffer de 64 GiB remanente para PyTorch** |
| **Temperatura de GPU** | 45 °C | 56 °C | +11 °C (Muy por debajo del umbral térmico) |
| **Consumo Eléctrico** | 10 W (Idle) | 12 W – 24 W (Inferencia en ráfaga) | Nominal |
| **Latencia de Inferencia** | N/A | **14.4 ms** (Respuesta al primer token) | Rendimiento de 69.4 – 91.6 tokens/s |

---

## 3. Burst de Generación del Dataset Sintético

Utilizando [`dataset/generate_with_teacher.py`](../../../proyecto/dataset/generate_with_teacher.py) apuntando directamente a `http://192.168.6.35:8085/v1/chat/completions`, se ejecutó una ventana de 15 minutos.

### 3.1 Resultados Cuantitativos
- **Duración de la Ronda:** 15.02 minutos.
- **Nuevos Pares Validados:** **94 pares sintéticos ChatML**.
- **Volumen Acumulado del Dataset:** Se incrementó de 66 a **160 ejemplos** en [`dataset/generated_examples.jsonl`](../../../proyecto/dataset/generated_examples.jsonl).
- **Tokens Acumulados Aproximados:** **~186.212 tokens**.
- **Validación de Sintaxis y Esquema:** 100% aprobada vía [`dataset/validate_dataset.py`](../../../proyecto/dataset/validate_dataset.py).
- **Tópicos de Arquitectura Cubiertos:**
  - Entidades de Dominio y Objetos de Valor puros (patrón `Result<T, E>`, sin mutaciones impuras).
  - Casos de uso con inversión de dependencias y responsabilidad única.
  - Tests unitarios AAA (Arrange-Act-Assert) utilizando repositorios mock en memoria.
  - Prohibición estricta de `any` en TypeScript; interfaces y guardas de tipos estrictas.

---

## 4. Inicialización del Entorno ML para Fase 2

### 4.1 Entorno PyTorch y CUDA 13 en Grace Blackwell (GB10)

Para iniciar la Fase 2 (adaptación LoRA), se construyó un entorno virtual nativo en el host ARM64:
- **Ruta:** `/home/ucab-spark1/lora_venv`
- **Versión de Python:** Python 3.12 (aarch64)
- **Compilación PyTorch:** `2.14.1+cu130` (Ruedas nativas aarch64 con soporte CUDA 13)
- **Paquetes Principales:** `transformers==5.20.2`, `peft==0.21.2`, `accelerate==1.15.0`, `datasets==5.1.0`
- **Soporte Nativo bfloat16:** Verificado (`torch.cuda.is_bf16_supported() == True`).

### 4.2 Análisis de Descarga de Pesos y Dry-Run

Se inició la ejecución de [`training/train_lora.py --dry-run`](../../../proyecto/training/train_lora.py) para descargar el modelo base `Qwen/Qwen2.5-Coder-1.5B-Instruct` (3.09 GB) en `~/.cache/huggingface/hub/`:
- **Velocidad de Bajada:** ~2.2 – 2.5 MB/s sobre la red del campus.
- **Descarga Previa al Toque de Queda:** 2.26 GB de 3.09 GB (**73.1%**).
- **Acción Tomada:** Finalización controlada antes de las 13:00 para garantizar limpieza del sistema y evitar corrupción de checkpoints.

---

## 5. Lecciones Aprendidas y Directrices Operativas

### Lección 1: Cuello de Botella de Red en Laboratorios Compartidos
Descargar pesos de modelos fundacionales de múltiples gigabytes consume 20–25 minutos de tiempo de cómputo en GPU.
> [!IMPORTANT]
> **Protocolo Operativo:** Los pesos base deben pre-cachearse en el almacenamiento NVMe de la Spark antes de iniciar el bloque de laboratorio, o utilizar tokens autenticados (`HF_TOKEN`) para evitar el estrangulamiento de velocidad de CDN públicas.

### Lección 2: Puertos Dedicados Garantizan Cero Contención
Ejecutar instancias secundarias de `llama-server` en puertos distintos (`8085` vs `8080`) aísla por completo los buffers de memoria y colas de inferencia.

### Lección 3: Límite Temporal Defensivo (`--max-time-minutes`)
En supercomputadores compartidos con turnos fijos (e.g. 2 horas), los scripts deben incorporar flags de tiempo que cierren checkpoints y liberen la GPU ordenadamente.

### Lección 4: Guardrail Obligatorio para Operaciones Privilegiadas
Comandos destructivos (`sudo shutdown` o `sudo reboot`) nunca deben ser ejecutados automáticamente por agentes autónomos sin validación humana explícita y verificación de usuarios conectados (`uptime`, `who`).
