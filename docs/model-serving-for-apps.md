# Serving Models for Real Applications

> **AI-first operational guide.** How to run a model behind a real app: runtime choice, capacity planning, topology, scaling, and a production checklist. Builds on lessons recorded in this repo. No benchmark numbers are claimed; measure on your hardware. Related: [Playbook: Production Readiness](./playbook/production-readiness.md), [Model Selection](./model-selection.md), [Scaling AI Workloads](./scaling-ai-workloads.md), [Prompt Caching](./prompt-caching.md), [Local SLMs vs. Cloud LLMs](./local-slm-vs-cloud-llm.md).
>
> **Verification status (2026-11-17):** `llama-server` flags and defaults read from `llama-server --help` on the local build `0.8.0-dev (build 11982)`. vLLM facts from the official vLLM docs (stable). Defaults change between builds: always check `--help` on the build you deploy.

---

## 1. Runtime Choice

| Runtime | Strengths | Limits | Pick when |
|---------|-----------|--------|-----------|
| `llama.cpp` `llama-server` | GGUF quantization, CPU/GPU/Apple Silicon, small footprint, parallel slots with continuous batching, OpenAI-style HTTP API, built-in API keys and Prometheus metrics | Throughput under heavy concurrency is below GPU-first servers | Edge, laptop, single GPU, few concurrent users (used in this repo) |
| vLLM | GPU-first, paged KV cache (PagedAttention), continuous batching, prefix caching, OpenAI-compatible server; also loads GGUF | Needs a supported GPU; heavier install; GGUF loading recommends the base model's tokenizer | Many concurrent users on a GPU server |
| Ollama | Easy install and model management (built on `llama.cpp`) | Less control over serving flags | Developer machines, prototypes |
| Hosted API | No hardware, frontier models, elastic capacity, provider-side caching and batching | Per-token cost, data leaves your boundary, rate limits | Frontier reasoning, bursty or unknown load |

## 2. `llama-server` Flags That Matter in Production

| Flag | Default (build 0.8.0-dev) | Why it matters |
|------|---------------------------|----------------|
| `--host` | `127.0.0.1` | Safe default; do not change to `0.0.0.0` without auth and a gateway |
| `--port` | `9931` on this build (older builds and repo scripts use `8080`/`8085`) | Pin it explicitly in scripts |
| `-c, --ctx-size` | `0` = taken from the model | Total KV budget |
| `-np, --parallel` | `-1` = auto | Number of concurrent slots |
| `-kvu, --kv-unified` | On when slots are auto | One KV buffer shared across sequences |
| `--kv-unified-per-slot N` | Unset | Caps context per slot |
| `-cb, --cont-batching` | Enabled | Continuous (dynamic) batching |
| `--cache-prompt` | Enabled | Prefix KV reuse between requests |
| `--api-key` / `--api-key-file` | None | Require a key on requests |
| `--metrics` | Disabled | Prometheus-compatible metrics endpoint |
| `-ngl` | Build-dependent | Layers offloaded to GPU (`-ngl 0` = CPU only, as used for the measured ≈12 tok/s) |

## 3. Capacity Planning

| Component | How to size |
|-----------|-------------|
| Weights memory | Use the actual quantized file size (e.g. the `.gguf`), not nominal bits × parameters |
| KV cache | `2 × layers × kv_heads × head_dim × bytes_per_value × context_tokens × concurrent_sequences` (values from the model config) |
| Overhead | Leave headroom for activations, runtime buffers, the prompt cache (`--cache-ram`), and the OS |
| Context per user | With a split (non-unified) KV, total context ÷ slots |

### Worked KV example (method only)

For a model with 28 layers, 4 KV heads, head dimension 128, FP16 cache (2 bytes):

```
per token = 2 × 28 × 4 × 128 × 2 bytes = 57,344 bytes ≈ 56 KiB
4,096 tokens × 1 sequence ≈ 224 MiB
```

Read the real values from the model's `config.json` or the GGUF metadata before sizing; the numbers above only show the arithmetic.

### Lesson from this repo: slots can slice the context

During Lab 4/6, `llama-server -c 4096` ran with 4 slots, so each conversation got **1024 tokens** and lost context after a few turns (see `qlora/POST_MORTEM_FAILURE_ANALYSIS.md`). That build split the context evenly across slots. The current local build defaults to automatic slots with a unified KV buffer, which behaves differently. Rule that holds either way: **know your slot count and per-slot context**, set `-np` explicitly, and size `-c` for `slots × needed context` (or use `--kv-unified-per-slot`). For a single-user assistant, `-np 1` gives one conversation the whole window.

### Lesson: isolate instances

Concurrent `llama-server` instances on distinct ports (e.g. `8085` vs `8080`) keep memory buffers and slot queues apart, so evaluation runs do not disturb live traffic (see `proyecto/docs/history/session-2026-10-22-burst-and-lessons.md`).

## 4. Deployment Topologies

| Topology | Description | Fits |
|----------|-------------|------|
| Embedded / local process | App spawns or talks to a local server on `127.0.0.1` | Desktop tools, CLI (e.g. `clean-copilot`) |
| Single server | One model server, app calls it over HTTP | Small team, internal tool |
| Replicas + load balancer | N identical servers behind a balancer | More concurrent users than one server handles |
| Split pools | Separate servers per model (small/fast vs. large) with a router | Cost-aware cascade ([Cost-Aware Routing](./cost-aware-routing.md)) |
| Remote GPU over tunnel | Server on the DGX Spark, reached via SSH tunnel | Burst compute; see the `secure-ssh-tunnels` skill |
| Hybrid | Local model for private or easy work, hosted API for the rest | Privacy plus frontier quality ([Playbook: Model Tier Decisions](./playbook/model-tier-decisions.md)) |

## 5. Scaling Patterns

| Bottleneck | Move |
|------------|------|
| Requests queue up | More slots/replicas, or a runtime with stronger batching (vLLM on GPU) |
| Long prompts dominate latency | Prefix caching ([Prompt Caching](./prompt-caching.md)), shorter prompts |
| Memory exhausted | Smaller model or quantization, lower context, fewer slots, smaller prompt cache |
| Quality, not speed, is the problem | Better model or data; more hardware will not help |
| Spiky load | Hosted API for overflow |

Measure first: record time-to-first-token, tokens/s, queue depth, and error rate under realistic load before scaling (`--metrics` exposes server-side numbers).

## 6. Production Checklist

| Area | Requirement |
|------|-------------|
| Network | Bind to `127.0.0.1` or a private interface; expose only through a gateway or tunnel |
| Auth | `--api-key` plus a gateway. **vLLM caveat:** its `--api-key` only covers the `/v1`, `/v2`, `/inference`, and `/cohere` prefixes. Other endpoints stay unauthenticated, including `/invocations` (same inference as `/v1`), operational controls such as `/pause`, `/abort_requests`, and `/update_weights`, and utilities such as `/metrics` and `/tokenize`. Never expose vLLM directly; put a reverse proxy in front that allowlists only the endpoints you need (vLLM security docs, fetched 2026-11-17) |
| Limits | Max tokens, request timeout, input size cap, rate limits |
| Health | Health endpoint, restart policy, readiness before routing traffic |
| Observability | Latency, tokens, errors, escalation tier; no sensitive prompts in logs |
| Security | Treat model output as untrusted; guard against prompt injection (see the `inference-security-hardening` skill and [Playbook: Hardening](./playbook/hardening-checklist.md)) |
| Artifacts | Pin model file hash and runtime version; never commit weights |
| Rollback | Keep the previous model artifact and a one-step switch back |
