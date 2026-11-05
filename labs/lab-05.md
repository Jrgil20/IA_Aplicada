# Lab 05: Preguntarle a los Documentos (RAG Empresarial y Hardening)

> **Status:** Completed & Empirically Validated (Problems 8, 9 & 10)  
> **Target Environment:** Local Workspace & NVIDIA DGX Spark Cluster (`spark-0fbc`, `192.168.6.35`)  
> **Source Workshop:** Workshop 3 (`ucab-ia-aplicada-workshops/workshops/03-preguntarle-a-los-documentos/`)  
> **Simulated Legal Date:** November 5, 2026 (`2026-11-05`)  
> **Company:** Comercial Los Samanes, C.A.  
> **Inference Infrastructure:** `llama-server` (port `8080`, `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`, context `32768`)  
> **Primary Deliverables:**
> - Penalty Calculation Engine & Legal Report: [`labs/lab5/salidas/8-penalidades.html`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/8-penalidades.html) · [`8-auditoria.md`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/8-auditoria.md)
> - Legal QA Evaluation Matrix (100% Accuracy): [`labs/lab5/salidas/9-evaluacion.html`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/9-evaluacion.html) · [`9-evaluacion.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/9-evaluacion.json) · [`9-auditoria.md`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/9-auditoria.md)
> - Hardened Document Assistant Server: [`labs/lab5/asistente/servidor.py`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/asistente/servidor.py) (Running on Spark port `8501`)
> - Model Context Protocol (MCP) Search Engine: [`labs/lab5/asistente/servidor_mcp.py`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/asistente/servidor_mcp.py)
> - OpenCode Multi-Agent Sandbox Configuration: [`labs/lab5/opencode.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/opencode.json)
> - Architectural Decision Report for IT: [`labs/lab5/salidas/10-comparacion.html`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/10-comparacion.html) · [`10-comparacion.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/10-comparacion.json) · [`10-condicion-ti.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/10-condicion-ti.json)

---

## 1. Executive Summary & Problem 8 (Contract Penalties)

Comercial Los Samanes, C.A. faced 15 delayed purchase orders across 6 key suppliers as of November 5, 2026. The legal and procurement departments required a strict, contractual deduction calculation according to active agreements, amendments, and legal notices.

### Key Legal Jurisprudence Applied:
1. **P04 (Importadora Margarita):**
   - Base Contract `CT-2025-P04`: 0.5%/day, 5 days grace, 10% cap.
   - Amendment N.º 1 (`AD-2026-P04-01`, effective July 1, 2026): 1.0%/day, 3 days grace, 15% cap.
   - *Application:* Both delayed orders (`PO-1295` issued Aug 15, and `PO-1324` issued Sep 20) fall under the amendment rules. Total deduction: **$1,675.24 USD**.
2. **P06 (Tecnología Zulia, `PO-1314`):**
   - Due date: September 26, 2026 ($19,206.60 USD). 40 days overdue as of Nov 5, 2026.
   - Supplier claimed customs hold force majeure via email on October 22, 2026.
   - *Legal Dismissal:* Clause 9 mandates written notice within 5 calendar days of occurrence (expired Oct 1, 2026; notification was 21 days late). Furthermore, email was sent to general support instead of `cuentasclave@` (violating Clause 10). Force majeure was rejected. Capped at 6% maximum penalty: **$1,152.40 USD**.
3. **Total Portfolio Penalty:**
   - Evaluated Orders: 15 overdue orders.
   - Total Deductions: **$11,343.33 USD** from pending supplier payments (accounting for exact 0.2%/day rate in CT-2025-P06 Cl. 8).

---

## 2. Problem 9: Hardened Corporate Document Assistant (RAG)

An enterprise retrieval-augmented generation assistant was engineered to serve branches across Caracas, Valencia, Maracaibo, and Barquisimeto over internal network access.

### 2.1 Architecture
- **Lexical Indexer & BM25 Engine (`busqueda.py`):** Parses and indexes 436 markdown documents into 826 semantic chunks (splitting on `##` sections) with domain term weighting and recency boosts.
- **Inference Integration (`llm.py`):** Connects to the local `llama-server` on DGX Spark (port `8080`, `qwen3-coder`).
- **HTTP Server (`servidor.py`):** Pure Python 3 standard library (`ThreadingHTTPServer`), binding to `0.0.0.0:8501` without third-party web frameworks.
- **Air-Gapped Corporate UI (`estaticos/`):** Clean, accessible interface with zero CDN or external web requests. Includes an embedded slide-in drawer for original source document verification.

### 2.2 Security Hardening Enforced (`inference-security-hardening`)
1. **Semantic Isolation:** Document excerpts injected into prompts are strictly bounded within `<untrusted_document_context>` to neutralize indirect prompt injection payloads hidden inside external vendor correspondence.
2. **Strict DOM XSS Defense:** Zero `innerHTML` usage in `app.js`. All dynamic strings, quotes, and citations are rendered using `textContent` and explicit DOM nodes (`createElement`, `appendChild`).
3. **Anti-Hallucination Anchor:** System prompt enforces strict provenance: every claim must cite `[DOC: <id> · <sección>]`. If facts are missing from retrieved fragments (e.g. Q12 supplier headcount), the assistant explicitly outputs `"No está en los documentos de compras."`.
4. **Citation Verification Pipeline:** Server validates that every cited document ID exists in the retrieved context set before transmitting answers to clients.

---

## 3. Legal QA Benchmark Results (`salidas/9-evaluacion.html`)

The assistant was benchmarked against the 12 legal test cases in `preguntas_de_prueba.csv`:

| ID | Test Question Topic | Expected Source | Verdict |
|---|---|---|:---:|
| **Q01** | Suministros Caroní early payment discount | `CT-2025-P03` Cl. 4 | ✅ Pass |
| **Q02** | Margarita late delivery penalty cap | `AD-2026-P04-01` Cl. 1 | ✅ Pass |
| **Q03** | 3-quote policy threshold ($3,000 in 2026) | `POL-COM-2026` Sec. 3 | ✅ Pass |
| **Q04** | Damage claim notification window (3 days) | `PR-ALM-02` Sec. 4.2 | ✅ Pass |
| **Q05** | Approval authority for claims > $10,000 | `PR-COM-03` Sec. 4 | ✅ Pass |
| **Q06** | Supplier response deadline for formal claims (5 days) | `PR-COM-03` Sec. 5 | ✅ Pass |
| **Q07** | P01 delivery reception hours in Valencia (7:30–14:30) | `LP-2026-P01` / emails | ✅ Pass |
| **Q08** | Tecnología Zulia early payment discount (None) | `CT-2025-P06` Cl. 4 | ✅ Pass |
| **Q09** | Minimum performance score for active suppliers (75 pts) | `PR-COM-05` Sec. 5 | ✅ Pass |
| **Q10** | Frequency of provider evaluations (Quarterly) | `PR-COM-05` Sec. 3 | ✅ Pass |
| **Q11** | Lowest scoring provider in Q3 2026 (P05 / 62 pts) | `EV-2026-T3-P05` | ✅ Pass |
| **Q12** | Supplier employee headcount (Out of scope / unrecorded) | Negative baseline | ✅ Pass |

- **Total Score:** **12/12 (100.0% accuracy)**
- **Audit File:** [`labs/lab5/salidas/9-evaluacion.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/salidas/9-evaluacion.json)

---

## 4. Problem 10: Model Context Protocol (MCP) Search Engine vs. Direct Files

To settle whether IT should maintain a dedicated lexical indexer for autonomous agents or allow agents to browse markdown files directly, both architectures were benchmarked across the 12 legal test cases under strict sandbox rules.

### 4.1 IT Security Condition & OpenCode Permissions
IT mandated that during the benchmark, the agent using the MCP tool was strictly forbidden from directly opening or browsing `documentos/`:
- **Modo A (`agente-directo`):** Unrestricted filesystem access using `glob`, `grep`, and `read`.
- **Modo B (`agente-mcp`):** Filesystem access to `documentos/**` explicitly set to `effect: "deny"` in [`labs/lab5/opencode.json`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab5/opencode.json). The agent interacts exclusively through MCP tool `mcp__buscador__buscar_documentos`.

### 4.2 Benchmark Results (`salidas/10-comparacion.html`)

| Metric | Modo A (Direct Files) | Modo B (MCP Search Tool) | Delta / Efficiency |
|---|:---:|:---:|:---:|
| **Legal Accuracy** | 12 / 12 (100.0%) | 12 / 12 (100.0%) | Parity (100% precision) |
| **Average Context per Query** | 24,437 characters | 2,377 characters | **90.3% reduction** |
| **Estimated Context Tokens** | 6,777 tokens | 1,262 tokens | **-81.4% KV cache footprint** |
| **Average Query Latency** | 5.26 seconds | 2.93 seconds | **44.2% faster** (-2.33 s) |
| **Tools Invoked per Turn** | `glob`, `grep`, `read` | `buscar_documentos` | Single deterministic call |

### 4.3 Executive IT Recommendation
**Adopt the MCP Search Server (`asistente/servidor_mcp.py`) as the sole documentary access channel for agents.**
1. **Context Window Preservation:** Slashes prompt size by 90.3%, preventing KV cache saturation and leaving context available for complex reasoning.
2. **Deterministic Governance:** IT gains an audit boundary where document access, queries, and permissions can be centrally logged and restricted.
3. **Latency & Cost:** Nearly 2x faster response times on local edge inference without any sacrifice in legal rigor.

