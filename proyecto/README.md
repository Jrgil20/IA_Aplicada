# Semester Project — Applied AI: Edge Clean Copilot

This directory contains all materials, technical documentation, datasets, training scripts, and client implementations for **Edge Clean Copilot**, the semester capstone project for the **Applied Artificial Intelligence** course at UCAB.

---

## 1. Project Documentation Index

- **[Technical Documentation Hub (`docs/`)](./docs/README.md):** Complete operational specifications, telemetry logs, and engineering records.
  - **[Detailed Execution Roadmap (Weeks 4–15)](./docs/detailed-roadmap.md):** The authoritative tactical master plan covering LoRA training, GGUF quantization, and benchmark criteria.
  - **[Progress & Verified Milestones](./docs/progress-and-milestones.md):** Live status board tracking deliverables across all 4 phases.
  - **[Session Report: 2026-10-22](./docs/session-2026-10-22-burst-and-lessons.md):** Root-cause analysis, port isolation (8085 vs 8080), 160-sample dataset burst, and lessons learned.
- **[Technical Proposal](./propuesta.md):** Original project vision, hypotheses, Clean Architecture principles, and academic articulation.
- **[Idea Bank](./ideas.md):** Preliminary architectural exploration and evaluated alternatives.

---

## 2. Project Subsystems

```
proyecto/
├── docs/       # Technical specifications, session logs, and roadmap
├── dataset/    # Seed and synthetic ChatML datasets (160 samples, ~186k tokens)
├── training/   # PyTorch LoRA fine-tuning pipeline with native merge capabilities
└── cli/        # Hexagonal CLI client in TypeScript (Ports & Adapters)
```

---

## 3. Current Project Status

- **Global Progress:** **57%**
- **Completed:** **Phase 1 (Infrastructure & Teacher Dataset)** — 100%
- **Active / Ready to Launch:** **Phase 2 (LoRA Adaptation & Specialization)** — 80% (Runtime and 73% of base weights staged on DGX Spark)
- **Pending:** **Phase 3 (Consolidation & GGUF Quantization)**
- **In Progress:** **Phase 4 (CLI Client & Edge Offline Inference)** — 50% (Core domain & mock adapters implemented)
