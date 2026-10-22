# Edge Clean Copilot — Dataset Specification

## 1. Objective
Curate high-quality, canonical Clean Architecture and Spec-Driven Development synthetic pairs to fine-tune Small Language Models (SLMs: Qwen-2.5-Coder-1.5B/3B) using LoRA.

---

## 2. Target Format: OpenAI / ChatML Format
To ensure full compatibility with Hugging Face `trl` (`SFTTrainer`) and Qwen's native chat template, all samples must follow standard ChatML structure in JSONL format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are Edge Clean Copilot, an expert software architect specialized in Clean Architecture, Domain-Driven Design (DDD), and SOLID principles. You strictly enforce the Dependency Rule: domain and application layers must never depend on external libraries, frameworks, databases, or infrastructure."
    },
    {
      "role": "user",
      "content": "<Task instruction + context or dirty code snippet>"
    },
    {
      "role": "assistant",
      "content": "<Canonical Clean Architecture solution with clear layer separation>"
    }
  ]
}
```

---

## 3. Dataset Taxonomy (Target Distribution)

| Category ID | Category Name | Description | Target % |
| :--- | :--- | :--- | :--- |
| `ARCH_REFACTOR` | Coupled to Clean Refactor | Taking messy, framework-coupled code (e.g., Express + raw SQL) and decomposing it into Domain, Application, Port, and Adapter. | 40% |
| `USE_CASE_GEN` | Use Case & Domain Impl | Given a business spec, producing pure Domain Entities, Value Objects, and Application Use Cases with DTOs and `Result<T, E>`. | 30% |
| `AAA_TEST_GEN` | Isolated Unit Testing | Generating Arrange-Act-Assert unit tests for Use Cases using pure in-memory test doubles (fakes/mocks) without external DBs. | 20% |
| `SOLID_CRITIQUE` | Architecture Lint / Critique | Analyzing a code snippet, pointing out Clean Architecture violations (Dependency Inversion, layer leakage), and providing targeted fixes. | 10% |

---

## 4. Quality Rules for Every Sample
1. **Zero Domain Pollution:** Domain entities and use cases must not import ORMs (Prisma, Mongoose, TypeORM), HTTP frameworks (Express, Nest, FastAPI), or external SDKs.
2. **Explicit Contracts:** Every infrastructure dependency must be inverted through an interface (Port) defined in Application or Domain.
3. **Deterministic Error Handling:** Domain/Application layers must return explicit `Result` types or typed domain errors, avoiding untyped exception throwing.

---

## 5. Stratified Partitioning & Data Leakage Prevention

To uphold strict scientific and academic validity, the cumulative dataset of 168 unified samples (`seed_examples.jsonl` + `generated_examples.jsonl`) is partitioned into two mutually exclusive sets using [`split_dataset.py`](./split_dataset.py) with a fixed random seed (`seed=42`):

```text
======================================================================
168 Unified Canonical Samples (~191,364 Total Tokens)
  ├── train.jsonl         : 138 samples (82.1%) — ~156,395 tokens
  └── eval_holdout.jsonl  :  30 samples (17.9%) —  ~34,969 tokens
======================================================================
```

| Architectural Category | Total Samples | Training Set (`train.jsonl`) | Holdout Evaluation Set (`eval_holdout.jsonl`) |
| :--- | :--- | :--- | :--- |
| **Port & Adapter Decoupling** | 68 | 56 | 12 |
| **Entity & Value Objects** | 46 | 38 | 8 |
| **AAA Unit Testing** | 30 | 25 | 5 |
| **SOLID Lint & Critiques** | 13 | 11 | 2 |
| **Architecture Refactoring** | 11 | 9 | 2 |
| **TOTAL** | **168** | **138** | **30** |

> [!IMPORTANT]
> The evaluation holdout set (`eval_holdout.jsonl`) is strictly isolated and never shown to the model during LoRA fine-tuning. It serves exclusively for the post-training benchmark evaluation in [`proyecto/evaluation/`](../evaluation/).
