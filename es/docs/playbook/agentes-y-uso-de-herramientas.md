# Agentes y Uso de Herramientas: Cuándo y Cómo

> **Guía práctica.** Un agente es un modelo que elige sus propias llamadas a herramientas a lo largo de varios pasos. Es el patrón más potente y también el más caro y riesgoso. Empieza por el nivel más simple que funcione. Ejemplos prácticos en este repositorio: Lab 03 (agentes de código autónomos y auditoría de datos, `labs/lab-03.md`) y Lab 04 (conexión de agentes a un ERP mediante MCP, `labs/lab-04.md`).
>
> **Estado de verificación (2026-11-17):** los detalles de Claude API provienen de la referencia de Claude API incluida con Claude Code.

---

## 1. Elegir el Nivel Más Simple

| Nivel | Forma | Usar cuando |
|-------|-------|-------------|
| Llamada única | Una solicitud, una respuesta | Clasificación, extracción, resumen, preguntas y respuestas |
| Workflow | Tu código ejecuta pasos fijos y llama al modelo donde hace falta | Los pasos se conocen de antemano |
| Agente | El modelo decide qué herramienta llamar a continuación, en un bucle | La tarea es abierta y difícil de especificar paso a paso |

Construye un agente solo si se cumplen **los cuatro**:

| Criterio | Pregunta |
|----------|----------|
| Complejidad | ¿La tarea tiene varios pasos y es difícil de especificar de antemano? |
| Valor | ¿El resultado justifica el mayor costo y latencia? |
| Viabilidad | ¿Puede el modelo realmente hacer este tipo de tarea? |
| Costo del error | ¿Se pueden detectar y deshacer los errores (tests, revisión, rollback)? |

Si alguna respuesta es "no", usa un workflow o una llamada única.

## 2. Diseño de Herramientas

| Regla | Por qué |
|-------|---------|
| Pocas herramientas, bien descritas | El modelo elige mejor entre opciones claras |
| Esquemas de entrada estrictos | Los argumentos inválidos se rechazan antes de ejecutar (en Claude API, `strict: true` en una herramienta) |
| Mínimo privilegio | Solo lectura por defecto; herramientas de escritura acotadas a lo que la tarea necesita |
| Devolver los errores como resultados | El modelo puede recuperarse; los fallos silenciosos provocan bucles |
| Idempotentes cuando sea posible | Los reintentos no repiten efectos secundarios |
| Aprobación humana para acciones riesgosas | Pagos, eliminaciones, mensajes salientes, cambios en producción |

## 3. Controles del Bucle

| Control | Propósito |
|---------|-----------|
| Máximo de pasos | Detiene bucles descontrolados |
| Presupuesto de tokens o por tarea | Acota el costo por tarea |
| Timeout por herramienta y por tarea | Acota la latencia |
| Condiciones de parada | Definición clara de "terminado" |
| Log de auditoría de cada llamada a herramienta | Depuración y rendición de cuentas |

## 4. Seguridad

| Amenaza | Control |
|---------|---------|
| Inyección de prompt a través de resultados de herramientas (páginas web, archivos, correos) | Tratar la salida de las herramientas como datos no confiables; separar contextos privilegiados y no confiables |
| Agencia excesiva | Permisos aplicados por código, no por el prompt |
| Exposición de credenciales | Mantener los secretos fuera del contexto del modelo; inyectarlos en la frontera de la herramienta |
| Exfiltración de datos | Restringir la red saliente y los dominios a los que el agente puede llegar |

Ver el [Checklist de Hardening](./checklist-de-hardening.md) y la skill `inference-security-hardening`.

## 5. Construir vs. Opciones Gestionadas (ecosistema Claude)

| Opción | Tú gestionas | Encaja con |
|--------|--------------|------------|
| Messages API con tu propio bucle | Bucle, herramientas, alojamiento | Control total, cualquier política de datos que puedas sostener |
| Tool runner del SDK | Herramientas y alojamiento; el SDK ejecuta el bucle | Menos código, sigue siendo autoalojado |
| Managed Agents (beta) | Configuración del agente y herramientas propias; el proveedor aloja el bucle y el sandbox | Arranque rápido, sesiones largas; se factura por tiempo de ejecución de la sesión más tokens; actualmente no elegible para ZDR/HIPAA |

Elige primero por política de datos ([Privacidad y Cumplimiento](./privacidad-y-cumplimiento.md)) y luego por cuánta infraestructura quieres operar.

## 6. Costo

Los agentes multiplican los tokens: cada paso reenvía la conversación. Usa prompt caching en el prefijo estable, limita los pasos, usa un modelo más barato para subtareas con mucha lectura y mide el **costo por tarea completada** ([Costos y Ahorros](./costos-y-ahorros.md)).

## 7. Evaluar

| Métrica | Significado |
|---------|-------------|
| Tasa de éxito de tareas | ¿Terminó el trabajo correctamente? |
| Pasos y tokens por tarea | Eficiencia y costo |
| Acciones inseguras o bloqueadas | Seguridad |
| Intervenciones humanas | Autonomía realmente lograda |

Ejecuta el mismo conjunto de tareas después de cada cambio en el modelo, el prompt o las herramientas ([Evaluación y Calidad](./evaluacion-y-calidad.md)).
