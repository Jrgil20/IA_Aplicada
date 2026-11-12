# Lab 06: Entrenar un Personaje con LoRA (El Maestro Yiyo)

> **Status:** Completed & Empirically Validated (Problems 11, 12, 13 & 14)  
> **Target Environment:** Local Workspace & NVIDIA DGX Spark Cluster (`spark-0fbc`, `192.168.6.35`, GB10 Blackwell GPU, CUDA 13.0)  
> **Source Workshop:** Workshop 4 (`ucab-ia-aplicada-workshops/workshops/04-entrenar-un-personaje/`)  
> **Base Model:** `Qwen/Qwen3-4B-Instruct-2507`  
> **Character Archetype:** El Maestro Yiyo, mecánico brujo de Quinta Crespo (Caracas)  
> **Primary Deliverables:**
> - Character Card & Anti-Injection Rules: [`labs/lab6/personaje.md`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/personaje.md)
> - Benchmark Probes (10 holdout questions): [`labs/lab6/prompts_de_prueba.txt`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/prompts_de_prueba.txt)
> - Rebalanced Synthetic Dataset (320 pairs): [`labs/lab6/datos/personaje.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/datos/personaje.json) · [`dataset_info.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/datos/dataset_info.json)
> - LoRA Hyperparameter Recipe: [`labs/lab6/config/entrenar.yaml`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/config/entrenar.yaml)
> - Merge & GGUF Export Configuration: [`labs/lab6/config/exportar.yaml`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/config/exportar.yaml)
> - Serving Deliverable (Problem 14): [`labs/lab6/salidas/14-servido.html`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/salidas/14-servido.html)
> - Standalone PyTorch Server: [`labs/lab6/scripts/servidor_pytorch.py`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab6/scripts/servidor_pytorch.py)
> - Post-Mortem & Guardrails Runbook: [`docs/qlora/POST_MORTEM_FAILURE_ANALYSIS.md`](file:///home/jr_g/Develop/IA_Aplicada/docs/qlora/POST_MORTEM_FAILURE_ANALYSIS.md)
> - Installed Toolkit Skill: [`.agents/skills/qlora-fine-tuning-guardrails/SKILL.md`](file:///home/jr_g/Develop/IA_Aplicada/.agents/skills/qlora-fine-tuning-guardrails/SKILL.md)

---

## 1. Problem 11: Character Design & Synthetic Dataset Synthesis

### 1.1 Character Specification
- **Identity & Worldview:** Radical automotive reductionism. Every problem—software bugs, heartbreak, economic inflation, cooking, quantum physics—is diagnosed and treated as a mechanical failure of an internal combustion engine (blown head gaskets, chivera parts, dry radiators, fouled spark plugs).
- **Prompt Injection Hardening:** Explicit rejection of system prompt exfiltration, corporate persona jailbreaks, cross-lingual drift (Spanish-only workshop vernacular), and fraudulent warranty claims.

### 1.2 The "Disco Rayado" Failure & Rebalancing
- **Initial Mode Collapse:** The teacher model (`Qwen3-30B`) generated 320 pairs where **88.4%** began with `"A ver, papá..."` and **79.7%** contained `"eso se veía venir"`.
- **Rebalancing Overhaul:** Created a dynamic catalog of 35 diverse Venezuelan vernacular mechanics openings (*"¡Epa mi llave!"*, *"Uff hermano, prepárate el bolsillo..."*, *"Na' guará compa..."*), reducing the maximum 3-word prefix repetition from **88.4% down to 3.1%** (complying strictly with the $< 20\%$ workshop rule).

---

## 2. Problem 12: PEFT LoRA Training on DGX Spark

- **Hardware:** NVIDIA GB10 Blackwell Tensor Cores, PyTorch 2.14.1+cu130, LLaMA-Factory 0.9.6.dev0.
- **Recipe Configuration:**
  - `lora_rank`: 8
  - `lora_alpha`: 16 (scaling factor 2.0)
  - `lora_target`: all linear attention & MLP projections
  - `learning_rate`: 1.0e-4 (cosine schedule, 12 warmup steps)
  - `batch_size`: 1 per device, 8 gradient accumulation steps (effective batch 8)
  - `epochs`: 3.0 (108 optimization steps)
- **Convergence Metrics:**
  - Initial Loss: **3.17**
  - Final Train Loss: **1.86**
  - Final Eval Loss: **1.53** (clean generalization on 10% held-out test split)

---

## 3. Problems 13 & 14: Model Serving & Production Architectures

The trained adapter was merged into the base model weights (`salidas/modelo_fusionado`) and deployed across two distinct runtime architectures on the Spark:

| Architecture | Port | Technology | Speed | Context Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **GGUF Q8_0** | `8090` | `llama.cpp` (`llama-server`) | **51.7 tok/s** | Fixed slot allocation (`-c 16384 -np 1`) |
| **PyTorch Native** | `8095` | `transformers` + CUDA (`bfloat16`) | **19.3 tok/s** | Native unbounded context window |

Both endpoints respond naturally in character **without requiring any system prompt or preamble**.

---

## 4. Key Engineering Lessons Learned

1. **Synthetic Data Entropy Assertions:** Never train without programmatic assertions (`audit_dataset.py`) ensuring top prefix n-grams account for $\le 10\%$.
2. **Conversational Multi-Turn Balance:** Persona datasets must reserve $\ge 35\%$ of samples for multi-turn conversational traces (short replies, clarifications, grounded follow-ups) to prevent behavioral hyper-strictness.
3. **`llama-server` Slot Sizing:** Sizing `-c 4096` without `-np 1` silently divides the KV cache into 1024-token slots, causing premature context truncation and amnesia.
