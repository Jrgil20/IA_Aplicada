# Environment Specifications

Hardware and execution environment details for the course.

---

## 1. Training Workstation: NVIDIA DGX Spark

- **Architecture:** NVIDIA Grace Blackwell (GB10)
- **Unified Memory:** 128 GB Unified Memory
- **Purpose:** LoRA training bursts (20–40 min), synthetic data generation with teacher model (Qwen-30B), and direct GGUF conversion.
- **Full Guide:** See the [NVIDIA DGX Spark Reference Guide](./dgx/README.md).

---

## 2. Target Inference Environment (Edge / Laptops)

- **Architecture:** Commercial x86_64 / ARM / iGPU CPU
- **RAM:** 8 GB – 16 GB
- **Goal:** 100% offline execution with no dedicated GPU dependencies, targeting 35–70 tokens/s throughput via `llama.cpp` or `Ollama`.
