# Guía de Referencia: CUDA y Aceleración por GPU

Guía técnica sobre la arquitectura CUDA, gestión de memoria GPU y toolchains para el desarrollo y entrenamiento de modelos de lenguaje (LLMs/SLMs).

---

## 1. Arquitectura de Cómputo CUDA

CUDA (Compute Unified Device Architecture) expone el paralelismo masivo de las GPUs de NVIDIA:

- **Jerarquía de Ejecución:** Threads → Warps (32 threads ejecutados en lockstep) → Thread Blocks → Grid.
- **Streaming Multiprocessors (SM):** Unidades de procesamiento compuestas por núcleos FP32, FP64, INT32 y **Tensor Cores** (diseñados para multiplicación matricial acelerada en FP16, BF16, FP8 y FP4).
- **Jerarquía de Memoria:**
  - **Global Memory / HBM / LPDDR5x:** Espacio principal de alta capacidad donde residen los pesos del modelo y el KV Cache.
  - **Shared Memory / L1 Cache:** Memoria ultra-rápida local por SM, clave para optimizaciones como **FlashAttention**.
  - **Registros:** Acceso inmediato por thread.

### Tabla de Arquitecturas y Compute Capability

| Arquitectura | Compute Capability (`sm_xx`) | Ejemplos de Hardware | Precisiones Clave |
| :--- | :--- | :--- | :--- |
| **Ampere** | `sm_80`, `sm_86` | A100, RTX 3090, T4 (`sm_75`) | FP16, BF16, TF32, INT8 |
| **Ada Lovelace** | `sm_89` | RTX 4090, L4 | FP8 (E4M3, E5M2), FP16, BF16 |
| **Hopper** | `sm_90` | H100, H200 | Transformer Engine (FP8 dinámico) |
| **Blackwell** | `sm_100`, `sm_120` | DGX B200, **DGX Spark (GB10)** | FP4, FP8 nativo de 2da gen, NVLink 5 |

---

## 2. Variables de Entorno Críticas

```bash
# Selección de GPU visible para el proceso
export CUDA_VISIBLE_DEVICES=0

# Prevenir fragmentación de memoria en PyTorch
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Configuración de compilación JIT de PyTorch / C++ extensions
export TORCH_CUDA_ARCH_LIST="8.9;9.0;10.0"
```

---

## 3. Toolchain y Diagnóstico

### 3.1 Verificación de Compilador y Drivers
```bash
# Versión del driver y estado de las GPUs
nvidia-smi

# Versión del compilador CUDA de bajo nivel
nvcc --version
```

### 3.2 Monitoreo Detallado de VRAM y Cómputo
```bash
# Monitoreo dinámico continuo cada segundo
watch -n 1 nvidia-smi --format=csv --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.free

# Monitor interactivo estilo htop para GPUs (si está instalado nvtop)
nvtop
```

### 3.3 Verificación desde Python / PyTorch
```python
import torch

print(f"CUDA disponible: {torch.cuda.is_available()}")
print(f"Versión de CUDA: {torch.version.cuda}")
print(f"Dispositivo activo: {torch.cuda.get_device_name(0)}")
print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
```

---

## 4. Técnicas de Optimización Clave para LLMs

1. **FlashAttention-2 / FlashAttention-3:** Reduce la complejidad de memoria de $O(N^2)$ a $O(N)$ evitando materializar la matriz de atención completa en memoria global.
2. **Precisiones Reducidas:**
   - **BF16 (Bfloat16):** Mantiene el rango dinámico de FP32 (8 bits de exponente) previniendo desbordamientos (*underflow/overflow*) durante el entrenamiento sin pérdida de precisión sensible.
   - **FP8 / FP4:** Específico para arquitecturas Ada, Hopper y Blackwell para acelerar el throughput de inferencia y fine-tuning.
3. **Activation Checkpointing (Gradient Checkpointing):** Sacrifica ~20% de tiempo de cómputo recalculando activaciones en el backward pass para ahorrar hasta un 60% de VRAM.
