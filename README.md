# Inteligencia Artificial Aplicada — UCAB

Repositorio central para la cátedra de **Inteligencia Artificial Aplicada** (Escuela de Ingeniería Informática, Universidad Católica Andrés Bello — Caracas, Venezuela).

**Estudiante:** Jesús Rodolfo Gil Farías  
**Período:** 2026-2027  

> 🌐 **[English version available →](./en/README.md)**

---

## Filosofía de Documentación: AI-First

> **La documentación de este repositorio está diseñada para consumo agéntico.**

Todo el contenido en `/docs`, `/proyecto` y `/labs` sigue principios de **documentación AI-first**:

- **Audiencia primaria:** Agentes de IA (coding assistants, agentes autónomos, pipelines de RAG) que necesitan contexto estructurado para operar sobre el repositorio.
- **Audiencia secundaria:** Humanos. Los documentos son perfectamente legibles por personas, pero las decisiones de formato priorizan la parsabilidad y el consumo automático.

### Convenciones AI-First aplicadas

| Convención | Propósito |
| :--- | :--- |
| Encabezados jerárquicos consistentes (`#`, `##`, `###`) | Permiten navegación semántica y chunking por secciones. |
| Tablas para datos estructurados | Extraíbles como key-value sin ambigüedad por un LLM. |
| Bloques de código con lenguaje explícito (` ```bash `, ` ```python `) | Identificables como comandos ejecutables vs. texto explicativo. |
| Listas con formato `- **Clave:** Valor` | Facilitan extracción de atributos sin parsing de prosa. |
| Un concepto por archivo, un archivo por concepto | Reduce el tamaño de contexto necesario para cada consulta. |
| `README.md` como índice en cada directorio | Proporciona al agente un mapa de navegación sin escanear el filesystem. |
| Metadatos al inicio del documento (título, estado, propósito) | Permite al agente decidir rápidamente si el documento es relevante antes de leerlo completo. |

> [!NOTE]
> Los agentes que operen sobre este repositorio deben comenzar leyendo este `README.md` para obtener el mapa completo de navegación, y luego consultar el `README.md` de cada subdirectorio para profundizar en un módulo específico.

---

## Estructura del Repositorio

```
.
├── proyecto/     # Proyecto de semestre: Edge Clean Copilot, propuesta e ideas
├── labs/         # Bitácoras, código y entregas de laboratorios prácticos
└── docs/         # Base de conocimiento técnico (DGX Spark, CUDA, QLoRA, etc.)
```

### Secciones

- [**Proyecto (`/proyecto`)**](./proyecto/README.md):
  - [Propuesta Técnica: Edge Clean Copilot](./proyecto/propuesta.md)
  - [Banco de Ideas](./proyecto/ideas.md)
- [**Laboratorios (`/labs`)**](./labs/README.md):
  - [Lab 01: Configuración de Entorno & Inferencia Local](./labs/lab-01.md)
- [**Documentación (`/docs`)**](./docs/README.md):
  - [NVIDIA DGX Spark](./docs/dgx/README.md)
  - [CUDA & GPU Acceleration](./docs/cuda/README.md)
  - [LoRA & QLoRA (PEFT)](./docs/qlora/README.md)
  - [Comandos Útiles](./docs/comandos-utiles.md)
  - [Especificaciones de Entorno](./docs/entorno.md)

---

## Licencia

Distribuido bajo la licencia especificada en [LICENSE](./LICENSE).