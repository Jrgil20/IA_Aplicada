# Reference Guide: CUDA and GPU Acceleration

Technical guide on CUDA architecture, GPU memory management, and toolchains for language model (LLM/SLM) development and training.

---

## 1. CUDA Compute Architecture

CUDA (Compute Unified Device Architecture) exposes the massive parallelism of NVIDIA GPUs:

- **Execution Hierarchy:** Threads → Warps (32 threads executed in lockstep) → Thread Blocks → Grid.
- **Streaming Multiprocessors (SM):** Processing units composed of FP32, FP64, INT32 cores and **Tensor Cores** (designed for accelerated matrix multiplication in FP16, BF16, FP8, and FP4).
- **Memory Hierarchy:**
  - **Global Memory / HBM / LPDDR5x:** High-capacity main space where model weights and KV Cache reside.
  - **Shared Memory / L1 Cache:** Ultra-fast per-SM local memory, critical for optimizations like **FlashAttention**.
  - **Registers:** Immediate per-thread access.

### Architecture and Compute Capability Table

| Architecture | Compute Capability (`sm_xx`) | Hardware Examples | Key Precisions |
| :--- | :--- | :--- | :--- |
| **Ampere** | `sm_80`, `sm_86` | A100, RTX 3090, T4 (`sm_75`) | FP16, BF16, TF32, INT8 |
| **Ada Lovelace** | `sm_89` | RTX 4090, L4 | FP8 (E4M3, E5M2), FP16, BF16 |
| **Hopper** | `sm_90` | H100, H200 | Transformer Engine (dynamic FP8) |
| **Blackwell** | `sm_100`, `sm_120` | DGX B200, **DGX Spark (GB10)** | FP4, 2nd-gen native FP8, NVLink 5 |

---

## 2. Critical Environment Variables

```bash
# Select visible GPU for the process
export CUDA_VISIBLE_DEVICES=0

# Prevent memory fragmentation in PyTorch
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# JIT compilation config for PyTorch / C++ extensions
export TORCH_CUDA_ARCH_LIST="8.9;9.0;10.0"
```

---

## 3. Toolchain and Diagnostics

### 3.1 Compiler and Driver Verification
```bash
# Driver version and GPU status
nvidia-smi

# Low-level CUDA compiler version
nvcc --version
```

### 3.2 Detailed VRAM and Compute Monitoring
```bash
# Continuous dynamic monitoring every second
watch -n 1 nvidia-smi --format=csv --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.free

# Interactive htop-style monitor for GPUs (if nvtop is installed)
nvtop
```

### 3.3 Verification from Python / PyTorch
```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"Active device: {torch.cuda.get_device_name(0)}")
print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
```

---

## 4. Key Optimization Techniques for LLMs

1. **FlashAttention-2 / FlashAttention-3:** Reduces memory complexity from $O(N^2)$ to $O(N)$ by avoiding materialization of the full attention matrix in global memory.
2. **Reduced Precisions:**
   - **BF16 (Bfloat16):** Maintains the dynamic range of FP32 (8 exponent bits) preventing underflow/overflow during training without meaningful precision loss.
   - **FP8 / FP4:** Specific to Ada, Hopper, and Blackwell architectures for accelerating inference and fine-tuning throughput.
3. **Activation Checkpointing (Gradient Checkpointing):** Trades ~20% compute time by recomputing activations in the backward pass to save up to 60% VRAM.
