# Applied Artificial Intelligence — UCAB

Central repository for the **Applied Artificial Intelligence** course (School of Computer Engineering, Universidad Católica Andrés Bello — Caracas, Venezuela).

**Student:** Jesús Rodolfo Gil Farías  
**Term:** 2026-2027  

> 🌐 **[Versión en español disponible →](../README.md)**

---

## Documentation Philosophy: AI-First

> **The documentation in this repository is designed for agentic consumption.**

All content in `/docs`, `/proyecto`, and `/labs` follows **AI-first documentation** principles:

- **Primary audience:** AI agents (coding assistants, autonomous agents, RAG pipelines) that require structured context to operate on the repository.
- **Secondary audience:** Humans. Documents are perfectly readable by humans, but formatting decisions prioritize parsability and automated consumption.

### Applied AI-First Conventions

| Convention | Purpose |
| :--- | :--- |
| Consistent heading hierarchy (`#`, `##`, `###`) | Enables semantic navigation and chunking by section. |
| Tables for structured data | Extractable as key-value pairs without ambiguity by an LLM. |
| Code blocks with explicit language (` ```bash `, ` ```python `) | Identifiable as executable commands vs. explanatory text. |
| Lists with `- **Key:** Value` format | Facilitates attribute extraction without prose parsing. |
| One concept per file, one file per concept | Reduces context window overhead required for each query. |
| `README.md` as index in each directory | Provides the agent with a navigation map without scanning the filesystem. |
| Metadata at document start (title, status, purpose) | Allows the agent to quickly decide document relevance before reading in full. |

> [!NOTE]
> Agents operating on this repository should start by reading this `README.md` to obtain the complete navigation map, and then consult the `README.md` in each subdirectory to delve deeper into a specific module.

---

## Repository Structure

```
.
├── proyecto/     # Semester project: Edge Clean Copilot, proposal and ideas
├── labs/         # Logs, code, and submissions for hands-on labs
└── docs/         # Technical knowledge base (DGX Spark, CUDA, QLoRA, etc.)
```

### Sections

- [**Project (`/proyecto`)**](./proyecto/README.md):
  - [Technical Proposal: Edge Clean Copilot](./proyecto/propuesta.md)
  - [Idea Bank](./proyecto/ideas.md)
- [**Labs (`/labs`)**](./labs/README.md):
  - [Lab 01: Environment Setup & Local Inference](./labs/lab-01.md)
- [**Documentation (`/docs`)**](./docs/README.md):
  - [NVIDIA DGX Spark](./docs/dgx/README.md)
  - [CUDA & GPU Acceleration](./docs/cuda/README.md)
  - [LoRA & QLoRA (PEFT)](./docs/qlora/README.md)
  - [Useful Commands](./docs/useful-commands.md)
  - [Environment Specifications](./docs/environment.md)

---

## License

Distributed under the license specified in [LICENSE](../LICENSE).
