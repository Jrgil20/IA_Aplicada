# Product Decision Framework: Should This Feature Use AI?

> **Go/no-go guide.** Run this before choosing any model. AI adds cost, latency, and failure modes; it must earn its place.

---

## 1. Three Questions First

| # | Question | If "no" |
|---|----------|---------|
| 1 | Can deterministic code solve it (rules, search, parser, query)? | Use code. It is exact, free, and testable |
| 2 | Is a wrong answer tolerable, or can it be caught automatically or by a human? | Add a validator or human review, or do not ship |
| 3 | Is there a measurable success metric and test data? | Define them first; you cannot improve what you cannot score |

## 2. Fit Test

| Signal | Good fit for AI | Poor fit |
|--------|-----------------|----------|
| Input | Unstructured text, code, images, speech | Clean structured fields |
| Output | Fuzzy, many valid answers | Exactly one correct answer |
| Rules | Too many or too fuzzy to write | Few and stable |
| Error cost | Low or reversible | High and irreversible (payments, medical, legal) without review |
| Volume | Enough to justify the setup | One-off tasks a person does faster |

## 3. Build, Buy, or Adapt

| Option | Choose when | Watch out for |
|--------|-------------|---------------|
| Hosted API | Fast start, frontier quality, variable load | Per-token cost, data leaves your boundary, vendor changes |
| Self-hosted open model | Privacy, steady high volume, offline | Hardware, ops work, lower general quality |
| Fine-tuned small model | Narrow repeated task with data | Training data, evaluation, retraining when needs change |
| Off-the-shelf AI product | The need is generic | Little control, lock-in |

## 4. Define Before Building

| Item | Example form |
|------|--------------|
| User job | "Reviewer gets a refactor suggestion for a file" |
| Success metric | One number tied to the job (task success rate, score on a test set) |
| Failure policy | What happens on a wrong or empty answer: retry, escalate, show "not sure", hand to human |
| Constraints | Data sensitivity, latency budget, monthly cost ceiling, languages |
| Owner | Who monitors and updates the feature after launch |

## 5. Go/No-Go Checklist

- [ ] A deterministic alternative was considered and rejected with a reason.
- [ ] Success metric and test set exist.
- [ ] Failure behavior is designed, not accidental.
- [ ] Data flow is approved ([Privacy and Compliance](./privacy-and-compliance.md)).
- [ ] Cost ceiling is set ([Cost and Savings](./cost-and-savings.md)).
- [ ] An owner is named.

Any unchecked box means: do not ship yet.
