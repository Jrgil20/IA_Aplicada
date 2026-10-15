# Lab 03: Autonomous Code Agents, Security Governance & Data Auditing

> **Target Environment:** NVIDIA DGX Spark (`ucab-spark2`, 128 GB Unified Memory, IP `192.168.6.34`)  
> **Working Directory on Spark:** `~/mesa-de-trabajo-equipo-1/lab3/`  
> **LLM Engine:** `llama-server` on `127.0.0.1:8080` (`Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`, `-ngl 99`)  
> **HTTP Dashboard Server:** Python HTTP server on port `8000` (`http://192.168.6.34:8000/`)  
> **Primary Purpose:** Comprehensive live demonstration protocol, SSH troubleshooting, command execution modes, and empirical corrections for Lab 3.

---

## 1. Quick Start & SSH Pre-Flight Checklist

When connecting via SSH (`ssh ucab-spark2@192.168.6.34`), execute the following setup to ensure binary discoverability and project context:

```bash
# 1. Ensure OpenCode binary is in PATH and aliased
mkdir -p ~/.local/bin
ln -sf ~/.opencode/bin/opencode ~/.local/bin/opencode

# 2. Add to shell profile if not already present
grep -q 'opencode' ~/.bashrc || cat << 'EOF' >> ~/.bashrc
export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
alias opencode="$HOME/.opencode/bin/opencode"
EOF
source ~/.bashrc

# 3. Navigate to the authoritative workspace
cd ~/mesa-de-trabajo-equipo-1/lab3

# 4. Verify OpenCode binary and config resolution
which opencode
test -f opencode.json && echo "✓ opencode.json detected in current directory"
```

---

## 2. OpenCode Execution Modes

| Mode | Command | When to Use | Execution Context |
| :--- | :--- | :--- | :--- |
| **Direct Shell** | `./informe-lunes.sh` | Instant demo, zero LLM token cost, determinism. | Native Bash subshell |
| **Non-Interactive CLI (One-Shot)** | `opencode run /informe-lunes` | Scripted SSH pipelines, remote demo without TUI. | OpenCode headless agent |
| **Interactive TUI** | `opencode` then `/informe-lunes` | Live professor inspection, interactive prompt exploration. | OpenCode full terminal UI |

### Mode A: Direct Linux Pipeline (Recommended for Fast Demo)
```bash
cd ~/mesa-de-trabajo-equipo-1/lab3
./informe-lunes.sh
```
Runs the 4-phase sequence:
1. Security & permission verification (`scripts/verificar_seguridad.py`).
2. Data quality quarantine & accounting audit (`scripts/validar_calidad_datos.py`).
3. Business reporting for overdue orders > 10 days (`scripts/generar_informe_lunes.py`).
4. Output verification in `salidas/2-lunes/`.

### Mode B: One-Shot OpenCode Command via SSH
```bash
cd ~/mesa-de-trabajo-equipo-1/lab3
opencode run /informe-lunes
```
OpenCode parses `opencode.json`, activates the declared template, runs the task with agent constraints, and exits cleanly.

### Mode C: Interactive OpenCode Session
```bash
cd ~/mesa-de-trabajo-equipo-1/lab3
opencode
```
Inside the interactive prompt:
- Type `/informe-lunes` to trigger the weekly operations report.
- Slash command auto-completion will display all commands defined in `opencode.json`.

---

## 3. SSH Troubleshooting & Diagnostics Matrix

| Symptom / Error | Root Cause | Immediate Fix |
| :--- | :--- | :--- |
| `bash: opencode: command not found` | `~/.opencode/bin` is not in `$PATH` for the SSH session. | Run `export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"` or execute via absolute path `~/.opencode/bin/opencode`. |
| Custom slash command (e.g. `/informe-lunes`) does not appear in autocomplete. | OpenCode was launched outside `~/mesa-de-trabajo-equipo-1/lab3` (e.g., from `$HOME`). | `cd ~/mesa-de-trabajo-equipo-1/lab3` before running `opencode`. |
| `opencode run: permission error` or invalid schema warning. | Invalid JSON permission format (using array instead of key-value map). | Ensure `opencode.json` follows `"permission": { "action": { "pattern": "deny" } }`. |
| HTTP dashboard unreachable at `http://192.168.6.34:8000/`. | Python HTTP daemon is not running on Spark. | Run `nohup python3 -m http.server 8000 --directory ~/mesa-de-trabajo-equipo-1/lab3/salidas > /tmp/http_server.log 2>&1 &`. |

---

## 4. Live Demonstration Protocol (Problems 1 to 5)

### Problem 1: Supplier Meeting Decision Model
- **Goal:** Justify opening the supplier renegotiation meeting with P04 (Importadora Margarita).
- **Core Formula:**
  $$\text{Score} = (\text{Normalized Overdue USD} \times 0.60) + (\text{Normalized Max Delay Days} \times 0.25) + (\text{Historical Delayed Penalty} \times 0.15)$$
- **Key Evidence:**
  - P04 accounts for **$44,978.06 USD** (43.2% of company-wide active overdue debt).
  - 100% of pending orders overdue (4/4), up to 38 days overdue.
  - Worst historical track record (14 late orders in 2026).
- **Demo Deliverable:** `salidas/1-reunion-proveedores.html` or `salidas/criterio-problema-1.md`.

### Problem 2: Weekly Operations (Monday Report & Claims)
- **Goal:** Filter orders strictly delayed > 10 days as of October 14, 2026 and draft formal claim letters without automated transmission.
- **Suppliers Identified:**
  - P04 ($44,978.06 USD, 4 orders, max delay 38d)
  - P06 ($20,281.22 USD, 4 orders, max delay 35d)
  - P01 ($2,309.40 USD, 3 orders, max delay 50d)
  - P02 ($1,858.50 USD, 2 orders, max delay 30d)
- **Demo Deliverable:** `salidas/2-lunes/estado-pedidos-jefe.html` and draft letters in `salidas/2-lunes/correo-*.md`.

### Problem 3: IT Security Audit & Red-Teaming
- **Goal:** Multi-layered defense demonstrating secret protection (`.env`, `secretos/**`) and immutability of raw CSVs.
- **Verification Script:**
  ```bash
  python3 scripts/verificar_seguridad.py
  ```
- **6 Evaluated Attack Vectors:**
  1. `VEC-01` (Tool Read API): Blocked by `opencode.json` `permission.read.deny`.
  2. `VEC-02` (Shell Command `cat .env`): Blocked by `opencode.json` `permission.bash.deny`.
  3. `VEC-03` (Base64 obfuscation): Mitigated by OS POSIX permissions (`chmod 0600 .env`).
  4. `VEC-04` (Python interpreter inline read): Vulnerable without container/jail; documented as structural recommendation.
  5. `VEC-05` (Git commit exfiltration): Blocked by `.gitignore` and pre-commit hook.
  6. `VEC-06` (Remote session share): Blocked by `"share": "disabled"`.
- **Demo Deliverable:** `salidas/3-auditoria.html` and `salidas/2-lunes/seguridad-auditoria.md`.

### Problem 4: Financial Data Quality & Governance
- **Goal:** Audit raw `pedidos.csv` without modifying source file; isolate anomalies into quarantine.
- **7 Anomalous Rows ($28,431.45 USD at risk):**
  - Row 73 (PO-1072, P02): Negative quantity (`-703.0`).
  - Row 116 (PO-1115, P01): Zero unit price (`$0.00`).
  - Row 153 (PO-1152, P03): Inverted timeline (delivered before order date).
  - Row 280 (PO-1279, P09): Orphaned supplier ID not in `proveedores.csv`.
  - Row 305 (PO-1303, P06): Duplicate clone of row 304.
  - Row 312 (PO-1310, P06): Marked `Entregado` with null `fecha_entrega`.
  - Row 328 (PO-1326, P05): Marked `Pendiente` with null `fecha_comprometida`.
- **Parallel Reconciliation:**
  - Raw Billing: `$1,200,741.63 USD`
  - Clean Billing: `$1,173,427.95 USD` (Net Delta: `-$27,313.68 USD`)
- **Demo Deliverable:** `salidas/4-calidad-datos.html`.

### Problem 5: General Manager C-Level Dashboard & Kraljic Matrix
- **Goal:** Strategic procurement executive overview and supplier portfolio classification.
- **Strategic Highlights:**
  - **Pareto Concentration:** Top 3 suppliers (P05, P06, P04) absorb 81.1% of budget ($951k).
  - **OTD %:** Global On-Time Delivery is 80.5%.
  - **Kraljic Quadrants:**
    - P04: Strategic Critical (intervene immediately, enforce late penalties).
    - P01: Bottleneck (tender alternate supplier due to 50d delay).
    - P05 & P06: High-Volume Leverage (renegotiate volume pricing).
    - P02 & P03: Routine / Reliable Partners (maintain automated workflow).
- **Demo Deliverable:** `salidas/5-tablero-gerente.html` and `salidas/5-tablero-gerente.md`.

---

## 5. Master Unified Executive Portal

The complete laboratory deliverable is centralized in a single responsive web portal:

```bash
# Verify portal generation script
python3 scripts/generar_portal_unificado.py

# Launch HTTP daemon on DGX Spark
nohup python3 -m http.server 8000 --directory salidas > /tmp/http_server.log 2>&1 &

# Verify live HTTP response
curl -I http://127.0.0.1:8000/index.html
```

**Browser Access:** Open `http://192.168.6.34:8000/index.html` from any machine on the lab subnet (`192.168.6.0/24`).

Tabs available in portal:
1. `🏢 Dirección General` (Problem 5: Kraljic & Pareto)
2. `🤝 Reunión Proveedores` (Problem 1: P04 Justification)
3. `📅 Operación de los Lunes` (Problem 2: Claims > 10 Days)
4. `🛡️ Auditoría de TI` (Problem 3: Red-Teaming Matrix)
5. `⚖️ Calidad Finanzas` (Problem 4: Quarantine & Reconciliation)
