# Case Study: Edge Clean Copilot Through the Playbook

> **Applied example.** Runs this repo's semester project (`proyecto/`) through each playbook question, using only documented evidence. Sources: `proyecto/docs/project/project-analysis.md`, `proyecto/docs/project/retrospective.md`, and the history logs. Findings reflect the analysis at the time it was written; some issues may have been fixed since (check `python3 proyecto/status.py`).

---

## 1. The Product

| Item | Value |
|------|-------|
| Job | Refactor TypeScript toward Clean Architecture/DDD, offline |
| Model | LoRA fine-tune of `Qwen2.5-Coder-1.5B-Instruct`, merged, GGUF Q4_K_M (941 MB) |
| Serving | `llama.cpp` (`llama-server`), local |
| App | Hexagonal TypeScript CLI (`clean-copilot`) |
| Training compute | DGX Spark, "Cold Staging, Hot Burst" |

## 2. Playbook Questions, Answered With Evidence

| Playbook step | What the project did | Assessment |
|---------------|----------------------|------------|
| [Decision](./product-decision-framework.md): is AI justified? | Fuzzy task (many valid refactors), offline requirement | Justified; a validator (AST score) exists |
| [Architecture](./needs-to-architecture.md) | Copilot pattern with an AST-based validator | Fits; output still needs code-block extraction and compile checks |
| [Privacy](./privacy-and-compliance.md) | Fully local inference | Strong: code never leaves the machine |
| [Model tier](./model-tier-decisions.md) | Small specialized model, self-hosted | Chosen for privacy and edge; no comparison against a cloud tier was run |
| [Evaluation](./evaluation-and-quality.md) | 30-case suite, CAS metric, bootstrap CI | Fine-tune beats its base by +16.8 CAS (74.8 vs 58.0), 95% CI [10.0, 25.2], 24 wins, 6 ties, 0 losses |
| [Cost](./cost-and-savings.md) | No per-token fee; laptop CPU | Measured ≈12 tok/s, about 47 s per answer on an i5-10310U |
| [Serving](../model-serving-for-apps.md) | `llama-server` locally; separate ports on the shared Spark | Port isolation avoided disturbing other tenants |
| [Production](./production-readiness.md) | Scripts, status dashboard | Gaps listed below |

## 3. What the Evidence Does Not Support

| Claim | Why not supported |
|-------|-------------------|
| Rivals commercial or frontier models | No such model was run on the suite |
| Produces correct code | The metric checks patterns, not compilation or behavior |
| Fast on a laptop | ≈12 tok/s; long answers take close to a minute |
| Generalizes to real code | Suite inputs are 3–18 lines, synthetic |

## 4. Gaps Found (at analysis time) and the Playbook Fix

| Gap | Playbook fix |
|-----|--------------|
| Training data: 18 distinct prompts (138 rows), 35% truncated answers, 15% with explicit `any` | Better data before more compute ([Model Selection](../model-selection.md), section 4) |
| CLI timeout of 60 s vs. ≈12 tok/s output | Size timeouts from measured speed ([Production Readiness](./production-readiness.md)) |
| `-o` wrote raw model reply (fences and prose) into `.ts` files | Validate and extract output before use ([Hardening Checklist](./hardening-checklist.md)) |
| Default URL pointed at another tenant's port on the Spark | Pin ports and isolate instances ([Model Serving](../model-serving-for-apps.md)) |
| No CI running the tests | Regression gate ([Evaluation and Quality](./evaluation-and-quality.md)) |
| VS Code Copilot routing (`copilot-local`) unevaluated | Do not route traffic to an unevaluated path ([Cost-Aware Routing](../cost-aware-routing.md)) |

## 5. Lessons for Other Products

1. **The process is the reusable asset.** Data → train → quantize → serve → evaluate worked end to end on limited, shared hardware.
2. **A specialized small model is justified by a measured gain on your task**, not by its size.
3. **Run the comparison group.** Without a frontier or prompted-base baseline, you cannot claim parity.
4. **Validators are the product.** A metric that checks patterns is not a compile or test check.
5. **Publish only measured numbers.** This project removed unmeasured claims (TTFT) on purpose.

## 6. Next Experiment That Would Most Change the Decision

Run the same 30-case suite against (a) the base model with a strong prompt and (b) a hosted small model (Haiku class), then compare quality, cost per task, and latency. That single table answers "local fine-tune or API?" for this product.
