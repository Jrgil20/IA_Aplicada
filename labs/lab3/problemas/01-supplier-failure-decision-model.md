# Problem 1: Supplier Failure Definition & Meeting Selection

> **Deliverable:** `salidas/1-reunion-proveedores.html`  
> **Documentation:** `salidas/criterio-problema-1.md`  
> **Status:** Empirically Validated & Delivered

---

## 1. Business Problem Context
The Procurement Director needed an objective, data-backed criterion to define what constitutes a "failing supplier" and determine which supplier should be called first to open renegotiation discussions.

---

## 2. Decision Model & Weighted Scoring Formula
To balance acute financial exposure with chronic operational delays, a weighted composite index was formulated:

$$\text{Composite Score} = (S_{\text{usd}} \times 0.60) + (S_{\text{delay}} \times 0.25) + (S_{\text{hist}} \times 0.15)$$

Where:
- $S_{\text{usd}}$: Normalized active overdue amount (USD) relative to total overdue debt.
- $S_{\text{delay}}$: Normalized maximum delay days among currently pending orders.
- $S_{\text{hist}}$: Normalized penalty based on historical late delivery count in 2026.

---

## 3. Empirical Supplier Ranking

| Rank | Supplier Code | Supplier Name | Active Overdue Debt (USD) | Overdue Orders Ratio | Max Delay Days | 2026 Historical Delays | Composite Score | Action / Decision |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **P04** | **Importadora Margarita** | **$44,978.06** | **4 / 4 (100%)** | **38 days** | **14** | **92.5** | **OPEN MEETING WITH P04 (Primary Target)** |
| 2 | P06 | Tecnología Zulia | $20,281.22 | 4 / 6 (66.7%) | 35 days | 9 | 49.8 | Secondary priority |
| 3 | P01 | Distribuidora Andina | $7,510.67 | 6 / 7 (85.7%) | 50 days | 12 | 47.0 | Critical delay outlier (50d) |
| 4 | P05 | Papelera Los Llanos | $25,254.81 | 2 / 4 (50.0%) | 10 days | 8 | 46.2 | High volume leverage review |
| 5 | P02 | Logística del Ávila | $4,770.75 | 5 / 6 (83.3%) | 30 days | 7 | 28.9 | Operational monitoring |
| 6 | P03 | Suministros Caroní | $1,220.40 | 1 / 2 (50.0%) | 3 days | 3 | 11.4 | Negligible exposure |

---

## 4. Key Takeaways for Demonstration
- P04 alone concentrates **43.2%** of all active overdue debt across the organization ($44,978.06 out of $104k).
- Every single pending order of P04 is overdue (100% failure rate).
- P04 is the single worst historical offender in the dataset with 14 late deliveries.
- Complete visual dashboard rendered standalone without CDN dependencies in `salidas/1-reunion-proveedores.html`.
