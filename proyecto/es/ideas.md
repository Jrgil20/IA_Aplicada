# Banco de Ideas de Proyecto

Registro de ideas exploradas, descartadas y seleccionadas para el proyecto de la materia.

---

## 1. Idea Seleccionada: Edge Clean Copilot

- **Concepto:** SLM (1.5B–3B) especializado mediante LoRA para garantizar reglas estrictas de Clean Architecture y suites BDD (Arrange-Act-Assert) en local (GGUF).
- **Justificación:** Resuelve un dolor real de ingeniería de software (acoplamiento y fuga de abstracción provocada por Copilots comerciales) con alta viabilidad técnica aprovechando la DGX Spark y ejecución local en hardware modesto.
- **Detalle completo:** Ver [Propuesta Técnica](./propuesta.md).

---

## 2. Ideas Alternativas Evaluadas

### A. RAG Especializado en Arquitectura de Software
- **Concepto:** Sistema de Retrieval-Augmented Generation sobre documentación formal de arquitectura (patrones GoF, Clean Code, DDD) con vector store local.
- **Trade-off:** Depende de recuperación en tiempo de ejecución y modelos generales; no internaliza los patrones en los pesos del modelo.

### B. Linters Asistidos por Modelos Livianos
- **Concepto:** Agente de análisis estático que evalúa commits antes de mergear en un hook de pre-push.
- **Trade-off:** Puede integrarse a futuro como cliente del SLM especializado.
