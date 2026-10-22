# Edge Clean Copilot — LoRA Training & GGUF Quantization Pipeline

Modular LoRA fine-tuning and quantization pipeline for Small Language Models (Qwen-2.5-Coder-1.5B/3B) using native PyTorch, Hugging Face `peft`, and `llama.cpp`.

---

## 1. Architecture & Execution Modes

The training script supports dual-mode execution to enforce our **Cold Staging, Hot Burst** methodology:

| Mode | Command Flag | Target Hardware | Purpose |
| :--- | :--- | :--- | :--- |
| **Cold Staging (Dry-Run)** | `--dry-run` | Local Laptop / CPU | Validates dataset tokenization, tensor shapes, gradient calculation, and LoRA weight saving in 1 step. |
| **Hot Burst (Full Training)** | `--train` (default) | NVIDIA DGX Spark (GB10) | Full multi-epoch fine-tuning using `bfloat16`, AdamW optimizer, and gradient accumulation. |

---

## 2. LoRA Fine-Tuning CLI Options

```bash
python3 train_lora.py \
  --model-id "Qwen/Qwen2.5-Coder-1.5B-Instruct" \
  --dataset "../dataset/train.jsonl" \
  --output-dir "./output" \
  --epochs 3 \
  --batch-size 2 \
  --grad-accum 4 \
  --lr 2e-4 \
  --lora-r 16 \
  --lora-alpha 32 \
  --max-time-minutes 15.0 \
  --merge
```

### Key Arguments:
- `--dry-run`: Runs exactly 1 training step on CPU/GPU to verify the pipeline without downloading or running full models.
- `--merge`: Automatically executes `model.merge_and_unload()` after training to save consolidated 16-bit weights ready for `llama.cpp` GGUF quantization.
- `--model-id`: Base model identifier on Hugging Face (default: `Qwen/Qwen2.5-Coder-1.5B-Instruct`).
- `--dataset`: Path to ChatML JSONL dataset (default: `../dataset/train.jsonl`).
- `--max-time-minutes`: Defensive time cutoff preventing sudden termination in shared compute environments.

---

## 3. Workflow to GGUF Export

```
[train.jsonl (138 samples)]
        │
        ▼ (train_lora.py)
[LoRA Adapter: adapter_model.safetensors]
        │
        ▼ (--merge)
[Merged Model: ./output/merged_model]
        │
        ▼ (convert_to_gguf.sh)
[F16 GGUF: ./output/gguf/clean-copilot-1.5b-f16.gguf] (~3.1 GB)
        │
        ▼ (llama-quantize)
[GGUF Model: clean-copilot-1.5b-q4_k_m.gguf] (~0.9 GB, Ready for edge CPU inference)
```

---

## 4. Automated One-Click GGUF Quantization (`convert_to_gguf.sh`)

After training with `--merge`, execute the automated quantization script:

```bash
# Standard 4-bit edge target (Q4_K_M)
./convert_to_gguf.sh

# Generate full multi-quantization matrix (Q4_K_M, Q5_K_M, Q8_0) and clean F16
./convert_to_gguf.sh --all --clean-f16
```

### Quantization Sizing Matrix:

| Quant Format | Output File Size (1.5B) | Target RAM | Speed on Standard CPU | Quality Retention |
| :--- | :--- | :--- | :--- | :--- |
| **Q4_K_M (Default)** | **~0.9 GB** | **~1.5 GB** | **45–70 tokens/s** | **>96.5%** |
| **Q5_K_M** | ~1.1 GB | ~1.8 GB | 35–55 tokens/s | >98.0% |
| **Q8_0** | ~1.6 GB | ~2.5 GB | 25–40 tokens/s | >99.5% |
| **F16 (Unquantized)** | ~3.1 GB | ~4.5 GB | 10–18 tokens/s | 100% (Baseline) |
