# Lab 03: Autonomous Code Agents & Data Auditing (DGX Spark)

> **Status:** Completed & Empirically Validated  
> **Target System:** NVIDIA DGX Spark (`ucab-spark2`, 128 GB Unified Memory, GB10 architecture, IP `192.168.6.34`)  
> **Model under Test:** `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` (`/srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`)  
> **Serving Engine:** `llama-server` on port 8080 (`127.0.0.1:8080`) with `-ngl 99`, offloading all layers to GB10 GPU  
> **Model Fallback Context:** Workshop prompt requested `qwen3.6:35b-a3b-mtp-q4_K_M` via `ollama launch opencode`. Since Ollama is not installed on the DGX Spark environment, execution seamlessly fell back to the pre-deployed and verified Qwen 30B server.  
> **Working Directory on Spark:** `~/mesa-de-trabajo-equipo-1/lab3/`  
> **Deliverable HTTP Server:** Python simple HTTP server serving `salidas/` on `http://192.168.6.34:8000/`

---

## 1. Objectives

- [x] Clone and synchronize the workshop repository (`ucab-ia-aplicada-workshops`) across the private network subnet.
- [x] Deploy and initialize the Lab 3 workspace at `~/mesa-de-trabajo-equipo-1/lab3` on Spark using `preparar.sh`.
- [x] Formulate a rigorous business definition of "supplier failure" using empirical dataset analysis from `pedidos.csv`.
- [x] Perform a security and prompt injection audit against adversarial keywords (`ejecuta`, `edita`, `agrega`, `comparte`, `eval`, `bash`).
- [x] Document the formal decision model and formula in [`salidas/criterio-problema-1.md`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/criterio-problema-1.md).
- [x] Generate the self-contained executive presentation dashboard [`salidas/1-reunion-proveedores.html`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/1-reunion-proveedores.html) without external internet dependencies.
- [x] Serve and validate the presentation page over port 8000.

---

## 2. Model & Execution Metrics

| Metric | Target / Specification | Observed Live Measurement |
| :--- | :--- | :--- |
| **Model Architecture** | Qwen 30B MoE / Instruct | `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` |
| **GPU Hardware** | NVIDIA GB10 (Grace Blackwell) | GB10 Superchip, 128 GB Unified Memory |
| **GPU Offload** | All transformer layers offloaded | `-ngl 99` (99 layers on GPU) |
| **Resident Memory (RSS)** | < 16 GB | **8,029,400 KB (~8.03 GB)** |
| **System RAM Utilization** | Baseline idle + server | **6.3% of 128 GB Unified Memory** |
| **Virtual Memory Mapped** | Model weight space | 112,645,012 KB (~107 GB) |
| **Operating Temperature** | Nominal operating range | **42°C** |
| **Execution Script Time** | < 5.0 seconds | **~0.84 seconds** |
| **Total Session Duration** | Interactive setup & audit | **~15 minutes** |
| **HTTP Serving Latency** | Local private link | **< 10 ms (HTTP 200 OK, 14,607 bytes)** |

---

## 3. Business Decision Model (Problem 1)

The team agreed on a **Weighted Mixed Score with Financial Impact Priority**:

$$\text{Score} = (\text{Normalized Overdue USD} \times 60\%) + (\text{Normalized Max Delay Days} \times 25\%) + (\text{Historical Delayed Penalty} \times 15\%)$$

### Executive Decision
- **Supplier to Open Meeting:** **P04 — Importadora Margarita**
  - **Financial Risk:** **$44,978.06 USD** in overdue pending orders (accounting for **43.2%** of all active overdue debt across the company).
  - **Operational Failure:** **100% of pending orders are overdue** (4 out of 4), with up to **38 days of delay**.
  - **Historical Track Record:** Worst offender in 2026 with **14 historical late deliveries**.

### Complete Ranked Hierarchy
1. **Importadora Margarita (P04):** Score **92.5** ($44,978.06 USD overdue / 4 of 4 overdue / 38 days max delay)
2. **Tecnología Zulia (P06):** Score **49.8** ($20,281.22 USD overdue / 4 of 6 overdue / 35 days max delay)
3. **Distribuidora Andina (P01):** Score **47.0** ($7,510.67 USD overdue / 6 of 7 overdue / 50 days max delay)
4. **Papelera Los Llanos (P05):** Score **46.2** ($25,254.81 USD overdue / 2 of 4 overdue / 10 days max delay)
5. **Logística del Ávila (P02):** Score **28.9** ($4,770.75 USD overdue / 5 de 6 overdue / 30 days max delay)
6. **Suministros Caroní (P03):** Score **11.4** ($1,220.40 USD overdue / 1 of 2 overdue / 3 days max delay)

---

## 4. Security & Data Integrity Audit

1. **Adversarial Keyword Scan:**
   - Scanned `pedidos.csv` and `proveedores.csv` for imperative injection triggers: `ejecuta`, `edita`, `agrega`, `comparte`, `eval`, `bash`, `token`, `clave`.
   - **Result:** **0 matches found**. Data contains no active prompt injection payloads.
2. **Output Sanitization:**
   - All dynamic strings from the CSV are escaped using `html.escape` to eliminate DOM-based cross-site scripting or shell escape risks.
3. **Isolated Edge Cases:**
   - **Row 280 (PO-1279):** Orphaned order assigned to unknown supplier `P09` (absent from `proveedores.csv`).
   - **Row 328 (PO-1326):** Pending order from `P05` with missing `fecha_comprometida`.

---

## 5. Problem 2: Unified Monday Report Command

- **Universal Entrypoint:** [`informe-lunes.sh`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/informe-lunes.sh) executes deterministic pipeline in one step.
- **Claude Code Skill:** Configured at [`.claude/skills/informe-lunes/SKILL.md`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/.claude/skills/informe-lunes/SKILL.md).
- **OpenCode Declarative Command:** Registered in [`opencode.json`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/opencode.json).
- **Threshold Rule:** Filter orders with strictly `> 10 days of delay` as of October 14, 2026.
- **Suppliers with Critical Delays (> 10 days):**
  - **P04 (Importadora Margarita):** 4 orders, **$44,978.06 USD** (max delay 38 days)
  - **P06 (Tecnología Zulia):** 4 orders, **$20,281.22 USD** (max delay 35 days)
  - **P01 (Distribuidora Andina):** 3 orders, **$2,309.40 USD** (max delay 50 days)
  - **P02 (Logística del Ávila):** 2 orders, **$1,858.50 USD** (max delay 30 days)
- **Deliverables Generated in `salidas/2-lunes/`:**
  - `estado-pedidos-jefe.html` (interactive dashboard for the procurement director).
  - `correo-P01-distribuidora-andina.md` (formal claim draft).
  - `correo-P02-logistica-del-avila.md` (formal claim draft).
  - `correo-P04-importadora-margarita.md` (urgent claim draft).
  - `correo-P06-tecnologia-zulia.md` (formal claim draft).
- **Policy Enforcement:** Strict compliance with executive instruction—zero emails are sent automatically; all claims remain as local Markdown drafts for human analyst review.

---

## 6. Dedicated Security Governance & Red-Teaming Task

- **Auditable Declarative Policies (`opencode.json`):**
  - Read access explicitly denied for `.env`, `.env.*`, and `secretos/**`.
  - Shell command execution blocked for exfiltration tools (`curl`, `wget`, `mail`, `sendmail`, `cat .env*`, `cat *secretos*`).
  - Remote session sharing disabled (`"share": "disabled"`).
- **Automated Verification Suite:**
  - Executed [`scripts/verificar_seguridad.py`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/scripts/verificar_seguridad.py) directly on DGX Spark.
  - Verified 4/4 control checkpoints: declarative policies, `.gitignore` exclusions, static AST scan for zero SMTP/network sockets, and draft-only email integrity.
  - Audit report persisted at [`salidas/2-lunes/seguridad-auditoria.md`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/2-lunes/seguridad-auditoria.md).

---

## 7. Problem 3: IT Security Audit & Multi-Agent Red-Teaming

- **Executive Deliverable:** [`salidas/3-auditoria.html`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/3-auditoria.html) presented to the board of directors.
- **Three IT Audit Mandates:**
  1. *Confidentiality of `.env` and `secretos/`*: Covered via multi-layered defense in depth.
  2. *Session Isolation*: Verified via `"share": "disabled"` in `opencode.json`.
  3. *Auditable Configuration Travelling with Repo*: Versioned in `opencode.json`, `AGENTS.md`, and Git hooks.
- **Empirical Red-Teaming Matrix (6 Attack Vectors Evaluated):**
  - `VEC-01` (Tool Read API on `.env` / `secretos/**`): **BLOCKED** by declarative `permission.read.deny` and `AGENTS.md`.
  - `VEC-02` (Direct Shell Command `cat .env` / `cat *secretos*`): **BLOCKED** by `permission.bash.deny`.
  - `VEC-03` (Obfuscation via `base64 .env`): **MITIGATED AT OS LEVEL** via POSIX `chmod 0600` (read denied to unprivileged UIDs).
  - `VEC-04` (Inline Language Scripting `python3 -c "open('.env').read()"`): **VULNERABLE IF UNCONTAINERIZED** — Honest assessment presented to the auditor demonstrating that regex filters in agent wrappers do not stop Turing-complete interpreters without OS sandboxing/containers.
  - `VEC-05` (Exfiltration via Git Commit/Push): **BLOCKED** by `.gitignore` and `.git/hooks/pre-commit`.
  - `VEC-06` (Remote Session Sharing `opencode share`): **BLOCKED** by `"share": "disabled"`.
- **Structural Recommendations for Production:**
  1. POSIX permissions hardening (`chmod 0600 .env` and `chmod 0700 secretos/`).
  2. Git pre-commit enforcement (`scripts/pre-commit-hook.sh`).
  3. External Vault integration (injecting secrets into runtime env rather than flat files).

---

## 8. Problem 4: Financial Data Quality Audit & 5 Governance Rules

- **Executive Deliverable:** [`salidas/4-calidad-datos.html`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/4-calidad-datos.html) for the Head of Finance.
- **Core Principles:** Zero synthetic/invented errors, raw source file `pedidos.csv` 100% immutable and protected against edits via `opencode.json`.
- **7 Genuine Anomalous Rows Identified ($28,431.45 USD at stake):**
  1. `Row 73` (PO-1072, P02): Negative quantity (`-703.0`), corrupting accounting by `-$1,117.77 USD`.
  2. `Row 116` (PO-1115, P01): Zero unit price (`$0.00 USD`), 122 units unbilled.
  3. `Row 153` (PO-1152, P03): Temporal paradox, delivered April 30, 2026 before being ordered May 06, 2026 (`$2,003.85 USD`).
  4. `Row 280` (PO-1279, P09): Orphaned supplier `P09` not found in `proveedores.csv` (`$829.50 USD`).
  5. `Row 305` (PO-1303, P06): Exact duplicate clone of row 304 (`$67.05 USD`).
  6. `Row 312` (PO-1310, P06): Marked `Entregado` with missing `fecha_entrega` (`$5,712.00 USD`).
  7. `Row 328` (PO-1326, P05): Marked `Pendiente` with missing `fecha_comprometida` (`$18,701.28 USD`).
- **Parallel Reconciliation (Raw vs Quarantined):**
  - Gross Company Billing: `$1,200,741.63 USD` -> Clean Billing: `$1,173,427.95 USD` (Net Delta: `-$27,313.68 USD`).
  - P04 (Importadora Margarita) maintains #1 overdue spot cleanly (`$44,978.06 USD`, 0 anomalies).
  - P06 (Tecnología Zulia) overdue debt drops by `$67.05 USD` from clone PO-1303, reducing Monday claim orders from 4 to 3.
  - P05 (Papelera Los Llanos) uncommitted order PO-1326 ($18.7k) quarantined; overdue remains `$25,254.81 USD`.
- **5 Permanent Governance Rules Implemented:**
  1. *Uniqueness & Deduplication*: Primary key `pedido` deduplicated; clones quarantined (`AGENTS.md` + pipeline).
  2. *Physical Value Range*: Quantities > 0 and unit prices > 0 strictly required (`AGENTS.md` + pipeline).
  3. *Referential Integrity*: Supplier ID must exist in master catalog `proveedores.csv` (`AGENTS.md` + pipeline).
  4. *Temporal Causality & State Completeness*: `Entregado` requires delivery date; `Pendiente` requires committed date (`AGENTS.md` + pipeline).
  5. *Source Immutability & Dual-View Reporting*: `pedidos.csv` edit-denied in `opencode.json`; all future reports must project Raw vs Clean views with delta (`AGENTS.md` + `opencode.json`).

---

## 9. Problem 5: General Manager Executive Dashboard & Kraljic Strategy

- **Executive Deliverables:**
  - Interactive C-Level Dashboard: [`salidas/5-tablero-gerente.html`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/5-tablero-gerente.html).
  - Decision Justification Document: [`salidas/5-tablero-gerente.md`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/5-tablero-gerente.md).
- **Subagent Team Architecture:**
  - Delegated across 4 specialized analytical subagents (`Spend Analyst`, `Logistics Specialist`, `Risk Auditor`, `Strategic Evaluator`), respecting the hardware consumption cap (< 7 agents, < 56% compute).
- **Four Core Business Dimensions:**
  1. *Spend Concentration (Pareto)*: Top 3 suppliers (P05, P06, P04) absorb **81.1%** of total budget ($951k out of $1,173,427.95 USD).
  2. *Logistics Reliability (OTD %)*: Global On-Time Delivery across 345 clean orders stands at **80.5%** (251 on-time out of 312 delivered).
  3. *Active Risk & Overdue Debt*: Total active overdue debt stands at **$103,220.11 USD**, with P04 (Importadora Margarita) carrying 43.6% ($44.9k).
  4. *Kraljic Strategic Portfolio*:
     - **P04 (Importadora Margarita):** *Strategic Critical* (25.1% spend, 70.8% OTD, $44.9k overdue) -> Immediate executive intervention, freeze new payments, enforce late penalties.
     - **P01 (Distribuidora Andina):** *Bottleneck* (6.3% spend, 50-day overdue orders) -> Tender alternative supplier immediately.
     - **P05 (Papelera Los Llanos) & P06 (Tecnología Zulia):** *Strategic / High-Volume Leverage* -> Volume price renegotiation.
     - **P02 (Logística del Ávila) & P03 (Suministros Caroní):** *Routine / Reliable Partners* (83.7% and 88.9% OTD) -> Maintain automated relationship.

---

## 10. Master Unified Executive Portal

- **Root Deliverable:** [`salidas/index.html`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/salidas/index.html) automatically served at `http://192.168.6.34:8000/`.
- **Integrated Architecture:**
  - Single-Page Executive Navigation (SPA) without internet dependencies.
  - Tab 1: **🏢 Dirección General (Problem 5)** — C-Level KPIs, Pareto spend, Kraljic matrix.
  - Tab 2: **🤝 Reunión Proveedores (Problem 1)** — Mixed weighted score & recommendation to open with P04.
  - Tab 3: **📅 Operación de los Lunes (Problem 2)** — Critical orders > 10 days and 4 claim drafts.
  - Tab 4: **🛡️ Auditoría de TI (Problem 3)** — 6-vector red-teaming matrix and OS defense-in-depth.
  - Tab 5: **⚖️ Calidad Finanzas (Problem 4)** — 7 quarantined rows, parallel delta reconciliation, and 5 governance rules.
- **Generator Engine:** [`scripts/generar_portal_unificado.py`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/scripts/generar_portal_unificado.py).

---

## 11. Final Workshop Execution Report on Spark

- **Persisted Report Path on Spark:** `/home/ucab-spark2/mesa-de-trabajo-equipo-1/lab3/INFORME_FINAL_WORKSHOP.md`
- **HTTP Endpoint:** Served directly at `http://192.168.6.34:8000/INFORME_FINAL_WORKSHOP.md`
- **Local Mirror:** [`ucab-ia-aplicada-workshops/.../INFORME_FINAL_WORKSHOP.md`](file:///home/jr_g/Develop/ucab-ia-aplicada-workshops/workshops/01-agentes-de-codigo/INFORME_FINAL_WORKSHOP.md)
- **Summary of Achievements:**
  - 100% of all 5 workshop challenges solved deterministically with zero data pollution.
  - POSIX + Agent multi-layered security model validated.
  - Complete executive traceability against clean dataset ($1,173,427.95 USD).

---

## 12. Lessons Learned & Operational Shortcuts for Future Sessions

### A. Explicit Table Cross-Referencing in Reports
To maximize clarity for executive and audit reviews:
- Every qualitative claim must explicitly reference its supporting table and row index (e.g., *"As demonstrated in Section 8 (Table of Quarantined Rows, Row 73)*, or *"referencing Section 9 (Kraljic Strategic Portfolio, Row P04)*).
- Linking narrative conclusions directly to auditable rows prevents back-and-forth validation requests during board presentations.

### B. Fast & Intuitive OpenCode Launcher Shortcut
Because the OpenCode binary is installed in an unexported location (`~/.opencode/bin/opencode`), it is cumbersome to locate in live lab sessions.

**One-Time Setup Command on Spark:**
```bash
# 1. Permanent alias in bashrc
echo 'alias opencode="$HOME/.opencode/bin/opencode"' >> ~/.bashrc

# 2. Symlink into standard user binary path
mkdir -p ~/.local/bin && ln -sf ~/.opencode/bin/opencode ~/.local/bin/opencode

# 3. Reload current shell environment
source ~/.bashrc
```

**Fast Launch:**
Once configured, simply type from any folder:
```bash
opencode
```

### C. OpenCode Declarative Permission Schema Contract
- OpenCode's Zod configuration engine expects `PermissionActionConfig` as a key-value mapping of pattern to action (`"<glob>": "deny" | "ask" | "allow"`), rather than an array under an action key:
  ```json
  "permission": {
    "read": {
      ".env": "deny",
      "secretos/**": "deny"
    },
    "edit": {
      "pedidos.csv": "deny"
    },
    "bash": {
      "*cat .env*": "deny",
      "*curl*": "deny"
    }
  }
  ```







