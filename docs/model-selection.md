# Choosing a Model for an Application

> **AI-first decision guide.** A repeatable process to pick, and later replace, a model. Model names and versions change quickly: the criteria matter more than the list. No benchmark scores are claimed; evaluate candidates on your own test set. Related: [Playbook: Model Tier Decisions](./playbook/model-tier-decisions.md), [Model Serving](./model-serving-for-apps.md), [Applied AI Use Cases](./applied-ai-use-cases.md), [Model Factory Architecture](../proyecto/docs/architecture/model-factory-architecture.md).

---

## 1. Process

1. **Define the task and a pass/fail metric** (for this project: the CAS score on the benchmark).
2. **Set hard constraints**: data sensitivity, hardware, latency, budget, license.
3. **Shortlist 2–4 candidates** that satisfy the constraints.
4. **Evaluate all candidates on the same test set**, including a no-fine-tune baseline.
5. **Pick the cheapest candidate that meets the metric**, then re-evaluate when new models appear.

## 2. Selection Criteria

| Criterion | Question | Why it matters |
|-----------|----------|----------------|
| Task fit | Code, chat, extraction, classification, multilingual? | Specialized models beat larger general ones on narrow tasks only if the task matches |
| Size class | Which tier from the [sizing matrix](./local-slm-vs-cloud-llm.md#42-recommended-hardware-sizing-matrix) fits the hardware? | Defines memory and speed |
| Instruct vs. base | Does it follow instructions out of the box? | Base models suit fine-tuning; instruct models suit direct use |
| Context length | Is the longest real input within the window? | Truncation silently degrades answers |
| Language | Does it handle the app's languages (e.g. Spanish)? | Small models often weaken outside English |
| License | Is commercial or redistributed use allowed? | Legal constraint |
| Quantization | What quality loss does Q4 vs. Q8 cause on your test set? | Memory vs. quality tradeoff |
| Tooling | Is there a GGUF/vLLM build and a stable tokenizer? | Determines how you serve it |
| Fine-tunability | Is LoRA/QLoRA supported with your stack? | Needed for task specialization |

## 3. Size Class → Role

| Class | Typical role | Caution |
|-------|--------------|---------|
| 1.5B–3B | Narrow, fine-tuned tasks; autocomplete; classification | Weak at open-ended reasoning |
| 7B–8B | General assistants, summarization, simple tool use | Needs a mid-range GPU or patience on CPU |
| 14B–32B | Harder local reasoning, batch generation | Needs 16–24 GB+ of fast memory |
| Cloud small (Haiku/Flash class) | Cheap general tasks at scale | Data leaves your boundary |
| Cloud frontier | Planning, hard reasoning, long synthesis | Highest per-token cost |

## 4. Fine-Tune, Prompt, or Go Bigger?

| Situation | Try first |
|-----------|-----------|
| Format or style is wrong | Better prompt and examples |
| Task is narrow and repeated, data available | LoRA/QLoRA fine-tune of a small model |
| Needs broad reasoning | Larger model, not more fine-tuning |
| Facts must be current or private | Retrieval (RAG), not weights |
| Cost per call is the issue | [Cost-aware routing](./cost-aware-routing.md) and [caching](./prompt-caching.md) |

## 5. Lessons from This Project

| Finding | Source |
|---------|--------|
| The fine-tuned 1.5B beat its own base model on the project suite (+16.8 CAS points, 95% bootstrap CI reported) | `proyecto/docs/project/project-analysis.md` |
| The proposal's comparison against general commercial models was never run | `proyecto/docs/project/retrospective.md` |
| Candidate bases are tracked in the model factory (Qwen2.5-Coder, Llama-3.2, Gemma-2, SmolLM2, DeepSeek) | `proyecto/docs/architecture/model-factory-architecture.md` |

Implication: a specialized small model is justified by a measured gain over its base on your task, not by size alone. Run the missing comparison before claiming parity with frontier models.

## 6. Replacement Checklist

1. New candidate trained or pulled with the same recipe.
2. Same benchmark, same scoring, report with confidence intervals.
3. Compare against the current model; replace only on a measured win.
4. Keep the old artifact for rollback.
