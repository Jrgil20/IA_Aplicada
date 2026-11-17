# Playbook de IA Aplicada

> **Guía práctica para llevar IA a productos.** Decisiones, costos, seguridad, privacidad, calidad y lanzamiento. Cada archivo es un concepto, escrito para actuar. El resto de `docs/` es el trasfondo técnico (DGX, CUDA, QLoRA); esta carpeta es la capa de "qué hago". No se afirman cifras de costo, latencia ni calidad: mídelas en tu propio producto.

---

## Empieza Aquí: ¿Qué Archivo Necesito?

| Necesito... | Leer |
|-------------|------|
| Decidir si la IA tiene lugar en esta función | [Marco de Decisión de Producto](./marco-de-decision-de-producto.md) |
| Mapear una necesidad de producto a una arquitectura | [Necesidades a Arquitectura](./necesidades-a-arquitectura.md) |
| Elegir nivel de modelo: quedarme en Haiku, subir, ir más barato o ir privado | [Decisiones de Nivel de Modelo](./decisiones-de-nivel-de-modelo.md) |
| Bajar la factura sin perder calidad | [Costos y Ahorros](./costos-y-ahorros.md) |
| Decidir a dónde pueden ir mis datos | [Privacidad y Cumplimiento](./privacidad-y-cumplimiento.md) |
| Asegurar una función de IA | [Checklist de Hardening](./checklist-de-hardening.md) |
| Saber si es suficientemente buena y si se mantiene así | [Evaluación y Calidad](./evaluacion-y-calidad.md) |
| Lanzarla y operarla | [Preparación para Producción](./preparacion-para-produccion.md) |
| Responder preguntas a partir de mis propios documentos | [RAG en la Práctica](./rag-en-la-practica.md) |
| Decidir si necesito un agente y construirlo de forma segura | [Agentes y Uso de Herramientas](./agentes-y-uso-de-herramientas.md) |
| Ver el playbook aplicado a un proyecto real | [Caso de Estudio: Edge Clean Copilot](./caso-de-estudio-edge-clean-copilot.md) |

## Orden de Lectura para una Función Nueva

1. Marco de Decisión de Producto → ¿se justifica la IA?
2. Necesidades a Arquitectura → ¿qué patrón?
3. Privacidad y Cumplimiento → ¿por dónde pueden fluir los datos?
4. Decisiones de Nivel de Modelo → ¿qué clase de modelo?
5. Evaluación y Calidad → ¿cómo sabré que funciona?
6. Checklist de Hardening y Preparación para Producción → lanzar con seguridad.
7. Costos y Ahorros → afinar cuando ya funciona.

## Referencias Técnicas Relacionadas

| Tema | Archivo |
|------|---------|
| Cascada de reglas, SLM local, LLM de frontera | [Enrutamiento por Costo](../enrutamiento-por-costo.md) |
| Qué nivel encaja con cada tarea | [Casos de Uso de IA Aplicada](../casos-de-uso-ia-aplicada.md) |
| Laptop vs. DGX Spark vs. nube | [Escalado de Cargas de IA](../escalado-cargas-ia.md) |
| Caché de respuesta, semántica y de prefijo | [Caché de Prompts](../cache-de-prompts.md) |
| Runtimes, capacidad, topología | [Servir Modelos para Apps](../servir-modelos-para-apps.md) |
| Criterios y proceso de selección | [Selección de Modelos](../seleccion-de-modelos.md) |
| Compromisos local vs. nube | [SLMs Locales vs. LLMs en la Nube](../local-slm-vs-cloud-llm.md) |
| Auditoría de seguridad y túneles | Skills `inference-security-hardening`, `secure-ssh-tunnels` |
