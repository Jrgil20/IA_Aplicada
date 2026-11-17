# Cost and Savings

> **How to model and reduce AI cost.** The worked example uses list prices to show the arithmetic; it is **not** a measured saving. Real savings must come from your own usage data.
>
> **Verification status (2026-11-17):** Claude prices, caching multipliers, and batch discount come from the Claude API reference bundled with Claude Code (pricing cached 2026-11-03) and were confirmed against the official pricing page `platform.claude.com/docs/en/about-claude/pricing` on 2026-11-17. Re-check before budgeting. Not covered here: US-only inference (`inference_geo`) adds a 1.1× multiplier on Claude 4.6 and later models.

---

## 1. Cost Model

```
cost per request = input_tokens × input_price + output_tokens × output_price
monthly cost     ≈ Σ requests × cost per request + retries + fixed costs
```

| Term | Notes |
|------|-------|
| Input tokens | System prompt + tools + context + user text; usually the largest and most reducible part |
| Output tokens | Priced several times higher than input on Claude models (5× on the current tiers); cap them |
| Thinking tokens | Billed as output on models that reason before answering; tune the effort setting |
| Fixed costs | Self-hosted hardware, operations, monitoring, engineering time |
| Hidden multipliers | Retries, agent loops, long conversations resent every turn |

**Measure, do not estimate:** read token counts from the API usage fields (or the provider's usage/cost reports). Judge **cost per completed task**, not per request: a cheaper request that needs extra retries or turns is not cheaper.

## 2. Reference Prices (Claude API, per million tokens)

| Model | Input | Output | Cache read |
|-------|-------|--------|------------|
| Claude Haiku 5.5 | $0.10 | $0.50 | $0.01 |
| Claude Sonnet 5.5 | $2.00 | $10.00 | $0.10 |
| Claude Opus 5.5 | $4.00 | $20.00 | $0.20 |

Haiku 5.5 prices apply to prompts up to 100K tokens ($0.50 / $2.50 beyond). Cache writes cost 1.25× (5-minute TTL) or 2× (1-hour TTL) the input price. The Batch API takes 50% off every token, cache tokens included. Prices on Amazon Bedrock and Vertex AI are set by those platforms.

## 3. Worked Example (arithmetic only)

Assumptions: 100,000 requests per month; 3,000 input tokens each (2,500 stable system prefix + 500 variable); 300 output tokens each.

| Scenario | Input cost | Output cost | Monthly total |
|----------|-----------:|------------:|--------------:|
| All Opus 5.5, no cache | $1,200 | $600 | $1,800 |
| All Sonnet 5.5, no cache | $600 | $300 | $900 |
| Sonnet 5.5 with prefix cache (prefix read at $0.10/MTok, writes ignored) | $125 | $300 | ~$425 |
| Same, run through the Batch API (non-urgent work only) | | | ~$213 |
| All Haiku 5.5, no cache | $30 | $15 | $45 |
| Cascade: every request tries Haiku, 20% escalate to Sonnet | | | $45 + $180 = $225 |

How to read this:

- Caching the stable prefix halves the Sonnet bill in this shape because input dominates. It only works if the prefix is byte-identical and requests arrive within the TTL.
- The cascade looks cheap **only if** Haiku's 80% is actually good enough. That is a quality claim you must prove on your test set ([Evaluation and Quality](./evaluation-and-quality.md)).
- Output tokens become the dominant cost once input is cached; capping output length is the next lever.

## 4. Savings Levers (free wins first)

| Order | Lever | What it does | Tradeoff |
|-------|-------|--------------|----------|
| 1 | Remove AI where code works | Zero inference cost | Needs a deterministic rule |
| 2 | Prompt-prefix caching | Repeated prefixes at a fraction of the price ([Prompt Caching](../prompt-caching.md)) | Requires stable prefixes and steady traffic |
| 3 | Input hygiene | Shorter prompts, only needed context, no duplicated instructions | Test quality after trimming |
| 4 | Output hygiene | Length limits, structured output, no restating the question | Truncation risk |
| 5 | Loop hygiene | Cap agent steps and retries; stop loops early | May end tasks that would have succeeded |
| 6 | Batch non-urgent work | 50% off; results within 24 hours | Not for users who are waiting |
| 7 | Lower the effort setting | Fewer thinking tokens on the same model | Quality on hard tasks; measure per route |
| 8 | Response / semantic cache | Skips the model for repeats | Stale or wrong hits |
| 9 | Route by difficulty | Cheap tier first, escalate on failure ([Cost-Aware Routing](../cost-aware-routing.md)) | Router errors; loses cache reuse across models |
| 10 | Cheaper or open model | Lower per-token or fixed cost | Must pass your evaluation |
| 11 | Self-host | No per-token fee | Hardware and operations cost |

**Before building a multi-model cascade**, measure the simpler alternative: one capable model at a lower effort setting. Newer models at low effort often match older models at high effort, and one model keeps one cache.

## 5. Cloud vs. Self-Host Break-Even

```
break-even volume = fixed monthly cost of self-hosting ÷ API cost per request saved
```

| Variable | Question |
|----------|----------|
| Volume | Tokens per month, sustained or spiky? |
| Hardware | Purchase or rental cost, amortization period, power |
| Operations | Who runs, patches, and monitors it? Count those hours |
| Utilization | Will the hardware be busy, or idle most of the time? |
| Quality | Does the open model meet your metric? If not, the comparison is void |

Self-hosting wins on cost only with steady, high utilization **and** an open model that passes your evaluation. At low or spiky volume, per-token pricing is usually cheaper (in the example above, Haiku costs $45/month, less than most hardware amortization). Privacy can still justify self-hosting at a higher cost ([Privacy and Compliance](./privacy-and-compliance.md)).

## 6. Guardrails Against Runaway Cost

| Guardrail | Purpose |
|-----------|---------|
| Per-user and global rate limits | Stop abuse and loops |
| Max tokens and max steps per request | Bound agents and long outputs |
| Budget alerts and spend limits | Catch spikes early |
| Spend logged per feature, route, and tier | Know where money goes |
| Cache hit rate monitored | Catch silent cache regressions |
| Kill switch to a cheaper path | Degrade gracefully when over budget |

## 7. Never Save Money By

- Skipping evaluation after switching to a cheaper path.
- Routing sensitive data to a cheaper host.
- Trimming safety checks or validators.
- Lowering `max_tokens` so far that answers get cut off and retried.
