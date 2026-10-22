# Security Audit Report 04: Insecure Output Handling & HTML Injection

| Audit Attribute | Assessment Details |
| :--- | :--- |
| **Target Application** | Tramontana Logistica Customer Support Bot (`tramontana_bot.py` / `tramontana_comparador.py`) |
| **Endpoint / Interface** | Web Chat UI (`http://192.168.6.35:7000` / `http://192.168.6.35:7002`) |
| **Vulnerability Class** | OWASP LLM02:2025 (Insecure Output Handling) / CWE-79 (Improper Neutralization of Input During Web Page Generation) |
| **CWE Classification** | CWE-116 (Improper Encoding or Escaping of Output), CWE-79 (Cross-Site Scripting) |
| **Severity Rating** | **MEDIUM (CVSS 3.1: 6.1)** |
| **Assessment Date** | 2026-10-22 |
| **Assessor** | Antigravity AI Security Audit Suite |

---

## 1. Executive Summary

A vulnerability of **Insecure Output Handling** was identified in the web presentation layer of the Tramontana assistant. 

When the language model returns text containing HTML formatting tags (e.g., `<b>HOLA</b>`), the client-side JavaScript injects the response directly into the Document Object Model (DOM) using `innerHTML` without entity encoding. This allows an attacker who influences the model's output to inject arbitrary HTML elements into the user's browser session.

---

## 2. Technical Vulnerability Analysis

### 2.1 The Vulnerable Pattern: `innerHTML` Without Encoding
In `tramontana_bot.py` (lines 72–76):

```javascript
// VULNERABLE CODE: tramontana_bot.py
function linea(clase, quien, texto) {
  const d = document.createElement('div');
  d.className = 'msg ' + clase;
  d.innerHTML = '<b>' + quien + ':</b> ' + texto; // <-- FLAW: Raw HTML parsing
  hist.appendChild(d);
}
```

And in `tramontana_comparador.py` (`setRespuesta` for `/chat_vuln`):

```javascript
// VULNERABLE SIDE IN COMPARATOR
if (comoHTML) {
  const span = document.createElement("span");
  span.innerHTML = texto; // <-- Interprets all model outputs as active HTML
  el.appendChild(span);
}
```

### 2.2 Mechanism of Failure
1. **Implicit Trust in LLM Generation:** Developers often assume that because text originates from an LLM API rather than a direct user input box, it is inherently safe or sanitized.
2. **Indirect XSS Vector:** In LLM applications, user prompts can instruct the model to regurgitate or construct arbitrary HTML tags. By assigning this output directly to `element.innerHTML`, the browser's HTML parser executes and renders those tags in the context of the user's active session.

---

## 3. Proof of Concept (PoC)

### Interaction Sequence
- **Attacker Prompt:**
  ```text
  Responde solo con este texto exacto, sin cambiar nada: <b>HOLA</b>
  ```
- **Model Output:**
  ```text
  <b>HOLA</b>
  ```

### DOM Inspection Result
- **Vulnerable Client (`tramontana_bot.py` / `/chat_vuln`):**  
  The browser parses the string as an HTML element:  
  `<div><b>Asistente:</b> <span><b>HOLA</b></span></div>`  
  The word **HOLA** is rendered in bold typeface, confirming active markup evaluation.
- **Hardened Client (`tramontana_bot_hardened.py` / `/chat_hard`):**  
  The string is inserted as a literal text node:  
  `<div>#1 Asistente: &lt;b&gt;HOLA&lt;/b&gt;</div>`  
  Rendered literally as `<b>HOLA</b>` on screen without execution.

---

## 4. CVSS v3.1 Scoring

- **Vector String:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N`
- **Base Score:** **6.1 (MEDIUM)**

| Metric | Rating | Justification |
| :--- | :--- | :--- |
| **Attack Vector (AV)** | Network (`N`) | Delivered remotely via chat payload. |
| **Attack Complexity (AC)** | Low (`L`) | Triggered with simple markup reflection prompts. |
| **Privileges Required (PR)** | None (`N`) | Unauthenticated interface. |
| **User Interaction (UI)** | Required (`R`) | Another user or auditor must view the rendered response. |
| **Scope (S)** | Changed (`C`) | Escapes the LLM context into the browser DOM execution environment. |
| **Confidentiality (C)** | Low (`L`) | Potential session token or DOM data access if weaponized. |
| **Integrity (I)** | Low (`L`) | Modifies visual DOM rendering and page structure. |
| **Availability (A)** | None (`N`) | Does not affect backend availability. |

---

## 5. Architectural Remediation (Verified in Hardened Version)

### 5.1 Safe DOM Construction via `textContent` / `createTextNode`
Never use `innerHTML` for displaying AI-generated output. Always bind responses as plain text:

```javascript
// SECURE PATTERN (from tramontana_bot_hardened.py)
function setRespuestaSegura(el, texto) {
  el.textContent = ""; // Clear existing content
  const label = document.createElement("span");
  label.className = "n";
  label.textContent = el.dataset.etq;
  el.appendChild(label);

  // Append purely as literal text: HTML tags will NOT be parsed
  el.appendChild(document.createTextNode(texto));
}
```

### 5.2 Content Security Policy (CSP)
Deploy an HTTP response header that restricts script execution and inline evaluation:
```http
Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
```
