# Semester Project — Applied AI

This directory contains all materials related to the final project for the **Applied Artificial Intelligence** course (UCAB).

## Documents

- [Technical Proposal: Edge Clean Copilot](./propuesta.md) — Core document covering vision, hypotheses, architecture (Ports & Adapters), and execution timeline.
- [Idea Bank](./ideas.md) — Preliminary ideas and evaluated alternatives for project development.

## Project Status

- **Current Phase:** Phase 1 — Infrastructure and Teacher Model (Weeks 1-3) [COMPLETED]
- **Next Phase:** Phase 2 — LoRA Adaptation and Specialization (Weeks 4-7)

### Phase 1 Completed Milestones

- [x] **Direct Network Topology:** Direct cable peer-to-peer connection established between client laptop (`eno2`, `192.168.6.50/26`) and NVIDIA DGX Spark 2 (`enp7s7`, `192.168.6.34/26`) with Auto-MDIX and passwordless Ed25519 SSH.
- [x] **Teacher Model Serving:** Validated `llama-server` on port 8080 serving `Qwen3-Coder-30B-A3B-Instruct` offloaded 99 layers onto the Blackwell GB10 GPU.
- [x] **Teacher Dataset Generator:** Implemented [`dataset/generate_with_teacher.py`](./dataset/generate_with_teacher.py) with configurable time-limit flag (`--max-time-minutes`) and automatic ChatML format verification.
- [x] **Seed Dataset Curation:** Curated canonical Clean Architecture pairs from real projects (ArrowMaze) covering Domain Entities, Value Objects, Use Cases with `Result<T, E>`, Ports/Adapters, and AAA unit tests.
- [x] **LoRA Training Pipeline:** Implemented [`training/train_lora.py`](./training/train_lora.py) with native PyTorch training loop, dynamic batch padding, `--dry-run` mode for cold staging, `--max-time-minutes` time-bounding flag, and `--merge` for GGUF consolidation.
- [x] **Dataset Validation Suite:** Implemented [`dataset/validate_dataset.py`](./dataset/validate_dataset.py) verifying syntax, ChatML roles, and token counts.
