# Model Tier Decisions: Stay, Go Up, Go Cheaper, or Go Private

> **Decision guide.** Typical situation: the feature runs on a small cloud model (Haiku class). Do you escalate to a bigger one, move to cheaper open models (Gemma class), or move to private infrastructure? Model names and prices change; decide by evidence on your own test set. See [Model Selection](../model-selection.md) for criteria.

---

## 1. Order of Questions

1. **Privacy first.** If the data cannot leave your boundary, the cloud tiers are out regardless of cost.
2. **Then quality.** Is the current tier failing on your test set?
3. **Then cost.** Is quality fine but the bill too high?
4. **Then latency.** Is it too slow for the user?

## 2. Situation → Move

| Situation | Move | Notes |
|-----------|------|-------|
| Haiku-class output is wrong because of prompt or format | Fix prompt, add examples, add validator | Cheapest fix; try before any model change |
| Wrong because the task needs deeper reasoning | Escalate that task class up (Sonnet class, then Opus class) | Escalate only the hard cases ([Cost-Aware Routing](../cost-aware-routing.md)) |
| Wrong because facts are missing or private | Add retrieval (RAG) | A bigger model does not know your data |
| Quality fine, bill too high | Caching, shorter prompts, batching, then a cheaper model | See [Cost and Savings](./cost-and-savings.md) |
| Cheaper open model (Gemma class) looks attractive | Test it on your set; adopt only if the metric holds | Quality on your task decides, not general rankings |
| Data is sensitive or regulated | Self-host an open model, or a provider with contractual guarantees | See section 3 |
| Latency too high | Smaller model, streaming, caching, closer region | Measure time-to-first-token first |
| Need offline or edge operation | Local small model | See [Model Serving](../model-serving-for-apps.md) |

## 3. "Cheaper" Is Not "Private"

| Option | Cheaper? | Private? |
|--------|----------|----------|
| Open model (e.g. Gemma) on a hosted third-party API | Often | **No**: your data still goes to that host |
| Open model self-hosted on your hardware | After fixed hardware cost | **Yes**, if you control the host and logs |
| Closed model on its provider's API | Per token | Depends on the provider's contract and retention terms; verify them |
| Closed model via an enterprise or cloud-marketplace agreement | Per token | Contractual guarantees may apply; verify in writing |

Privacy comes from where the data is processed and who can keep it, not from the model's license or size.

## 4. Going Cheaper: Test Before Switching

1. Run the cheaper candidate on the same test set as the current model.
2. Compare the product metric, not just general quality.
3. Include failure cases and your languages (small models often weaken outside English).
4. Switch only if quality holds, and keep the old model for rollback.
5. Count the full cost: hosting, operations, and engineering time, not only token price.

## 5. Going Up: Escalate Selectively

| Do | Do not |
|----|--------|
| Send only failed or low-confidence cases to the bigger model | Move all traffic up because some cases fail |
| Define the trigger (validator fails, confidence low, task out of scope) | Escalate "when it feels wrong" |
| Log escalation rate and quality per tier | Assume the bigger model fixes it without testing |

## 6. Levers Inside One Model

Before changing models, check the settings of the model you already use (Claude API, verified 2026-11-17):

| Lever | Effect | Note |
|-------|--------|------|
| Effort (`output_config.effort`: `low` … `max`) | Trades thoroughness for tokens on the same model | Defaults differ by model (`medium` on Opus 5.5 and Haiku 5.5, `high` on Sonnet 5.5); tune per route |
| Prompt caching | Cheaper repeated prefixes | Caches are per model; switching models loses them |
| Batch API | 50% off for non-urgent work | Asynchronous, up to 24 hours |
| Structured outputs | Fewer invalid answers and retries | Validates format, not correctness |

Reference prices per million input/output tokens: Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20 (cached 2026-11-03; see [Cost and Savings](./cost-and-savings.md)). The jump from Haiku to Sonnet is about 20×, so escalate only the cases that need it.

## 7. Quick Matrix

| Priority | Lean toward |
|----------|-------------|
| Privacy above all | Self-hosted open model |
| Best quality on hard tasks | Larger cloud tier, selectively |
| Lowest cost on easy, high-volume tasks | Rules, cache, small or open model |
| Fast to market, unknown load | Hosted API, small tier first |
| Offline or edge | Local small model |
