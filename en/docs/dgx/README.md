# Reference Guide: NVIDIA DGX Spark

Technical and operational guide for development, training, and inference on the **NVIDIA DGX Spark** workstation.

---

## 1. Hardware Architecture

The NVIDIA DGX Spark is a compact desktop AI supercomputer designed for prototyping, fine-tuning, and local deployment of language models and artificial intelligence workloads.

| Component | Technical Specification |
| :--- | :--- |
| **Superchip** | **NVIDIA GB10 (Grace Blackwell)** |
| **CPU** | 20 Arm cores (10 Performance + 10 Efficiency cores) |
| **GPU** | NVIDIA Blackwell architecture |
| **System Memory** | **128 GB LPDDR5x unified coherent memory** (shared CPU/GPU address space) |
| **AI Performance** | ~1 PFLOPS (1,000 AI TOPS) |
| **Networking** | NVIDIA ConnectX-7 (up to 200 GbE for multi-node clustering) |
| **Form Factor** | Compact desktop (silent workstation) |

> [!NOTE]
> The **128 GB coherent unified memory** allows loading and training models with memory footprints that exceed the VRAM of conventional consumer dedicated GPUs, eliminating PCIe CPU-GPU transfer bottlenecks.

---

## 2. Software Stack and Operating System

The workstation runs **NVIDIA DGX OS** (optimized distribution based on Ubuntu Linux):

- **Drivers & Runtime:** Pre-installed proprietary NVIDIA drivers, CUDA Toolkit, cuDNN, and TensorRT.
- **Containers:** **NVIDIA Container Toolkit** (`nvidia-docker`) pre-configured out of the box for NVIDIA NGC images.
- **Supported Frameworks:** PyTorch (native CUDA/aarch64), Hugging Face (`transformers`, `peft`, `bitsandbytes`), `vLLM`, `Ollama`, `llama.cpp`, and NVIDIA NIM microservices.

---

## 3. Connection and Remote Development Workflow

For lab sessions at UCAB, access is typically done over the network:

### 3.1 SSH Connection
```bash
# Remote terminal connection
ssh <user>@<dgx-spark-ip>
```

### 3.2 VS Code Remote Development
1. Install the **Remote - SSH** extension in local Visual Studio Code.
2. Connect to `Host dgx-spark` by configuring `~/.ssh/config`.
3. Open the repository folder directly on the DGX Spark filesystem.

### 3.3 File Synchronization
* **Git:** Clone and push intermediate branches to the remote repository.
* **Rsync:** For transferring weights or local datasets:
```bash
rsync -avzP ./dataset.jsonl <user>@<dgx-spark-ip>:~/Develop/IA_Aplicada/data/
```

---

## 4. Essential DGX OS Commands

### 4.1 Resource Monitoring
```bash
# GPU and unified memory status
nvidia-smi

# Real-time monitoring every second
watch -n 1 nvidia-smi

# Arm CPU cores and system RAM monitoring
htop
```

### 4.2 Running NGC Containers
```bash
# Launch an interactive PyTorch container with full GPU support
docker run --gpus all --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -it --rm -v $(pwd):/workspace nvcr.io/nvidia/pytorch:latest
```

### 4.3 Local Inference Server (`llama-server`)
```bash
# Start the teacher model (Qwen 30B GGUF) on the DGX Spark
llama-server \
  -m /models/qwen3-coder-30b.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 8192 \
  --n-gpu-layers 99
```

---

## 5. Methodology: "Cold Staging, Hot Burst"

Given the limited compute budget (~2-hour weekly sessions on the DGX Spark):

1. **Pre-lab (on laptop):**
   - Validate JSONL dataset syntax.
   - Run single-step synthetic tests on CPU to verify training scripts don't crash due to dependencies or format issues.
2. **On DGX Spark:**
   - Set up the environment or launch the pre-approved container.
   - Launch the LoRA fine-tuning burst (20 to 40 minutes).
   - Merge adapters (`merge_and_unload`).
   - Immediately quantize to GGUF format (`Q4_K_M`, `Q5_K_M`).
3. **Post-lab (on laptop):**
   - Download the quantized `.gguf` binary.
   - Evaluate performance metrics and architectural adherence locally without consuming DGX Spark time.

---

## 6. Official Resources and Playbooks

- **Central Documentation:** [NVIDIA DGX Spark User Guide](https://docs.nvidia.com/dgx/dgx-spark/)
- **Operating System Guide:** [NVIDIA DGX OS Documentation](https://docs.nvidia.com/dgx/dgx-os-7-user-guide/introduction.html)
- **Workload Playbooks (GitHub):** [NVIDIA/dgx-spark-playbooks](https://github.com/NVIDIA/dgx-spark-playbooks)
- **Developer Portal:** [NVIDIA Spark Developer Portal](https://build.nvidia.com/spark)
