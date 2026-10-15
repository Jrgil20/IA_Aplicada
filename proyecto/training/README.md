# Edge Clean Copilot — LoRA Training Pipeline

Modular LoRA fine-tuning pipeline for Small Language Models (Qwen-2.5-Coder-1.5B/3B) using native PyTorch and Hugging Face `peft`.

---

## 1. Architecture & Execution Modes

The training script supports dual-mode execution to enforce our **Cold Staging, Hot Burst** methodology:

| Mode | Command Flag | Target Hardware | Purpose |
| :--- | :--- | :--- | :--- |
| **Cold Staging (Dry-Run)** | `--dry-run` | Local Laptop / CPU | Validates dataset tokenization, tensor shapes, gradient calculation, and LoRA weight saving in 1 step. |
| **Hot Burst (Full Training)** | `--train` (default) | NVIDIA DGX Spark (GB10) | Full multi-epoch fine-tuning using `bfloat16`, AdamW optimizer, and gradient accumulation. |

---

## 2. CLI Options

```bash
python3 train_lora.py \
  --model-id "Qwen/Qwen2.5-Coder-1.5B-Instruct" \
  --dataset "../dataset/seed_examples.jsonl" \
  --output-dir "./output" \
  --epochs 3 \
  --batch-size 2 \
  --grad-accum 4 \
  --lr 2e-4 \
  --lora-r 16 \
  --lora-alpha 32 \
  --merge
```

### Key Arguments:
- `--dry-run`: Runs exactly 1 training step on CPU/GPU to verify the pipeline without downloading or running full models.
- `--merge`: Automatically executes `model.merge_and_unload()` after training to save consolidated 16-bit weights ready for `llama.cpp` GGUF quantization.
- `--model-id`: Base model identifier on Hugging Face (default: `Qwen/Qwen2.5-Coder-1.5B-Instruct`).
- `--dataset`: Path to ChatML JSONL dataset (default: `../dataset/seed_examples.jsonl`).

---

## 3. Workflow to GGUF Export

```
[seed_examples.jsonl]
        │
        ▼ (train_lora.py)
[LoRA Adapter: adapter_model.safetensors]
        │
        ▼ (--merge)
[Merged Model: ./output/merged]
        │
        ▼ (llama.cpp / convert_hf_to_gguf.py)
[GGUF Model: clean-copilot-q4_k_m.gguf] (Ready for edge CPU inference)
```
