# Useful Commands

Cheat sheet of frequently used commands for operations on the NVIDIA DGX Spark workstation, quantization with `llama.cpp`, and daily development.

---

## 1. Hardware Monitoring

```bash
# Continuous NVIDIA GPU monitoring
watch -n 1 nvidia-smi

# Detailed VRAM and process information
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv
```

---

## 2. Inference with llama.cpp

```bash
# Start local llama-server
llama-server \
  -m /path/to/model.gguf \
  --port 8080 \
  --ctx-size 8192 \
  -ngl 99

# Quick inference test via CLI
llama-cli \
  -m /path/to/model.gguf \
  -p "Describe the Dependency Rule in Clean Architecture:" \
  -n 256 \
  -ngl 99
```

---

## 3. GGUF Quantization

```bash
# Convert to standard GGUF format (FP16)
python3 convert_hf_to_gguf.py /path/to/hf_model/ --outtype f16 --outfile model-f16.gguf

# Quantize to 4-bit (Q4_K_M)
llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

---

## 4. Hugging Face CLI

```bash
# Login
huggingface-cli login

# Download weights or dataset
huggingface-cli download <repo_id> <filename> --local-dir ./weights
```
