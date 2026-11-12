# Technical Post-Mortem & Failure Mode Analysis: Character LoRA Fine-Tuning

**Subject:** Architectural, Data Engineering, and Runtime Post-Mortem of "El Maestro Yiyo" (Qwen3-4B-Instruct LoRA Adaptation)  
**Hardware:** NVIDIA DGX Spark (Grace Blackwell GB10, CUDA 13.0)  
**Date:** November 2026  
**Audience:** Applied AI Engineering Team  

---

## Executive Summary

During the implementation of Lab 4/6 (Fine-Tuning a Persona using QLoRA/LoRA on Qwen3-4B-Instruct), several critical failures occurred across the pipeline: synthetic dataset mode collapse, behavioral overfitting resulting in hyper-rigid single-turn caricaturization, misconfigured multi-tenant context allocation in `llama-server`, and premature delivery without end-to-end multi-turn verification.

This document analyzes each failure mode forensically, identifies root causes, and establishes engineering guardrails to prevent regression.

```
+---------------------------------------------------------------------------------------------------+
|                                  FAILURE CASCADE ARCHITECTURE                                     |
+---------------------------------------------------------------------------------------------------+
| 1. Teacher Generation (Low Entropy) ---> 88.4% Prefix Collapse ("A ver, papá...")                 |
|                                                     |                                             |
| 2. LoRA Fine-Tuning (Alpha=16, 3 Epochs) ---------> Overfitting: Monolithic Single-Turn Caricature|
|                                                     |                                             |
| 3. Runtime llama-server (-c 4096, default -np 4) -> 1024 Token Slot Budget (Rapid Context Amnesia) |
|                                                     |                                             |
| 4. User Testing ----------------------------------> "Suena a disco rayado y se degrada el contexto"|
+---------------------------------------------------------------------------------------------------+
```

---

## Failure Mode 1: Synthetic Dataset Mode Collapse ("Disco Rayado")

### 1.1 What Happened
The initial 320 synthetic training pairs produced by the teacher model (`Qwen3-30B`) exhibited catastrophic lexical and structural collapse:
- **88.4% of responses** (283/320) started with `"A ver, papá..."`.
- **79.7% of responses** contained `"eso se veía venir"`.
- **80.6% of responses** contained `"meterle el ojo"`.

Despite the workshop rubric explicitly warning that any prefix repetition exceeding 20% would render the model useless, the validation report (`11-dataset.html`) was compiled, visually displayed the 88.4% violation, and training was executed regardless.

### 1.2 Root Cause Analysis
1. **Teacher Prompt Anchoring:** The prompt given to the teacher model provided static few-shot examples dominated by a single greeting pattern. Autoregressive teacher models under greedy or low-temperature decoding collapse into repetitive syntactic templates.
2. **Missing Automated CI/CD Assertions:** The generation script had no programmatic exit gates or assert checks. It logged the violation to an HTML file but did not halt execution or reject aberrant samples.

### 1.3 How It Should Have Been Corrected
- **Hard Guardrail Assertions in Data Pipeline:**
  ```python
  def validate_dataset_entropy(dataset: list[dict], max_ngram_rep: float = 0.10):
      prefixes = [" ".join(d["output"].split()[:3]) for d in dataset]
      counts = Counter(prefixes)
      top_ratio = counts.most_common(1)[0][1] / len(dataset)
      if top_ratio > max_ngram_rep:
          raise ValueError(f"Mode collapse detected: top prefix accounts for {top_ratio:.1%} (> {max_ngram_rep:.1%})")
  ```
- **Dynamic Few-Shot Sampling:** Randomly sample 3 examples from a heterogeneous pool of 50 diverse seed pairs for every teacher query, preventing syntactic template fixation.
- **Temperature & Top-p Stochastics:** Sample the teacher at `temperature = 0.95` and `top_p = 0.9` during synthetic generation rather than deterministic decoding.

---

## Failure Mode 2: Single-Turn Bias and Behavioral Hyper-Strictness

### 1.1 What Happened
In live testing, the character felt unnatural, claustrophobic, and exhausting:
- Any input—even a simple greeting (*"Hola"*) or an inquiry (*"¿Cuánto cobras?"*)—triggered an exhaustive 120-word speech containing multiple forced automotive metaphors (*"empacadura de la cámara"*, *"bujías"*, *"chivera"*).
- The model could not sustain a coherent back-and-forth dialogue or answer technical questions simply when requested.

### 2.2 Root Cause Analysis
1. **100% Single-Turn Dataset Architecture:** All 320 training examples were atomic pairs (`Instruction -> Exhaustive Diagnostic Monologue`). The LoRA adapter was never conditioned on multi-turn dialogue dynamics:
   $$P(\text{Automotive Metaphor} \mid \text{Any Input Token}) \approx 1.0$$
2. **Aggressive LoRA Scaling:** Training 3 full epochs with `lora_rank=8` and `lora_alpha=16` (scaling ratio 2.0) on a homogeneous dataset heavily warped the attention projections (`q_proj`, `v_proj`, `k_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`). This erased the base model's conversational pacing in favor of forced jargon density.

### 2.3 How It Should Have Been Corrected
1. **Multi-Turn Curriculum:** Allocate at least 35% of the dataset to multi-turn conversations (3 to 6 turns) reflecting realistic conversational cadence:
   - *Turn 1:* Diagnostic analogy + short question back to user.
   - *Turn 2:* Brief clarification (*"Pásame la llave trece"*).
   - *Turn 3:* Direct pragmatic advice without metaphors.
2. **Hyperparameter Softening:**
   - Lower `lora_alpha` to 8 (scaling ratio 1.0) to preserve base model flexibility.
   - Cap training at 1.5 - 2.0 epochs, evaluating loss plateaus before the weights overfit on phrasing.

---

## Failure Mode 3: Runtime Context Degradation in `llama-server`

### 3.1 What Happened
The user reported: *"en una conversación con llama en el enlace que pasaste se degrada demasiado rápido el contexto"* (the context degrades too quickly during conversation). The immediate suspicion fell onto `llama.cpp` itself as "ruining the model".

### 3.2 Root Cause Analysis
- `llama-server` was launched with:
  ```bash
  llama-server -m salidas/maestro_yiyo_4b_q8.gguf -c 4096 --host 0.0.0.0 --port 8090 -ngl 99
  ```
- By default, `llama-server` allocates slots for concurrent requests when `--parallel` (`-np`) is omitted. The server initialized with:
  ```text
  load_model: initializing, n_slots = 4, n_ctx_slot = 4096 / 4 = 1024 tokens
  ```
- Each conversation slot was physically allocated **only 1,024 tokens of KV cache**.
- In the web chat UI, each turn re-sends full conversation history. By turn 3 or 4, prompt + history reached ~900 tokens. The next generation exceeded 1,024 tokens, triggering context truncation (context shift). The server evicted early conversation turns, making the model appear to lose its mind and repeat itself.

### 3.3 How It Should Have Been Corrected
- Explicitly size single-user context allocation:
  ```bash
  llama-server \
      -m salidas/maestro_yiyo_4b_q8.gguf \
      -c 16384 \
      -np 1 \
      --repeat-penalty 1.15 \
      --port 8090
  ```
- Passing `-np 1` guarantees the active user owns the entire 16,384 token window, completely preventing context degradation.

---

## Failure Mode 4: Lack of Automated E2E Verification Before Delivery

### 4.1 What Happened
Changes were validated using single-shot curl queries (*"el carro me bota humo blanco"*) rather than interactive multi-turn stress tests. As a result, the user acted as the QA tester, encountering the broken record syndrome and context exhaustion firsthand.

### 4.2 How It Should Have Been Corrected
- Implement an automated E2E verification script executing a 5-turn simulated dialogue before presenting any serving endpoint:
  ```python
  def verify_conversational_health(endpoint_url: str):
      dialogue = ["Hola Maestro", "Tengo un problema con Python", "Pero explícamelo más simple", "¿Cuánto me cobras?", "Gracias"]
      history = []
      for turn in dialogue:
          resp = query_model(endpoint_url, history, turn)
          history.append({"user": turn, "bot": resp})
          assert len(resp) > 10, "Empty response"
      # Verify lexical diversity across turns
      words = " ".join([h["bot"] for h in history]).split()
      assert len(set(words)) / len(words) > 0.45, "Repetitive speech detected"
  ```

---

## Summary Matrix of Failures & Corrections

| Failure Area | Root Cause | Symptom | Engineering Correction |
| :--- | :--- | :--- | :--- |
| **Data Generation** | Unchecked few-shot teacher generation. | 88.4% starting with *"A ver, papá..."*. | Programmatic `assert max_ngram < 0.10` in CI/CD pipeline. |
| **Persona Modeling** | 100% single-turn dataset; high LoRA alpha. | Hyper-rigid, over-the-top caricature in multi-turn chat. | 35% multi-turn dataset; `lora_alpha=8` to preserve base conversational fluency. |
| **Serving Runtime** | Default `-np 4` in `llama-server` sliced `-c 4096` into 1024-token slots. | Amnesia & context hallucination after 3 turns. | Set `-np 1` with `-c 16384` for dedicated single-user KV cache. |
| **Validation** | Single-shot curl tests instead of multi-turn harnesses. | User discovered obvious bugs live in browser. | Automated multi-turn conversational healthcheck script prior to delivery. |
