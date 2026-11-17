# IA Aplicada: Qué Herramienta para Qué Tarea

> **Guía de decisión AI-first.** Asigna tareas comunes de IA aplicada al nivel más barato que pueda resolverlas de forma aceptable. Parte del conjunto de ruteo por costo: [Enrutamiento por Costo](./enrutamiento-por-costo.md), [Escalado](./escalado-cargas-ia.md), [Caché de Prompts](./cache-de-prompts.md). Estado: guía, no resultados medidos.

---

## 1. Niveles

| Nivel | Qué es | Perfil de costo típico |
|-------|--------|------------------------|
| T0 Determinista | Reglas, regex, tablas, parsers, linters | Sin costo de inferencia |
| T1 Caché | Caché de respuestas (exacta/semántica), caché de prefijo de prompt | Se paga una vez, se reutiliza |
| T2 SLM local | Modelo cuantizado de 1.5B–30B en hardware propio (p. ej. Qwen2.5-Coder-1.5B Q4_K_M) | Costo fijo de hardware, sin tarifa por token |
| T3 Modelo pequeño en la nube | API tipo Haiku/Flash | Tarifa baja por token |
| T4 Modelo de frontera en la nube | Modelos de razonamiento más grandes | Mayor tarifa por token |

## 2. Cuándo Usar Cada Nivel

| Tarea | Empezar en | Escalar cuando | Por qué |
|-------|------------|----------------|---------|
| Formatear/validar JSON, fechas, IDs | T0 | Nunca | Un parser es exacto y gratis |
| FAQ, preguntas repetidas | T1 | Falla el caché y no aplica ninguna regla | Se reutiliza la misma respuesta |
| Clasificación de intención, etiquetas de ruteo | T0 → T2 | Las reglas son ambiguas | Salidas cortas favorecen modelos pequeños |
| Autocompletado corto, boilerplate | T2 | La salida falla la validación (parseo, lint, tests) | Latencia y privacidad favorecen lo local |
| Refactor de tarea específica (alcance afinado) | T2 | Fuera del alcance entrenado | La especialización LoRA es la fortaleza del modelo local |
| Resumir o extraer de un documento conocido | T3 | Largo, ambiguo o de alto riesgo | Razonamiento moderado, contexto grande |
| Planificación multi-paso, revisión de arquitectura | T4 | — | Requiere razonamiento fuerte |
| Datos sensibles o air-gapped | Solo T2 | Nunca a la nube | Compuerta de política (ver `local-slm-vs-cloud-llm.md` §3.5) |

## 3. Heurísticas de Selección

1. **¿El código puede resolverlo con exactitud?** Usar T0.
2. **¿Ya se respondió antes?** Usar T1.
3. **¿La salida se verifica automáticamente?** Empezar barato; el validador decide el escalado.
4. **¿Una respuesta errónea es costosa o difícil de detectar?** Empezar más arriba; no ahorrar tokens en salidas de alto riesgo.
5. **¿Los datos son sensibles?** Quedarse en local sin importar el costo.

## 4. Antipatrones

| Antipatrón | Problema |
|------------|----------|
| Modelo de frontera para todo | Se paga precio de frontera por trabajo T0/T1 |
| Modelo local para todo | Pérdida de calidad en tareas de razonamiento (el modelo de 1.5B de este repo es especializado, no general) |
| Escalar "a ojo" | Sin datos; usar validadores y confianza medida |
| Rutear sin benchmark | No se sabe si el ahorro cuesta calidad |
