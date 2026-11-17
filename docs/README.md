# Technical Documentation — Applied AI

> **AI-first knowledge base.** Each module (`/dgx`, `/cuda`, `/qlora`) is a self-contained unit with its own `README.md` as an entry point. Agents should consult this index to decide which module to read based on the active task; it is not necessary to load all documentation into context.

---

## Applied AI Playbook (start here for products)

**[Playbook index](./playbook/README.md)** — the practical layer: when to use AI, which architecture, which model tier (stay, go up, go cheaper, go private), costs and savings, privacy, hardening, evaluation, and production readiness. The modules below are the technical background.

---

## Documentation Modules

### 1. [NVIDIA DGX Spark (`/dgx`)](./dgx/README.md)
Technical and operational guide for the desktop supercomputing workstation (GB10 Grace Blackwell, 128 GB Unified Memory).
- Hardware architecture and superchip specifications.
- NVIDIA DGX OS software stack and NGC containers.
- "Cold Staging, Hot Burst" methodology.
- Links to official documentation and playbooks.

### 2. [CUDA & GPU Acceleration (`/cuda`)](./cuda/README.md)
Parallelism and optimization concepts for NVIDIA GPUs.
- Streaming Multiprocessors, Warps, and memory hierarchy.
- Compute Capability and architecture support (Ampere to Blackwell).
- Critical environment variables and monitoring toolchain (`nvidia-smi`, `nvtop`).
- FlashAttention and memory optimization.

### 3. [LoRA & QLoRA PEFT (`/qlora`)](./qlora/README.md)
Guide to parameter-efficient fine-tuning for language models.
- Mathematical foundations of low-rank decomposition ($W = W_0 + B \cdot A$).
- QLoRA innovations: NormalFloat4 (NF4), Double Quantization, and Paged Optimizers.
- Selection of `target_modules` for Qwen and Llama architectures.
- Complete pipeline: training, merging (`merge_and_unload`), and preparation for GGUF.

---

## Quick Guides

- [Useful Commands](./useful-commands.md) — Command cheat sheet for terminal, hardware, llama.cpp, and GGUF.
- [Environment Specifications](./environment.md) — Comparison between the DGX Spark workstation and the edge deployment environment.
- [Local SLMs vs. Cloud LLMs](./local-slm-vs-cloud-llm.md) — Architectural decision record, economic ROI thresholds, and hybrid tiering guide.
- [Cost-Aware Routing](./cost-aware-routing.md) — Design note (not implemented): cascade of rules, local SLM, and frontier LLM to cut cost on small queries.
- [Applied AI Use Cases](./applied-ai-use-cases.md) — Which tier (rules, cache, local SLM, cloud) fits which task, and when to escalate.
- [Scaling AI Workloads](./scaling-ai-workloads.md) — Model escalation vs. compute scaling: laptop, DGX Spark, cloud.
- [Prompt Caching](./prompt-caching.md) — Response, semantic, and prefix/KV caching: when to use each, verified numbers, risks.
- [Model Serving for Apps](./model-serving-for-apps.md) — Runtimes (llama.cpp, vLLM, Ollama, APIs), flags, capacity, topologies, production checklist.
- [Model Selection](./model-selection.md) — Process and criteria to choose and replace a model.
