# Problem 2: Weekly Operations (Monday Routine) & Supplier Claims

> **Universal Entrypoint:** `./informe-lunes.sh`  
> **OpenCode Slash Command:** `/informe-lunes` (via `opencode.json`)  
> **Claude Code Skill:** `.claude/skills/informe-lunes/SKILL.md`  
> **Deliverable Folder:** `salidas/2-lunes/`  
> **Status:** Empirically Validated & Delivered

---

## 1. Business Problem Context
Every Monday, the Procurement team needed a single automated command to:
1. Identify all supplier orders with critical delays (**strictly > 10 days of delay** as of the reference date: October 14, 2026).
2. Generate an executive dashboard for the Procurement Director (`estado-pedidos-jefe.html`).
3. Prepare customized formal claim letters for each delinquent supplier.
4. **Strict Safety Policy:** No emails are to be sent automatically; all claims must remain as local Markdown drafts for manual review by human buyers.

---

## 2. Threshold Filtering (> 10 Days Delay)

| Supplier Code | Supplier Name | Critical Delayed Orders (> 10d) | Total Value in Moratorium (USD) | Maximum Delay Recorded | Claim Document Generated |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **P04** | Importadora Margarita | 4 orders | **$44,978.06** | 38 days | `salidas/2-lunes/correo-P04-importadora-margarita.md` |
| **P06** | Tecnología Zulia | 4 orders (pre-clean) / 3 (post-clean) | **$20,281.22** | 35 days | `salidas/2-lunes/correo-P06-tecnologia-zulia.md` |
| **P01** | Distribuidora Andina | 3 orders | **$2,309.40** | 50 days | `salidas/2-lunes/correo-P01-distribuidora-andina.md` |
| **P02** | Logística del Ávila | 2 orders | **$1,858.50** | 30 days | `salidas/2-lunes/correo-P02-logistica-del-avila.md` |

*Note: P03 and P05 had zero pending orders exceeding 10 days of delay as of October 14, 2026, and were excluded from claim dispatch.*

---

## 3. Architecture of `informe-lunes.sh`

The script executes 4 deterministic stages:
```bash
#!/usr/bin/env bash
# 1. Security Check
python3 scripts/verificar_seguridad.py

# 2. Data Quality & Quarantine
python3 scripts/validar_calidad_datos.py

# 3. Business Analysis & Monday Outputs
python3 scripts/generar_informe_lunes.py

# 4. Deliverable Verification
ls -lh salidas/2-lunes/
```

---

## 4. Safety & Policy Verification
An AST scanner in `verificar_seguridad.py` verifies that:
- Zero SMTP client sockets or email transmission functions (`smtplib`, `sendmail`, `mail`, `curl`) are called.
- All email outputs are strictly formatted as `.md` files in `salidas/2-lunes/`.
- No modification of `pedidos.csv` occurs during execution.
