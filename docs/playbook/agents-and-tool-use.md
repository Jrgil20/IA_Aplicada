# Agents and Tool Use: When and How

> **Practical guide.** An agent is a model that chooses its own tool calls over several steps. It is the most powerful pattern and the most expensive and risky one. Start with the simplest tier that works. Hands-on examples in this repo: Lab 03 (autonomous code agents and data auditing, `labs/lab-03.md`) and Lab 04 (connecting agents to an ERP through MCP, `labs/lab-04.md`).
>
> **Verification status (2026-11-17):** Claude API details come from the Claude API reference bundled with Claude Code.

---

## 1. Pick the Simplest Tier

| Tier | Shape | Use when |
|------|-------|----------|
| Single call | One request, one response | Classification, extraction, summarization, Q&A |
| Workflow | Your code runs fixed steps, calling the model where needed | The steps are known in advance |
| Agent | The model decides which tool to call next, in a loop | The task is open-ended and hard to specify step by step |

Build an agent only if **all four** hold:

| Criterion | Question |
|-----------|----------|
| Complexity | Is the task multi-step and hard to specify in advance? |
| Value | Does the outcome justify the higher cost and latency? |
| Viability | Can the model actually do this kind of task? |
| Cost of error | Can mistakes be caught and undone (tests, review, rollback)? |

If any answer is "no", use a workflow or a single call.

## 2. Tool Design

| Rule | Why |
|------|-----|
| Few, well-described tools | The model chooses better among clear options |
| Strict input schemas | Invalid arguments are rejected before execution (on the Claude API, `strict: true` on a tool) |
| Least privilege | Read-only by default; write tools scoped to what the task needs |
| Return errors as results | The model can recover; silent failures cause loops |
| Idempotent where possible | Retries do not repeat side effects |
| Human approval for risky actions | Payments, deletions, outbound messages, production changes |

## 3. Loop Controls

| Control | Purpose |
|---------|---------|
| Maximum steps | Stops runaway loops |
| Token or task budget | Bounds cost per task |
| Timeout per tool and per task | Bounds latency |
| Stop conditions | Clear definition of "done" |
| Audit log of every tool call | Debugging and accountability |

## 4. Security

| Threat | Control |
|--------|---------|
| Prompt injection through tool results (web pages, files, emails) | Treat tool output as untrusted data; separate privileged and untrusted contexts |
| Excessive agency | Permissions enforced by code, not by the prompt |
| Credential exposure | Keep secrets out of the model's context; inject them at the tool boundary |
| Data exfiltration | Restrict outbound network and domains the agent can reach |

See the [Hardening Checklist](./hardening-checklist.md) and the `inference-security-hardening` skill.

## 5. Build vs. Managed Options (Claude ecosystem)

| Option | You own | Fits |
|--------|---------|------|
| Messages API with your own loop | Loop, tools, hosting | Full control, any data policy you can support |
| SDK tool runner | Tools and hosting; SDK runs the loop | Less code, still self-hosted |
| Managed Agents (beta) | Agent config and custom tools; provider hosts loop and sandbox | Fast start, long sessions; billed per session runtime plus tokens; not currently ZDR/HIPAA eligible |

Choose by data policy first ([Privacy and Compliance](./privacy-and-compliance.md)), then by how much infrastructure you want to run.

## 6. Cost

Agents multiply tokens: every step resends the conversation. Use prompt caching on the stable prefix, cap steps, use a cheaper model for reading-heavy sub-tasks, and measure **cost per completed task** ([Cost and Savings](./cost-and-savings.md)).

## 7. Evaluate

| Metric | Meaning |
|--------|---------|
| Task success rate | Did it finish the job correctly? |
| Steps and tokens per task | Efficiency and cost |
| Unsafe or blocked actions | Safety |
| Human interventions | Autonomy actually achieved |

Run the same task set after every change to the model, prompt, or tools ([Evaluation and Quality](./evaluation-and-quality.md)).
