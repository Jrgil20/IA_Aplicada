# Enrutamiento por Costo: Decisiones Basadas en Datos Antes de Escalar a una IA Grande

> **Nota de diseño AI-first.** Estado: **idea / no implementada**. Describe una cascada que responde consultas baratas con lógica determinista o un modelo local pequeño y escala a un LLM de frontera solo cuando hace falta. Complementa [SLMs Locales vs. LLMs en la Nube](./local-slm-vs-cloud-llm.md), que separa por niveles según **sensibilidad de datos y tipo de tarea**, no por consulta.

---

## 1. Auditoría del Repositorio (verificada 2026-11-17)

| Pregunta | Hallazgo |
|----------|----------|
| ¿Router por consulta o cascada de escalado en el código? | **No.** |
| ¿Documentado? | **Parcialmente.** `local-slm-vs-cloud-llm.md` §3.5 y §5 definen niveles estáticos (datos sensibles vs. públicos). No hay escalado basado en confianza ni en costo. |
| Código existente más cercano | `proyecto/bin/copilot-local`: interruptor manual de todo o nada entre GitHub Copilot en la nube y el modelo local. No decide por solicitud. Sin evaluar (`project-analysis.md`, C5). |
| ¿`ideas.md` / `next-steps.md` mencionan ruteo por costo? | **No.** |
| Ruido en grep (no es ruteo) | Gateway de red del DGX, fallback regex en el scoring AST, "escalates" de CVSS en el lab 2. |

## 2. Piezas Reutilizables

| Pieza | Dónde | Uso en un router |
|-------|-------|------------------|
| Modelo local barato | Qwen2.5-Coder-1.5B Q4_K_M con `llama.cpp` (≈12 tok/s, solo CPU i5-10310U, medido) | Respondedor del nivel 1 |
| Benchmark de calidad | `proyecto/evaluation/` (30 casos, score CAS, IC bootstrap 95%) | Medir la pérdida de calidad causada por el ruteo |
| Puerto de inferencia | `proyecto/cli/src/application/ports` (hexagonal) | Router como adaptador; dominio intacto |
| Política de niveles estática | `local-slm-vs-cloud-llm.md` §5 | Restricciones duras (nunca enviar datos sensibles a la nube) |

## 3. Patrón Propuesto: Cascada

```
consulta → [0] compuerta de política → [1] caché / reglas → [2] SLM local → [3] chequeo de confianza → [4] LLM de frontera
```

| Nivel | Entrada de decisión (basada en datos) | Se escala cuando |
|-------|---------------------------------------|------------------|
| 0 Compuerta de política | Clasificación del dato (¿sensible?) | Nunca escalar a la nube si es sensible |
| 1 Caché / reglas | Coincidencia exacta o semántica, reglas regex/de intención | No hay acierto |
| 2 SLM local | Rasgos de la consulta: longitud, tipo de tarea, idioma | La tarea está fuera del alcance entrenado del SLM |
| 3 Chequeo de confianza | Logprobs de tokens, autoconsistencia, validadores de salida (p. ej. el AST parsea) | Confianza bajo el umbral o falla la validación |
| 4 LLM de frontera | — | Último nivel |

## 4. Modelos de Decisión (opciones)

| Modelo | Costo | ¿Requiere datos de entrenamiento? | Notas |
|--------|-------|-----------------------------------|-------|
| Reglas / intenciones por palabra clave | Mínimo | No | Empezar aquí; transparente |
| Clasificador de rasgos de la consulta (regresión logística, árbol pequeño) | Bajo | Sí (etiquetas fácil/difícil) | Predice "el SLM es suficiente" antes de llamarlo |
| Umbrales de confianza sobre la salida del SLM | Bajo | Conjunto pequeño de calibración | Requiere calibración; los logprobs del SLM pueden ser sobreconfiados |
| Router aprendido (embedding + clasificador) | Medio | Sí | Solo si el volumen lo justifica |

## 5. Advertencias Antes de Construir una Cascada (verificadas 2026-11-17)

| Advertencia | Consecuencia |
|-------------|--------------|
| Las cachés de prompts del proveedor son por modelo | Cada nivel tiene su propia caché; una cascada renuncia a reutilizar la caché entre niveles |
| Un modelo capaz con menor effort puede igualar a un modelo anterior con effort alto | Medir primero "un modelo, menor effort"; puede superar a una cascada en costo y simplicidad |
| Las solicitudes escaladas pagan dos veces (intento barato + reintento caro) | El ahorro depende de la proporción respondida bien en el nivel barato |
| Los errores del router son silenciosos | Registrar el nivel por solicitud y muestrear respuestas escaladas y no escaladas |
| El costo por tarea completada es la métrica real | Un primer intento barato que falla y se reintenta puede costar más |

## 6. Plan de Validación (requerido antes de afirmar nada)

1. Etiquetar las consultas del benchmark según qué nivel las responde de forma aceptable.
2. Ejecutar la cascada sobre el benchmark; comparar CAS y tasa de escalado contra siempre-frontera y siempre-local.
3. Reportar ahorros solo a partir de conteos de tokens y precios medidos. **No publicar cifras estimadas de ahorro ni de latencia** (regla del proyecto: sin métricas no medidas).

## 7. Guías Relacionadas

| Guía | Cubre |
|------|-------|
| [Casos de Uso de IA Aplicada](./casos-de-uso-ia-aplicada.md) | Qué nivel encaja con cada tarea |
| [Escalado de Cargas de IA](./escalado-cargas-ia.md) | Escalado de modelo vs. escalado de cómputo |
| [Caché de Prompts](./cache-de-prompts.md) | Cachés del nivel 1 y caché de prefijo |

## 8. Preguntas Abiertas

| # | Pregunta |
|---|----------|
| 1 | ¿Es para el CLI `clean-copilot` o solo una guía general? |
| 2 | ¿Cuál es la verdad de referencia para "pregunta fácil" en este proyecto? |
| 3 | ¿Qué modelo de frontera y qué fuente de precios para la línea base de costo? |
