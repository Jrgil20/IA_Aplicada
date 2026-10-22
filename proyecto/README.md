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
├── docs/        # Technical specifications, session logs, and roadmap
├── dataset/     # Seed, generated pool, and train/eval partitions (168 samples)
├── training/    # PyTorch LoRA pipeline and automated GGUF quantization
├── cli/         # Hexagonal CLI client in TypeScript (28 unit tests, 100% green)
├── evaluation/  # Automated Clean Architecture benchmark harness (CAS 0-100)
└── status.py    # Zero-dependency instant diagnostic & session resume dashboard
```

---

## 3. Current Project Status

- **Global Progress:** **70%**
- **Completed:** **Phase 1 (Infrastructure & Teacher Dataset)** — 100%
- **Staged / Ready for Burst:** **Phase 2 (LoRA Adaptation & Specialization)** — 85% (Runtime and 73% of base weights staged on DGX Spark)
- **Staged / Automation Ready:** **Phase 3 (Consolidation & GGUF Quantization)** — 50% (`convert_to_gguf.sh` verified)
- **In Progress / Benchmark Operational:** **Phase 4 (CLI Client & Edge Offline Inference)** — 70% (28 unit tests green, benchmark harness operational)
