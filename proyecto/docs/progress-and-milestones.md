# Edge Clean Copilot: Progress & Verified Milestones

> **Project:** Edge Clean Copilot — Specialized Small Language Model (SLM) for Clean Architecture  
> **Course:** Applied Artificial Intelligence (UCAB)  
> **Author:** Jesús Rodolfo Gil Farías  
> **Current Global Progress:** **70%**  
> **Last Verification:** October 22, 2026 (Consolidation & Session Close)  

---

## 1. Executive Status Board

| Phase | Description | Scheduled Window | Completion | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Infrastructure, Networking & Teacher Dataset Generation | Weeks 1–3 | **100%** | **COMPLETED & VERIFIED** |
| **Phase 2** | LoRA Adaptation & Small Language Model Specialization | Weeks 4–7 | **85%** (Runtime ready, 73% weights in NVMe) | **ACTIVE / READY FOR SPARK BURST** |
| **Phase 3** | Weight Consolidation, Quantization & GGUF Export | Weeks 8–11 | **50%** (Pipeline script automated & tested) | STAGED |
| **Phase 4** | Hexagonal CLI, Unit Tests & Automated Benchmark | Weeks 12–15 | **70%** (28/28 tests green, benchmark live) | IN PROGRESS |

---

## 2. Phase 1 Milestones (Completed & Validated)

- [x] **Direct Network Topology (Auto-MDIX):**
  - Peer-to-peer Ethernet link between client laptop (`192.168.6.44/26`) and NVIDIA DGX Spark (`192.168.6.35/26`).
  - Ed25519 passwordless authentication verified via `~/.ssh/config`.
  - Subnetting policy `/26` (`255.255.255.192`) strictly documented and enforced.

- [x] **Teacher Model Serving (`llama-server`):**
  - Teacher model `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` offloaded 99 layers onto Grace Blackwell GB10 GPU.
  - Multi-instance deployment on port `8085` preventing queue or context contention with lab port `8080`.
  - Real-time generation speed validated at **~91.6 tokens/s** with sub-15ms first-token latency.

- [x] **Clean Architecture Seed Dataset Curation:**
  - 8 hand-crafted canonical pairs extracted from real-world domain models (ArrowMaze).
  - Explicit enforcement of Domain Entities, pure Value Objects, Use Cases with `Result<T, DomainError>`, abstract Ports, and AAA unit tests.

- [x] **Automated Teacher Dataset Generator:**
  - Implemented [`dataset/generate_with_teacher.py`](../dataset/generate_with_teacher.py) with time-bounding flag (`--max-time-minutes`).
  - Generated **160 verified ChatML pairs** (~186k tokens) stored in [`dataset/generated_examples.jsonl`](../dataset/generated_examples.jsonl).

- [x] **Stratified Dataset Partitioning (Zero Data Leakage):**
  - Implemented [`dataset/split_dataset.py`](../dataset/split_dataset.py) with deterministic seed (`seed=42`).
  - Created [`dataset/train.jsonl`](../dataset/train.jsonl) (**138 samples**, ~156k tokens, 82.1%).
  - Created [`dataset/eval_holdout.jsonl`](../dataset/eval_holdout.jsonl) (**30 samples**, ~35k tokens, 17.9%) strictly isolated for evaluation.
  - Syntax validated via [`dataset/validate_dataset.py`](../dataset/validate_dataset.py).

---

## 3. Phase 2 Milestones (In Progress / 85% Completed)

- [x] **Native PyTorch Fine-Tuning Pipeline:**
  - Implemented [`training/train_lora.py`](../training/train_lora.py) with AdamW, dynamic batch padding, `--max-time-minutes`, and `--merge`.
  - LoRA rank $r=16$, $\alpha=32$, targeting all attention and MLP projections.
  - Default dataset pointing to `../dataset/train.jsonl`.

- [x] **Grace Blackwell (GB10) Environment Setup:**
  - Dedicated virtualenv `/home/ucab-spark1/lora_venv` on Spark 1.
  - PyTorch `2.14.1+cu130` with native CUDA 13.0 and `bfloat16` hardware acceleration verified.

- [x] **Base Model Weight Download (73% complete):**
  - Downloaded 2.26 GB of 3.09 GB for `Qwen/Qwen2.5-Coder-1.5B-Instruct` into `~/.cache/huggingface/hub/`.

- [ ] **First Hot Burst Fine-Tuning Run (Pending Next Spark Session):**
  - Resume ~800 MB remaining weight download (~3 min).
  - Execute 10–15 minute training burst on `train.jsonl` with `--merge`.

---

## 4. Phase 3 Milestones (Staged / 50% Completed)

- [x] **Automated One-Click GGUF Quantization Script:**
  - Implemented [`training/convert_to_gguf.sh`](../training/convert_to_gguf.sh) with autodetection of `llama.cpp` and `lora_venv`.
  - Defensive error handling against missing models or unbuilt binaries.
  - Generates `Q4_K_M` (default) and multi-quantization matrix (`Q4_K_M`, `Q5_K_M`, `Q8_0`) with `--clean-f16`.

- [ ] **Physical Quantization Execution:**
  - Awaits consolidated weights from Phase 2 burst on Spark.

---

## 5. Phase 4 Milestones (CLI Client & Benchmark — 70% Completed)

- [x] **Hexagonal Architecture Implementation (Ports & Adapters):**
  - TypeScript CLI under [`proyecto/cli/`](../cli/) strictly separating Domain, Application, Ports, and Infrastructure.
  - Defensive URL normalization in [`LlamaServerAdapter.ts`](../cli/src/infrastructure/ai/LlamaServerAdapter.ts) tolerating `/`, `/v1`, and `/v1/chat/completions`.

- [x] **Comprehensive Vitest Unit Testing Suite:**
  - **28 tests passing in 278 ms (100% green)** across all 5 test suites:
    - `SourceFile.test.ts` (10 tests)
    - `RefactorCodeUseCase.test.ts` (5 tests)
    - `Result.test.ts` (4 tests)
    - `LlamaServerAdapter.test.ts` (7 tests)
    - `FileDiskReader.test.ts` (2 tests)

- [x] **Automated Architectural Benchmark Harness:**
  - Implemented [`evaluation/eval_benchmark.py`](../evaluation/eval_benchmark.py) in pure Python 3 (zero dependencies).
  - Clean Architecture Score (CAS, 0–100 pts) evaluating Domain Boundary (30%), Invariants (25%), Ports (25%), and Type Safety (20%).
  - Calibrated against 10 control test cases in [`evaluation/test_benchmark_cases.jsonl`](../evaluation/test_benchmark_cases.jsonl) (canonical 100/100, coupled $\le 50/100$).
