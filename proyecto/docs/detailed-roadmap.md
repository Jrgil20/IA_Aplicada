# Edge Clean Copilot: Detailed Execution Roadmap (Weeks 4–15)

> **Document Type:** Operational Master Plan & Engineering Specification  
> **Target Delivery:** Semester Final Evaluation — Applied AI (UCAB)  
> **Methodology:** "Cold Staging, Hot Burst"  
> **Hardware Budget:** 1.5 to 2.0 hours per weekly session on NVIDIA DGX Spark  

---

## 1. Roadmap Overview & Timeline Gantt (ASCII)

```text
WEEKS           04   05   06   07   08   09   10   11   12   13   14   15
─────────────────────────────────────────────────────────────────────────────
PHASE 2: LoRA   [========]
  - 1.5B Burst      XX
  - 3B Burst             XX
  - Eval / Loss               XX
─────────────────────────────────────────────────────────────────────────────
PHASE 3: GGUF             [=============]
  - Merge                               XX
  - Quantize                                 XX
  - Bench VRAM                                    XX
─────────────────────────────────────────────────────────────────────────────
PHASE 4: CLI                                  [=============================]
  - Unit Tests                                      XX
  - Eval Harness                                         XX
  - Packaging                                                 XX
  - Final Report                                                   XX
─────────────────────────────────────────────────────────────────────────────
```

---

## 2. Phase 2: LoRA Adaptation & Specialization (Weeks 4–7)

### 2.1 Technical Objective
Fine-tune base Small Language Models (`Qwen/Qwen2.5-Coder-1.5B-Instruct` and optionally `3B`) using Low-Rank Adaptation (LoRA) on the canonical Clean Architecture dataset, forcing the model to prioritize architectural boundaries over arbitrary snippet completion.

### 2.2 Hyperparameter & Training Configuration

```python
LORA_SPECIFICATION = {
    "base_model": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "r": 16,                        # Rank dimension: balance between expressiveness and memory
    "lora_alpha": 32,               # Scaling factor: 2 * r
    "lora_dropout": 0.05,
    "bias": "none",
    "precision": "bfloat16",        # Native hardware acceleration on Blackwell GB10
    "learning_rate": 2e-4,          # AdamW optimizer with cosine schedule
    "batch_size": 2,                # Per-device batch size
    "gradient_accumulation_steps": 4, # Effective batch size = 8
    "max_seq_len": 1024,
    "epochs": 3,
    "max_time_minutes": 15.0        # Mandatory time guardrail
}
```

### 2.3 Actionable Work Breakdown:
- **Week 4 (Session A): First Hot Burst & Adapter Generation**
  - [ ] Resume and complete cached weight download of `Qwen2.5-Coder-1.5B` (~800 MB remaining).
  - [ ] Execute 1-step dry run on DGX Spark to verify loss gradient computation.
  - [ ] Launch 15-minute training burst on `dataset/train.jsonl` (138 samples) (`train_lora.py --max-time-minutes 15 --merge`).
  - [ ] Save trained adapter weights (`lora_adapters/adapter_model.safetensors`).
- **Week 5 (Session B): Convergence & Hyperparameter Tuning**
  - [ ] Analyze training loss curve (target: smooth convergence from ~2.2 to <0.6).
  - [ ] If loss diverges or overfits, adjust `learning_rate` to `1e-4` and test `lora_alpha=16`.
  - [ ] Conduct preliminary qualitative evaluation on 5 unseen refactoring prompts.
- **Week 6 (Session C): Model Scale Exploration (3B Evaluation)**
  - [ ] If 1.5B exhibits syntactic limitations, stage `Qwen/Qwen2.5-Coder-3B-Instruct`.
  - [ ] Run comparative 15-minute training burst under identical dataset conditions.
- **Week 7 (Session D): Catastrophic Forgetting & Generalization Audit**
  - [ ] Test the fine-tuned model against general coding tasks (e.g., standard algorithmic problem).
  - [ ] Ensure the model has not lost basic programming syntax while acquiring Clean Architecture discipline.

---

## 3. Phase 3: Consolidation, Quantization & GGUF Export (Weeks 8–11)

### 3.1 Technical Objective
Transform the separate LoRA adapter and base model into a single unified 16-bit weight matrix, then apply post-training quantization (PTQ) to produce compact GGUF binaries executable on commodity laptop CPUs.

### 3.2 Quantization Targets & Memory Sizing Matrix

| Format | Quantization Method | File Size (1.5B) | Target RAM | Speed on Standard CPU | Quality Retention |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BF16 / FP16** | Unquantized Merged Base | ~3.1 GB | ~4.5 GB | 10–18 tokens/s | 100% (Baseline) |
| **Q8_0** | 8-bit Integer Symmetric | ~1.6 GB | ~2.5 GB | 25–40 tokens/s | >99.5% |
| **Q5_K_M** | 5-bit Medium K-Quants | ~1.1 GB | ~1.8 GB | 35–55 tokens/s | >98.0% |
| **Q4_K_M** | **4-bit Medium K-Quants (Target)**| **~0.9 GB** | **~1.5 GB** | **45–70 tokens/s** | **>96.5%** |

### 3.3 Actionable Work Breakdown:
- **Week 8: Consolidation via `merge_and_unload()`**
  - [ ] Execute `train_lora.py --merge` to output `./output/merged_model/`.
  - [ ] Validate that merged weights retain identical forward pass output to base+adapter.
- **Week 9: Automated GGUF Conversion Scripting**
  - [x] Create [`proyecto/training/convert_to_gguf.sh`](../training/convert_to_gguf.sh) utilizing `llama.cpp/convert_hf_to_gguf.py` and `llama-quantize`.
  - [ ] Produce `clean-copilot-1.5b-f16.gguf` upon LoRA merge on DGX Spark.
- **Week 10: Multi-Quantization Pipeline**
  - [ ] Quantize intermediate F16 GGUF into `q4_k_m`, `q5_k_m`, and `q8_0` binaries using `llama-quantize`.
  - [ ] Measure file sizes and output checksums.
- **Week 11: Edge Hardware Benchmarking**
  - [ ] Deploy quantized GGUFs onto the student laptop (CPU only, offline).
  - [ ] Measure tokens/s throughput and peak RAM consumption using `llama-bench`.

---

## 4. Phase 4: CLI Hardening, Benchmark Suite & Delivery (Weeks 12–15)

### 4.1 Technical Objective
Deliver a production-ready developer tool adhering strictly to Hexagonal Architecture, equipped with an automated evaluation benchmark that mathematically proves superiority in Clean Architecture compliance over unspecialized models.

### 4.2 Automated Benchmark Harness Specification
To prove the core hypothesis of the project, an automated evaluation harness ([`proyecto/evaluation/eval_benchmark.py`](../evaluation/eval_benchmark.py)) evaluates models against unseen legacy/coupled code files and pre-generated completion datasets:

```
Benchmark Metrics (Documented in proyecto/evaluation/README.md):
1. Domain Boundary Score (30%): 100% if domain layer imports 0 external frameworks/DBs.
2. Invariant Safety Score (25%): Strict validation in constructors and use of Result<T, E>.
3. Port/Adapter Decoupling (25%): Presence of abstract interface + concrete test double/injection.
4. Any-Type Penalty (20%): Strict avoidance of explicit TypeScript `any` (-5 pts per occurrence).
```

### 4.3 Actionable Work Breakdown:
- **Week 12: CLI Test Suite & In-Memory Verification**
  - [ ] Install `vitest` in `proyecto/cli/`.
  - [ ] Write unit tests for `SourceFile`, `RefactorCodeUseCase`, and `Result<T, E>`.
  - [ ] Implement integrated testing via `MockInferenceAdapter`.
- **Week 13: Local Inference Engine Adapter**
  - [ ] Implement `LlamaCppNativeAdapter` or finalize `LlamaServerAdapter` to connect directly to local edge `llama-server`.
  - [ ] Add CLI flags: `--temperature`, `--max-tokens`, `--output-diff`.
- **Week 14: Empirical Comparative Evaluation**
  - [ ] Run benchmark suite across:
    1. Base Model (`Qwen-2.5-Coder-1.5B-Instruct` un-fine-tuned).
    2. Edge Clean Copilot (`clean-copilot-q4_k_m.gguf`).
    3. Commercial Cloud Model baseline (reference score).
  - [ ] Tabulate comparative metrics and generate empirical performance graphs.
- **Week 15: Academic Delivery, Release & Publication**
  - [ ] Package CLI executable (`pnpm build`).
  - [ ] Publish model weights and GGUF quants to Hugging Face Model Hub.
  - [ ] Produce final technical report and academic slide deck for course presentation.
