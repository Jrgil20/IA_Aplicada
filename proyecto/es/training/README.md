# Pipeline de Entrenamiento LoRA y Cuantización a GGUF — Edge Clean Copilot

Pipeline modular de fine-tuning y cuantización con LoRA para Small Language Models (Qwen-2.5-Coder-1.5B/3B) utilizando PyTorch nativo, Hugging Face `peft` y `llama.cpp`.

---

## 1. Arquitectura y Modos de Ejecución

El script de entrenamiento soporta ejecución en modo dual según la metodología **"Cold Staging, Hot Burst"**:

| Modo | Flag del Comando | Hardware Objetivo | Propósito |
| :--- | :--- | :--- | :--- |
| **Cold Staging (Dry-Run)** | `--dry-run` | Laptop Local / CPU | Valida tokenización, dimensiones de tensores, cálculo de gradientes y guardado de LoRA en 1 paso. |
| **Hot Burst (Entrenamiento)**| `--train` (default) | NVIDIA DGX Spark (GB10) | Fine-tuning multi-época usando `bfloat16`, optimizador AdamW y acumulación de gradientes. |

---

## 2. Opciones de CLI para Fine-Tuning LoRA

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

### Argumentos Principales:
- `--dry-run`: Ejecuta exactamente 1 paso de entrenamiento en CPU/GPU para verificar el pipeline sin descargar ni correr modelos enteros.
- `--merge`: Ejecuta automáticamente `model.merge_and_unload()` tras entrenar para consolidar los pesos de 16-bit listos para `llama.cpp`.
- `--model-id`: Identificador del modelo base en Hugging Face (default: `Qwen/Qwen2.5-Coder-1.5B-Instruct`).
- `--dataset`: Ruta al dataset ChatML (default: `../dataset/train.jsonl`).
- `--max-time-minutes`: Límite defensivo de tiempo que previene cortes abruptos en infraestructuras compartidas.

---

## 3. Flujo hacia la Exportación GGUF

```
[train.jsonl (138 muestras)]
        │
        ▼ (train_lora.py)
[Adaptador LoRA: adapter_model.safetensors]
        │
        ▼ (--merge)
[Modelo Fusionado: ./output/merged_model]
        │
        ▼ (convert_to_gguf.sh)
[F16 GGUF: ./output/gguf/clean-copilot-1.5b-f16.gguf] (~3.1 GB)
        │
        ▼ (llama-quantize)
[Modelo GGUF: clean-copilot-1.5b-q4_k_m.gguf] (~0.9 GB, listo para CPU edge)
```

---

## 4. Cuantización Automatizada One-Click (`convert_to_gguf.sh`)

Tras entrenar con `--merge`, ejecuta el script de automatización:

```bash
# Cuantización estándar a 4-bit para el edge (Q4_K_M)
./convert_to_gguf.sh

# Matriz completa (Q4_K_M, Q5_K_M, Q8_0) y limpieza del F16 intermedio
./convert_to_gguf.sh --all --clean-f16
```

### Matriz de Dimensionamiento de Cuantización:

| Formato | Tamaño en Disco (1.5B) | RAM Objetivo | Velocidad en CPU Estándar | Retención de Calidad |
| :--- | :--- | :--- | :--- | :--- |
| **Q4_K_M (Default)** | **~0.9 GB** | **~1.5 GB** | **45–70 tokens/s** | **>96.5%** |
| **Q5_K_M** | ~1.1 GB | ~1.8 GB | 35–55 tokens/s | >98.0% |
| **Q8_0** | ~1.6 GB | ~2.5 GB | 25–40 tokens/s | >99.5% |
| **F16 (Sin cuantizar)** | ~3.1 GB | ~4.5 GB | 10–18 tokens/s | 100% (Base) |
