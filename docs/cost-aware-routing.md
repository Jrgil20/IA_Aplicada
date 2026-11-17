# Cost-Aware Routing: Data-Driven Decisions Before Escalating to a Large AI

> **AI-first design note.** Status: **idea / not implemented**. Describes a cascade that answers cheap queries with deterministic logic or a small local model and escalates to a frontier LLM only when needed. Complements [Local SLMs vs. Cloud LLMs](./local-slm-vs-cloud-llm.md), which tiers by **data sensitivity and task type**, not per query.

---

## 1. Repository Audit (verified 2026-11-17)

| Question | Finding |
|----------|---------|
| Per-query router or escalation cascade in code? | **No.** |
| Documented? | **Partially.** `local-slm-vs-cloud-llm.md` §3.5 and §5 define static tiers (sensitive vs. public data). No confidence-based or cost-based escalation. |
| Closest existing code | `proyecto/bin/copilot-local`: manual all-or-nothing switch between GitHub Copilot cloud and the local model. Does not decide per request. Unevaluated (`project-analysis.md`, C5). |
| `ideas.md` / `next-steps.md` mention cost routing? | **No.** |
| Grep noise (not routing) | DGX network gateway, regex fallback in AST scoring, CVSS "escalates" in lab 2. |

## 2. Reusable Building Blocks

| Block | Where | Use in a router |
|-------|-------|-----------------|
| Cheap local model | Qwen2.5-Coder-1.5B Q4_K_M via `llama.cpp` (≈12 tok/s, CPU-only i5-10310U, measured) | Tier 1 answerer |
| Quality benchmark | `proyecto/evaluation/` (30 cases, CAS score, 95% bootstrap CI) | Measure quality loss caused by routing |
| Inference port | `proyecto/cli/src/application/ports` (hexagonal) | Router as an adapter; domain untouched |
| Static tiering policy | `local-slm-vs-cloud-llm.md` §5 | Hard constraints (never send sensitive data to cloud) |

## 3. Proposed Pattern: Cascade

```
query → [0] policy gate → [1] cache / rules → [2] local SLM → [3] confidence check → [4] frontier LLM
```

| Tier | Decision input (data-driven) | Escalate when |
|------|------------------------------|---------------|
| 0 Policy gate | Data classification (sensitive?) | Never escalate to cloud if sensitive |
| 1 Cache / rules | Exact or semantic match, regex/intent rules | No hit |
| 2 Local SLM | Query features: length, task type, language | Task outside the SLM's trained scope |
| 3 Confidence check | Token logprobs, self-consistency, output validators (e.g. AST parses) | Confidence below threshold or validation fails |
| 4 Frontier LLM | — | Final tier |

## 4. Decision Models (options)

| Model | Cost | Needs training data | Notes |
|-------|------|---------------------|-------|
| Rules / keyword intents | Lowest | No | Start here; transparent |
| Query-feature classifier (logistic regression, small tree) | Low | Yes (labelled easy/hard) | Predicts "SLM is enough" before calling it |
| Confidence thresholds on SLM output | Low | Small calibration set | Needs calibration; SLM logprobs can be overconfident |
| Learned router (embedding + classifier) | Medium | Yes | Only if volume justifies it |

## 5. Validation Plan (required before any claim)

1. Label benchmark queries with which tier answers them acceptably.
2. Run the cascade on the benchmark; compare CAS and escalation rate vs. always-frontier and always-local.
3. Report savings only from measured token counts and prices. **Do not publish estimated savings or latency figures** (project rule: no unmeasured metrics).

## 6. Open Questions

| # | Question |
|---|----------|
| 1 | Is this for the `clean-copilot` CLI or a general guideline only? |
| 2 | What is the ground truth for "easy question" in this project? |
| 3 | Which frontier model and pricing source for the cost baseline? |
