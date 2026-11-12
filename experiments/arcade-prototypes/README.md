# Retro Arcade Prototypes — Parallel LLM Generation Experiment

Autonomous multi-instance experiment leveraging **Qwen3-Coder-30B** running on NVIDIA DGX Spark to generate four complete, dependency-free HTML5 retro arcade game prototypes in parallel.

---

## 1. Experiment Overview & Hardware Setup

| Metric / Parameter | Value / Detail |
| :--- | :--- |
| **Compute Host** | NVIDIA DGX Spark (`spark-0fbc`, IP: `192.168.6.35`) |
| **GPU Accelerator** | NVIDIA GB10 (CUDA 13.0, Driver 580.173.02) |
| **Model** | `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` (30.5B params, MoE architecture) |
| **Inference Server** | `llama-server` (`llama.cpp` build) |
| **Concurrency Configuration** | `n_slots = 4`, `n_ctx_slot = 32768`, Unified KV cache (`kv_unified = true`) |
| **VRAM Consumption** | ~20,108 MiB dedicated GPU memory |
| **Generation Throughput** | ~35–47 tokens/sec per slot (~140–170 tokens/sec aggregate cluster throughput) |
| **Total Code Generated** | > 20,000 completion tokens across 4 self-contained engines in ~145 seconds |

---

## 2. Architecture & Concurrency Flow

The experiment orchestrator dispatched four independent game specifications simultaneously over HTTP to the `llama-server` OpenAI-compatible `/v1/chat/completions` endpoint, utilizing all 4 hardware slots of the DGX Spark in parallel.

```
+-----------------------------------------------------------------------------------+
|                           Antigravity Local Orchestrator                         |
|                    (Python ThreadPoolExecutor - 4 Workers)                        |
+--------+---------------------+-----------------------+---------------------+------+
         |                     |                       |                     |
   Slot 0 (POST)         Slot 1 (POST)           Slot 2 (POST)         Slot 3 (POST)
         |                     |                       |                     |
+--------v---------------------v-----------------------v---------------------v------+
|                       NVIDIA DGX Spark (llama-server:8080)                        |
|                                                                                   |
|  [Slot 0: Gridlock]    [Slot 1: Shattered]    [Slot 2: Climber]     [Slot 3: Bazaar]      |
|  ~43 tokens/sec        ~43 tokens/sec         ~43 tokens/sec        ~43 tokens/sec        |
+--------+---------------------+-----------------------+---------------------+------+
         |                     |                       |                     |
         v                     v                       v                     v
+-----------------+   +-----------------+     +-----------------+   +---------------+
| 01-gridlock/    |   | 02-shattered/   |     | 03-climber/     |   | 04-bazaar/    |
| index.html (23K)|   | index.html (26K)|     | index.html (29K)|   | index.html(28K|
+-----------------+   +-----------------+     +-----------------+   +---------------+
```

---

## 3. Game Prototypes Specification & Technical Analysis

### 🎮 Game 1: Gridlock Protocol (`01-gridlock-protocol`)
* **Core Concept:** Real-time network routing & traffic management in downtown Caracas. Data packets enter along screen boundaries with variable priority and velocity.
* **Key Mechanics:**
  - Dynamic intersection switching: Clicking an intersection toggles routing gates (North/South vs. East/West).
  - Buffer queues with overflow penalties: Stalling or misdirecting packets overfills node buffers, leading to thermal stress and system collapse.
  - Spatial collision detection: Intersecting packets collide and explode into particle debris.
* **Technical Highlights:**
  - Clean spatial grid partitioning for $O(1)$ collision and intersection checks.
  - Procedural sound synthesis using Web Audio API oscillators for traffic clicks, routing toggles, and warning sirens.
  - Complete zero-dependency implementation (~680 lines of standalone code).

### 🚀 Game 2: Shattered Vector (`02-shattered-vector`)
* **Core Concept:** Twin-stick neon vector shooter set in the gravitational pull of an unstable central singularity.
* **Key Mechanics:**
  - Dual-force physics: Central black hole continuously exerts inverse-square gravitational acceleration ($\vec{a} = -\frac{G M}{r^2} \hat{r}$) on the player's craft and enemy swarms.
  - Polarity Shift: Player weapon toggles between **Repel** (push back incoming enemies) and **Attract** (pull enemies into the core hazard).
  - Procedural recoil and orbital inertia requiring constant thrust counter-steering.
* **Technical Highlights:**
  - Symplectic Euler numerical integration for orbital mechanics.
  - High-performance particle pooling for glowing neon vector trails and core distortion rings.
  - Vector line-rendering pipeline with glow effects (`ctx.shadowBlur` and composite operations).

### 🧗 Game 3: Glitch Climber (`03-glitch-climber`)
* **Core Concept:** Vertical precision platformer ascending a disintegrating cyber tower where terrain states continuously mutate.
* **Key Mechanics:**
  - Mutation Timer / Glitch Tick: Every 5 seconds, digital platforms shift state:
    - **Green:** Solid bedrock.
    - **Red:** Lethal corrupted data (instant death on contact).
    - **Blue:** Permeable / phase-through (drop down).
    - **Yellow:** Boost / acceleration pad.
  - High-precision movement: Variable jump height, wall-slide, and horizontal dash mechanics.
* **Technical Highlights:**
  - Procedural vertical chunk generation seeded with progressive difficulty.
  - Real-time CRT scanlines and digital chromatic aberration glitch artifacts rendered via Canvas composite operations.
  - State Machine architecture decoupling platform physical state from visual rendering.

### 💼 Game 4: Bazaar Broker (`04-bazaar-broker`)
* **Core Concept:** Frenetic inventory management and speed-crafting in a clandestine cyber-hardware market stall under customer rush.
* **Key Mechanics:**
  - Grid Inventory: Compact 5x4 slot matrix where components (Capacitors, Heat Sinks, SATA Cables, Quantum Cores) must be rapidly sorted.
  - Drag-and-Drop Crafting: Dragging components onto customer workbenches or combining damaged components to fulfill dynamic orders.
  - Escalating impatience bars with customer rage-quit mechanics.
* **Technical Highlights:**
  - Robust pointer event handling with offset tracking and slot snapping.
  - Recipe evaluation engine matching inventory combinations against customer request sets.
  - Multi-channel audio synthesizer with pitch-shifted feedback for successful sales vs. customer departures.

---

## 4. Evaluation of Qwen3-Coder-30B Performance

### Strengths Demonstrated
1. **Architectural Separation:** In all four cases, Qwen3-Coder-30B organized the code into well-delineated modules: Constants, Audio Synth, Entities, State Management, Game Loop, and Event Listeners.
2. **Procedural Web Audio Mastery:** Instead of dummy audio or external MP3 dependencies, the model implemented complete Web Audio API classes (`AudioContext`, `createOscillator`, exponential ramp gain nodes) for retro sounds.
3. **No External CDNs:** Strict adherence to zero-dependency constraints; everything runs completely offline.

### Edge Case Handled (Token Window Recovery)
When generating single-file engines of 600+ lines, the 5,120 token output window cut off the tail of games 2, 3, and 4. The orchestrator detected the missing closure tags and dispatched targeted continuation prompts to Qwen3-Coder-30B, seamlessly stitching the game loop, render tails, and closing tags without code duplication.

---

## 5. How to Launch & Play

A unified portal is included at `experiments/arcade-prototypes/index.html`.

### Method A: Direct Browser File Open
Open `experiments/arcade-prototypes/index.html` in any modern web browser (Firefox, Chrome, Edge).

### Method B: Local HTTP Server
```bash
cd experiments/arcade-prototypes
python3 -m http.server 8080
# Open http://localhost:8080 in your browser
```
