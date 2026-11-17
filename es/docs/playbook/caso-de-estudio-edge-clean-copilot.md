# Caso de Estudio: Edge Clean Copilot a Través del Playbook

> **Ejemplo aplicado.** Pasa el proyecto semestral de este repositorio (`proyecto/`) por cada pregunta del playbook, usando solo evidencia documentada. Fuentes: `proyecto/docs/project/project-analysis.md`, `proyecto/docs/project/retrospective.md` y los logs históricos. Los hallazgos reflejan el análisis en el momento en que se escribió; algunos problemas pueden haberse corregido desde entonces (verificar con `python3 proyecto/status.py`).

---

## 1. El Producto

| Elemento | Valor |
|----------|-------|
| Tarea | Refactorizar TypeScript hacia Clean Architecture/DDD, offline |
| Modelo | Fine-tune LoRA de `Qwen2.5-Coder-1.5B-Instruct`, fusionado, GGUF Q4_K_M (941 MB) |
| Servicio | `llama.cpp` (`llama-server`), local |
| App | CLI hexagonal en TypeScript (`clean-copilot`) |
| Cómputo de entrenamiento | DGX Spark, "Cold Staging, Hot Burst" |

## 2. Preguntas del Playbook, Respondidas con Evidencia

| Paso del playbook | Qué hizo el proyecto | Evaluación |
|-------------------|----------------------|------------|
| [Decisión](./marco-de-decision-de-producto.md): ¿se justifica la IA? | Tarea difusa (muchas refactorizaciones válidas), requisito offline | Justificada; existe un validador (puntaje AST) |
| [Arquitectura](./necesidades-a-arquitectura.md) | Patrón copiloto con un validador basado en AST | Encaja; la salida aún necesita extracción de bloques de código y verificaciones de compilación |
| [Privacidad](./privacidad-y-cumplimiento.md) | Inferencia completamente local | Fuerte: el código nunca sale de la máquina |
| [Nivel de modelo](./decisiones-de-nivel-de-modelo.md) | Modelo pequeño especializado, autoalojado | Elegido por privacidad y borde; no se ejecutó ninguna comparación contra un nivel de nube |
| [Evaluación](./evaluacion-y-calidad.md) | Suite de 30 casos, métrica CAS, IC bootstrap | El fine-tune supera a su base por +16.8 CAS (74.8 vs 58.0), IC 95% [10.0, 25.2], 24 victorias, 6 empates, 0 derrotas |
| [Costo](./costos-y-ahorros.md) | Sin tarifa por token; CPU de laptop | Medido ≈12 tok/s, unos 47 s por respuesta en un i5-10310U |
| [Servicio](../servir-modelos-para-apps.md) | `llama-server` en local; puertos separados en el Spark compartido | El aislamiento de puertos evitó afectar a otros tenants |
| [Producción](./preparacion-para-produccion.md) | Scripts, dashboard de estado | Brechas listadas abajo |

## 3. Lo que la Evidencia No Respalda

| Afirmación | Por qué no se respalda |
|------------|------------------------|
| Rivaliza con modelos comerciales o de frontera | No se ejecutó ningún modelo así en la suite |
| Produce código correcto | La métrica verifica patrones, no compilación ni comportamiento |
| Rápido en una laptop | ≈12 tok/s; las respuestas largas tardan cerca de un minuto |
| Generaliza a código real | Las entradas de la suite tienen 3–18 líneas y son sintéticas |

## 4. Brechas Encontradas (en el momento del análisis) y la Corrección del Playbook

| Brecha | Corrección del playbook |
|--------|-------------------------|
| Datos de entrenamiento: 18 prompts distintos (138 filas), 35% de respuestas truncadas, 15% con `any` explícito | Mejores datos antes que más cómputo ([Selección de Modelos](../seleccion-de-modelos.md), sección 4) |
| Timeout del CLI de 60 s vs. salida de ≈12 tok/s | Dimensionar los timeouts a partir de la velocidad medida ([Preparación para Producción](./preparacion-para-produccion.md)) |
| `-o` escribía la respuesta cruda del modelo (fences y prosa) en archivos `.ts` | Validar y extraer la salida antes de usarla ([Checklist de Hardening](./checklist-de-hardening.md)) |
| La URL por defecto apuntaba al puerto de otro tenant en el Spark | Fijar puertos y aislar instancias ([Servir Modelos](../servir-modelos-para-apps.md)) |
| Sin CI que ejecute los tests | Puerta de regresión ([Evaluación y Calidad](./evaluacion-y-calidad.md)) |
| Enrutamiento de VS Code Copilot (`copilot-local`) sin evaluar | No enrutar tráfico a una ruta no evaluada ([Enrutamiento por Costo](../enrutamiento-por-costo.md)) |

## 5. Lecciones para Otros Productos

1. **El proceso es el activo reutilizable.** Datos → entrenar → cuantizar → servir → evaluar funcionó de extremo a extremo en hardware limitado y compartido.
2. **Un modelo pequeño especializado se justifica por una mejora medida en tu tarea**, no por su tamaño.
3. **Ejecuta el grupo de comparación.** Sin una línea base de frontera o de la base con prompt, no puedes afirmar paridad.
4. **Los validadores son el producto.** Una métrica que verifica patrones no es una verificación de compilación ni de tests.
5. **Publica solo cifras medidas.** Este proyecto eliminó a propósito las afirmaciones no medidas (TTFT).

## 6. Próximo Experimento que Más Cambiaría la Decisión

Ejecutar la misma suite de 30 casos contra (a) el modelo base con un prompt fuerte y (b) un modelo pequeño hospedado (clase Haiku), y luego comparar calidad, costo por tarea y latencia. Esa única tabla responde "¿fine-tune local o API?" para este producto.
