# Problem 4: Financial Data Quality Audit & 5 Governance Rules

> **Deliverable:** `salidas/4-calidad-datos.html`  
> **Sanitization Script:** `scripts/validar_calidad_datos.py`  
> **Source Data Protection:** `opencode.json` (`permission.edit.deny` for `pedidos.csv`)  
> **Status:** Empirically Validated & Delivered

---

## 1. Business Problem Context
The Head of Finance discovered discrepancies in total invoice billing and required a forensic data audit of `pedidos.csv`.
- **Core Requirement:** The raw source file `pedidos.csv` must remain 100% immutable.
- Errors must never be synthesized or invented; all anomalies must be empirically isolated into quarantine.
- Dual-view reporting (Raw vs Clean reconciliation) must be provided with exact financial delta calculations.

---

## 2. Forensic Analysis: 7 Quarantined Anomalous Rows

Total financial amount at risk across 7 anomalous entries: **$28,431.45 USD**.

| Row # | Order ID | Supplier | Category of Anomaly | Exact Error Description | Financial Impact (USD) | Action Taken |
| :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **73** | PO-1072 | P02 | Negative Quantity | `cantidad = -703.0` | **-$1,117.77** | Quarantined. Corrupted ledger by subtracting revenue. |
| **116** | PO-1115 | P01 | Zero Unit Price | `precio_unitario = 0.0` | **$0.00** (122 units) | Quarantined. 122 physical units unbilled. |
| **153** | PO-1152 | P03 | Temporal Paradox | Delivered `2026-04-30` before ordered `2026-05-06` | **$2,003.85** | Quarantined. Chronological causality violation. |
| **280** | PO-1279 | P09 | Referential Orphan | Supplier `P09` missing from `proveedores.csv` | **$829.50** | Quarantined. Foreign key referential violation. |
| **305** | PO-1303 | P06 | Exact Duplicate | Identical duplicate clone of Row 304 | **$67.05** | Quarantined. Primary key duplicate billing. |
| **312** | PO-1310 | P06 | Incomplete State | Status `Entregado` but `fecha_entrega` is NULL | **$5,712.00** | Quarantined. Cannot calculate lead time / on-time delivery. |
| **328** | PO-1326 | P05 | Incomplete State | Status `Pendiente` but `fecha_comprometida` is NULL | **$18,701.28** | Quarantined. Cannot calculate delay days or overdue debt. |

---

## 3. Financial Reconciliation (Raw vs Clean)

| Metric | Raw Dataset (352 rows) | Clean Dataset (345 rows) | Net Delta / Variance | Audit Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Total Company Spend** | $1,200,741.63 USD | **$1,173,427.95 USD** | **-$27,313.68 USD** | Negative quantity and uncommitted orders adjusted. |
| **Total Delivered Orders** | 314 orders | **312 orders** | -2 orders | Row 153 (paradox) and Row 312 (null delivery) quarantined. |
| **P04 (Margarita) Overdue** | $44,978.06 USD | **$44,978.06 USD** | **$0.00** | Zero data defects in P04. #1 status reinforced. |
| **P06 (Zulia) Overdue** | $20,281.22 USD | **$20,214.17 USD** | **-$67.05 USD** | Clone PO-1303 removed. Monday claim orders drop from 4 to 3. |
| **P05 (Los Llanos) Overdue**| $25,254.81 USD | **$25,254.81 USD** | **$0.00** | Order PO-1326 ($18.7k) had no promised date; overdue unchanged. |

---

## 4. Five Permanent Data Governance Rules
1. **Uniqueness & Primary Key Integrity:** Order IDs (`pedido`) must be unique across the ledger; duplicate records are quarantined immediately.
2. **Physical Value Range Validation:** Quantities and unit prices must be strictly positive real numbers ($> 0$).
3. **Foreign Key Referential Integrity:** Every order's supplier ID must exist within the master catalog `proveedores.csv`.
4. **Temporal Causality & State Completeness:**
   - Any order marked `Entregado` requires a valid `fecha_entrega >= fecha_pedido`.
   - Any order marked `Pendiente` requires a valid `fecha_comprometida >= fecha_pedido`.
5. **Source Immutability & Dual-View Reporting:** Raw transactional logs are read-only (`permission.edit.deny`). All downstream analytics must present Raw vs Clean reconciliations.
