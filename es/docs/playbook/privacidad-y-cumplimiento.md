# Privacidad y Cumplimiento: ¿A Dónde Pueden Ir los Datos?

> **Guía práctica, no asesoría legal.** Decidir la ruta de los datos antes de elegir el modelo. Confirmar los puntos legales y contractuales con los responsables de tu organización.

---

## 1. Clasificar los Datos

| Clase | Ejemplos | Destinos permitidos |
|-------|----------|---------------------|
| Públicos | Documentación publicada, código abierto | Cualquier nivel |
| Internos | Código no público, documentos internos | Proveedores con contratos aprobados, o autoalojado |
| Confidenciales | Datos de clientes, credenciales, finanzas | Autoalojado, o proveedores con garantías explícitas por escrito |
| Regulados | Salud, pagos, datos personales bajo ley | Solo rutas aprobadas por cumplimiento; con frecuencia autoalojado |

Ante la duda, tratar los datos como una clase superior.

## 2. Preguntas por Proveedor

| Pregunta | Por qué |
|----------|---------|
| ¿Se retienen los datos del prompt y por cuánto tiempo? | La retención es una superficie de fuga |
| ¿Se usan los datos para entrenar modelos? | Los términos difieren por plan; verificar por escrito |
| ¿Dónde se procesan los datos (región)? | Requisitos de residencia |
| ¿Quién en el proveedor puede acceder? | Acceso de soporte y revisión de abuso |
| ¿Existe acuerdo empresarial u opción de cero retención? | Puede cambiar la respuesta |

No asumir la respuesta a partir del marketing del producto; leer los términos vigentes.

### Ejemplo: las restricciones de retención son por función (Claude API, verificado 2026-11-17)

| Función | Estado de Zero Data Retention (ZDR) |
|---------|-------------------------------------|
| Claude Fable 5.2 | Requiere retención de 30 días; no disponible bajo ZDR salvo autorización expresa de Anthropic |
| Hilos de mensajes (conversación conservada en el servidor, beta) | No elegible para ZDR |
| Managed Agents (bucle de agente hospedado) | Actualmente no elegible para ZDR ni para cobertura HIPAA BAA; el historial de sesión se conserva hasta que se elimina |

Lección: la elegibilidad depende del modelo **y** de la función, no solo del proveedor. Verificar cada función que se habilite contra tus requisitos de retención.

## 3. Minimizar lo que se Envía

| Técnica | Efecto |
|---------|--------|
| Enviar solo los campos que la tarea necesita | Menos exposición |
| Redactar o seudonimizar identificadores antes de la llamada | Reduce datos personales en los prompts |
| Mantener secretos (claves, contraseñas) fuera de los prompts | Los prompts pueden registrarse o filtrarse |
| Gateway sanitizador: un modelo local elimina partes sensibles antes de cualquier llamada a la nube | Defensa en profundidad (ver [SLMs Locales vs. LLMs en la Nube](../local-slm-vs-cloud-llm.md), sección 3.5) |

## 4. Tus Propios Logs y Cachés

| Elemento | Regla |
|----------|-------|
| Logs de prompts y respuestas | Redactar contenido sensible; retención corta; acceso restringido |
| Cachés | Acotar claves por usuario o tenant; nunca compartir entre fronteras de privacidad ([Caché de Prompts](../cache-de-prompts.md)) |
| Conjuntos de evaluación | Eliminar datos personales antes de almacenar o compartir |
| Datos de fine-tuning | Misma clasificación que los datos de origen; el modelo puede memorizarlos |

## 5. Regla de Decisión

```
clase de dato → destinos permitidos → niveles de modelo disponibles → luego optimizar costo
```

La privacidad limita el menú; el costo y la calidad eligen entre lo que queda.

## 6. Checklist

- [ ] Datos clasificados para esta función.
- [ ] Cada destino (proveedor o host) tiene términos verificados.
- [ ] Campos sensibles minimizados o redactados.
- [ ] Logs y cachés siguen las reglas anteriores.
- [ ] El responsable de cumplimiento aprobó la ruta de datos.
