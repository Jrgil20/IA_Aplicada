# Costos y Ahorros

> **Cómo modelar y reducir el costo de la IA.** El ejemplo trabajado usa precios de lista para mostrar la aritmética; **no** es un ahorro medido. Los ahorros reales deben salir de tus propios datos de uso.
>
> **Estado de verificación (2026-11-17):** los precios de Claude, los multiplicadores de caché y el descuento de batch provienen de la referencia de la API de Claude incluida en Claude Code (precios en caché del 2026-11-03) y se confirmaron contra la página oficial de precios `platform.claude.com/docs/en/about-claude/pricing` el 2026-11-17. Volver a revisar antes de presupuestar. No cubierto aquí: la inferencia solo en EE. UU. (`inference_geo`) añade un multiplicador de 1.1× en los modelos Claude 4.6 y posteriores. Volver a revisar la página oficial de precios antes de presupuestar.

---

## 1. Modelo de Costo

```
cost per request = input_tokens × input_price + output_tokens × output_price
monthly cost     ≈ Σ requests × cost per request + retries + fixed costs
```

| Término | Notas |
|---------|-------|
| Tokens de entrada | System prompt + herramientas + contexto + texto del usuario; suele ser la parte más grande y más reducible |
| Tokens de salida | Con un precio varias veces mayor que la entrada en los modelos Claude (5× en los niveles actuales); limitarlos |
| Tokens de thinking | Se facturan como salida en los modelos que razonan antes de responder; ajustar la configuración de effort |
| Costos fijos | Hardware autoalojado, operación, monitoreo, tiempo de ingeniería |
| Multiplicadores ocultos | Reintentos, bucles de agentes, conversaciones largas reenviadas en cada turno |

**Medir, no estimar:** leer los conteos de tokens desde los campos de uso de la API (o los reportes de uso/costo del proveedor). Juzgar el **costo por tarea completada**, no por solicitud: una solicitud más barata que necesita reintentos o turnos adicionales no es más barata.

## 2. Precios de Referencia (API de Claude, por millón de tokens)

| Modelo | Entrada | Salida | Lectura de caché |
|--------|---------|--------|------------------|
| Claude Haiku 5.5 | $0.10 | $0.50 | $0.01 |
| Claude Sonnet 5.5 | $2.00 | $10.00 | $0.10 |
| Claude Opus 5.5 | $4.00 | $20.00 | $0.20 |

Los precios de Haiku 5.5 aplican a prompts de hasta 100K tokens ($0.50 / $2.50 por encima). Las escrituras de caché cuestan 1.25× (TTL de 5 minutos) o 2× (TTL de 1 hora) el precio de entrada. La Batch API descuenta un 50% en cada token, incluidos los tokens de caché. Los precios en Amazon Bedrock y Vertex AI los fijan esas plataformas.

## 3. Ejemplo Trabajado (solo aritmética)

Supuestos: 100,000 solicitudes al mes; 3,000 tokens de entrada cada una (2,500 de prefijo de sistema estable + 500 variables); 300 tokens de salida cada una.

| Escenario | Costo de entrada | Costo de salida | Total mensual |
|-----------|-----------------:|----------------:|--------------:|
| Todo Opus 5.5, sin caché | $1,200 | $600 | $1,800 |
| Todo Sonnet 5.5, sin caché | $600 | $300 | $900 |
| Sonnet 5.5 con caché de prefijo (prefijo leído a $0.10/MTok, escrituras ignoradas) | $125 | $300 | ~$425 |
| Lo mismo, ejecutado mediante la Batch API (solo trabajo no urgente) | | | ~$213 |
| Todo Haiku 5.5, sin caché | $30 | $15 | $45 |
| Cascada: cada solicitud prueba Haiku, el 20% escala a Sonnet | | | $45 + $180 = $225 |

Cómo leerlo:

- Cachear el prefijo estable reduce a la mitad la factura de Sonnet con esta forma porque la entrada domina. Solo funciona si el prefijo es idéntico byte a byte y las solicitudes llegan dentro del TTL.
- La cascada parece barata **solo si** el 80% de Haiku es realmente suficientemente bueno. Esa es una afirmación de calidad que debes demostrar con tu conjunto de pruebas ([Evaluación y Calidad](./evaluacion-y-calidad.md)).
- Los tokens de salida pasan a ser el costo dominante una vez que la entrada está cacheada; limitar la longitud de salida es la siguiente palanca.

## 4. Palancas de Ahorro (primero las gratuitas)

| Orden | Palanca | Qué hace | Compromiso |
|-------|---------|----------|------------|
| 1 | Quitar la IA donde el código sirve | Costo de inferencia cero | Requiere una regla determinista |
| 2 | Caché de prefijo de prompt | Prefijos repetidos a una fracción del precio ([Caché de Prompts](../cache-de-prompts.md)) | Requiere prefijos estables y tráfico constante |
| 3 | Higiene de entrada | Prompts más cortos, solo el contexto necesario, sin instrucciones duplicadas | Probar la calidad tras recortar |
| 4 | Higiene de salida | Límites de longitud, salida estructurada, sin repetir la pregunta | Riesgo de truncamiento |
| 5 | Higiene de bucles | Limitar pasos de agentes y reintentos; detener bucles temprano | Puede terminar tareas que habrían tenido éxito |
| 6 | Procesar por lotes lo no urgente | 50% de descuento; resultados en menos de 24 horas | No sirve para usuarios que están esperando |
| 7 | Bajar la configuración de effort | Menos tokens de thinking con el mismo modelo | Calidad en tareas difíciles; medir por ruta |
| 8 | Caché de respuesta / semántica | Evita llamar al modelo en repeticiones | Aciertos obsoletos o erróneos |
| 9 | Rutear por dificultad | Nivel barato primero, escalar al fallar ([Enrutamiento por Costo](../enrutamiento-por-costo.md)) | Errores del router; se pierde la reutilización de caché entre modelos |
| 10 | Modelo más barato o abierto | Menor costo por token o fijo | Debe pasar tu evaluación |
| 11 | Autoalojar | Sin tarifa por token | Costo de hardware y operación |

**Antes de construir una cascada multimodelo**, medir la alternativa más simple: un modelo capaz con una configuración de effort más baja. Los modelos más nuevos con effort bajo suelen igualar a modelos anteriores con effort alto, y un solo modelo mantiene una sola caché.

## 5. Punto de Equilibrio Nube vs. Autoalojado

```
break-even volume = fixed monthly cost of self-hosting ÷ API cost per request saved
```

| Variable | Pregunta |
|----------|----------|
| Volumen | ¿Tokens por mes, sostenidos o con picos? |
| Hardware | Costo de compra o alquiler, período de amortización, energía |
| Operación | ¿Quién lo ejecuta, parchea y monitorea? Contar esas horas |
| Utilización | ¿El hardware estará ocupado, o ocioso la mayor parte del tiempo? |
| Calidad | ¿El modelo abierto cumple tu métrica? Si no, la comparación no es válida |

Autoalojar gana en costo solo con una utilización alta y constante **y** un modelo abierto que pase tu evaluación. Con volumen bajo o con picos, el precio por token suele ser más barato (en el ejemplo anterior, Haiku cuesta $45/mes, menos que la mayoría de las amortizaciones de hardware). La privacidad aún puede justificar autoalojar a un costo mayor ([Privacidad y Cumplimiento](./privacidad-y-cumplimiento.md)).

## 6. Barandillas contra Costos Descontrolados

| Barandilla | Propósito |
|------------|-----------|
| Rate limits por usuario y globales | Frenar abusos y bucles |
| Máximo de tokens y de pasos por solicitud | Acotar agentes y salidas largas |
| Alertas de presupuesto y límites de gasto | Detectar picos temprano |
| Gasto registrado por función, ruta y nivel | Saber a dónde va el dinero |
| Tasa de aciertos de caché monitoreada | Detectar regresiones silenciosas de la caché |
| Interruptor hacia una ruta más barata | Degradar con gracia al exceder el presupuesto |

## 7. Nunca Ahorrar Dinero A Costa De

- Omitir la evaluación tras pasar a una ruta más barata.
- Enviar datos sensibles a un host más barato.
- Recortar controles de seguridad o validadores.
- Bajar `max_tokens` tanto que las respuestas se corten y haya que reintentarlas.
