# Lab 01: Environment Setup & Local Inference (DGX Spark)

> **Status:** Ready for Lab Session Execution  
> **Target System:** NVIDIA DGX Spark (`ucab-spark2`, 128 GB Unified Memory, GB10 architecture)  
> **Model under Test:** `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` (`/srv/models/`)  
> **Interactive Agent / Tool:** OpenCode CLI + `llama-server` local endpoint

---

## 1. Objectives

- [x] Identify hardware paths and toolchain on DGX Spark (`/srv/models/`, `llama.cpp`).
- [ ] Execute pre-flight check script ([`preflight.sh`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab1/preflight.sh)) via PuTTY.
- [ ] Launch `llama-server` on port 8080 offloading all 99 layers to unified GPU memory.
- [ ] Connect OpenCode CLI to `http://localhost:8080/v1`.
- [ ] Use Qwen 30B to synthesize `classify_tickets.py` using standard Python (`csv`, `urllib.request`).
- [ ] Process all 85 tickets from `tickets_tramontana.csv` without crashes.
- [ ] Flag duplicates and order output queue prioritizing `urgencia: "alta"`.
- [ ] Record baseline inference throughput (tokens/s) and memory consumption.

---

## 2. Pre-flight Setup & Verification

Before starting execution on PuTTY, run the automated verification script:

```bash
cd ~/mesa-de-trabajo/lab1
bash preflight.sh
```

Verifications checked:
1. GGUF model exists at `/srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`.
2. `llama-server` binary presence and executable permissions.
3. Port 8080 free of collisions.
4. Python 3 environment and core modules (`csv`, `json`, `urllib.request`).
5. OpenCode CLI binary discovery and configuration.
6. Internet access / download capability via `wget` or `curl`.

---

## 3. Step-by-Step Execution Plan

### Step 1: Workspace & Dataset Retrieval
```bash
mkdir -p ~/mesa-de-trabajo/lab1
cd ~/mesa-de-trabajo/lab1
wget -O tickets_tramontana.csv https://raw.githubusercontent.com/rsanchezsoutec/tramontana-datos-ficticios/main/01_mesa_de_soporte/tickets_tramontana.csv
wc -l tickets_tramontana.csv
```

### Step 2: Start `llama-server`
```bash
LLAMA_BIN=$(which llama-server 2>/dev/null || echo "$HOME/llama.cpp/build/bin/llama-server")

$LLAMA_BIN \
  -m /srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 8192 \
  --n-gpu-layers 99
```

### Step 3: Prompting OpenCode
In a second terminal window, run OpenCode using the prompt in [`prompts.md`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab1/prompts.md) to generate `classify_tickets.py`.

### Step 4: Run & Inspect Classification
```bash
python3 classify_tickets.py
```

---

## 4. Execution Log & Metrics

*(To be filled during live session)*

| Metric | Target / Expected | Observed Result |
| :--- | :--- | :--- |
| **Model Load Time** | < 15 seconds | |
| **Unified Memory Allocated** | ~18–22 GB | |
| **Generation Speed** | > 30 tokens/s | |
| **Processed Tickets** | 85 / 85 | |
| **Graceful Fallbacks (`sin_clasificar`)** | 0 or unhandled only | |
| **Detected Duplicates** | >= 1 | |

---

## 5. Deliverables & Lab Criteria

- **Generated code:** `classify_tickets.py`
- **Output dataset:** `tickets_clasificados.json` (sorted by urgency, duplicates marked)
- **Execution guide:** [README.md](file:///home/jr_g/Develop/IA_Aplicada/labs/lab1/README.md)
- **Detailed prompts:** [prompts.md](file:///home/jr_g/Develop/IA_Aplicada/labs/lab1/prompts.md)
