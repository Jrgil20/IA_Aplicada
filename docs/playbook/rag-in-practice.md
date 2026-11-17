# RAG in Practice: Answering From Your Own Data

> **Practical guide.** Retrieval-Augmented Generation (RAG) gives a model your documents at question time instead of training them into its weights. This repo's Lab 05 built question answering over documents with RAG (see `labs/lab-05.md` and `labs/lab5/`). No retrieval-quality numbers are asserted here; measure on your own questions.

---

## 1. When RAG Is the Right Tool

| Need | RAG? | Alternative |
|------|------|-------------|
| Answers from private or frequently changing documents | Yes | — |
| Answers must cite their source | Yes | — |
| Model must adopt a style or narrow behavior | No | Fine-tune or prompt ([Model Selection](../model-selection.md)) |
| Whole corpus fits comfortably in the context window and is reused | Maybe not | Put it in a cached prompt prefix ([Prompt Caching](../prompt-caching.md)) |
| Exact lookups (an ID, a price, a status) | No | A database query or API call |

Long context windows (up to 1M tokens on current Claude models) make "just send the documents" viable for small, stable corpora. RAG still wins when the corpus is large, changes often, or must be filtered per user.

## 2. Pipeline

```
ingest → clean → chunk → embed/index → [query] → retrieve → rerank → build prompt → generate → cite + validate
```

| Stage | Decision | Common mistake |
|-------|----------|----------------|
| Ingest | Which sources, how often to refresh | Stale index nobody updates |
| Clean | Strip boilerplate, keep headings and tables | Navigation menus and footers in every chunk |
| Chunk | Split on structure (headings, paragraphs), with small overlap | Fixed-size cuts through the middle of tables or code |
| Index | Vector embeddings, keyword (BM25), or both (hybrid) | Vector-only search missing exact terms such as codes and names |
| Retrieve | Top-k candidates, filtered by user permissions | Retrieving documents the user may not see |
| Rerank | Reorder candidates by relevance before prompting | Sending too many weak chunks |
| Prompt | Put retrieved text in clearly delimited data blocks | Mixing instructions and retrieved text |
| Generate | Instruct to answer only from the provided sources and to say when the answer is missing | Letting the model fill gaps from memory |
| Cite + validate | Check that cited passages exist and support the answer | Trusting citations without checking |

## 3. Evaluate Retrieval and Generation Separately

| Layer | Question | How to measure |
|-------|----------|----------------|
| Retrieval | Did the right passage reach the prompt? | For each test question, label the passage(s) that answer it; check if they are in the top-k |
| Generation | Given the right passage, is the answer correct and grounded? | Grade answers against the labelled passage |
| End to end | Is the final answer correct? | Product metric on the full pipeline |

If end-to-end quality is poor, this split tells you whether to fix search or the prompt/model. Most RAG failures are retrieval failures.

## 4. Security and Privacy

| Risk | Control |
|------|---------|
| Indirect prompt injection in documents | Treat retrieved text as data; never let it trigger tools or change permissions ([Hardening Checklist](./hardening-checklist.md)) |
| Cross-user leakage | Filter by permissions at retrieval time, not after generation |
| Sensitive data in the index | Classify sources before ingesting ([Privacy and Compliance](./privacy-and-compliance.md)) |
| Index poisoning | Control who can add documents; log ingestion |

## 5. Cost Levers

| Lever | Effect |
|-------|--------|
| Fewer, better chunks (rerank, smaller k) | Fewer input tokens per question |
| Cache the stable system prompt | Cheaper repeated prefix |
| Small model for query rewriting or classification | Keeps the expensive model for the final answer |
| Response cache for frequent questions | Skips retrieval and generation |

## 6. Checklist

- [ ] Test questions with labelled source passages exist.
- [ ] Retrieval respects user permissions.
- [ ] Prompt separates instructions from retrieved data.
- [ ] The model says "not found" when sources do not contain the answer.
- [ ] Citations are checked.
- [ ] The index has an owner and a refresh schedule.
