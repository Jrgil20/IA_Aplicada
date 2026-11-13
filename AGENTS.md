# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> This file is the single source of truth: `CLAUDE.md`, `.cursorrules`, `.windsurfrules`, `.clinerules` and `GEMINI.md` are all symlinks to `AGENTS.md`. Edit `AGENTS.md`, never the links.

## Conventions

- **Artifacts in English** (code, comments, docs, commits, file names). Chat replies may follow the user's language.
- **Spanish mirror under `es/`** (and `proyecto/es/`): when root English docs change, mirror them there. Spanish file names are allowed only inside `es/`.
- **AI-first docs:** tables/key-value lists over prose, one concept per file, a `README.md` index in every directory.
- File names: lowercase-with-hyphens. Commits: Conventional Commits, English.

## Repository layout

Course repo (UCAB Applied AI) with three content areas: `docs/` (knowledge base: DGX Spark, CUDA, QLoRA), `labs/` (lab logs/code), `proyecto/` (semester project). `scratch/` is gitignored throwaway; `.agents/skills/` holds agent skills (`edge-clean-copilot`, `inference-security-hardening`, `secure-ssh-tunnels`).

### Git submodules (easy to get wrong)

- `proyecto/` is a **separate repo** (`Jrgil20/edge-clean-copilot`, branch `main`). Commit and push inside `proyecto/` first, then commit the updated pointer in this parent repo (history shows `chore(submodule): update edge-clean-copilot pointer ...`).
- `.agents/dev-ai-toolkit` is also a submodule.
- `*.gguf` and model weights are gitignored; never commit them.

## Semester project: Edge Clean Copilot (`proyecto/`)

Fine-tuned SLM (Qwen2.5-Coder-1.5B-Instruct, LoRA) quantized to GGUF Q4_K_M, served via `llama.cpp`, wrapped by a hexagonal TypeScript CLI that refactors code toward Clean Architecture/DDD offline. Operating model: "Cold Staging, Hot Burst" — develop/test offline on a laptop with mocks, then burst to the DGX Spark cluster (over SSH) for distillation/training.

Start a session with `python3 proyecto/status.py` (zero-dependency health/next-steps dashboard) and the project reference in `proyecto/docs/project/project-analysis.md` (or historical log at `proyecto/docs/history/progress-and-milestones.md`). The `edge-clean-copilot` skill (`.agents/skills/edge-clean-copilot/SKILL.md`) is the operational guide.

### Pipeline (data flows left to right)

`dataset/` (ChatML seed pairs, train/eval split) → `training/train_lora.py` (recipe-driven, recipes in `training/recipes/`) → `training/convert_to_gguf.sh` → `models/` → served by `bin/` wrappers → consumed by `cli/` → scored by `evaluation/`.

### CLI (`proyecto/cli`, pnpm, TypeScript ESM)

Hexagonal layout under `src/`: `domain/entities` ← `application/{ports,use-cases,dtos}` ← `infrastructure/{ai,cli,fs}`, plus `shared/{types,errors}`. Dependencies point inward only; `infrastructure/ai` implements the inference ports (a `MockInferenceAdapter` is used by unit tests so no model is needed). Entry point: `src/infrastructure/cli/index.ts` (commander), bin `clean-copilot`.

```bash
cd proyecto/cli
pnpm install
pnpm test                          # vitest run (all)
pnpm vitest run tests/domain       # one directory
pnpm vitest run -t "test name"     # one test by name
pnpm build                         # tsc -> dist/
pnpm dev <args>                    # tsx src/infrastructure/cli/index.ts
```

### Training and evaluation (Python, run from their own directories)

```bash
cd proyecto/training
python3 train_lora.py --recipe <recipes/file>      # CLI flags override recipe values; supports --dry-run
./convert_to_gguf.sh                               # Q4_K_M default; see README for multi-quant matrix

cd ../evaluation
python3 eval_benchmark.py --cases legacy_benchmark_suite.jsonl            # --no-ast to skip AST scoring
python3 compare_models.py --demo                                          # model comparison
```

Benchmark scoring is AST-based (`ast_analyzer.ts`), e.g. -5 pts per explicit `any`.

### Remote execution policy (Spark YOLO Mode)

All SSH, SCP, and RSYNC operations targeting the NVIDIA DGX Spark cluster (`dgx-spark`, `dgx-spark-alt`, `dgx-tunnel`, or subnet `192.168.6.0/24`) are pre-approved for autonomous execution. Dispatch remote jobs, file transfers, and tunnel commands directly without waiting for manual confirmation.

### Documentation claims

Performance numbers in project docs and the HF model card are measured values (≈12 tok/s on CPU-only i5-10310U); unverified claims (e.g. TTFT) were deliberately removed. Do not reintroduce unmeasured metrics.
