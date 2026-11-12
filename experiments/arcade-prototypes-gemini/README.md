# Retro Arcade Prototypes — Gemini 3.8 Flash Multi-Agent Run

Autonomous multi-agent generation experiment leveraging **Gemini 3.8 Flash** to engineer four complete, dependency-free HTML5 retro arcade game engines.

This suite is the direct comparative counterpart to the [DGX Spark Qwen3-Coder-30B baseline](file:///home/jr_g/Develop/IA_Aplicada/experiments/arcade-prototypes/README.md). For an exhaustive architectural, audio, and physics audit between both models, see the [Full Technical Benchmark (COMPARISON.md)](file:///home/jr_g/Develop/IA_Aplicada/experiments/arcade-prototypes-gemini/COMPARISON.md).

---

## 1. Quick Launch & Play

A unified retro arcade portal is provided at [`experiments/arcade-prototypes-gemini/index.html`](file:///home/jr_g/Develop/IA_Aplicada/experiments/arcade-prototypes-gemini/index.html).

### Method A: Direct Browser Launch
Open [`index.html`](file:///home/jr_g/Develop/IA_Aplicada/experiments/arcade-prototypes-gemini/index.html) directly in any modern browser (Chrome, Firefox, Safari, Edge).

### Method B: Local HTTP Server
```bash
cd experiments/arcade-prototypes-gemini
python3 -m http.server 8081
# Open http://localhost:8081 in your browser
```

---

## 2. Experiment Highlights & Key Metrics

| Metric | Gemini 3.8 Flash Suite | Qwen3-Coder-30B Baseline | Delta |
| :--- | :--- | :--- | :--- |
| **Total Lines of Code (LOC)** | **7,968 LOC** | 3,020 LOC | **+163.7%** |
| **Total Source Size** | **260,686 bytes (~254.6 KB)** | 107,211 bytes (~104.7 KB) | **+143.1%** |
| **ES6 Classes Defined** | **29 classes** | 3 classes | **+866.7%** |
| **Procedural White Noise Buffers** | **4 / 4 engines (100%)** | 0 / 4 engines (0%) | +100% |
| **Dynamic Biquad Filter Nodes** | **4 / 4 engines (100%)** | 0 / 4 engines (0%) | +100% |
| **Web Audio Context Unlocking** | **4 / 4 functional** | 2 / 4 functional (2 silent) | **+100%** |
| **Particle & Bullet Object Pooling** | **Preallocated pools (Zero GC)** | Array allocation / splice (High GC) | High fidelity |
| **Orbital Mechanics Integration** | **Symplectic Euler + Softening** | Naive Euler (unsoftened $G M/r^2$) | Energy conserving |

---

## 3. Game Prototypes Specification & Engineering Overview

```
experiments/arcade-prototypes-gemini/
├── index.html                   # Central retro arcade portal with live cards & links
├── COMPARISON.md                # Full technical audit & benchmark vs. Qwen3-Coder-30B
├── README.md                    # Project documentation & run overview
├── 01-gridlock-protocol/        # Real-time traffic routing & buffer overflow simulator
│   ├── index.html               # 1,680 LOC single-file engine (55 KB)
│   └── generation_meta.json     # Execution metrics & metadata
├── 02-shattered-vector/         # Twin-stick orbital shooter with singularity physics
│   ├── index.html               # 2,237 LOC single-file engine (72 KB)
│   └── generation_meta.json     # Execution metrics & metadata
├── 03-glitch-climber/           # Precision vertical cyber-tower mutation platformer
│   ├── index.html               # 2,027 LOC single-file engine (62 KB)
│   └── generation_meta.json     # Execution metrics & metadata
└── 04-bazaar-broker/            # Cyber-hardware inventory & speed-crafting stall
    ├── index.html               # 2,024 LOC single-file engine (71 KB)
    └── generation_meta.json     # Execution metrics & metadata
```

---

### 🎮 Game 1: Gridlock Protocol (`01-gridlock-protocol`)
* **Core Concept:** Real-time network routing in a high-density cyber-grid. Data packets enter along screen boundaries with variable priority and velocity.
* **Architecture:** Decoupled into `AudioSynth`, `ParticleSystem`, `GridSystem`, `PacketManager`, and `GameEngine`.
* **Key Mechanics:**
  - 4 Packet Archetypes: Standard Data, High-Velocity VIP, Heavy Payload, and Corrupted Malware.
  - Interactive intersection direction gates with animated orientation arrows.
  - Thermal stress and buffer queue overflow mechanics: misdirected packets heat up nodes, triggering emergency sirens.
  - Procedural sound synthesis: ambient 55Hz cyber drone, dynamic alarm siren reacting to grid heat, and multi-channel sound effects.

### 🚀 Game 2: Shattered Vector (`02-shattered-vector`)
* **Core Concept:** Twin-stick neon vector shooter trapped in the accretion disk of a supermassive singularity.
* **Architecture:** 13 specialized ES6 classes including `VectorMath`, `BlackHole`, `WarpGrid`, `Player`, `BulletPool`, `ParticlePool`, and `EnemyManager`.
* **Key Mechanics:**
  - **Symplectic Euler Integration:** Energy-conserving orbital physics with Plummer-softened gravitational potential ($a = -\frac{G M}{r^2 + \epsilon^2}\hat{r}$, $\epsilon = 45$).
  - **Dynamic WarpGrid:** Interactive spacetime mesh inspired by *Geometry Wars* that deforms toward the black hole and ripples under explosive shockwaves.
  - **Kinetic Polarity Weapons:**
    - *Repel (Cyan):* Kinetic outward knockback pushing swarms away.
    - *Attract (Magenta):* Kinetic tractor beam pulling swarms directly into the event horizon.
    - *Singularity Sacrifices:* Feeding enemies into the black hole awards a $3\times$ score bonus.
  - **Memory Pooling:** Preallocated `BulletPool` (200 instances) and `ParticlePool` (400 instances) eliminating runtime garbage collection pauses.
  - **Proximity Audio Drone:** Pitch and lowpass filter cutoff dynamically scale as the player craft approaches the event horizon.

### 🧗 Game 3: Glitch Climber (`03-glitch-climber`)
* **Core Concept:** Precision vertical platformer ascending a disintegrating cyber-tower where digital terrain mutates state every 5 seconds.
* **Architecture:** Decoupled into `AudioSynth`, `ParticleSystem`, `PlatformManager`, `PlayerPhysics`, `GlitchRenderer`, and `GameEngine`.
* **Key Mechanics:**
  - **4-State Platform Machine:** Bedrock (Green), Lethal Corrupted Data (Red), Permeable Phase-through (Blue), and Super Boost Pad (Yellow).
  - **Telegraphed Mutation Warning:** A 1.4-second warning window triggers countdown audio beeps (`3`, `2`, `1`) and causes platform geometry to visually shiver/pulse before mutating.
  - **Agile Physics Engine:** Variable jump height, wall-slide, wall-jump, horizontal dash with after-image ghosts, and drop-through phase mechanics.
  - **GlitchRenderer:** Real-time canvas CRT scanlines, rising corruption void, and horizontal chromatic aberration slices using `globalCompositeOperation = 'screen'`.
  - **Algorithmic 8-bit Music:** Procedural arpeggiator step sequencer generating dynamic background music.

### 💼 Game 4: Bazaar Broker (`04-bazaar-broker`)
* **Core Concept:** Frenetic inventory management and speed-crafting in a clandestine cyber-hardware market stall under high customer rush.
* **Architecture:** Decoupled into `AudioSynth`, `InventoryGrid`, `OrderSystem`, `DragManager`, and `GameEngine`.
* **Key Mechanics:**
  - $5 \times 4$ slot inventory matrix with smooth pointer and touch drag-and-drop.
  - Multi-tier crafting engine: Dragging and combining components on the inventory grid or recycler zone to synthesize upgraded hardware modules.
  - Customer ticket bays with dynamic patience timers, speed tips ($+40\%$), critical rage audio warnings, and customer rage-quit strikes.
  - Smuggler cargo airdrop refill button with currency cost deductions.

---

## 4. Cross-Run Comparison

For the full comparative analysis between this Gemini run and the local Qwen DGX Spark run, consult:
* [`COMPARISON.md`](file:///home/jr_g/Develop/IA_Aplicada/experiments/arcade-prototypes-gemini/COMPARISON.md): Exhaustive benchmark tables, physics formulas, audio graphs, root-cause bug analysis, and production recommendations.
* Baseline Portal: [`../arcade-prototypes/index.html`](file:///home/jr_g/Develop/IA_Aplicada/experiments/arcade-prototypes/index.html).
