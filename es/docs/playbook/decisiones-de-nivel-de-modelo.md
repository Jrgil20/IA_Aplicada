# Decisiones de Nivel de Modelo: Quedarse, Subir, Ir Más Barato o Ir Privado

> **Guía de decisión.** Situación típica: la función corre en un modelo pequeño de nube (clase Haiku). ¿Escalas a uno más grande, te pasas a modelos abiertos más baratos (clase Gemma) o a infraestructura privada? Los nombres y precios cambian; decide con evidencia en tu propio conjunto de pruebas. Ver [Selección de Modelos](../seleccion-de-modelos.md) para los criterios.

---

## 1. Orden de las Preguntas

1. **Privacidad primero.** Si los datos no pueden salir de tu frontera, los niveles de nube quedan fuera sin importar el costo.
2. **Luego calidad.** ¿El nivel actual falla en tu conjunto de pruebas?
3. **Luego costo.** ¿La calidad es buena pero la factura es alta?
4. **Luego latencia.** ¿Es demasiado lento para el usuario?

## 2. Situación → Movimiento

| Situación | Movimiento | Notas |
|-----------|------------|-------|
| La salida clase Haiku falla por prompt o formato | Arreglar prompt, agregar ejemplos, agregar validador | Lo más barato; probar antes de cambiar de modelo |
| Falla porque la tarea requiere razonamiento más profundo | Escalar esa clase de tarea (clase Sonnet, luego clase Opus) | Escalar solo los casos difíciles ([Enrutamiento por Costo](../enrutamiento-por-costo.md)) |
| Falla porque faltan hechos o son privados | Agregar recuperación (RAG) | Un modelo más grande no conoce tus datos |
| Calidad bien, factura alta | Caché, prompts más cortos, batching, luego un modelo más barato | Ver [Costos y Ahorros](./costos-y-ahorros.md) |
| Un modelo abierto más barato (clase Gemma) parece atractivo | Probarlo en tu conjunto; adoptar solo si la métrica se mantiene | Decide la calidad en tu tarea, no los rankings generales |
| Los datos son sensibles o regulados | Autoalojar un modelo abierto, o un proveedor con garantías contractuales | Ver sección 3 |
| Latencia demasiado alta | Modelo más pequeño, streaming, caché, región más cercana | Medir primero el time-to-first-token |
| Se necesita operación offline o en el borde | Modelo pequeño local | Ver [Servir Modelos](../servir-modelos-para-apps.md) |

## 3. "Más Barato" No Es "Privado"

| Opción | ¿Más barato? | ¿Privado? |
|--------|--------------|-----------|
| Modelo abierto (p. ej. Gemma) en una API hospedada de terceros | Con frecuencia | **No**: tus datos igual van a ese host |
| Modelo abierto autoalojado en tu hardware | Tras el costo fijo de hardware | **Sí**, si controlas el host y los logs |
| Modelo cerrado en la API de su proveedor | Por token | Depende del contrato y la retención del proveedor; verificar |
| Modelo cerrado vía acuerdo empresarial o marketplace de nube | Por token | Pueden aplicar garantías contractuales; verificar por escrito |

La privacidad viene de dónde se procesan los datos y quién puede conservarlos, no de la licencia ni del tamaño del modelo.

## 4. Ir Más Barato: Probar Antes de Cambiar

1. Ejecutar el candidato más barato en el mismo conjunto de pruebas que el modelo actual.
2. Comparar la métrica del producto, no solo la calidad general.
3. Incluir casos de fallo y tus idiomas (los modelos pequeños suelen debilitarse fuera del inglés).
4. Cambiar solo si la calidad se mantiene, y conservar el modelo anterior para rollback.
5. Contar el costo completo: alojamiento, operación y tiempo de ingeniería, no solo el precio por token.

## 5. Subir: Escalar de Forma Selectiva

| Hacer | No hacer |
|-------|----------|
| Enviar al modelo mayor solo los casos fallidos o de baja confianza | Subir todo el tráfico porque algunos casos fallan |
| Definir el disparador (falla el validador, baja confianza, tarea fuera de alcance) | Escalar "cuando se siente mal" |
| Registrar tasa de escalado y calidad por nivel | Asumir que el modelo mayor lo arregla sin probar |

## 6. Palancas Dentro de un Mismo Modelo

Antes de cambiar de modelo, revisa la configuración del modelo que ya usas (Claude API, verificado 2026-11-17):

| Palanca | Efecto | Nota |
|---------|--------|------|
| Esfuerzo (`output_config.effort`: `low` … `max`) | Intercambia exhaustividad por tokens en el mismo modelo | Los valores por defecto varían por modelo (`medium` en Opus 5.5 y Haiku 5.5, `high` en Sonnet 5.5); ajustar por ruta |
| Prompt caching | Prefijos repetidos más baratos | Las cachés son por modelo; cambiar de modelo las pierde |
| Batch API | 50% de descuento para trabajo no urgente | Asíncrono, hasta 24 horas |
| Salidas estructuradas | Menos respuestas inválidas y reintentos | Valida el formato, no la corrección |

Precios de referencia por millón de tokens de entrada/salida: Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20 (en caché 2026-11-03; ver [Costos y Ahorros](./costos-y-ahorros.md)). El salto de Haiku a Sonnet es de unas 20×, así que escala solo los casos que lo necesitan.

## 7. Matriz Rápida

| Prioridad | Inclinarse hacia |
|-----------|------------------|
| Privacidad ante todo | Modelo abierto autoalojado |
| Mejor calidad en tareas difíciles | Nivel de nube mayor, de forma selectiva |
| Menor costo en tareas fáciles de alto volumen | Reglas, caché, modelo pequeño o abierto |
| Salir rápido al mercado, carga desconocida | API hospedada, nivel pequeño primero |
| Offline o borde | Modelo pequeño local |
