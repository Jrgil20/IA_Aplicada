# Comandos Útiles

Cheat sheet de comandos frecuentes para operaciones en la estación NVIDIA DGX Spark, quantización con `llama.cpp` y desarrollo diario.

---

## 1. Monitoreo de Hardware

```bash
# Monitoreo continuo de GPUs NVIDIA
watch -n 1 nvidia-smi

# Información detallada de memoria VRAM y procesos
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv
```

---

## 2. Inferencia con llama.cpp

```bash
# Iniciar servidor local llama-server
llama-server \
  -m /path/to/model.gguf \
  --port 8080 \
  --ctx-size 8192 \
  -ngl 99

# Test de inferencia rápido vía CLI
llama-cli \
  -m /path/to/model.gguf \
  -p "Describe the Dependency Rule in Clean Architecture:" \
  -n 256 \
  -ngl 99
```

---

## 3. Cuantización GGUF

```bash
# Conversión a formato GGUF estándar (FP16)
python3 convert_hf_to_gguf.py /path/to/hf_model/ --outtype f16 --outfile model-f16.gguf

# Cuantización a 4-bit (Q4_K_M)
llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

---

## 4. Hugging Face CLI

```bash
# Login
huggingface-cli login

# Descarga de pesos o dataset
huggingface-cli download <repo_id> <filename> --local-dir ./weights
```
