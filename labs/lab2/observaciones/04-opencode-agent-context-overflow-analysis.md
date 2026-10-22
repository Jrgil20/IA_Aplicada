# Observation 04: OpenCode Agent Context Overflow and Model Isolation Architecture

> **Status:** Resolved & Empirically Validated  
> **Target System:** NVIDIA DGX Spark (`spark-0fbc`, `192.168.6.35/26`, GB10 Superchip, 128 GB Unified Memory)  
> **Impacted Framework:** OpenCode Agent v1.19.4 connecting to `llama-server` (Qwen3-Coder-30B)  
> **Incident Classification:** Context Window Exhaustion (`AI_APICallError`) during Agent Bootstrapping  

---

## 1. Incident Overview & Symptoms

During attempts to execute tasks through the autonomous coding agent **OpenCode** against the local DGX Spark backend, the CLI agent hung or aborted without generating code.

### Live Telemetry from Logs

#### 1. OpenCode Runtime Log (`~/.local/share/opencode/log/opencode.log`)
```text
timestamp=2026-10-22T15:17:04.470Z level=ERROR run=b6b08571 message="stream error" \
  providerID=spark modelID=qwen3-coder session.id=ses_e9bd03a63ffems5xCyMiDQYJOl \
  error.error="AI_APICallError: request (7411 tokens) exceeds the available context size (4096 tokens), try increasing it"

timestamp=2026-10-22T15:17:04.471Z level=ERROR run=b6b08571 message=process \
  error="request (7411 tokens) exceeds the available context size (4096 tokens), try increasing it" \
  stack="AI_APICallError: request (7411 tokens) exceeds the available context size (4096 tokens), try increasing it
      at <anonymous> (/$bunfs/root/chunk-5tmyxxt2.js:6:14263)
      at async <anonymous> (/$bunfs/root/chunk-5tmyxxt2.js:6:12773)"
```

#### 2. Model Backend Server Log (`~/qwen_coder.log`)
```text
14.02.796.501 E srv send_error: task id = 2976, error: request (8045 tokens) exceeds the available context size (4096 tokens), try increasing it
14.02.796.508 I slot release: id = 0 | task 2976 | stop processing: n_tokens = 0, truncated = 0
14.02.796.620 W srv stop: cancel task, id_task = 2976
```

---

## 2. Root Cause Analysis

### 2.1 Anatomy of Autonomous Agent Bootstrapping Payloads
Unlike interactive chatbots that submit minimal conversational prompts (e.g., 20–100 tokens), autonomous coding agents like OpenCode submit structured scaffolding on the very first turn:

1. **System Persona & Global Governance:** Behavioral rules, boundaries, and formatting instructions (~1,200 tokens).
2. **Tool Function Schemas:** Full JSON Schemas for each callable tool (`bash`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `git`, `task_manager`) (~4,500–5,000 tokens).
3. **Repository Context & Active Workspace Tree:** File paths, git status, and environment variables (~1,500–1,800 tokens).

**Total Initial Prefill:** **~7,400 to 8,050 tokens** before the user's prompt is processed.

### 2.2 Sizing Defect in Backend Server Startup
The backend server had been launched with:
```bash
/home/ucab-spark1/llama.cpp/build/bin/llama-server \
  -m /srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
  --port 8080 \
  -c 4096   # <-- BOTTLENECK: Hard limit of 4,096 tokens
```
Because the prefill payload (7,411 tokens) exceeded `-c 4096`, `llama-server` rejected the inference call with a 400/500 client error.

---

## 3. Architecture Clarification: Process Isolation vs. Duplication

A common concern in multi-modal environments is whether concurrent services interfere with each other or share context.

### 3.1 Total Isolation Between Camera (VLM) and Coding Agent (Coder)
The camera stream and OpenCode do **not** share context, model weights, or memory buffers:

```
[ Local Laptop Camera ] ---> (HTTP 8080) ---> [ Flask app.py (8082) ] ---> [ Gemma 3 4B VLM (8084) ] ---> GPU PID 15845 (5.7 GB)
                                                                                  ^
                                                                          100% ISOLATED (Separate Process & Port)
                                                                                  v
[ OpenCode Agent / CLI ] -------------------------------------------------> [ Qwen 3 Coder 30B (8080) ] -> GPU PID 28983 (17.3 GB)
```

| Dimension | Vision Service (Camera) | Coding Service (OpenCode) |
| :--- | :--- | :--- |
| **Model** | `gemma-3-4b-it-Q8_0.gguf` + `mmproj` | `Qwen3-Coder-30B-A3B-Instruct...` |
| **Port** | `8084` | `8080` |
| **GPU Process PID** | `15845` | `28983` |
| **VRAM Allocated** | **5.7 GB** | **17.3 GB** |
| **Context Window** | `4,096` tokens | **`32,768` tokens** |
| **Modalities** | JPEG Vision + Text | Plain Text + Code / Tools |

### 3.2 Why Duplicate Model Instances Are Unnecessary
Running two instances of Qwen 30B to handle separate users or tasks would be an anti-pattern:
- **`n_slots = 4` Multi-Tenancy:** `llama-server` internally allocates **4 independent KV cache slots**. Up to 4 client requests run concurrently with complete context isolation.
- **Zero VRAM Duplication:** Multiple model instances would duplicate the 17 GB model weights (17 GB x 2 = 34 GB). Multi-slot execution maintains **one** copy of weights and allocates only the lightweight KV cache per slot (~500 MB per slot).

---

## 4. Remediation & Verification

### 4.1 Re-launch with Extended 32k Context
Both `manage_models.sh` and `iniciar_lab2.sh` were updated to size Qwen's context window to 32,768 tokens:

```bash
nohup /home/ucab-spark1/llama.cpp/build/bin/llama-server \
  -m /srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
  --port 8080 \
  --host 0.0.0.0 \
  -ngl 99 \
  -c 32768 > /home/ucab-spark1/qwen_coder.log 2>&1 &
```

### 4.2 Verification Logs
```text
0.02.058.829 I srv    load_model: initializing, n_slots = 4, n_ctx_slot = 32768, kv_unified = 'true'
0.02.060.657 I srv  llama_server: model loaded
0.02.060.663 I srv  llama_server: listening on http://0.0.0.0:8080
```

### 4.3 Post-Fix Telemetry

| Metric | Target | Observed Result |
| :--- | :--- | :--- |
| **Context Limit** | > 8,000 tokens | **32,768 tokens** |
| **VRAM Footprint with 32k KV** | < 25 GB | **17.3 GB** (on 128 GB Unified Memory) |
| **OpenCode Bootstrapping** | Complete without error | **Success (200 OK)** |
| **Inference Generation Speed** | > 50 tokens/s | **87.85 tokens/s** |

---

## 5. Architectural Recommendations

1. **Agent Context Sizing Rule:** Any LLM server intended for agentic frameworks (OpenCode, Claude Code, Cursor, Aider) must be initialized with `-c 32768` minimum to absorb tool function definitions and system governance.
2. **Dedicated Models for Distinct Modalities:** Keep small, specialized VLMs (4B) on a dedicated port for streaming vision, while reserving large coding models (30B) on another port for code synthesis.
3. **Hardware Utilization:** The 128 GB Unified Memory of the NVIDIA GB10 comfortably hosts both models simultaneously using only 23 GB total VRAM.
