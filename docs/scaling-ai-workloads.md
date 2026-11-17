# Scaling AI Workloads: Laptop → DGX Spark → Cloud

> **AI-first decision guide.** Explains when to scale up compute or escalate to a bigger model, and when not to. Part of the cost-routing set: [Cost-Aware Routing](./cost-aware-routing.md), [Use Cases](./applied-ai-use-cases.md), [Prompt Caching](./prompt-caching.md).

---

## 1. Two Different Kinds of Scaling

| Kind | Question | Example |
|------|----------|---------|
| Model escalation | Does this query need a bigger model? | Local 1.5B → cloud frontier |
| Compute scaling | Does this job need more hardware? | Laptop CPU → DGX Spark for training |

Do not mix them: a training job scaling to the Spark says nothing about which model answers a query.

## 2. Compute Tiers in This Project

| Environment | Use for | Not for |
|-------------|---------|---------|
| Laptop (CPU, mocks) | Development, unit tests, inference with the quantized GGUF (≈12 tok/s measured, i5-10310U) | Training, large batch evaluation |
| DGX Spark (128 GB unified memory) | LoRA/QLoRA training, distillation, GGUF conversion, large-batch evals | Interactive edge latency targets |
| Cloud API | Frontier reasoning, burst capacity, no hardware to own | Sensitive data, offline operation |

This is the "Cold Staging, Hot Burst" model: develop offline, burst to the Spark when the job needs it.

## 3. When to Scale Up

| Signal | Action |
|--------|--------|
| Training or conversion does not fit laptop memory/time | Burst to DGX Spark |
| Escalation rate to cloud stays high on a task class | Fine-tune a local model for that class, or accept cloud cost |
| Latency target missed on local inference | Smaller/more quantized model, or GPU host |
| Quality below threshold on the benchmark | Larger model or better data, not just more compute |

## 4. When Not to Scale

| Situation | Better move |
|-----------|-------------|
| Repeated identical prompts | Add a cache ([Prompt Caching](./prompt-caching.md)) |
| Long shared prefix on every call | Prefix/KV caching |
| Simple deterministic task | Rules (T0) |
| Unmeasured "feels slow" | Measure first; do not add metrics to docs until measured |

## 5. Escalation Policy Checklist

1. Policy gate for sensitive data runs first.
2. Each escalation has a stated trigger (validator failure, low confidence, out-of-scope).
3. Escalation rate and quality per tier are logged and compared against the benchmark.
4. Cost claims come from measured token counts and current price lists.
