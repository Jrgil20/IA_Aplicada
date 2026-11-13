# Next Session Handoff — Spark evaluation run

> **Status:** pending. Prepared 2026-11-05 for execution on 2026-11-06.
> **Audience:** an AI agent (e.g. Antigravity via `/agy`) acting on behalf of the user, or the user directly.
> **Delete or mark DONE** at the bottom when finished, and remove the pointer in `AGENTS.md`.

## 0. Rules for the agent (read first)

- **Do not open SSH connections yourself.** Ask the user which shell is already connected to the DGX Spark and run commands only there. If you are not on the Spark, stop and ask.
- **Never touch ports 8080 or 8084** or any process you did not start. If port 8085 or 8086 is busy with another model, stop and report.
- **Do not improvise around failures.** If `spark_day.sh` fails, report the exact message and the fix from section 3; do not edit the scripts to make a check pass.
- **Do not use the regex fallback** (`--no-ast`): it is not comparable with earlier runs.
- **Do not edit published claims if the run is `INVALID`.**
- **Ask the user before `git push`, and before editing `MODEL_CARD.md`** (it mirrors a public Hugging Face page; never run `training/upload_to_hf.sh`).
- Artifacts (docs, code, commits) in English; chat may follow the user's language.

## 1. Goal

Replace unattributed and hard-coded benchmark numbers with a reproducible base-vs-fine-tune comparison on the DGX Spark. Context and findings: `proyecto/docs/evaluation/evaluation-audit-2026-11-05.md`.

## 2. Steps

| # | Command (on the Spark) | Expected |
| :-- | :-- | :-- |
| 1 | `cd ~/proyecto && git pull --ff-only` | Fast-forward to the latest `main`. If `~/proyecto` is not a git checkout, ask the user to copy `evaluation/`, `dataset/audit_dataset.py`, `docs/`. |
| 2 | `cd evaluation && ./spark_day.sh --preflight-only` | Ends with `Preflight OK.` and changes nothing. |
| 3 | `./spark_day.sh` | Builds the base GGUF if missing, serves both models on 8085/8086, runs the 30-case suite, writes `RESULT.md`. |
| 4 | `cat reports/spark-*/RESULT.md` (latest) | All checks ticked and a verdict line. |
| 5 | Ask the user to run the `scp -r ...` line printed at the end (from the laptop), or copy the folder yourself if you are on the laptop. | Folder in `proyecto/evaluation/reports/`. |

Detailed plan: `proyecto/docs/evaluation/spark-day-plan.md`. Manual fallback: `proyecto/docs/evaluation/spark-eval-runbook.md`.

## 3. If preflight fails

| Message | Fix |
| :-- | :-- |
| `llama-server not found` | `export LLAMA_SERVER=/path/to/llama-server` |
| `llama.cpp directory not found` | `export LLAMA_CPP_DIR=/path/to/llama.cpp` |
| `base model not cached` | Pre-cache `Qwen/Qwen2.5-Coder-1.5B-Instruct` or `export BASE_SNAPSHOT=<snapshot dir>` (ask the user before downloading). |
| `AST engine unavailable` | `cd ~/proyecto/cli && pnpm install --frozen-lockfile` |
| port 8085/8086 busy with another model | Stop and report; do not kill it. |
| `less than 8 GB free` | Ask the user to free disk space. |

## 4. How to read the result

- `INVALID RUN`: report which check failed; do not use any number.
- CAS gives **50/100 to empty or refusal output** (finding F9). A score near 50 means no usable code.
- Difference between fine-tune and base under 5 points: **do not claim improvement**. Two fine-tune runs already differ by ~4 points (76.33 vs 72.5).
- Read 5 completions per model in `reports/spark-*/cas/completions_*.jsonl`; confirm they are refactored TypeScript, not echoed input.

## 5. After a VALID run (docs only; keep each edit minimal and factual)

| Action | File |
| :-- | :-- |
| Replace base/cloud values with measured numbers, or keep them labeled "unmeasured" if not measured. | `proyecto/evaluation/compare_models.py` |
| Update scores and wording to match the report (with the uncertainty from section 4). | `proyecto/README.md`, `proyecto/docs/project/final-report-and-presentation.md`, `proyecto/docs/history/progress-and-milestones.md` |
| Mirror every change in Spanish. | `proyecto/es/...` |
| Add the measured results to the audit (new subsection). | `proyecto/docs/evaluation/evaluation-audit-2026-11-05.md` (+ `es/`) |
| Propose (do not apply without asking) edits to the public model card. | `proyecto/MODEL_CARD.md` |

Then: commit inside `proyecto/` (Conventional Commits, English, end with the attribution line the session provides), push, commit the updated submodule pointer in this repo, push.

## 6. Final report to the user

Return: verdict line, table of both models (avg, n, failed, degenerate), whether every check passed, anything skipped or failed, and files changed.

## 7. Out of scope (needs retraining, do not start)

- Rebuild the train/eval split and increase prompt diversity beyond 18 tasks.
- Fix `proyecto/training/train_lora.py:344` (`args.lora_dropout or ...` ignores `0.0`).
- Add validation during training.

---

**Completion:** DONE (2026-11-05). Measured run spark-20261105T143540Z: ecc-ft 74.83 vs qwen-base 58.00 (+16.83 delta). All checks passed. Docs updated.
