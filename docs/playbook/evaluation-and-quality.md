# Evaluation and Quality: Is It Good Enough, and Does It Stay Good?

> **Evaluation guide.** Every decision in this playbook (model tier, routing, cheaper model, caching) depends on measuring quality on your task. This repo's own example: `proyecto/evaluation/` scores outputs with an AST-based metric (CAS) and reports bootstrap confidence intervals.

---

## 1. Build a Test Set

| Step | Detail |
|------|--------|
| Collect real cases | From actual or realistic usage, not only easy examples |
| Cover the edges | Rare inputs, failures, long inputs, each language you support |
| Label the expected result | Exact answer, or rubric/criteria when many answers are valid |
| Keep a held-out part | Never tune the prompt or model on the final check set |
| Protect it | Remove personal data ([Privacy and Compliance](./privacy-and-compliance.md)) |

## 2. Choose Scoring

| Output type | Scoring |
|-------------|---------|
| Structured (JSON, classes) | Exact match, field accuracy |
| Code | Parses, lints, tests pass, static analysis (like the AST score here) |
| Free text | Rubric scored by humans or a judge model, spot-checked by humans |
| Retrieval answers | Correct and grounded in the cited source |

Automatic validators are cheap and also serve as runtime escalation triggers.

## 3. Compare Fairly

| Rule | Reason |
|------|--------|
| Same test set and scoring for every candidate | Valid comparison |
| Include a baseline (current model, base model without tuning) | Shows the real gain |
| Report confidence intervals or repeated runs | Small sets are noisy |
| Report cost and latency next to quality | The decision is a trade-off |

## 4. Monitor in Production

| Signal | Use |
|--------|-----|
| Validator failure rate | Early quality drop |
| Escalation rate per tier | Router health and cost |
| User feedback (edits, thumbs, handoffs) | Real-world quality |
| Input drift (new topics, languages) | Test set no longer representative |
| Sampled human review | Catches what automatic checks miss |

## 5. Regression Gate

1. Any change to model, prompt, tools, or retrieval triggers the test set.
2. Block release if the metric drops beyond the agreed tolerance.
3. Add every production failure you fix to the test set.

## 6. Honesty Rules

| Rule | Why |
|------|-----|
| Publish only measured numbers | Unmeasured claims were removed from this project's docs on purpose |
| State sample size and conditions | Results depend on hardware and data |
| Record what was not tested | Prevents false confidence |
