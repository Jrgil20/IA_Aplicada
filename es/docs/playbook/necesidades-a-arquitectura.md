# Necesidades a Arquitectura: Patrón por Necesidad de Producto

> **Tabla de consulta.** Relaciona lo que el producto debe hacer con un patrón probado, su riesgo principal y lo primero que hay que medir.

---

## 1. Patrones

| Necesidad de producto | Patrón | Piezas centrales | Riesgo principal | Primera métrica |
|-----------------------|--------|------------------|------------------|-----------------|
| Responder preguntas desde nuestros documentos | RAG (recuperación + generación) | Chunking, embeddings, búsqueda vectorial/por palabras, prompt fundamentado | Recuperación errónea o faltante; citas alucinadas | Corrección de la respuesta vs. la fuente citada |
| Clasificar o rutear texto | Clasificador (reglas → modelo pequeño) | Etiquetas, validador, etiqueta de respaldo | Deriva silenciosa en la mezcla de entradas | Exactitud por clase |
| Extraer campos de documentos | Extracción estructurada | Esquema, validación JSON, reintento si es inválido | Valores plausibles pero erróneos | Exactitud por campo |
| Redactar o reescribir texto | Generación con restricciones | Guía de estilo en el prompt, límites de longitud, aprobación humana | Contenido fuera de marca o falso | Tasa de edición por revisores |
| Asistencia de código | Copilot (completado/refactor) | Constructor de contexto, validadores (parseo, lint, tests) | Código inseguro o que no compila | Tasa de aprobación de validadores |
| Soporte conversacional | Chatbot con herramientas y traspaso | System prompt, herramientas de mínimo privilegio, escalado a humano | Prompt injection, mal uso de herramientas | Tasa de resolución, tasa de traspaso |
| Automatización multi-paso | Agente | Planificador, permisos de herramientas, límites de pasos, log de auditoría | Acciones descontroladas, bucles de costo | Éxito de tareas, pasos por tarea |
| Reducir costo con tráfico mixto | Router en cascada | Compuerta de política, caché, modelo pequeño, escalado ([Enrutamiento por Costo](../enrutamiento-por-costo.md)) | Pérdida de calidad por ruteo errado | Tasa de escalado, calidad por nivel |

## 2. Elegir Entre Vecinos

| Pregunta | Respuesta |
|----------|-----------|
| ¿RAG o fine-tune? | Hechos que cambian o son privados → RAG. Estilo o comportamiento de una tarea estrecha → fine-tune |
| ¿Agente o flujo fijo? | Si los pasos se conocen, usar un flujo fijo; los agentes añaden costo y riesgo |
| ¿Un prompt grande o varias llamadas? | Dividir cuando los pasos necesitan distintos modelos, validación o caché |
| ¿Interfaz de chat o función embebida? | Si el usuario necesita una sola acción, embeberla; el chat añade ambigüedad |

## 3. Arquitectura Mínima (todos los patrones)

```
entrada → chequeos de entrada → constructor de contexto → llamada al modelo → validador de salida → respuesta
                ↓                       ↓                        ↓                    ↓
         compuerta de política      caché/RAG              logs + métricas     respaldo / humano
```

Todo patrón necesita: un chequeo de entrada, un validador de salida, una ruta de respaldo y logs sin contenido sensible.
