# Project Idea Bank

Record of ideas explored, discarded, and selected for the course project.

---

## 1. Selected Idea: Edge Clean Copilot

- **Concept:** SLM (1.5B–3B) specialized via LoRA to enforce strict Clean Architecture rules and BDD test suites (Arrange-Act-Assert) locally (GGUF).
- **Rationale:** Addresses a real pain point in software engineering (coupling and abstraction leaks caused by commercial copilots) with high technical feasibility, leveraging the DGX Spark and local execution on modest hardware.
- **Full Details:** See [Technical Proposal](./propuesta.md).

---

## 2. Evaluated Alternative Ideas

### A. Software Architecture Specialized RAG
- **Concept:** Retrieval-Augmented Generation system over formal architecture documentation (GoF patterns, Clean Code, DDD) with a local vector store.
- **Trade-off:** Relies on runtime retrieval and general-purpose models; does not internalize patterns within the model weights.

### B. Lightweight Model-Assisted Linters
- **Concept:** Static analysis agent that evaluates commits before merging in a pre-push hook.
- **Trade-off:** Can be integrated in the future as a client for the specialized SLM.
