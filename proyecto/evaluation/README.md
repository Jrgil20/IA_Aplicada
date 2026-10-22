# Edge Clean Copilot — Automated Architectural Benchmark Harness

> **Module:** Architectural Compliance & Evaluation Harness  
> **Target Models:** Base SLM (`Qwen-2.5-Coder-1.5B/3B`), LoRA Specialized Model, and Commercial Frontier Baselines  
> **Execution Engine:** Pure Python 3 (Zero external dependencies)  

This directory contains the automated benchmark harness ([`eval_benchmark.py`](./eval_benchmark.py)) designed to empirically measure, score, and prove the core hypothesis of the **Edge Clean Copilot** project.

---

## 1. Core Hypothesis Verification Formula

$$\text{Clean Architecture Score (CAS)} = S_{\text{boundary}} + S_{\text{invariant}} + S_{\text{ports}} + S_{\text{typing}}$$

Where:
- **$S_{\text{boundary}} \in [0, 30]$ (Domain Boundary Isolation):**
  - **30 pts:** Zero prohibited database, ORM, or web framework imports (`express`, `fastapi`, `typeorm`, `prisma`, `axios`, `mongoose`, `pg`, `redis`).
  - **15 pts:** Exactly 1 prohibited import.
  - **0 pts:** 2 or more prohibited imports.
- **$S_{\text{invariant}} \in [0, 25]$ (Invariant & Result Pattern Safety):**
  - **15 pts:** Functional `Result<T, E>` return type and `Result.ok` / `Result.fail` handling.
  - **10 pts:** Explicit constructor invariant validation guards (`throw new ValidationError` or length/type checks).
- **$S_{\text{ports}} \in [0, 25]$ (Port & Adapter Decoupling):**
  - **15 pts:** Explicit abstraction interface definition (`interface I...Repository`, `interface I...Port`, `interface I...Gateway`).
  - **10 pts:** Dependency injection via constructor (`constructor(private readonly repo: I...Repository)`) or adapter implementation (`implements I...Port`).
- **$S_{\text{typing}} \in [0, 20]$ (TypeScript Type Rigor):**
  - Base score: **20 pts**.
  - **Penalty:** $-5\text{ pts}$ per explicit `any` usage (`: any`, `<any>`, `as any`).
  - Comments and string literals are automatically stripped prior to inspection to avoid false positives (e.g. `company`, `many`).
  - Floor: **0 pts**.

---

## 2. Qualitative Grade Thresholds

| Total Score Range | Architectural Classification | Description |
| :--- | :--- | :--- |
| **85 – 100 pts** | **Grade A (Clean Architecture Certified)** | Strictly complies with Dependency Rule, invariant safety, and typed ports. |
| **70 – 84 pts** | **Grade B (Partially Clean)** | Minor omission (e.g., missing port interface or singular `any` type). |
| **50 – 69 pts** | **Grade C (Architectural Violations)** | Conflates infrastructure logic with domain rules; throws unhandled exceptions. |
| **0 – 49 pts** | **Grade F (Coupled Anti-Pattern)** | Imports ORMs or web frameworks directly into business entities. |

---

## 3. Usage & Recipes

### 3.1 Offline Evaluation (Batch JSONL)
Evaluate generated datasets or model completion files without needing an active inference server:

```bash
python3 eval_benchmark.py --offline test_benchmark_cases.jsonl --output benchmark_report.json
```

### 3.2 Live Evaluation (Real-Time Endpoint)
Evaluate live inference responses against a local or remote `llama-server` (e.g., port 8085 on DGX Spark):

```bash
python3 eval_benchmark.py \
  --url "http://192.168.6.35:8085/v1/chat/completions" \
  --prompts "prompts_suite.jsonl" \
  --output "live_report.json"
```
