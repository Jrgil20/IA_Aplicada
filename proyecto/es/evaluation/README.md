# Arnés de Evaluación Automatizado y Benchmark de Arquitectura Limpia

> **Módulo:** Cumplimiento Arquitectónico y Arnés de Evaluación  
> **Modelos Objetivo:** SLM Base (`Qwen-2.5-Coder-1.5B/3B`), Modelo Especializado LoRA y Modelos Comerciales de Referencia  
> **Motor de Ejecución:** Python 3 Puro (Cero dependencias externas)  

Este directorio contiene el arnés de benchmarking automatizado ([`eval_benchmark.py`](../../../proyecto/evaluation/eval_benchmark.py)), diseñado para medir, calificar y demostrar empíricamente la hipótesis central del proyecto **Edge Clean Copilot**.

---

## 1. Fórmula de Verificación de la Hipótesis

$$\text{Puntaje de Arquitectura Limpia (CAS)} = S_{\text{frontera}} + S_{\text{invariantes}} + S_{\text{puertos}} + S_{\text{tipado}}$$

Donde:
- **$S_{\text{frontera}} \in [0, 30]$ (Aislamiento de la Frontera de Dominio):**
  - **30 pts:** Cero imports de bases de datos, ORMs o frameworks web (`express`, `fastapi`, `typeorm`, `prisma`, `axios`, `mongoose`, `pg`, `redis`).
  - **15 pts:** Exactamente 1 import prohibido.
  - **0 pts:** 2 o más imports prohibidos.
- **$S_{\text{invariantes}} \in [0, 25]$ (Seguridad de Invariantes y Patrón Result):**
  - **15 pts:** Uso del tipo de retorno funcional `Result<T, E>` y manejo de `Result.ok` / `Result.fail`.
  - **10 pts:** Validación explícita de invariantes en constructores (`throw new ValidationError` o chequeos de longitud/tipo).
- **$S_{\text{puertos}} \in [0, 25]$ (Desacoplamiento de Puertos y Adaptadores):**
  - **15 pts:** Definición explícita de interfaces de abstracción (`interface I...Repository`, `interface I...Port`, `interface I...Gateway`).
  - **10 pts:** Inyección de dependencias en el constructor (`constructor(private readonly repo: I...Repository)`) o implementación en adaptadores (`implements I...Port`).
- **$S_{\text{tipado}} \in [0, 20]$ (Rigor de Tipos en TypeScript):**
  - Base: **20 pts**.
  - **Penalización:** $-5\text{ pts}$ por cada uso explícito de `any` (`: any`, `<any>`, `as any`).
  - Comentarios y cadenas de texto se eliminan automáticamente antes de la inspección para evitar falsos positivos (e.g. `company`, `many`).
  - Piso mínimo: **0 pts**.

---

## 2. Umbrales de Calificación Cualitativa

| Rango de Puntaje Total | Clasificación Arquitectónica | Descripción |
| :--- | :--- | :--- |
| **85 – 100 pts** | **Grado A (Certificado Clean Architecture)** | Cumple estrictamente la regla de dependencias, invariantes y puertos tipados. |
| **70 – 84 pts** | **Grado B (Parcialmente Limpio)** | Omisión menor (ej. falta interfaz de puerto o un `any` aislado). |
| **50 – 69 pts** | **Grado C (Violaciones de Arquitectura)** | Mezcla lógica de infraestructura con reglas de negocio; excepciones no controladas. |
| **0 – 49 pts** | **Grado F (Antipatrón Acoplado)** | Importa ORMs o frameworks web directamente en entidades de negocio. |

---

## 3. Guía de Ejecución

### 3.1 Evaluación Offline (Lotes JSONL)
Evaluar datasets generados o salidas de modelos sin necesidad de encender un servidor de inferencia:

```bash
python3 eval_benchmark.py --offline test_benchmark_cases.jsonl --output benchmark_report.json
```

### 3.2 Evaluación en Vivo (Endpoints HTTP)
Evaluar respuestas en tiempo real contra un endpoint local o remoto de `llama-server` (ej. puerto 8085 en la DGX Spark):

```bash
python3 eval_benchmark.py \
  --url "http://192.168.6.35:8085/v1/chat/completions" \
  --prompts "prompts_suite.jsonl" \
  --output "live_report.json"
```
