# Reference Guide: LoRA and QLoRA (PEFT)

Technical guide on Parameter-Efficient Fine-Tuning (PEFT) via **LoRA** (Low-Rank Adaptation) and **QLoRA** (Quantized Low-Rank Adaptation) for language models.

---

## 1. Theoretical Foundations

### 1.1 From Full Fine-Tuning to LoRA
In full fine-tuning, all network weights ($W \in \mathbb{R}^{d \times k}$) are updated, requiring storage in memory of the weights, gradients, and optimizer states (e.g., AdamW requires 8 additional bytes per parameter in FP32).

**LoRA** freezes the pre-trained weights $W_0$ and decomposes the update matrix $\Delta W$ into the product of two low-rank matrices:

$$\Delta W = B \cdot A \quad \text{where } A \in \mathbb{R}^{r \times k}, \; B \in \mathbb{R}^{d \times r}, \; r \ll \min(d, k)$$

The output of the linear layer during inference is:

$$h = W_0 x + \frac{\alpha}{r} (B \cdot A) x$$

- **$r$ (Rank):** Decomposition rank (typically 8, 16, or 32). Controls the expressive capacity of the adaptation.
- **$\alpha$ (Alpha):** Constant scaling factor. A common convention is to set $\alpha = 2r$.
- **Dropout:** Regularization rate applied to adapters (typically 0.05 to 0.1).

---

### 1.2 Key QLoRA Innovations (Dettmers et al., 2023)

QLoRA enables training LoRA adapters on a 4-bit quantized base model without degrading precision:

1. **4-bit NormalFloat (NF4):** Optimal data type for weights following a zero-centered normal distribution, outperforming traditional FP4 and INT4 in information fidelity.
2. **Double Quantization (DQ):** Quantizes the quantization constants themselves for 64-parameter blocks, saving an average of 0.37 bits per parameter (~3 GB savings on a 65B model).
3. **Paged Optimizers:** Uses CUDA unified memory paging to mitigate optimizer memory spikes (OOM) by temporarily offloading inactive pages to RAM.

---

## 2. Target Modules for Modern Architectures (Qwen / Llama)

For maximum retention and capability on reasoning and Clean Architecture tasks, it is recommended to adapt both the attention layers and the multi-layer perceptron (MLP):

```python
target_modules = [
    # Attention Layers
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    # MLP / Feed-Forward Layers
    "gate_proj",
    "up_proj",
    "down_proj"
]
```

---

## 3. Canonical Example with Hugging Face (`peft` + `bitsandbytes`)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model_id = "Qwen/Qwen2.5-Coder-1.5B"

# 1. 4-bit Quantization Config (NF4)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# 2. Load quantized base model
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# 3. Prepare model for k-bit training
model = prepare_model_for_kbit_training(model)

# 4. Configure LoRA hyperparameters
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

## 4. Adapter Merging and Export

Once training is complete, the adapter weights are merged with the original base model at full precision (FP16 or BF16) to enable GGUF quantization:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

# Load base model in FP16 (without bitsandbytes)
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-1.5B",
    torch_dtype=torch.float16,
    device_map="cpu",
)

# Load and merge trained adapters
model = PeftModel.from_pretrained(base_model, "./lora_output_dir")
merged_model = model.merge_and_unload()

# Save consolidated model for llama.cpp export
merged_model.save_pretrained("./merged_model_fp16")
```

The model at `./merged_model_fp16` is ready to be processed through `convert_hf_to_gguf.py` and `llama-quantize`.
