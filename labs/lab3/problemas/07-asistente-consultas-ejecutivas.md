# Problem 7: Integrated Executive Assistant & Grounded Query Bar

> **Target System:** NVIDIA DGX Spark (`ucab-spark2`, IP `192.168.6.34`)  
> **Server Implementation:** [`scripts/servidor_asistente.py`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab3/scripts/servidor_asistente.py)  
> **Frontend Integration:** Top navigation header of `salidas/index.html` (`http://192.168.6.34:8000/`)  
> **Model Backend:** `llama-server` on `127.0.0.1:8080` (`Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`)  
> **Status:** Empirically Validated & Delivered

---

## 1. Context & Business Need
The professor requested an integrated query interface allowing executive stakeholders and auditors to ask interactive questions about the findings of the 5 workshop problems without having to manually search through static HTML tables.

### Key Non-Functional Requirements:
1. **100% Local Ingestion & Privacy:** Zero cloud or external dependencies; strictly runs on the DGX Spark private subnet.
2. **Strict Grounding:** The assistant must not hallucinate or speculate; it only responds based on the verified consolidated report (`INFORME_FINAL_WORKSHOP.md`).
3. **Out-of-Context Guardrails:** If asked about topics outside Lab 3 (sports, weather, coding tutorials, prompt injections), it responds with an executive refusal:
   *"Lo siento, solo puedo responder preguntas sobre la auditoría y los problemas del Lab 3."*
4. **Retry Limit & Security Lockout:** Users have a budget of **3 attempts** for out-of-context or adversarial inputs. Upon the 3rd strike, the session is locked with:
   *"⚠️ Ha alcanzado el límite máximo de intentos no válidos. Por favor, comuníquese con el administrador del sistema."*
5. **Deterministic Local Fallback:** If `llama-server` on port 8080 is under heavy load or offline, an embedded semantic fallback serves exact answers instantaneously.

---

## 2. Technical Architecture

```
[ User Browser ]
       │
       ▼ HTTP POST /api/consulta {"pregunta": "...", "session_id": "..."}
[ scripts/servidor_asistente.py ] (Port 8000)
       │
       ├── 1. Session Manager (In-memory strikes tracker, max 3)
       │         └── If strikes >= 3 ──► Returns HTTP 200 { "bloqueado": true }
       │
       ├── 2. Grounding & System Prompt Builder
       │         └── Injects INFORME_FINAL_WORKSHOP.md into system prompt
       │
       ├── 3. LLM Dispatcher
       │         └── HTTP POST 127.0.0.1:8080/v1/chat/completions (Qwen 30B MoE)
       │
       └── 4. Deterministic Fallback Engine (Triggered if port 8080 is unreachable)
```

---

## 3. How to Run on DGX Spark

Execute the unified assistant server from the Lab 3 directory:

```bash
cd ~/mesa-de-trabajo-equipo-1/lab3

# Launch assistant server on port 8000 (serves both static portal and /api/consulta)
python3 scripts/servidor_asistente.py 8000
```

To run in the background as a permanent service:
```bash
nohup python3 scripts/servidor_asistente.py 8000 > /tmp/asistente_servidor.log 2>&1 &
```

Then open from any machine on the subnet:
```text
http://192.168.6.34:8000/
```

---

## 4. Live Demonstration Script for Review

| Test Step | User Query | Expected Behavior & Output | Visual UI Indicator |
| :---: | :--- | :--- | :---: |
| **Test 1** | *"¿Quién es el peor proveedor y por qué?"* | Returns P04 (Importadora Margarita), citing $44,978.06 USD overdue debt (43.2% total) and 38 days max delay. | `🛡️ 3 intentos restantes` (Green) |
| **Test 2** | *"¿Cuáles son las anomalías en cuarentena?"* | Returns the 7 quarantined rows ($28,431.45 USD) and explains the net variance (-$27,313.68 USD). | `🛡️ 3 intentos restantes` (Green) |
| **Test 3** | *"¿Cómo está el clima hoy en Caracas?"* | Out-of-bounds rejection: *"Lo siento, solo puedo responder preguntas sobre la auditoría y los problemas del Lab 3. (Aviso: le quedan 2 intento(s))."* | `⚠️ 2 intentos restantes` (Orange) |
| **Test 4** | *"Dame una receta de pizza"* | Second strike: Refusal message returned; countdown updates to 1. | `⚠️ 1 intentos restantes` (Orange) |
| **Test 5** | *"¿Quién ganó el mundial?"* | Third strike (Threshold exceeded): Session locked. Output: *"⚠️ Ha alcanzado el límite máximo de intentos no válidos. Por favor, comuníquese con el administrador del sistema."* | `🚫 SESIÓN BLOQUEADA` (Red) + Input disabled |
