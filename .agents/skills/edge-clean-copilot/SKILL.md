---
name: edge-clean-copilot
description: >-
  Operational knowledge, Clean Architecture guardrails, and execution workflows for the
  Edge Clean Copilot semester project. Use when training LoRA adapters on DGX Spark,
  generating synthetic architecture datasets, converting models to GGUF, developing
  the hexagonal TypeScript CLI, or evaluating offline SLM refactoring quality.
---

# Edge Clean Copilot Runbook & Operational Skill

This skill provides autonomous agents with the complete architectural constraints, hardware protocols, and execution workflows for the **Edge Clean Copilot** project.

---

## 1. Architectural Guardrails (Non-Negotiable)

Any code produced, refactored, or trained under this project MUST strictly comply with:

1. **Clean Architecture Dependency Rule:**
   - Inner layers (`domain`, `application`) MUST NEVER import from outer layers (`infrastructure`, `cli`, frameworks, databases, or third-party SDKs).
   - Domain entities and value objects contain zero external dependencies.
2. **Type Safety & Zero `any` Policy:**
   - The TypeScript `any` type is strictly forbidden.
   - Always use concrete interfaces, dedicated value types, or `unknown` with narrow type guards.
3. **Deterministic Error Handling (`Result<T, E>`):**
   - Use cases and domain operations must return functional `Result<T, DomainError>` rather than throwing unhandled exceptions.
4. **Ports & Adapters (Hexagonal Decoupling):**
   - The application layer interacts with language models strictly through the [`IInferenceEngine`](file:///home/jr_g/Develop/IA_Aplicada/proyecto/cli/src/application/ports/IInferenceEngine.ts) port interface.
   - Core CLI logic must be 100% testable offline via [`MockInferenceAdapter`](file:///home/jr_g/Develop/IA_Aplicada/proyecto/cli/src/infrastructure/ai/MockInferenceAdapter.ts).

---

## 2. Operational Methodology: "Cold Staging, Hot Burst"

```
[ Cold Staging (Local Laptop) ]
  ├── Curation of ChatML pairs (seed_examples.jsonl)
  ├── 1-step dry run on CPU/GPU (--dry-run)
  └── Offline unit testing of CLI layers via MockInferenceAdapter
               │
               ▼ (Burst Execution)
[ Hot Burst (NVIDIA DGX Spark) ]
  ├── Teacher synthetic generation burst (port 8085)
  ├── Multi-epoch LoRA training (train_lora.py with --max-time-minutes)
  └── Consolidated weight merge (model.merge_and_unload())
               │
               ▼ (Consolidation)
[ Edge Deployment (100% Offline) ]
  └── GGUF quantization (Q4_K_M) served locally at 45-70 tokens/s
```

---

## 3. Hardware Protocols & DGX Spark Multi-Tenancy

When connecting to the **NVIDIA DGX Spark** (`192.168.6.35`, `ucab-spark1`):

1. **Port Isolation:**
   - Port `8080`: Reserved for live educational laboratory services (`llama-server` Qwen 30B).
   - Port `8084`: Reserved for multimodal visual model (`gemma-3-4b-it` + `mmproj`).
   - **Port `8085`**: Dedicated endpoint for **Edge Clean Copilot** project workloads. Never hijack port 8080.
2. **Execution Time Limits (`--max-time-minutes`):**
   - Never launch unbounded training loops on the shared Spark. Always specify defensive cutoffs (e.g., `--max-time-minutes 15.0`).
3. **Privileged Operation Guardrails:**
   - NEVER issue `sudo reboot` or `sudo shutdown` without explicit, unprompted human confirmation. Always inspect active users (`uptime`, `who`) first.
4. **Pre-Caching Requirement:**
   - Base foundation models must be pre-cached on the host NVMe (`~/.cache/huggingface/hub/`) to avoid burning GPU session time on 2 MB/s network downloads.

---

## 4. Standard Commands & Recipes

### 4.1 Synthetic Dataset Generation
```bash
python3 proyecto/dataset/generate_with_teacher.py \
  --url "http://192.168.6.35:8085/v1/chat/completions" \
  --max-time-minutes 15.0 \
  --output "proyecto/dataset/generated_examples.jsonl"
```

### 4.2 Dataset Validation
```bash
python3 proyecto/dataset/validate_dataset.py \
  proyecto/dataset/generated_examples.jsonl
```

### 4.3 LoRA Fine-Tuning Burst (on Spark)
```bash
/home/ucab-spark1/lora_venv/bin/python3 proyecto/training/train_lora.py \
  --model-id "Qwen/Qwen2.5-Coder-1.5B-Instruct" \
  --dataset "proyecto/dataset/train.jsonl" \
  --output-dir "proyecto/training/output" \
  --epochs 3 \
  --batch-size 2 \
  --grad-accum 4 \
  --lr 2e-4 \
  --max-time-minutes 15.0 \
  --merge
```

### 4.4 Automated One-Click GGUF Quantization (Phase 3)
```bash
cd proyecto/training
./convert_to_gguf.sh --all --clean-f16
```

### 4.5 Local CLI Development & Testing
```bash
cd proyecto/cli
pnpm install
pnpm test
pnpm run dev refactor src/domain/entities/SourceFile.ts --mock
```
