# Escalado de Cargas de IA: Laptop → DGX Spark → Nube

> **Guía de decisión AI-first.** Explica cuándo escalar cómputo o escalar a un modelo más grande, y cuándo no. Parte del conjunto de ruteo por costo: [Enrutamiento por Costo](./enrutamiento-por-costo.md), [Casos de Uso](./casos-de-uso-ia-aplicada.md), [Caché de Prompts](./cache-de-prompts.md).

---

## 1. Dos Tipos Distintos de Escalado

| Tipo | Pregunta | Ejemplo |
|------|----------|---------|
| Escalado de modelo | ¿Esta consulta necesita un modelo más grande? | 1.5B local → frontera en la nube |
| Escalado de cómputo | ¿Este trabajo necesita más hardware? | CPU de laptop → DGX Spark para entrenar |

No mezclarlos: que un entrenamiento escale al Spark no dice nada sobre qué modelo responde una consulta.

## 2. Niveles de Cómputo en Este Proyecto

| Entorno | Usar para | No usar para |
|---------|-----------|--------------|
| Laptop (CPU, mocks) | Desarrollo, tests unitarios, inferencia con el GGUF cuantizado (≈12 tok/s medido, i5-10310U) | Entrenamiento, evaluación en lotes grandes |
| DGX Spark (128 GB de memoria unificada) | Entrenamiento LoRA/QLoRA, destilación, conversión a GGUF, evaluaciones grandes | Metas de latencia interactiva en el borde |
| API en la nube | Razonamiento de frontera, capacidad en ráfagas, sin hardware propio | Datos sensibles, operación offline |

Es el modelo "Cold Staging, Hot Burst": desarrollar offline y enviar ráfagas al Spark cuando el trabajo lo requiere.

## 3. Cuándo Escalar

| Señal | Acción |
|-------|--------|
| Entrenamiento o conversión no cabe en memoria/tiempo de la laptop | Ráfaga al DGX Spark |
| La tasa de escalado a la nube se mantiene alta en una clase de tarea | Afinar un modelo local para esa clase, o aceptar el costo de la nube |
| No se cumple la latencia objetivo en inferencia local | Modelo más pequeño/cuantizado, o host con GPU |
| Calidad bajo el umbral en el benchmark | Modelo más grande o mejores datos, no solo más cómputo |

## 4. Cuándo No Escalar

| Situación | Mejor movimiento |
|-----------|------------------|
| Prompts idénticos repetidos | Agregar caché ([Caché de Prompts](./cache-de-prompts.md)) |
| Prefijo largo compartido en cada llamada | Caché de prefijo/KV |
| Tarea determinista simple | Reglas (T0) |
| "Se siente lento" sin medir | Medir primero; no agregar métricas a la documentación hasta medirlas |

## 5. Checklist de Política de Escalado

1. La compuerta de política para datos sensibles corre primero.
2. Cada escalado tiene un disparador explícito (falla de validador, baja confianza, fuera de alcance).
3. La tasa de escalado y la calidad por nivel se registran y comparan con el benchmark.
4. Las afirmaciones de costo salen de conteos de tokens medidos y listas de precios vigentes.
