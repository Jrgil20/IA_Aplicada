# Applied AI: Which Tool for Which Job

> **AI-first decision guide.** Maps common applied-AI tasks to the cheapest tier that can do them acceptably. Part of the cost-routing set: [Cost-Aware Routing](./cost-aware-routing.md), [Scaling](./scaling-ai-workloads.md), [Prompt Caching](./prompt-caching.md). Status: guidance, not measured results.

---

## 1. Tiers

| Tier | What it is | Typical cost profile |
|------|------------|----------------------|
| T0 Deterministic | Rules, regex, lookup tables, parsers, linters | No inference cost |
| T1 Cache | Exact/semantic response cache, prompt-prefix cache | Pay once, reuse |
| T2 Local SLM | 1.5B–30B quantized model on own hardware (e.g. Qwen2.5-Coder-1.5B Q4_K_M) | Fixed hardware cost, no per-token fee |
| T3 Cloud small/fast model | Haiku/Flash-class API | Low per-token fee |
| T4 Cloud frontier model | Largest reasoning models | Highest per-token fee |

## 2. When to Use Each Tier

| Task | Start at | Escalate when | Why |
|------|----------|---------------|-----|
| Format/validate JSON, dates, IDs | T0 | Never | A parser is exact and free |
| FAQ, repeated questions | T1 | Cache miss and no rule applies | Same answer reused |
| Intent classification, routing labels | T0 → T2 | Rules ambiguous | Short outputs suit small models |
| Short code completion, boilerplate | T2 | Output fails validation (parse, lint, tests) | Latency and privacy favor local |
| Task-specific refactor (fine-tuned scope) | T2 | Outside trained scope | LoRA specialization is the local model's strength |
| Summarize or extract from a known document | T3 | Long, ambiguous, or high-stakes | Moderate reasoning, large context |
| Multi-step planning, architecture review | T4 | — | Needs strong reasoning |
| Sensitive or air-gapped data | T2 only | Never to cloud | Policy gate (see `local-slm-vs-cloud-llm.md` §3.5) |

## 3. Selection Heuristics

1. **Can code do it exactly?** Use T0.
2. **Has it been answered before?** Use T1.
3. **Is the output verifiable automatically?** Start cheap; the validator decides escalation.
4. **Is a wrong answer costly or hard to detect?** Start higher; do not save tokens on high-stakes output.
5. **Is the data sensitive?** Stay local regardless of cost.

## 4. Anti-patterns

| Anti-pattern | Problem |
|--------------|---------|
| Frontier model for everything | Pays frontier price for T0/T1 work |
| Local model for everything | Quality loss on reasoning-heavy tasks (this repo's 1.5B model is specialized, not general) |
| Escalating on vibes | No data; use validators and measured confidence |
| Routing without a benchmark | Cannot tell whether savings cost quality |
