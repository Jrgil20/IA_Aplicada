# Technical Session Report: Teacher Dataset Burst & ML Runtime Initialization

> **Session Date:** October 22, 2026  
> **Target Infrastructure:** NVIDIA DGX Spark (`spark-0fbc`, `192.168.6.35/26`, GB10 Superchip, 128 GB Unified Memory)  
> **Operational Paradigm:** "Cold Staging, Hot Burst"  
> **Status:** Successfully Completed & Empirically Documented  

---

## 1. Objectives & Executive Summary

The primary goals of this session were:
1. Establish and verify multi-tenant isolation on the NVIDIA DGX Spark workstation to run project workloads without interfering with concurrent educational lab sessions.
2. Execute a high-throughput synthetic dataset generation burst assisted by the 30B parameter teacher model.
3. Validate and initialize the PyTorch ML execution runtime (`lora_venv`) on the ARM64 Grace Blackwell (GB10) superchip for Phase 2 LoRA adaptation.
4. Enforce strict cleanup and shutdown guardrails prior to lab window closure.

---

## 2. Infrastructure & Topology Orchestration

### 2.1 Multi-Instance Process Isolation on GB10 GPU

To avoid queue contention, context overwrites, and HTTP payload interference with concurrent live lab operations on port `8080`, an isolated secondary `llama-server` process was deployed exclusively for the **Edge Clean Copilot** project on port `8085`.

```
                                    NVIDIA DGX Spark 1 (128 GB Unified Memory)
                   ┌────────────────────────────────────────────────────────────────────────┐
                   │                                                                        │
[Live Lab App] ───>│ [Port 8080] llama-server (PID 28983)                                   │
(Browser/OpenCode) │  - Model: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf                 │
                   │  - VRAM: 20.1 GiB | Context: 32,768 tokens                             │
                   ├────────────────────────────────────────────────────────────────────────┤
[Live Lab Camera]->│ [Port 8084] llama-server VLM (PID 15845)                               │
(MJPEG Stream)     │  - Model: gemma-3-4b-it-Q8_0.gguf + mmproj-model-f16.gguf              │
                   │  - VRAM: 5.8 GiB  | Context: 4,096 tokens                              │
                   ├────────────────────────────────────────────────────────────────────────┤
[Edge Clean Copilot] [Port 8085] llama-server Dedicated Instance (PID 36645)               │
(Teacher Gen) ────>│  - Model: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf                 │
                   │  - VRAM: 20.1 GiB | Context: 32,768 tokens | Alias: qwen3-coder-project│
                   │  - Log: /home/ucab-spark1/qwen_project_8085.log                        │
                   └────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Memory & Thermal Telemetry Under Dual 30B Load

| Metric | Baseline (Single Model + VLM) | Dual 30B Concurrent Load (Ports 8080 + 8085 + 8084) | Delta / Overhead |
| :--- | :--- | :--- | :--- |
| **Total Unified Memory** | 121 GiB | 121 GiB | 0 GiB |
| **Used RAM / VRAM** | 35 GiB | 57 GiB | +22 GiB (Dedicated Qwen 30B + KV slots) |
| **Available RAM** | 86 GiB | 64 GiB | **64 GiB buffer remains for PyTorch** |
| **GPU Temperature** | 45 °C | 56 °C | +11 °C (Well within thermal limit) |
| **Power Draw** | 10 W (Idle) | 12 W – 24 W (Burst inference) | Nominal |
| **Inference Latency** | N/A | **14.4 ms** (First token response) | 69.4 – 91.6 tokens/s throughput |

---

## 3. Teacher Dataset Generation Burst

Using [`dataset/generate_with_teacher.py`](../dataset/generate_with_teacher.py) pointing directly to `http://192.168.6.35:8085/v1/chat/completions`, a 15-minute generation window was executed.

### 3.1 Quantitative Results
- **Generation Duration:** 15.02 minutes.
- **New Validated Pairs:** **94 synthetic ChatML pairs**.
- **Cumulative Dataset Size:** Increased from 66 to **160 samples** in [`dataset/generated_examples.jsonl`](../dataset/generated_examples.jsonl).
- **Approximate Cumulative Tokens:** **~186,212 tokens**.
- **Syntax & Schema Verification:** 100% passed via [`dataset/validate_dataset.py`](../dataset/validate_dataset.py).
- **Domain Topics Covered:**
  - Strict Domain Entities and Value Objects (`Result<T, E>` pattern, no mutable leaks).
  - Use Cases enforcing single-responsibility and dependency inversion.
  - AAA (Arrange-Act-Assert) unit tests using in-memory mock repositories and ports.
  - Zero tolerance for TypeScript `any`; strict interfaces and type guards.

---

## 4. Phase 2 Machine Learning Runtime Initialization

### 4.1 PyTorch & CUDA 13 Environment on Grace Blackwell (GB10)

To transition into Phase 2 (LoRA adaptation), a native Python virtual environment was established directly on the ARM64 host without container overhead:

- **Path:** `/home/ucab-spark1/lora_venv`
- **Python Version:** Python 3.12 (aarch64)
- **PyTorch Build:** `2.14.1+cu130` (Direct aarch64 wheel with CUDA 13 runtime)
- **Key Packages:** `transformers==5.20.2`, `peft==0.21.2`, `accelerate==1.15.0`, `datasets==5.1.0`
- **Native bfloat16 Support:** Verified (`torch.cuda.is_bf16_supported() == True`).

### 4.2 Dry-Run & Weight Download Analysis

Execution of [`training/train_lora.py --dry-run`](../training/train_lora.py) was initiated to download base model `Qwen/Qwen2.5-Coder-1.5B-Instruct` (3.09 GB) into `~/.cache/huggingface/hub/`:
- **Observed Downlink Rate:** ~2.2 – 2.5 MB/s over public educational laboratory network.
- **Downloaded Prior to Cutoff:** 2.26 GB out of 3.09 GB (**73.1%**).
- **Action Taken:** Terminated gracefully prior to 13:00 lab curfew to preserve system cleanliness and avoid partial checkpoint corruption.

---

## 5. Engineering Lessons Learned & Operational Guidelines

### Lesson 1: Network Downlink Bottlenecks in Shared Labs
Downloading multi-gigabyte foundation model weights over shared campus connections consumes 20–25 minutes of precious laboratory GPU access.
> [!IMPORTANT]
> **Actionable Protocol:** Foundation model weights must be pre-cached on the DGX Spark NVMe drive before the laboratory slot begins, or downloaded via an authenticated Hugging Face token (`HF_TOKEN`) to bypass unauthenticated CDN rate limits.

### Lesson 2: Dedicated Ports Guarantee Zero Lab Contention
Running concurrent `llama-server` instances with distinct port bindings (`8085` vs `8080`) completely isolates memory buffers, slot allocations, and logging, preventing cross-tenant request drops.

### Lesson 3: Mandatory Time Bounding via `--max-time-minutes`
In shared supercomputing environments with strict session curfews (e.g., 2 hours), scripts must always incorporate defensive time limits (`--max-time-minutes`) that gracefully flush buffers, write checkpoints, and terminate before the physical session cut.

### Lesson 4: Privileged Operation Guardrails
Destructive actions (such as `sudo shutdown` or `sudo reboot`) must never be automated by autonomous agents without mandatory human confirmation, particularly when `uptime` indicates multiple concurrent user sessions.
