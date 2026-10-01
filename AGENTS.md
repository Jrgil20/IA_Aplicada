# Repository Rules for AI Agents

> **This file is the authoritative source of project conventions for any AI model, coding assistant, or autonomous agent operating on this repository.**

---

## 1. Language Policy

- **All written artifacts default to English.** This includes: code, comments, commit messages, documentation, file names, variable names, UI strings, and any generated content.
- **Spanish (`es/`) is the secondary locale.** A full Spanish mirror exists under `es/`. When new documentation is created or updated in the root (English), it should eventually be mirrored in `es/`.
- **Conversational replies to the user may be in Spanish** (or whichever language the user writes in), but the artifacts produced (files, code, docs) remain in English.

## 2. Documentation Philosophy: AI-First

- **Primary audience:** AI agents (coding assistants, autonomous agents, RAG pipelines).
- **Secondary audience:** Humans.
- Formatting decisions prioritize parsability and automated consumption over visual aesthetics.
- One concept per file, one file per concept.
- Every directory has a `README.md` that serves as a navigation index.
- Use structured formats (tables, key-value lists, typed code blocks) over free-form prose.

## 3. Repository Structure

```
.                    # English (native / AI-first)
├── docs/            # Technical knowledge base (DGX Spark, CUDA, QLoRA, etc.)
├── labs/            # Lab session logs, code, and deliverables
├── proyecto/        # Semester project: Edge Clean Copilot
├── es/              # Spanish mirror of all documentation
└── AGENTS.md        # This file — project rules for AI agents
```

## 4. Commit Conventions

- Use [Conventional Commits](https://www.conventionalcommits.org/) format.
- Commit messages are always in English.
- Common prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`.

## 5. File Naming

- Use lowercase with hyphens for file names: `useful-commands.md`, `lab-01.md`.
- Use `README.md` as the index file in every directory.
- No Spanish in file names at root level; Spanish file names are acceptable only inside `es/`.
