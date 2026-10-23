# Base de Conocimiento Técnico — Edge Clean Copilot

> **Audiencia Principal:** Agentes de Inteligencia Artificial (Asistentes de código, pipelines RAG, planificadores autónomos)  
> **Audiencia Secundaria:** Desarrolladores y evaluadores académicos  

Este directorio contiene la documentación técnica oficial, registros de telemetría de sesiones, bitácoras de hitos y el roadmap de ingeniería para el proyecto de semestre **Edge Clean Copilot**.

---

## 1. Índice de Documentación

| Documento | Propósito | Contenido Clave |
| :--- | :--- | :--- |
| **[Roadmap Detallado de Ejecución](./detailed-roadmap.md)** | Plan Maestro Operativo (Semanas 4–15) | Hiperparámetros, metas de cuantización, métricas de evaluación automatizadas y tareas semanales. |
| **[Progreso e Hitos Verificados](./progress-and-milestones.md)** | Tablero de Estado en Vivo | Desglose empírico de avances en las Fases 1, 2, 3 y 4. |
| **[Reporte de Sesión: 2026-10-22](./session-2026-10-22-burst-and-lessons.md)** | Informe Técnico y Análisis de Causa Raíz | Aislamiento multi-instancia en puertos (8085 vs 8080), burst de dataset a 160 muestras, setup del runtime en GB10. |

---

## 2. Recursos Relacionados del Proyecto

- **[Propuesta y Visión Técnica](../propuesta.md):** Articulación académica, hipótesis central y marco teórico.
- **[Directorio del Dataset](../../../proyecto/dataset/README.md):** Generadores sintéticos, ejemplos semilla canónicos y suites de validación.
- **[Pipeline de Entrenamiento LoRA](../../../proyecto/training/README.md):** Bucle de entrenamiento en PyTorch, collator dinámico y utilidades de merge.
- **[CLI Hexagonal](../../../proyecto/cli/README.md):** Implementación en TypeScript con Ports & Adapters y adaptadores mock offline.
