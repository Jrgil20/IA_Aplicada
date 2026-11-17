# Production Readiness: Ship and Operate an AI Feature

> **Launch checklist.** Operational counterpart of the playbook. Infrastructure details live in [Model Serving for Apps](../model-serving-for-apps.md); security items in the [Hardening Checklist](./hardening-checklist.md).

---

## 1. Before Launch

| Area | Requirement |
|------|-------------|
| Evaluation | Test set passes the agreed metric ([Evaluation and Quality](./evaluation-and-quality.md)) |
| Failure behavior | Defined for wrong, empty, slow, and refused answers |
| Fallbacks | Secondary model or non-AI path when the primary fails |
| Limits | Rate limits, token caps, timeouts, budget alerts |
| Security | Hardening checklist complete |
| Privacy | Data path approved |
| Rollback | Previous model and prompt versions kept, one-step revert |
| Owner | Named person on call for the feature |

## 2. Rollout

| Stage | Practice |
|-------|----------|
| Shadow | Run the AI path silently and compare with the current behavior |
| Small cohort | Release to a small share of users; watch metrics |
| Gradual increase | Expand only while quality, cost, and error rate hold |
| Full release | Keep the kill switch |

## 3. Observability

| Metric | Why |
|--------|-----|
| Latency (time-to-first-token, total) | User experience |
| Tokens and cost per request and per feature | Budget control |
| Error, timeout, and refusal rate | Reliability |
| Validator failures and escalations | Quality and routing health |
| Queue depth and slot usage (self-hosted) | Capacity |

Log without sensitive content; keep retention short.

## 4. Versioning

| Item | Practice |
|------|----------|
| Model | Pin the exact model ID, not a moving alias; re-run evaluation before moving to a new version and before the provider retires the old one |
| Prompt | Store in version control, review changes like code |
| Retrieval index | Version with the document set |
| Artifacts | Pin hash for self-hosted weights; never commit weights |

## 5. Incident Playbook

| Symptom | First moves |
|---------|-------------|
| Quality drop | Check recent model, prompt, or data changes; roll back; run the test set |
| Cost spike | Check loops, retries, and traffic; apply rate limits or switch to the cheaper path |
| Latency spike | Check queue depth, provider status, context size |
| Suspected leak or injection | Disable the affected tool or feature, preserve logs, review data exposure |
| Provider outage | Switch to fallback path |

## 6. Ongoing

- Review the test set and add new failure cases regularly.
- Re-evaluate the model choice when new models or prices appear ([Model Tier Decisions](./model-tier-decisions.md)).
- Revisit costs against the budget on a fixed schedule ([Cost and Savings](./cost-and-savings.md)).
