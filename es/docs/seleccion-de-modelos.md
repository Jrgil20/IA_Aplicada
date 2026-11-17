# Elegir un Modelo para una Aplicación

> **Guía de decisión AI-first.** Un proceso repetible para elegir, y luego reemplazar, un modelo. Los nombres y versiones cambian rápido: importan más los criterios que la lista. No se afirman puntajes de benchmark; evaluar los candidatos con tu propio conjunto de pruebas. Relacionado: [Playbook: Decisiones de Nivel de Modelo](./playbook/decisiones-de-nivel-de-modelo.md), [Servir Modelos](./servir-modelos-para-apps.md), [Casos de Uso de IA Aplicada](./casos-de-uso-ia-aplicada.md), [Arquitectura Model Factory](../../proyecto/es/docs/architecture/model-factory-architecture.md).

---

## 1. Proceso

1. **Definir la tarea y una métrica de éxito/fallo** (en este proyecto: el score CAS del benchmark).
2. **Fijar restricciones duras**: sensibilidad de datos, hardware, latencia, presupuesto, licencia.
3. **Preseleccionar 2–4 candidatos** que cumplan las restricciones.
4. **Evaluar todos con el mismo conjunto de pruebas**, incluyendo una línea base sin fine-tuning.
5. **Elegir el candidato más barato que cumpla la métrica**, y reevaluar cuando salgan modelos nuevos.

## 2. Criterios de Selección

| Criterio | Pregunta | Por qué importa |
|----------|----------|-----------------|
| Ajuste a la tarea | ¿Código, chat, extracción, clasificación, multilingüe? | Los modelos especializados superan a los generales más grandes solo si la tarea coincide |
| Clase de tamaño | ¿Qué nivel de la [matriz de dimensionamiento](./local-slm-vs-cloud-llm.md#42-matriz-de-dimensionamiento-de-hardware) cabe en el hardware? | Define memoria y velocidad |
| Instruct vs. base | ¿Sigue instrucciones sin ajustes? | Los base sirven para fine-tuning; los instruct para uso directo |
| Longitud de contexto | ¿La entrada real más larga cabe en la ventana? | El truncamiento degrada respuestas en silencio |
| Idioma | ¿Maneja los idiomas de la app (p. ej. español)? | Los modelos pequeños suelen debilitarse fuera del inglés |
| Licencia | ¿Se permite uso comercial o redistribución? | Restricción legal |
| Cuantización | ¿Qué pérdida de calidad causa Q4 vs. Q8 en tu conjunto de pruebas? | Compromiso memoria vs. calidad |
| Herramientas | ¿Hay build GGUF/vLLM y tokenizer estable? | Determina cómo se sirve |
| Afinabilidad | ¿LoRA/QLoRA está soportado en tu stack? | Necesario para especializar la tarea |

## 3. Clase de Tamaño → Rol

| Clase | Rol típico | Precaución |
|-------|------------|------------|
| 1.5B–3B | Tareas estrechas afinadas; autocompletado; clasificación | Débil en razonamiento abierto |
| 7B–8B | Asistentes generales, resumen, uso simple de herramientas | Requiere GPU de gama media o paciencia en CPU |
| 14B–32B | Razonamiento local más exigente, generación por lotes | Requiere 16–24 GB+ de memoria rápida |
| Nube pequeña (clase Haiku/Flash) | Tareas generales baratas a escala | Los datos salen de tu frontera |
| Nube de frontera | Planificación, razonamiento difícil, síntesis larga | Mayor costo por token |

## 4. ¿Afinar, Mejorar el Prompt o un Modelo Más Grande?

| Situación | Probar primero |
|-----------|----------------|
| El formato o estilo es incorrecto | Mejor prompt y ejemplos |
| Tarea estrecha y repetida, hay datos | Fine-tune LoRA/QLoRA de un modelo pequeño |
| Requiere razonamiento amplio | Modelo más grande, no más fine-tuning |
| Los hechos deben ser actuales o privados | Recuperación (RAG), no pesos |
| El problema es el costo por llamada | [Enrutamiento por costo](./enrutamiento-por-costo.md) y [caché](./cache-de-prompts.md) |

## 5. Lecciones de Este Proyecto

| Hallazgo | Fuente |
|----------|--------|
| El 1.5B afinado superó a su propio modelo base en la suite del proyecto (+16.8 puntos CAS, IC bootstrap 95% reportado) | `proyecto/docs/project/project-analysis.md` |
| La comparación de la propuesta contra modelos comerciales generales nunca se ejecutó | `proyecto/docs/project/retrospective.md` |
| Las bases candidatas se siguen en el model factory (Qwen2.5-Coder, Llama-3.2, Gemma-2, SmolLM2, DeepSeek) | `proyecto/docs/architecture/model-factory-architecture.md` |

Implicación: un modelo pequeño especializado se justifica por una mejora medida frente a su base en tu tarea, no solo por el tamaño. Ejecutar la comparación faltante antes de afirmar paridad con modelos de frontera.

## 6. Checklist de Reemplazo

1. Candidato nuevo entrenado o descargado con la misma receta.
2. Mismo benchmark, mismo scoring, reporte con intervalos de confianza.
3. Comparar contra el modelo actual; reemplazar solo ante una mejora medida.
4. Conservar el artefacto anterior para rollback.
