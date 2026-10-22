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
├── docs/        # Especificaciones técnicas, bitácoras de sesión y roadmap
├── dataset/     # Datasets semilla, pool sintético y particiones train/eval (168 muestras)
├── training/    # Pipeline de fine-tuning LoRA en PyTorch y script de cuantización GGUF
├── cli/         # Cliente CLI con Arquitectura Hexagonal en TypeScript (28 tests en verde)
├── evaluation/  # Harness automatizado de benchmark de Clean Architecture (CAS 0-100)
└── status.py    # Diagnóstico instantáneo y tablero de reanudación sin dependencias
```

---

## 3. Estado Actual del Proyecto

- **Progreso Global:** **70%**
- **Completada:** **Fase 1 (Infraestructura y Dataset del Teacher)** — 100%
- **Lista para Ráfaga:** **Fase 2 (Adaptación LoRA y Especialización)** — 85% (Runtime y 73% de pesos base en la DGX Spark)
- **Automatización Lista:** **Fase 3 (Consolidation y Cuantización a GGUF)** — 50% (`convert_to_gguf.sh` probado)
- **En Progreso / Benchmark Operativo:** **Fase 4 (Cliente CLI e Inferencia Offline)** — 70% (28 tests unitarios en verde, benchmark funcional)
