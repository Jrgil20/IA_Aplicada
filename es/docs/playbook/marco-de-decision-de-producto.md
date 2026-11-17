# Marco de Decisión de Producto: ¿Esta Función Debe Usar IA?

> **Guía go/no-go.** Ejecutarla antes de elegir cualquier modelo. La IA añade costo, latencia y modos de fallo; debe ganarse su lugar.

---

## 1. Tres Preguntas Primero

| # | Pregunta | Si la respuesta es "no" |
|---|----------|--------------------------|
| 1 | ¿Puede resolverlo código determinista (reglas, búsqueda, parser, consulta)? | Usar código. Es exacto, gratis y testeable |
| 2 | ¿Es tolerable una respuesta errónea, o se puede detectar automáticamente o por una persona? | Agregar un validador o revisión humana, o no lanzar |
| 3 | ¿Hay una métrica de éxito medible y datos de prueba? | Definirlas primero; no se puede mejorar lo que no se puede puntuar |

## 2. Prueba de Ajuste

| Señal | Buen ajuste para IA | Mal ajuste |
|-------|---------------------|------------|
| Entrada | Texto no estructurado, código, imágenes, voz | Campos estructurados limpios |
| Salida | Difusa, muchas respuestas válidas | Una única respuesta correcta |
| Reglas | Demasiadas o demasiado difusas para escribirlas | Pocas y estables |
| Costo del error | Bajo o reversible | Alto e irreversible (pagos, médico, legal) sin revisión |
| Volumen | Suficiente para justificar la inversión | Tareas únicas que una persona hace más rápido |

## 3. Construir, Comprar o Adaptar

| Opción | Elegir cuando | Cuidado con |
|--------|---------------|-------------|
| API hospedada | Arranque rápido, calidad de frontera, carga variable | Costo por token, los datos salen de tu frontera, cambios del proveedor |
| Modelo abierto autoalojado | Privacidad, alto volumen constante, offline | Hardware, trabajo de operación, menor calidad general |
| Modelo pequeño afinado | Tarea estrecha y repetida con datos | Datos de entrenamiento, evaluación, reentrenar si cambian las necesidades |
| Producto de IA listo | La necesidad es genérica | Poco control, dependencia del proveedor |

## 4. Definir Antes de Construir

| Elemento | Forma de ejemplo |
|----------|------------------|
| Trabajo del usuario | "El revisor recibe una sugerencia de refactor para un archivo" |
| Métrica de éxito | Un número ligado al trabajo (tasa de éxito, score en un conjunto de pruebas) |
| Política de fallo | Qué pasa ante una respuesta errónea o vacía: reintentar, escalar, mostrar "no estoy seguro", pasar a una persona |
| Restricciones | Sensibilidad de datos, presupuesto de latencia, tope mensual de costo, idiomas |
| Responsable | Quién monitorea y actualiza la función tras el lanzamiento |

## 5. Checklist Go/No-Go

- [ ] Se consideró una alternativa determinista y se rechazó con una razón.
- [ ] Existen métrica de éxito y conjunto de pruebas.
- [ ] El comportamiento ante fallos está diseñado, no es accidental.
- [ ] El flujo de datos está aprobado ([Privacidad y Cumplimiento](./privacidad-y-cumplimiento.md)).
- [ ] Hay un tope de costo ([Costos y Ahorros](./costos-y-ahorros.md)).
- [ ] Hay un responsable nombrado.

Cualquier casilla sin marcar significa: aún no lanzar.
