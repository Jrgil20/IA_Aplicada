# Guía de Referencia: LoRA y QLoRA (PEFT)

Guía técnica sobre adaptación eficiente de parámetros (PEFT) mediante **LoRA** (Low-Rank Adaptation) y **QLoRA** (Quantized Low-Rank Adaptation) para modelos de lenguaje.

---

## 1. Fundamentos Teóricos

### 1.1 De Full Fine-Tuning a LoRA
En el ajuste fino completo (*Full Fine-Tuning*), se actualizan todos los pesos de la red ($W \in \mathbb{R}^{d \times k}$), requiriendo almacenar en memoria los pesos, gradientes y estados del optimizador (e.g. AdamW necesita 8 bytes adicionales por parámetro en FP32).

**LoRA** congela los pesos pre-entrenados $W_0$ y descompone la matriz de actualización $\Delta W$ en el producto de dos matrices de bajo rango:

$$\Delta W = B \cdot A \quad \text{donde } A \in \mathbb{R}^{r \times k}, \; B \in \mathbb{R}^{d \times r}, \; r \ll \min(d, k)$$

La salida de la capa lineal durante la inferencia es:

$$h = W_0 x + \frac{\alpha}{r} (B \cdot A) x$$

- **$r$ (Rank):** Rango de descomposición (típicamente 8, 16 o 32). Controla la capacidad expresiva de la adaptación.
- **$\alpha$ (Alpha):** Factor de escala constante. Una convención común es fijar $\alpha = 2r$.
- **Dropout:** Tasa de regularización aplicada a los adaptadores (típicamente 0.05 a 0.1).

---

### 1.2 Innovaciones Clave de QLoRA (Dettmers et al., 2023)

QLoRA permite entrenar adaptadores LoRA sobre un modelo base cuantizado a 4 bits sin degradar la precisión:

1. **4-bit NormalFloat (NF4):** Tipo de datos óptimo para pesos que siguen una distribución normal centrada en cero, superando a FP4 e INT4 tradicionales en fidelidad de información.
2. **Double Quantization (DQ):** Cuantiza las propias constantes de cuantización de los bloques de 64 parámetros, ahorrando un promedio de 0.37 bits por parámetro (~3 GB de ahorro en un modelo de 65B).
3. **Paged Optimizers:** Utiliza paginación de memoria unificada de CUDA para mitigar picos de memoria (OOM) en el optimizador enviando páginas inactivas a RAM temporalmente.

---

## 2. Target Modules para Arquitecturas Modernas (Qwen / Llama)

Para máxima retención y capacidad en tareas de razonamiento y Clean Architecture, se recomienda adaptar tanto las capas de atención como las del perceptrón multicapa (MLP):

```python
target_modules = [
    # Capas de Atención
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    # Capas MLP / Feed-Forward
    "gate_proj",
    "up_proj",
    "down_proj"
]
```

---

## 3. Ejemplo Canónico con Hugging Face (`peft` + `bitsandbytes`)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model_id = "Qwen/Qwen2.5-Coder-1.5B"

# 1. Configuración de Cuantización a 4 bits (NF4)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# 2. Cargar modelo base cuantizado
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# 3. Preparar modelo para entrenamiento en k-bits
model = prepare_model_for_kbit_training(model)

# 4. Configurar hiperparámetros LoRA
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, peft_config)
model.print_trainable_parameters()
```

---

## 4. Fusión de Adaptadores y Exportación

Una vez finalizado el entrenamiento, los pesos de los adaptadores se fusionan con el modelo base original en precisión completa (FP16 o BF16) para permitir su cuantización a GGUF:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

# Cargar modelo base en FP16 (sin bitsandbytes)
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-1.5B",
    torch_dtype=torch.float16,
    device_map="cpu",
)

# Cargar y fusionar los adaptadores entrenados
model = PeftModel.from_pretrained(base_model, "./lora_output_dir")
merged_model = model.merge_and_unload()

# Guardar modelo consolidado para exportación a llama.cpp
merged_model.save_pretrained("./merged_model_fp16")
```

El modelo en `./merged_model_fp16` queda listo para ejecutarse a través de `convert_hf_to_gguf.py` y `llama-quantize`.
