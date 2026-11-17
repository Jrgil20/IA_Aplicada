# Needs to Architecture: Pattern per Product Need

> **Lookup table.** Match what the product must do to a proven pattern, its main risk, and the first thing to measure.

---

## 1. Patterns

| Product need | Pattern | Core pieces | Main risk | First metric |
|--------------|---------|-------------|-----------|--------------|
| Answer questions from our documents | RAG (retrieval + generation) | Chunking, embeddings, vector/keyword search, grounded prompt | Wrong or missing retrieval; hallucinated citations | Answer correctness vs. cited source |
| Classify or route text | Classifier (rules → small model) | Labels, validator, fallback label | Silent drift in input mix | Accuracy per class |
| Extract fields from documents | Structured extraction | Schema, JSON validation, retry on invalid | Plausible but wrong values | Field-level accuracy |
| Draft or rewrite text | Generation with constraints | Style guide in prompt, length limits, human approval | Off-brand or false content | Edit rate by reviewers |
| Code assistance | Copilot (completion/refactor) | Context builder, validators (parse, lint, tests) | Insecure or non-compiling code | Pass rate of validators |
| Conversational support | Chatbot with tools and handoff | System prompt, tools with least privilege, escalation to human | Prompt injection, tool misuse | Resolution rate, handoff rate |
| Multi-step automation | Agent | Planner, tool permissions, step limits, audit log | Runaway actions, cost loops | Task success, steps per task |
| Cost reduction on mixed traffic | Cascade router | Policy gate, cache, small model, escalation ([Cost-Aware Routing](../cost-aware-routing.md)) | Quality loss from wrong routing | Escalation rate, quality per tier |

## 2. Choosing Between Neighbors

| Question | Answer |
|----------|--------|
| RAG or fine-tune? | Facts that change or are private → RAG. Style or narrow task behavior → fine-tune |
| Agent or fixed workflow? | If the steps are known, use a fixed workflow; agents add cost and risk |
| One big prompt or several calls? | Split when steps need different models, validation, or caching |
| Chat UI or embedded feature? | If users need one action, embed it; chat adds ambiguity |

## 3. Minimal Architecture (all patterns)

```
user input → input checks → context builder → model call → output validator → response
                  ↓              ↓                ↓              ↓
              policy gate     cache/RAG       logs + metrics   fallback / human
```

Every pattern needs: an input check, a validator on the output, a fallback path, and logging without sensitive content.
