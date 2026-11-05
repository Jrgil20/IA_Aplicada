# Problema 9 · Pregúntale a compras

Cada semana llegan a compras decenas de preguntas de las sedes: cuántos días de gracia tiene un proveedor, a qué correo se manda un reclamo, cuántas cotizaciones hacen falta. Las respuestas están en los documentos, pero en las sedes nadie usa OpenCode y nadie se los va a leer.

La gerente quiere un asistente web: una página a la que cualquiera de la empresa entra desde el navegador, escribe su pregunta en español y recibe la respuesta sacada de los documentos de compras. Todos los documentos juntos no caben en lo que el modelo puede leer de una vez.

**Material:** `documentos/` y `preguntas_de_prueba.csv`, las preguntas que Legal usará para aprobar el asistente.

**Entregable:** el asistente web en la carpeta `asistente/`, funcionando en el Spark, y `salidas/9-evaluacion.html`, para Legal: cada pregunta de prueba, lo que respondió el asistente, de qué documentos lo sacó y si la respuesta es correcta, con el total de aciertos arriba.

**Condiciones de la gerente:**

- Que lo use alguien de una sede sin que nadie le explique nada, en la pantalla de una laptop o de un teléfono.
- Que se vea como una herramienta de la empresa, no como un ejercicio de clase.
- Que quien pregunte pueda ver de qué documento salió la respuesta sin salir de la página.

**Condiciones de Legal:**

- Ninguna respuesta sin su fuente: documento y sección.
- Si la respuesta no está en los documentos, el asistente lo dice. Inventar es peor que no saber.
- Responde con lo que está vigente hoy.
- El asistente usa el modelo del Spark: ningún documento sale de la empresa.

**Legal no va a usar solo la lista: también hará preguntas que ustedes no vieron, desde su propio navegador.**
