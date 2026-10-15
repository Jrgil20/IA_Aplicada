# Problem 5: General Manager C-Level Dashboard & Kraljic Strategic Matrix

> **Executive Dashboard:** `salidas/5-tablero-gerente.html`  
> **Strategic Justification:** `salidas/5-tablero-gerente.md`  
> **Master Portal Integration:** Tab 1 of `salidas/index.html` (`http://192.168.6.34:8000/`)  
> **Status:** Empirically Validated & Delivered

---

## 1. Business Problem Context
The General Manager requested a strategic C-level dashboard providing high-level business intelligence across 4 dimensions:
1. **Budget & Spend Concentration (Pareto Principle)**.
2. **Logistics Reliability (On-Time Delivery %)**.
3. **Active Exposure & Overdue Debt**.
4. **Strategic Supplier Portfolio Classification (Kraljic Matrix)**.

---

## 2. Multi-Agent Analytical Architecture
To avoid overloading compute and context window on DGX Spark, the analysis was distributed across 4 specialized subagents:
- **Spend Analyst:** Audited total clean billing ($1,173,427.95 USD) and computed Pareto cumulative percentages.
- **Logistics Specialist:** Calculated lead times, on-time delivery rates (OTD %), and maximum delay days.
- **Risk Auditor:** Isolated active debt ($103,220.11 USD) and evaluated chronic vs acute risk profiles.
- **Strategic Evaluator:** Mapped each supplier to the 4 quadrants of the Kraljic portfolio matrix.

---

## 3. Four Core Business Dimensions

### Dimension 1: Spend Concentration (Pareto 80/20)
- Top 3 suppliers absorb **81.1%** of total procurement capital:
  1. **P05 (Papelera Los Llanos):** $374,251.05 USD (31.9%)
  2. **P06 (Tecnología Zulia):** $282,752.48 USD (24.1%)
  3. **P04 (Importadora Margarita):** $294,364.55 USD (25.1%)
- Remaining 3 suppliers share only **18.9%** ($222,059.87 USD).

### Dimension 2: Logistics Reliability (OTD %)
- Global On-Time Delivery across 312 delivered orders: **80.5%** (251 on-time, 61 delayed).
- Best Logistics Partner: **P03 (Suministros Caroní)** at **88.9% OTD**.
- Worst Logistics Partner: **P04 (Importadora Margarita)** at **70.8% OTD**.

### Dimension 3: Active Financial Risk
- Total overdue debt across company: **$103,220.11 USD**.
- **P04** carries **$44,978.06 USD** (43.6% of active overdue exposure).

---

## 4. Kraljic Strategic Portfolio Matrix

```
                      High Profit Impact (Spend)
                                  ▲
                                  │
          LEVERAGE                │            STRATEGIC
    [ P05 Papelera Los Llanos ]   │   [ P04 Importadora Margarita ]
    [ P06 Tecnología Zulia ]      │   - 25.1% spend, 70.8% OTD
    - High spend, lower risk      │   - $44.9k overdue debt
    - Action: Renegotiate volume  │   - Action: Executive intervention,
              pricing & rebates   │             enforce penalties
                                  │
  ────────────────────────────────┼────────────────────────────────► Supply Risk
                                  │
          ROUTINE                 │            BOTTLENECK
    [ P02 Logística del Ávila ]   │   [ P01 Distribuidora Andina ]
    [ P03 Suministros Caroní ]    │   - Low spend (6.3%), high risk
    - Low spend, high reliability │   - Outlier 50-day overdue orders
    - Action: Automate purchase   │   - Action: Tender alternative
              orders & simplify   │             qualified vendors
                                  │
```

---

## 5. C-Level Executive Directives
1. **P04 (Importadora Margarita):** Freeze new purchase orders until overdue backlog is resolved; apply contractual late-delivery penalties.
2. **P01 (Distribuidora Andina):** Issue RFPs immediately to replace them due to chronic 50-day delivery bottlenecks.
3. **P05 & P06:** Consolidate volume contracts to negotiate a 3% to 5% corporate discount.
