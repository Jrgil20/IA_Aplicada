# Evaluación y Calidad: ¿Es Suficientemente Buena y Se Mantiene Así?

> **Guía de evaluación.** Toda decisión de este playbook (nivel de modelo, ruteo, modelo más barato, caché) depende de medir la calidad en tu tarea. Ejemplo de este repo: `proyecto/evaluation/` puntúa salidas con una métrica basada en AST (CAS) y reporta intervalos de confianza bootstrap.

---

## 1. Construir un Conjunto de Pruebas

| Paso | Detalle |
|------|---------|
| Recolectar casos reales | De uso real o realista, no solo ejemplos fáciles |
| Cubrir los bordes | Entradas raras, fallos, entradas largas, cada idioma soportado |
| Etiquetar el resultado esperado | Respuesta exacta, o rúbrica/criterios cuando hay muchas respuestas válidas |
| Reservar una parte | Nunca ajustar el prompt o modelo con el conjunto de chequeo final |
| Protegerlo | Eliminar datos personales ([Privacidad y Cumplimiento](./privacidad-y-cumplimiento.md)) |

## 2. Elegir el Scoring

| Tipo de salida | Scoring |
|----------------|---------|
| Estructurada (JSON, clases) | Coincidencia exacta, exactitud por campo |
| Código | Parsea, pasa lint, pasan tests, análisis estático (como el score AST de aquí) |
| Texto libre | Rúbrica puntuada por personas o un modelo juez, con muestreo humano |
| Respuestas con recuperación | Correctas y fundamentadas en la fuente citada |

Los validadores automáticos son baratos y además sirven como disparadores de escalado en ejecución.

## 3. Comparar con Justicia

| Regla | Razón |
|-------|-------|
| Mismo conjunto y scoring para cada candidato | Comparación válida |
| Incluir una línea base (modelo actual, base sin afinar) | Muestra la ganancia real |
| Reportar intervalos de confianza o corridas repetidas | Los conjuntos pequeños son ruidosos |
| Reportar costo y latencia junto a la calidad | La decisión es un compromiso |

## 4. Monitorear en Producción

| Señal | Uso |
|-------|-----|
| Tasa de fallo de validadores | Caída temprana de calidad |
| Tasa de escalado por nivel | Salud del router y costo |
| Feedback de usuarios (ediciones, pulgares, traspasos) | Calidad en el mundo real |
| Deriva de entradas (temas, idiomas nuevos) | El conjunto de pruebas ya no es representativo |
| Revisión humana por muestreo | Detecta lo que los chequeos automáticos no ven |

## 5. Compuerta de Regresión

1. Cualquier cambio de modelo, prompt, herramientas o recuperación dispara el conjunto de pruebas.
2. Bloquear el lanzamiento si la métrica cae más allá de la tolerancia acordada.
3. Agregar al conjunto cada fallo de producción que se corrige.

## 6. Reglas de Honestidad

| Regla | Por qué |
|-------|---------|
| Publicar solo números medidos | Las afirmaciones no medidas se eliminaron a propósito de la documentación de este proyecto |
| Indicar tamaño de muestra y condiciones | Los resultados dependen del hardware y los datos |
| Registrar lo que no se probó | Evita falsa confianza |
