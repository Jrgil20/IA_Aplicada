# Edge Clean Copilot: Roadmap Detallado de Ejecución (Semanas 4–15)

> **Tipo de Documento:** Plan Maestro Operativo y Especificación de Ingeniería  
> **Entrega:** Evaluación Final de Semestre — Inteligencia Artificial Aplicada (UCAB)  
> **Metodología:** "Cold Staging, Hot Burst"  
> **Presupuesto de Cómputo:** 1.5 a 2.0 horas por sesión semanal en NVIDIA DGX Spark  

---

## 1. Cronograma General y Diagrama de Gantt (ASCII)

```text
SEMANAS         04   05   06   07   08   09   10   11   12   13   14   15
─────────────────────────────────────────────────────────────────────────────
FASE 2: LoRA    [========]
  - Ráfaga 1.5B     XX
  - Ráfaga 3B            XX
  - Eval / Loss               XX
─────────────────────────────────────────────────────────────────────────────
FASE 3: GGUF              [=============]
  - Merge                               XX
  - Cuantización                             XX
  - Bench VRAM                                    XX
─────────────────────────────────────────────────────────────────────────────
FASE 4: CLI                                   [=============================]
  - Tests Unitarios                                 XX
  - Harness Benchmark                                    XX
  - Empaquetado                                               XX
  - Informe Final                                                  XX
─────────────────────────────────────────────────────────────────────────────
```

---

## 2. Fase 2: Adaptación y Especialización LoRA (Semanas 4–7)

### 2.1 Objetivo Técnico
Especializar modelos de lenguaje pequeños (`Qwen2.5-Coder-1.5B-Instruct` y opcionalmente `3B`) mediante LoRA sobre el dataset canónico de Clean Architecture, internalizando las reglas de límites arquitectónicos directamente en los pesos.

### 2.2 Configuración de Hiperparámetros

```python
LORA_SPECIFICATION = {
    "base_model": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "r": 16,                        # Dimensión de rango LoRA
    "lora_alpha": 32,               # Factor de escala (2 * r)
    "lora_dropout": 0.05,
    "precision": "bfloat16",        # Soporte nativo de hardware Blackwell GB10
    "learning_rate": 2e-4,          # Optimizador AdamW
    "batch_size": 2,                # Tamaño de lote por dispositivo
    "gradient_accumulation_steps": 4, # Lote efectivo = 8
    "max_seq_len": 1024,
    "epochs": 3,
    "max_time_minutes": 15.0        # Límite de tiempo defensivo
}
```

### 2.3 Desglose Táctico de Tareas:
- **Semana 4: Primera Ráfaga y Generación de Adaptador**
  - [ ] Reanudar y completar la descarga de `Qwen2.5-Coder-1.5B` (~800 MB restantes).
  - [ ] Ejecutar dry-run en Spark para verificar el paso de gradientes.
  - [ ] Lanzar ráfaga de entrenamiento de 15 minutos sobre `dataset/train.jsonl` (138 muestras) (`train_lora.py --max-time-minutes 15 --merge`).
  - [ ] Guardar pesos del adaptador (`lora_adapters/adapter_model.safetensors`).
- **Semana 5: Análisis de Convergencia**
  - [ ] Evaluar curva de pérdida (meta: descenso suave de ~2.2 a <0.6).
  - [ ] Evaluación cualitativa sobre 5 prompts de refactorización no vistos.
- **Semana 6: Exploración de Escala (3B)**
  - [ ] Evaluar si el modelo 1.5B presenta limitaciones de sintaxis; preparar variante de 3B.
- **Semana 7: Auditoría de Olvido Catastrófico**
  - [ ] Validar que el modelo retiene capacidades de programación general sin degradar su lógica algorítmica.

---

## 3. Fase 3: Consolidación, Cuantización y Exportación GGUF (Semanas 8–11)

### 3.1 Objetivo Técnico
Consolidar el adaptador LoRA con el modelo base en una matriz de pesos unificada de 16 bits y cuantizar a formato GGUF para inferencia en CPU sin GPU dedicada.

### 3.2 Matriz de Cuantización y Memoria

| Formato | Método de Cuantización | Tamaño (1.5B) | RAM Objetivo | Velocidad en CPU Estándar | Retención de Calidad |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BF16 / FP16** | Base Unificada Sin Cuantizar | ~3.1 GB | ~4.5 GB | 10–18 tokens/s | 100% (Base) |
| **Q8_0** | Entero Simétrico 8-bit | ~1.6 GB | ~2.5 GB | 25–40 tokens/s | >99.5% |
| **Q5_K_M** | K-Quants Medio 5-bit | ~1.1 GB | ~1.8 GB | 35–55 tokens/s | >98.0% |
| **Q4_K_M** | **K-Quants Medio 4-bit (Objetivo)**| **~0.9 GB** | **~1.5 GB** | **45–70 tokens/s** | **>96.5%** |

### 3.3 Desglose Táctico de Tareas:
- **Semana 8: Fusión de Pesos con `merge_and_unload()`**
  - [ ] Ejecutar `train_lora.py --merge` para emitir `./output/merged_model/`.
- **Semana 9: Scripting de Conversión a GGUF**
  - [x] Crear script [`proyecto/training/convert_to_gguf.sh`](../../../proyecto/training/convert_to_gguf.sh) utilizando `llama.cpp/convert_hf_to_gguf.py` y `llama-quantize`.
  - [ ] Producir `clean-copilot-1.5b-f16.gguf` tras la consolidación LoRA en la DGX Spark.
- **Semana 10: Pipeline Multi-Cuantización**
  - [ ] Cuantizar binarios `q4_k_m`, `q5_k_m` y `q8_0` con `llama-quantize`.
- **Semana 11: Benchmarks en Hardware Edge**
  - [ ] Desplegar en la laptop del estudiante (100% offline).
  - [ ] Medir velocidad (tokens/segundo) y pico de RAM consumido con `llama-bench`.

---

## 4. Fase 4: CLI, Harness de Evaluación y Entrega (Semanas 12–15)

### 4.1 Objetivo Técnico
Entregar una herramienta CLI production-ready con Arquitectura Hexagonal y un arnés automatizado que evalúe y demuestre matemáticamente la superioridad en adherencia a Clean Architecture frente a modelos generales.

### 4.2 Métricas del Benchmark Automatizado (`eval_benchmark.py`):
Para demostrar la hipótesis central del proyecto, el arnés de evaluación automatizado ([`proyecto/evaluation/eval_benchmark.py`](../../../proyecto/evaluation/eval_benchmark.py)) califica modelos contra código acoplado y datasets sintéticos:

```
Métricas del Benchmark (Documentadas en es/proyecto/evaluation/README.md):
1. Puntuación de Frontera de Dominio (30%): 100% si el dominio importa 0 frameworks/bases de datos.
2. Seguridad de Invariantes (25%): Validación estricta en constructores y uso de Result<T, E>.
3. Desacoplamiento de Puertos (25%): Presencia de interfaz abstracta + inyección/doble de prueba.
4. Penalización por 'any' (20%): Prohibición estricta de `any` explícito en TypeScript (-5 pts por uso).
```

### 4.3 Desglose Táctico de Tareas:
- **Semana 12: Suite de Tests Unitarios del CLI**
  - [ ] Configurar `vitest` en `proyecto/cli/`.
  - [ ] Escribir tests AAA para `SourceFile`, `RefactorCodeUseCase` y `Result<T, E>`.
- **Semana 13: Adaptador Local de Inferencia**
  - [ ] Conectar el CLI al binario `.gguf` local vía motor de inferencia edge.
- **Semana 14: Evaluación Comparativa Empírica**
  - [ ] Comparar modelo base sin entrenar vs. Edge Clean Copilot (`q4_k_m`) vs. modelo comercial en la nube.
- **Semana 15: Publicación y Entrega Académica**
  - [ ] Publicar pesos y GGUFs en Hugging Face Hub.
  - [ ] Presentación técnica final y defensa del proyecto.
