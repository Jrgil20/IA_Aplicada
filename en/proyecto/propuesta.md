# Edge Clean Copilot: Specialized SLM for Clean Architecture & Spec-Driven Development

**Author:** Jesús Rodolfo Gil Farías  
**Institution:** Universidad Católica Andrés Bello (UCAB) — Caracas, Venezuela  
**Degree Program:** School of Computer Engineering  
**Academic Articulation:** Applied Artificial Intelligence & Software Development  
**Training Hardware:** NVIDIA DGX Spark (GB10 Grace Blackwell, 128 GB Unified Memory)  
**Target Execution Environment:** Resource-constrained hardware (Standard laptops, CPU / iGPU, 100% Offline)  

---

## 1. Project Vision and Summary

Cloud-based massive model programming assistants (such as GitHub Copilot or ChatGPT) generate code that compiles, but they frequently violate the **Clean Architecture Dependency Rule**, conflate domain logic with infrastructure, and require sending proprietary code to external servers under paid subscriptions.

Unlike prompt wrappers such as *Gentle-AI* or *gentle-pi* (which operate as context harnesses over frontier APIs like Claude), this project addresses the problem at the level of **Artificial Intelligence Systems and Edge Inference**:
1. Train and adapt a compact **Small Language Model (SLM)** (1.5B to 3B) using **LoRA** to internalize formal Clean Architecture patterns and BDD tests (Arrange-Act-Assert) directly into its weights.
2. Deploy the quantized model in **GGUF (Q4_K_M)** format for high-speed autonomous execution (35–70 tokens/s) on common commercial laptops.
3. Build a decoupled CLI tool following the **Ports & Adapters** pattern to isolate system logic from the inference engine.

---

## 2. Technical Hypothesis and Methodology

### Core Hypothesis
A small language model (< 3B parameters), highly specialized via LoRA on canonical synthetic software architecture pairs and constrained by deterministic grammars (GBNF / type schemas), can outperform general commercial models in strict adherence to Clean Architecture within offline, local environments.

### Operational Strategy: "Cold Staging, Hot Burst"
* **Compute Budget:** 7 to 9 atomic sessions of ~2 hours per week on the NVIDIA DGX Spark station.
* **Pre-lab (At home):** Curation and tokenization of validated synthetic datasets in JSONL format; local 1-step dry run on CPU.
* **Lab (On DGX Spark):** LoRA training burst (20 to 40 minutes), adapter merging (`merge_and_unload`), and immediate GGUF quantization using `llama.cpp`.
* **Post-lab (On modest laptop):** Regression testing, VRAM/RAM usage measurement, and CLI application layer development.

---

## 3. System Architecture (Ports & Adapters)

```
                     ┌────────────────────────────────────────┐
                     │          Domain Layer / CLI            │
                     │  - AST Parsing & Code Slicing          │
                     │  - SOLID Rule Verification             │
                     │  - AAA Test Suite Generation           │
                     └───────────────────┬────────────────────┘
                                         │
                              [Port: InferenceEngine]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
     [Adapter: LlamaCppEngine]                         [Adapter: MockEngine]
                 │                                               │
     (Local 4-bit GGUF Model)                              (Unit Tests)
```

---

## 4. Semester Phase Schedule

* **Phase 1: Infrastructure and Teacher Model (Weeks 1–3):**
  * Validation of the local environment on the DGX Spark (CUDA, native `llama.cpp`, and `llama-server` server with Qwen3-Coder-30B).
  * Extraction and generation of the Clean Architecture synthetic dataset assisted by the 30B model as a teacher model.
* **Phase 2: LoRA Adaptation and Specialization (Weeks 4–7):**
  * Training LoRA adapters on base SLMs (Qwen-2.5/3-Coder 1.5B / 3B).
  * Evaluation of convergence, loss, and catastrophic forgetting rate.
* **Phase 3: Optimization, Merging, and Quantization (Weeks 8–11):**
  * Weight merging and multi-quantization export (`Q4_K_M`, `Q5_K_M`, `Q8_0`).
  * Benchmarking speed (tokens/second) and memory footprint on a standard laptop.
* **Phase 4: Client Development and Publication (Weeks 12–15):**
  * Building the CLI in TypeScript / Go / Python.
  * Publication of weights on Hugging Face, GitHub repository with automated CI/CD, and final technical documentation.

---

## 5. Democratic Replicability

The project design is intentionally independent of expensive hardware for its usage and reproduction:
* **Daily inference:** Requires only 8–16 GB of RAM on a commercial CPU via `llama.cpp` or `Ollama`.
* **Training replicability:** Compatible with free **Google Colab (16 GB T4 GPU)** environments or consumer GPUs with 6 GB VRAM via QLoRA.

---

## 6. References and Associated Documentation
* [Formal Technical Proposal Document (Google Docs)](https://docs.google.com/document/d/1fZsRbir6Os1fA-eled90wLnMfbrQe4B7YVNMrOHMmIU/edit)
