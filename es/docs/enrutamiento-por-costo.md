# Enrutamiento por Costo: Decisiones Basadas en Datos Antes de Escalar a una IA Grande

> **Nota de diseño AI-first.** Estado: **idea / no implementada**. Describe una cascada que responde consultas baratas con lógica determinista o un modelo local pequeño y escala a un LLM de frontera solo cuando hace falta. Complementa [SLMs Locales vs. LLMs en la Nube](./local-slm-vs-cloud-llm.md), que separa por **sensibilidad de datos y tipo de tarea**, no por consulta.

---

## 1. Auditoría del Repositorio (verificada 2026-11-17)

| Pregunta | Hallazgo |
|----------|----------|
| ¿Router o cascada de escalado por consulta en código? | **No.** |
| ¿Documentado? | **Parcialmente.** `local-slm-vs-cloud-llm.md` §3.5 y §5 definen niveles estáticos (datos sensibles vs. públicos). No hay escalado por confianza ni por costo. |
| Código más cercano | `proyecto/bin/copilot-local`: interruptor manual todo o nada entre Copilot en la nube y el modelo local. No decide por solicitud. Sin evaluar (`project-analysis.md`, C5). |
| ¿`ideas.md` / `next-steps.md` mencionan ruteo por costo? | **No.** |
| Ruido en grep (no es ruteo) | Gateway de red del DGX, fallback regex del scoring AST, "escalates" de CVSS en el lab 2. |

## 2. Piezas Reutilizables

| Pieza | Dónde | Uso en un router |
|-------|-------|------------------|
| Modelo local barato | Qwen2.5-Coder-1.5B Q4_K_M con `llama.cpp` (≈12 tok/s, CPU i5-10310U, medido) | Respondedor del nivel 1 |
| Benchmark de calidad | `proyecto/evaluation/` (30 casos, score CAS, IC bootstrap 95%) | Medir la pérdida de calidad por el ruteo |
| Puerto de inferencia | `proyecto/cli/src/application/ports` (hexagonal) | Router como adaptador; dominio intacto |
| Política de niveles estática | `local-slm-vs-cloud-llm.md` §5 | Restricciones duras (nunca enviar datos sensibles a la nube) |

## 3. Patrón Propuesto: Cascada

```
consulta → [0] compuerta de política → [1] caché / reglas → [2] SLM local → [3] chequeo de confianza → [4] LLM de frontera
```

| Nivel | Entrada de decisión (basada en datos) | Se escala cuando |
|-------|---------------------------------------|------------------|
| 0 Compuerta de política | Clasificación del dato (¿sensible?) | Nunca escalar a la nube si es sensible |
| 1 Caché / reglas | Coincidencia exacta o semántica, intents por regex | No hay coincidencia |
| 2 SLM local | Rasgos de la consulta: longitud, tipo de tarea, idioma | La tarea excede el alcance entrenado del SLM |
| 3 Chequeo de confianza | Logprobs de tokens, autoconsistencia, validadores de salida (p. ej. el AST parsea) | Confianza bajo el umbral o falla la validación |
| 4 LLM de frontera | — | Último nivel |

## 4. Modelos de Decisión (opciones)

| Modelo | Costo | ¿Requiere datos de entrenamiento? | Notas |
|--------|-------|-----------------------------------|-------|
| Reglas / intents por palabra clave | Mínimo | No | Empezar aquí; transparente |
| Clasificador de rasgos (regresión logística, árbol pequeño) | Bajo | Sí (etiquetas fácil/difícil) | Predice "el SLM alcanza" antes de llamarlo |
| Umbrales de confianza sobre la salida del SLM | Bajo | Conjunto pequeño de calibración | Requiere calibrar; los logprobs del SLM pueden ser sobreconfiados |
| Router aprendido (embedding + clasificador) | Medio | Sí | Solo si el volumen lo justifica |

## 5. Plan de Validación (requerido antes de afirmar nada)

1. Etiquetar las consultas del benchmark según qué nivel las responde de forma aceptable.
2. Ejecutar la cascada sobre el benchmark; comparar CAS y tasa de escalado contra siempre-frontera y siempre-local.
3. Reportar ahorros solo con conteos de tokens y precios medidos. **No publicar ahorros ni latencias estimados** (regla del proyecto: sin métricas no medidas).

## 6. Preguntas Abiertas

| # | Pregunta |
|---|----------|
| 1 | ¿Es para el CLI `clean-copilot` o solo una guía general? |
| 2 | ¿Cuál es la verdad de referencia para "pregunta fácil" en este proyecto? |
| 3 | ¿Qué modelo de frontera y fuente de precios para la línea base de costo? |
