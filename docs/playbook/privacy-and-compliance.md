# Privacy and Compliance: Where May the Data Go?

> **Practical guide, not legal advice.** Decide the data path before choosing the model. Confirm legal and contractual points with the responsible people in your organization.

---

## 1. Classify the Data

| Class | Examples | Allowed destinations |
|-------|----------|----------------------|
| Public | Published docs, open-source code | Any tier |
| Internal | Non-public code, internal docs | Providers with approved contracts, or self-hosted |
| Confidential | Customer data, credentials, financials | Self-hosted, or providers with explicit written guarantees |
| Regulated | Health, payment, personal data under law | Only paths approved by compliance; often self-hosted |

When unsure, treat the data as one class higher.

## 2. Questions per Provider

| Question | Why |
|----------|-----|
| Is prompt data retained, and for how long? | Retention is a leak surface |
| Is data used to train models? | Contractual terms differ by plan; verify in writing |
| Where is data processed (region)? | Residency requirements |
| Who at the provider can access it? | Support and abuse-review access |
| Is there an enterprise agreement or zero-retention option? | May change the answer |

Do not assume the answer from the product's marketing; read the current terms.

### Example: retention constraints are per feature (Claude API, verified 2026-11-17)

| Feature | Zero Data Retention (ZDR) status |
|---------|----------------------------------|
| Claude Fable 5.2 | Requires 30-day retention; not available under ZDR unless Anthropic expressly authorizes it |
| Message threads (server-kept conversation, beta) | Not ZDR eligible |
| Managed Agents (hosted agent loop) | Not currently eligible for ZDR or HIPAA BAA coverage; session history is kept until deleted |

Lesson: eligibility depends on the model **and** the feature, not only the provider. Check each feature you enable against your retention requirements.

## 3. Minimize What You Send

| Technique | Effect |
|-----------|--------|
| Send only the fields the task needs | Less exposure |
| Redact or pseudonymize identifiers before the call | Reduces personal data in prompts |
| Keep secrets (keys, passwords) out of prompts entirely | Prompts can be logged or leaked |
| Sanitizing gateway: a local model strips sensitive parts before any cloud call | Defense in depth (see [Local SLMs vs. Cloud LLMs](../local-slm-vs-cloud-llm.md), section 3.5) |

## 4. Your Own Logs and Caches

| Item | Rule |
|------|------|
| Prompt and response logs | Redact sensitive content; short retention; restricted access |
| Caches | Scope keys per user or tenant; never share across privacy boundaries ([Prompt Caching](../prompt-caching.md)) |
| Evaluation datasets | Remove personal data before storing or sharing |
| Fine-tuning data | Same classification as the source data; the model can memorize it |

## 5. Decision Rule

```
data class → allowed destinations → model tiers available → then optimize cost
```

Privacy limits the menu; cost and quality choose from what remains.

## 6. Checklist

- [ ] Data classified for this feature.
- [ ] Each destination (provider or host) has verified terms.
- [ ] Sensitive fields minimized or redacted.
- [ ] Logs and caches follow the rules above.
- [ ] Compliance owner has approved the data path.
