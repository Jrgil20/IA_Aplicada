# Edge Clean Copilot: Progress & Verified Milestones

> **Project:** Edge Clean Copilot — Specialized Small Language Model (SLM) for Clean Architecture  
> **Course:** Applied Artificial Intelligence (UCAB)  
> **Author:** Jesús Rodolfo Gil Farías  
> **Current Global Progress:** **57%**  
> **Last Verification:** October 22, 2026  

---

## 1. Executive Status Board

| Phase | Description | Scheduled Window | Completion | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Infrastructure, Networking & Teacher Dataset Generation | Weeks 1–3 | **100%** | **COMPLETED** |
| **Phase 2** | LoRA Adaptation & Small Language Model Specialization | Weeks 4–7 | **80%** (Pre-trained runtime ready) | **ACTIVE / READY TO LAUNCH** |
| **Phase 3** | Weight Consolidation, Quantization & GGUF Export | Weeks 8–11 | **0%** | PENDING |
| **Phase 4** | Hexagonal CLI, Offline Edge Inference & Publication | Weeks 12–15 | **50%** (Core architecture implemented) | IN PROGRESS |

---

## 2. Phase 1 Milestones (Completed & Validated)

- [x] **Direct Network Topology (Auto-MDIX):**
  - Peer-to-peer Ethernet link between client laptop (`192.168.6.44/26`) and NVIDIA DGX Spark (`192.168.6.35/26`).
  - Ed25519 passwordless authentication verified via `~/.ssh/config`.
  - Subnetting policy `/26` (`255.255.255.192`) strictly documented and enforced.

- [x] **Teacher Model Serving (`llama-server`):**
  - Teacher model `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` successfully offloaded 99 layers onto Grace Blackwell GB10 GPU.
  - Multi-instance deployment validated on port `8085` to guarantee zero interference with educational lab port `8080`.
  - Real-time generation speed validated at **~91.6 tokens/s** with sub-15ms first-token latency.

- [x] **Clean Architecture Seed Dataset Curation:**
  - 8 hand-crafted canonical pairs extracted from real-world domain models (ArrowMaze).
  - Explicit enforcement of:
    - Domain Entities with invariant checks in factory constructors.
    - Pure Value Objects with immutable properties and structural equality.
    - Application Use Cases returning `Result<T, DomainError>`.
    - Ports (interfaces) and Adapters (implementations) adhering to the Dependency Inversion Principle.
    - AAA (Arrange-Act-Assert) unit tests using in-memory mock repositories.

- [x] **Automated Teacher Dataset Generator:**
  - Implemented [`dataset/generate_with_teacher.py`](../dataset/generate_with_teacher.py) featuring:
    - Strict ChatML schema formatting.
    - Time-bounding defensive flag (`--max-time-minutes`).
    - Domain architectural prompt catalog spanning refactoring, use cases, ports, and SOLID critiques.
  - Successfully generated **160 verified ChatML pairs** (~186,212 tokens) stored in [`dataset/generated_examples.jsonl`](../dataset/generated_examples.jsonl).

- [x] **Dataset Validation Suite:**
  - Implemented [`dataset/validate_dataset.py`](../dataset/validate_dataset.py) verifying role integrity (`system`, `user`, `assistant`), non-empty payloads, and token approximations.

---

## 3. Phase 2 Milestones (In Progress / 80% Completed)

- [x] **Native PyTorch Fine-Tuning Pipeline:**
  - Implemented [`training/train_lora.py`](../training/train_lora.py) utilizing PyTorch, Hugging Face `transformers`, and `peft`.
  - Architecture highlights:
    - Dual execution modes: `--dry-run` (1-step CPU/GPU verification) and full multi-epoch training.
    - Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
    - Configurable LoRA rank ($r=16$) and scaling factor ($\alpha=32$).
    - Dynamic sequence length padding with attention masking in collate function.
    - Graceful time-limit cutoff (`--max-time-minutes`) preventing sudden session termination.
    - Integrated `--merge` flag invoking `model.merge_and_unload()` for immediate GGUF conversion.

- [x] **Grace Blackwell (GB10) Environment Setup:**
  - Created dedicated Python virtual environment `/home/ucab-spark1/lora_venv` on Spark 1.
  - Verified PyTorch `2.14.1+cu130` with native CUDA 13.0 and `bfloat16` hardware acceleration.
  - Installed all required libraries (`peft`, `transformers`, `accelerate`, `safetensors`).

- [x] **Base Model Weight Download (73% complete):**
  - Downloaded 2.26 GB of 3.09 GB for `Qwen/Qwen2.5-Coder-1.5B-Instruct` into `~/.cache/huggingface/hub/`.

- [ ] **First Hot Burst Fine-Tuning Run (Pending):**
  - Complete remaining ~800 MB weight download.
  - Execute 10–15 minute training burst on 160 synthetic pairs.
  - Monitor convergence, loss progression, and GPU VRAM footprint.

---

## 4. Phase 4 Milestones (CLI Client — 50% Completed)

- [x] **Hexagonal Architecture Implementation (Ports & Adapters):**
  - Built TypeScript CLI under [`proyecto/cli/`](../cli/) with strict separation of concerns:
    - **Domain:** [`SourceFile.ts`](../cli/src/domain/entities/SourceFile.ts) entity enforcing file size limits (<50k chars) and allowed extensions.
    - **Application:** [`RefactorCodeUseCase.ts`](../cli/src/application/use-cases/RefactorCodeUseCase.ts) orchestrating refactoring logic and returning `Result<T, E>`.
    - **Application Ports:** [`IInferenceEngine.ts`](../cli/src/application/ports/IInferenceEngine.ts) defining the abstraction contract for LLM inference.
    - **Infrastructure Adapters:**
      - [`MockInferenceAdapter.ts`](../cli/src/infrastructure/ai/MockInferenceAdapter.ts) for deterministic offline testing.
      - [`LlamaServerAdapter.ts`](../cli/src/infrastructure/ai/LlamaServerAdapter.ts) for live HTTP inference.
      - [`FileDiskReader.ts`](../cli/src/infrastructure/fs/FileDiskReader.ts) for filesystem operations.
    - **Composition Root:** [`index.ts`](../cli/src/infrastructure/cli/index.ts) utilizing Commander CLI.

- [ ] **Offline Edge Inference with Trained SLM (Pending Phase 3):**
  - Integration of locally quantized `.gguf` student model via `llama.cpp` or local server adapter.
