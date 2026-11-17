# Prompt Caching: Types, Fit, Numbers, and Pitfalls

> **AI-first reference.** "Caching" covers three distinct mechanisms with different savings and risks. Part of the cost-routing set: [Cost-Aware Routing](./cost-aware-routing.md), [Use Cases](./applied-ai-use-cases.md), [Scaling](./scaling-ai-workloads.md), [Playbook: Cost and Savings](./playbook/cost-and-savings.md).
>
> **Verification status (2026-11-17):** Anthropic figures come from the Claude API reference bundled with Claude Code (pricing cached 2026-11-03); prices and multipliers confirmed against the official pricing page on 2026-11-17. `llama.cpp` flags were read from `llama-server --help` on the local build `0.8.0-dev (build 11982)`. vLLM behavior comes from the official vLLM docs. Prices and defaults change: re-check before relying on them.

---

## 1. Three Mechanisms

| Mechanism | What is reused | Where | Model still called? |
|-----------|----------------|-------|---------------------|
| Response cache (exact) | Full answer for an identical request | Your app | No |
| Semantic cache | Answer for a similar request (embedding match) | Your app | No |
| Prompt-prefix / KV cache | Computation over a stable prompt prefix | Provider API, `llama.cpp`, vLLM | Yes (only the new suffix is processed) |

## 2. When to Use Each

| Mechanism | Use when | Avoid when |
|-----------|----------|------------|
| Exact response cache | Same input repeats, answer is deterministic and not time-sensitive | Answers depend on changing data or user context |
| Semantic cache | Many paraphrased FAQs | Near-miss answers are harmful (code, numbers, legal/security text); a wrong hit returns a confident wrong answer |
| Prompt-prefix cache | Large static prefix (system prompt, tool definitions, documents) reused across calls | Prefix changes every call, the prompt is below the minimum size, or calls are further apart than the TTL |

## 3. Prefix Caching on the Claude API (verified)

### 3.1 Mechanics

| Fact | Detail |
|------|--------|
| Matching | Exact byte prefix. Any change invalidates everything after it |
| Render order | `tools` → `system` → `messages`; put stable content first |
| Markers | `cache_control: {"type": "ephemeral"}` on a block, or top-level automatic caching on the request |
| Breakpoints | Maximum 4 per request |
| TTL | 5 minutes by default; `"ttl": "1h"` for 1 hour. A cache read refreshes the timer at no cost |
| Minimum prefix | Model-dependent: 512 tokens on the newest models (Opus 5.5, Sonnet 5.5, Haiku 5.5); 1024–4096 on older ones (e.g. 4096 on Haiku 4.5). Shorter prefixes silently do not cache |
| Scope | Caches are per model: switching models (for example in a cascade) does not reuse the cache |

### 3.2 Economics

| Operation | Price relative to base input |
|-----------|------------------------------|
| Cache write, 5-minute TTL | 1.25× |
| Cache write, 1-hour TTL | 2× |
| Cache read | ~0.1× (0.05× on Opus 5.5 and Sonnet 5.5; 0.025× on Fable 5.1/5.2) |
| Batch API | 50% off every token, including cache reads and writes (discounts stack) |

**Break-even:** with a 5-minute TTL, two requests already pay off (1.25 + 0.1 = 1.35× vs. 2× uncached). With a 1-hour TTL you need at least three (2 + 0.2 = 2.2× vs. 3×).

**Choosing the TTL:**

| Gap between requests sharing the prefix | TTL |
|------------------------------------------|-----|
| Under 5 minutes (continuous traffic, agent loops) | 5-minute (every request refreshes it) |
| 5 to 60 minutes (user replies later, slow side tasks) | 1-hour |
| Over 60 minutes | Caching rarely pays; reconsider |

### 3.3 Verify Hits, Do Not Assume Them

| Usage field | Meaning |
|-------------|---------|
| `cache_creation_input_tokens` | Tokens written this request (you paid the write premium) |
| `cache_read_input_tokens` | Tokens served from cache (you paid the read rate) |
| `input_tokens` | Only the uncached remainder |

Total prompt size = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. If `cache_read_input_tokens` stays at zero across identical requests, a silent invalidator is at work.

### 3.4 Silent Invalidators

| Invalidator | Fix |
|-------------|-----|
| Timestamp or request ID in the system prompt | Move it after the last breakpoint |
| Unsorted JSON or tool list built in varying order | Serialize deterministically |
| Tool set changes between calls | Keep a fixed tool list |
| Changing model or thinking/effort settings mid-conversation | Keep them stable per conversation |

## 4. Local Serving

### 4.1 `llama.cpp` (`llama-server`, verified on local build 0.8.0-dev)

| Flag | Default | Effect |
|------|---------|--------|
| `--cache-prompt` | Enabled | Reuses the KV cache of a matching prompt prefix between requests |
| `--cache-reuse N` | 0 (off) | Minimum chunk size to reuse cached KV by shifting, when the prefix is not identical |
| `-sps, --slot-prompt-similarity` | 0.10 | How closely a prompt must match a slot's prompt to reuse that slot |
| `-cram, --cache-ram N` | 8192 MiB | Upper bound for the prompt cache held in RAM |
| `--slot-save-path` | Disabled | Persist slot KV caches to disk |

Useful on CPU-only hardware, where prompt processing dominates latency. Measure before documenting any gain.

### 4.2 vLLM

vLLM implements automatic prefix caching through its paged KV cache. Whether it is on by default depends on the version and model type (the engine logs whether it enabled it); check the startup log and the docs for your version.

## 5. Where It Fits in the Cascade

```
query → policy gate → [exact / semantic cache] → rules → local SLM (prefix cache) → cloud LLM (prefix cache)
```

Response caches sit at tier 1 and skip inference entirely. Prefix caches sit inside the model tiers and make each call cheaper. Note the tension: because provider caches are per model, a multi-model cascade gives up cache reuse across tiers.

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Stale answers | TTL and invalidation on source change |
| Semantic false positives | High similarity threshold, validate on a labelled set, exclude high-stakes tasks |
| Cross-user leakage | Scope cache keys by user/tenant; never share caches across privacy boundaries |
| Hidden quality loss | Evaluate cached vs. fresh answers on the benchmark |
| Silent cost regression | Monitor `cache_read_input_tokens` continuously, not only at setup |
