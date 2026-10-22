# Proyecto de Semestre — IA Aplicada: Edge Clean Copilot

Este directorio contiene los materiales, documentación técnica, datasets sintéticos, scripts de entrenamiento e implementaciones cliente de **Edge Clean Copilot**, el proyecto final de la asignatura **Inteligencia Artificial Aplicada** en la UCAB.

---

## 1. Índice de Documentación del Proyecto

- **[Centro de Documentación Técnica (`docs/`)](./docs/README.md):** Especificaciones operativas completas, registros de telemetría y memorias técnicas de ingeniería.
  - **[Roadmap Detallado de Ejecución (Semanas 4–15)](./docs/detailed-roadmap.md):** Plan maestro táctico cubriendo el entrenamiento LoRA, cuantización GGUF y métricas de benchmark.
  - **[Progreso e Hitos Verificados](./docs/progress-and-milestones.md):** Tablero en vivo con el avance verificado a lo largo de las 4 fases.
  - **[Reporte de Sesión: 2026-10-22](./docs/session-2026-10-22-burst-and-lessons.md):** Análisis de causa raíz, aislamiento de puertos (8085 vs 8080), burst de 160 muestras y lecciones aprendidas.
- **[Propuesta Técnica](./propuesta.md):** Visión original del proyecto, hipótesis, principios de Clean Architecture y articulación académica.
- **[Banco de Ideas](./ideas.md):** Exploración preliminar de alternativas arquitectónicas.

---

## 2. Subsistemas del Proyecto

```
proyecto/
├── docs/       # Especificaciones técnicas, bitácoras de sesión y roadmap
├── dataset/    # Datasets ChatML semilla y sintéticos (160 ejemplos, ~186k tokens)
├── training/   # Pipeline de fine-tuning LoRA en PyTorch con consolidación nativa
└── cli/        # Cliente CLI con Arquitectura Hexagonal en TypeScript (Ports & Adapters)
```

---

## 3. Estado Actual del Proyecto

- **Progreso Global:** **57%**
- **Completada:** **Fase 1 (Infraestructura y Dataset del Teacher)** — 100%
- **Activa / Lista para Disparar:** **Fase 2 (Adaptación LoRA y Especialización)** — 80% (Runtime y 73% de pesos base en la DGX Spark)
- **Pendiente:** **Fase 3 (Consolidación y Cuantización a GGUF)**
- **En Progreso:** **Fase 4 (Cliente CLI e Inferencia Offline en el Edge)** — 50% (Dominio central y adaptadores mock listos)
