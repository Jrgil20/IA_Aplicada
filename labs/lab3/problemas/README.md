# Lab 03 Problems & Technical Incidents Registry

> **Target Environment:** NVIDIA DGX Spark (`ucab-spark2`, 128 GB Unified Memory, IP `192.168.6.34`)  
> **Source Workspace:** `~/mesa-de-trabajo-equipo-1/lab3/`  
> **Index Scope:** Detailed registry of the 5 workshop business challenges, empirical solutions, data governance rules, and technical incident post-mortems encountered during Lab 3.

---

## 1. Workshop Problem Statements & Solutions

| Problem | Domain | Key Objective | Primary Deliverable | Status |
| :--- | :--- | :--- | :--- | :--- |
| **[Problem 1](./01-supplier-failure-decision-model.md)** | Procurement & Strategy | Formulate empirical failure metric; select meeting opening supplier (P04). | `salidas/1-reunion-proveedores.html` | Completed |
| **[Problem 2](./02-monday-operations-and-claims.md)** | Operations Automation | Weekly pipeline for overdue orders > 10 days; draft claim letters. | `salidas/2-lunes/estado-pedidos-jefe.html` | Completed |
| **[Problem 3](./03-it-security-and-red-teaming.md)** | IT Security & Governance | Multi-agent sandbox hardening; evaluate 6 adversarial attack vectors. | `salidas/3-auditoria.html` | Completed |
| **[Problem 4](./04-financial-data-quality-governance.md)** | Financial Integrity | Quarantine 7 anomalous rows ($28.4k); formulate 5 permanent governance rules. | `salidas/4-calidad-datos.html` | Completed |
| **[Problem 5](./05-general-manager-kraljic-dashboard.md)** | C-Level Executive Dashboard | Kraljic matrix portfolio classification; Pareto spend & OTD analysis. | `salidas/5-tablero-gerente.html` | Completed |
| **[Problem 7](./07-asistente-consultas-ejecutivas.md)** | AI Assistant & Grounding | Interactive query bar with 3-strike guardrails backed by local LLM. | `scripts/servidor_asistente.py` | Completed |

---

## 2. Technical Incidents & Operational Gotchas

| Incident | Root Cause | Impact | Resolution Documented |
| :--- | :--- | :--- | :--- |
| **SSH PATH Visibility** | `~/.opencode/bin` unexported in SSH sessions. | `opencode: command not found` | Symlink to `~/.local/bin` and export in `.bashrc`. |
| **Working Directory Context** | OpenCode launched from `~` instead of project directory. | Custom slash commands (`/informe-lunes`) missing. | Ensure `cd ~/mesa-de-trabajo-equipo-1/lab3` before launch. |
| **Model Runtime Fallback** | Workshop requested Ollama; DGX Spark uses `llama-server`. | Model unavailable if using default Ollama commands. | Seamless fallback to Qwen3-Coder-30B on port 8080. |
| **Permission Schema Syntax** | Zod schema expects key-value map, not arrays under action keys. | OpenCode config load failure. | Key-value mapping: `"<pattern>": "deny"`. |
| **See Full Technical Log** | — | — | **[Technical Incidents & Fixes](./06-technical-incidents-and-fixes.md)** |
