# RAG en la Práctica: Responder a Partir de tus Propios Datos

> **Guía práctica.** Retrieval-Augmented Generation (RAG) entrega al modelo tus documentos en el momento de la pregunta en lugar de entrenarlos en sus pesos. El Lab 05 de este repositorio construyó respuesta a preguntas sobre documentos con RAG (ver `labs/lab-05.md` y `labs/lab5/`). Aquí no se afirman cifras de calidad de recuperación; mídelas con tus propias preguntas.

---

## 1. Cuándo RAG Es la Herramienta Correcta

| Necesidad | ¿RAG? | Alternativa |
|-----------|-------|-------------|
| Respuestas a partir de documentos privados o que cambian con frecuencia | Sí | — |
| Las respuestas deben citar su fuente | Sí | — |
| El modelo debe adoptar un estilo o un comportamiento acotado | No | Fine-tuning o prompt ([Selección de Modelos](../seleccion-de-modelos.md)) |
| Todo el corpus cabe holgadamente en la ventana de contexto y se reutiliza | Quizás no | Ponerlo en un prefijo de prompt en caché ([Caché de Prompts](../cache-de-prompts.md)) |
| Búsquedas exactas (un ID, un precio, un estado) | No | Una consulta a base de datos o una llamada a API |

Las ventanas de contexto largas (hasta 1M de tokens en los modelos Claude actuales) hacen viable "simplemente enviar los documentos" para corpus pequeños y estables. RAG sigue ganando cuando el corpus es grande, cambia con frecuencia o debe filtrarse por usuario.

## 2. Pipeline

```
ingest → clean → chunk → embed/index → [query] → retrieve → rerank → build prompt → generate → cite + validate
```

| Etapa | Decisión | Error común |
|-------|----------|-------------|
| Ingesta | Qué fuentes y con qué frecuencia actualizar | Índice desactualizado que nadie mantiene |
| Limpieza | Quitar contenido repetitivo, conservar encabezados y tablas | Menús de navegación y pies de página en cada fragmento |
| Fragmentación | Dividir según la estructura (encabezados, párrafos), con un pequeño solapamiento | Cortes de tamaño fijo en medio de tablas o código |
| Indexación | Embeddings vectoriales, palabras clave (BM25) o ambos (híbrido) | Búsqueda solo vectorial que pierde términos exactos como códigos y nombres |
| Recuperación | Candidatos top-k, filtrados por permisos del usuario | Recuperar documentos que el usuario no puede ver |
| Reordenamiento | Reordenar candidatos por relevancia antes de armar el prompt | Enviar demasiados fragmentos débiles |
| Prompt | Poner el texto recuperado en bloques de datos claramente delimitados | Mezclar instrucciones y texto recuperado |
| Generación | Indicar que responda solo a partir de las fuentes provistas y que diga cuándo falta la respuesta | Dejar que el modelo rellene huecos de memoria |
| Citar + validar | Verificar que los pasajes citados existen y respaldan la respuesta | Confiar en las citas sin verificarlas |

## 3. Evaluar Recuperación y Generación por Separado

| Capa | Pregunta | Cómo medir |
|------|----------|------------|
| Recuperación | ¿Llegó el pasaje correcto al prompt? | Para cada pregunta de prueba, etiquetar el o los pasajes que la responden; verificar si están en el top-k |
| Generación | Dado el pasaje correcto, ¿la respuesta es correcta y está fundamentada? | Calificar las respuestas contra el pasaje etiquetado |
| Extremo a extremo | ¿Es correcta la respuesta final? | Métrica de producto sobre el pipeline completo |

Si la calidad extremo a extremo es mala, esta separación indica si corregir la búsqueda o el prompt/modelo. La mayoría de los fallos de RAG son fallos de recuperación.

## 4. Seguridad y Privacidad

| Riesgo | Control |
|--------|---------|
| Inyección de prompt indirecta en documentos | Tratar el texto recuperado como datos; nunca dejar que dispare herramientas ni cambie permisos ([Checklist de Hardening](./checklist-de-hardening.md)) |
| Fuga entre usuarios | Filtrar por permisos en el momento de la recuperación, no después de la generación |
| Datos sensibles en el índice | Clasificar las fuentes antes de ingerirlas ([Privacidad y Cumplimiento](./privacidad-y-cumplimiento.md)) |
| Envenenamiento del índice | Controlar quién puede agregar documentos; registrar la ingesta |

## 5. Palancas de Costo

| Palanca | Efecto |
|---------|--------|
| Menos fragmentos y mejores (reordenamiento, k más pequeño) | Menos tokens de entrada por pregunta |
| Cachear el system prompt estable | Prefijo repetido más barato |
| Modelo pequeño para reescribir o clasificar consultas | Reserva el modelo caro para la respuesta final |
| Caché de respuestas para preguntas frecuentes | Evita la recuperación y la generación |

## 6. Checklist

- [ ] Existen preguntas de prueba con pasajes fuente etiquetados.
- [ ] La recuperación respeta los permisos del usuario.
- [ ] El prompt separa las instrucciones de los datos recuperados.
- [ ] El modelo dice "no encontrado" cuando las fuentes no contienen la respuesta.
- [ ] Las citas se verifican.
- [ ] El índice tiene un responsable y un calendario de actualización.
