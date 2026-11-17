# Applied AI Playbook

> **Practical guide for putting AI into products.** Decisions, costs, security, privacy, quality, and launch. Each file is one concept, written to be acted on. The rest of `docs/` is the technical background (DGX, CUDA, QLoRA); this folder is the "what do I do" layer. No cost, latency, or quality numbers are asserted here: measure them in your own product.

---

## Start Here: Which File Do I Need?

| I need to... | Read |
|--------------|------|
| Decide if AI belongs in this feature at all | [Product Decision Framework](./product-decision-framework.md) |
| Map a product need to an architecture | [Needs to Architecture](./needs-to-architecture.md) |
| Pick a model tier: stay on Haiku, go up, go cheaper, or go private | [Model Tier Decisions](./model-tier-decisions.md) |
| Cut the bill without hurting quality | [Cost and Savings](./cost-and-savings.md) |
| Decide where my data may go | [Privacy and Compliance](./privacy-and-compliance.md) |
| Secure an AI feature | [Hardening Checklist](./hardening-checklist.md) |
| Know if the feature is good enough, and stays good | [Evaluation and Quality](./evaluation-and-quality.md) |
| Ship and operate it | [Production Readiness](./production-readiness.md) |
| Answer questions from my own documents | [RAG in Practice](./rag-in-practice.md) |
| Decide whether I need an agent, and build it safely | [Agents and Tool Use](./agents-and-tool-use.md) |
| See the playbook applied to a real project | [Case Study: Edge Clean Copilot](./case-study-edge-clean-copilot.md) |

## Reading Order for a New Feature

1. Product Decision Framework → is AI justified?
2. Needs to Architecture → which pattern?
3. Privacy and Compliance → where may data flow?
4. Model Tier Decisions → which model class?
5. Evaluation and Quality → how will I know it works?
6. Hardening Checklist and Production Readiness → ship safely.
7. Cost and Savings → tune once it works.

## Related Technical References

| Topic | File |
|-------|------|
| Cascade of rules, local SLM, frontier LLM | [Cost-Aware Routing](../cost-aware-routing.md) |
| Which tier fits which task | [Applied AI Use Cases](../applied-ai-use-cases.md) |
| Laptop vs. DGX Spark vs. cloud | [Scaling AI Workloads](../scaling-ai-workloads.md) |
| Response, semantic, and prefix caching | [Prompt Caching](../prompt-caching.md) |
| Runtimes, capacity, topology | [Model Serving for Apps](../model-serving-for-apps.md) |
| Selection criteria and process | [Model Selection](../model-selection.md) |
| Local vs. cloud trade-offs | [Local SLMs vs. Cloud LLMs](../local-slm-vs-cloud-llm.md) |
| Security audit and tunnels | Skills `inference-security-hardening`, `secure-ssh-tunnels` |
