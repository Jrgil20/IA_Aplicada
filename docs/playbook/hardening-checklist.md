# Hardening Checklist for AI Features

> **Security checklist.** Covers the main failure classes of LLM-backed features. For audits and implementation details use the skills `inference-security-hardening` (inference servers, VLM and agent injection) and `secure-ssh-tunnels` (remote access).

---

## 1. Threats and Controls

| Threat | What happens | Controls |
|--------|--------------|----------|
| Prompt injection (direct) | User text overrides instructions | Separate instructions from data, restrict what the model can do, validate outputs |
| Prompt injection (indirect) | Documents, web pages, or images carry hidden instructions | Treat all retrieved content as untrusted; no privileged tools on untrusted input |
| Data leakage | Secrets or other users' data appear in answers | Keep secrets out of prompts; scope retrieval per user; scope caches per tenant |
| Insecure output handling | Output rendered or executed unsafely (HTML, shell, SQL) | Escape on render; never execute model output; parameterize queries |
| Excessive agency | Agent takes harmful actions | Least-privilege tools, human approval for risky actions, step limits |
| Denial of wallet / service | Abuse inflates cost or exhausts capacity | Rate limits, token and step caps, budget alerts |
| Exposed inference endpoint | Open model port used by anyone | Bind to private interface, authenticate, tunnel or gateway only |
| Supply chain | Malicious models or packages | Pin versions and hashes, use trusted sources, scan dependencies |
| Context exhaustion | Slot or context sizing silently truncates | Size context per user ([Model Serving](../model-serving-for-apps.md)) |

## 2. Design Rules

| Rule | Detail |
|------|--------|
| Assume the model can be manipulated | Security cannot depend on the prompt alone |
| Authorize outside the model | Permissions are checked by code, not by asking the model |
| Least privilege for tools | Read-only by default; scoped credentials |
| Validate both ways | Check inputs before the call and outputs after |
| Fail closed | On validator failure, refuse or hand to a human; do not guess |

## 3. Infrastructure

| Item | Requirement |
|------|-------------|
| Network | Private bind; expose via gateway or SSH tunnel |
| Authentication | API key or gateway auth on every endpoint. Check what the server's key actually covers: vLLM's `--api-key` protects only `/v1`, `/v2`, `/inference`, and `/cohere`, leaving `/invocations` and control endpoints such as `/update_weights` open, so allowlist endpoints in a reverse proxy (vLLM security docs, fetched 2026-11-17). `llama-server` binds to `127.0.0.1` by default and supports `--api-key` |
| Secrets | Environment or secret manager; never in prompts, repos, or logs |
| Weights and artifacts | Never committed; hash pinned |
| Logging | No sensitive prompts; retention limit |
| Remote GPU access | Authorized tunnels only (see the `secure-ssh-tunnels` skill) |

## 4. Test It

| Test | Example |
|------|---------|
| Injection suite | Instructions hidden in documents and images; expect them to be ignored |
| Leak test | Ask for the system prompt and for other users' data |
| Output safety | Feed outputs containing HTML/script/SQL to the renderer |
| Abuse test | Burst of requests; confirm limits trigger |
| Tool boundary test | Try to make the agent call tools beyond its scope |

Re-run after every model, prompt, or tool change.

## 5. Checklist

- [ ] Endpoint is private and authenticated.
- [ ] Untrusted content cannot trigger privileged actions.
- [ ] Outputs are validated and escaped before use.
- [ ] Rate limits and token/step caps are set.
- [ ] Secrets and sensitive data are kept out of prompts and logs.
- [ ] Injection and leak tests exist and pass.
- [ ] Model and dependency versions are pinned.
