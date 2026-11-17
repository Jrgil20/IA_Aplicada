# Preparación para Producción: Lanzar y Operar una Función de IA

> **Checklist de lanzamiento.** Contraparte operativa del playbook. Los detalles de infraestructura están en [Servir Modelos para Apps](../servir-modelos-para-apps.md); los de seguridad en el [Checklist de Hardening](./checklist-de-hardening.md).

---

## 1. Antes del Lanzamiento

| Área | Requisito |
|------|-----------|
| Evaluación | El conjunto de pruebas cumple la métrica acordada ([Evaluación y Calidad](./evaluacion-y-calidad.md)) |
| Comportamiento ante fallos | Definido para respuestas erróneas, vacías, lentas y rechazadas |
| Respaldos | Modelo secundario o ruta sin IA cuando falla el primario |
| Límites | Rate limits, topes de tokens, timeouts, alertas de presupuesto |
| Seguridad | Checklist de hardening completo |
| Privacidad | Ruta de datos aprobada |
| Rollback | Versiones previas de modelo y prompt conservadas, reversión en un paso |
| Responsable | Persona nombrada de guardia para la función |

## 2. Despliegue Gradual

| Etapa | Práctica |
|-------|----------|
| Sombra | Ejecutar la ruta de IA en silencio y compararla con el comportamiento actual |
| Cohorte pequeña | Liberar a una fracción de usuarios; vigilar métricas |
| Aumento gradual | Expandir solo mientras calidad, costo y tasa de error se mantengan |
| Lanzamiento completo | Conservar el interruptor de apagado |

## 3. Observabilidad

| Métrica | Por qué |
|---------|---------|
| Latencia (time-to-first-token, total) | Experiencia del usuario |
| Tokens y costo por solicitud y por función | Control de presupuesto |
| Tasa de error, timeout y rechazo | Fiabilidad |
| Fallos de validadores y escalados | Calidad y salud del ruteo |
| Profundidad de cola y uso de slots (autoalojado) | Capacidad |

Registrar sin contenido sensible; retención corta.

## 4. Versionado

| Elemento | Práctica |
|----------|----------|
| Modelo | Fijar el ID exacto del modelo, no un alias que cambia; reevaluar antes de pasar a una versión nueva y antes de que el proveedor retire la anterior |
| Prompt | Guardar en control de versiones, revisar cambios como código |
| Índice de recuperación | Versionar junto con el conjunto de documentos |
| Artefactos | Fijar hash de pesos autoalojados; nunca commitear pesos |

## 5. Guía de Incidentes

| Síntoma | Primeros movimientos |
|---------|----------------------|
| Caída de calidad | Revisar cambios recientes de modelo, prompt o datos; revertir; ejecutar el conjunto de pruebas |
| Pico de costo | Revisar bucles, reintentos y tráfico; aplicar rate limits o pasar a la ruta más barata |
| Pico de latencia | Revisar profundidad de cola, estado del proveedor, tamaño de contexto |
| Sospecha de fuga o inyección | Deshabilitar la herramienta o función afectada, conservar logs, revisar exposición de datos |
| Caída del proveedor | Cambiar a la ruta de respaldo |

## 6. Continuo

- Revisar el conjunto de pruebas y agregar casos de fallo nuevos con regularidad.
- Reevaluar la elección de modelo cuando aparezcan modelos o precios nuevos ([Decisiones de Nivel de Modelo](./decisiones-de-nivel-de-modelo.md)).
- Revisar los costos contra el presupuesto en un calendario fijo ([Costos y Ahorros](./costos-y-ahorros.md)).
