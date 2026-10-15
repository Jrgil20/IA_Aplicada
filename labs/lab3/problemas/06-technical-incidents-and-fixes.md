# Problem 6: Technical Incidents, Runtime Gotchas & Solutions

> **Target System:** NVIDIA DGX Spark (`ucab-spark2`, IP `192.168.6.34`)  
> **Topic:** Post-mortem log of technical anomalies encountered during Lab 03 setup, execution, and demonstration.

---

## 1. Incident 1: OpenCode Binary Not Found in SSH Sessions

### Symptom
When logging into the DGX Spark via SSH and executing `opencode`, the terminal returned:
```text
bash: opencode: command not found
```

### Root Cause
OpenCode installs its executable to `~/.opencode/bin/opencode`. Non-interactive SSH sessions and standard login shells do not append `~/.opencode/bin` to the system `$PATH` unless explicitly configured in `.bashrc`.

### Permanent Resolution
```bash
# 1. Symlink into standard user bin directory
mkdir -p ~/.local/bin
ln -sf ~/.opencode/bin/opencode ~/.local/bin/opencode

# 2. Append PATH and alias to .bashrc
cat << 'EOF' >> ~/.bashrc
export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
alias opencode="$HOME/.opencode/bin/opencode"
EOF
source ~/.bashrc
```

---

## 2. Incident 2: Custom Commands Not Visible in OpenCode

### Symptom
Inside the OpenCode TUI, typing `/` did not display `/informe-lunes` or other custom workshop commands.

### Root Cause
OpenCode looks for `opencode.json` in the current working directory (`pwd`). If the user ran `opencode` from `~` (home) instead of `~/mesa-de-trabajo-equipo-1/lab3/`, OpenCode ran with vanilla default settings.

### Permanent Resolution
Always switch to the project directory before launching:
```bash
cd ~/mesa-de-trabajo-equipo-1/lab3
opencode
```
Or run directly from shell via:
```bash
cd ~/mesa-de-trabajo-equipo-1/lab3
opencode run /informe-lunes
```

---

## 3. Incident 3: Model Serving Fallback (Ollama Missing on Spark)

### Symptom
Workshop instructions recommended launching:
```bash
ollama launch opencode --model qwen3.6:35b-a3b-mtp-q4_K_M
```
However, Ollama was not installed or configured on the Spark box for Lab 3.

### Root Cause & Fallback
The DGX Spark environment hosts models natively via `llama-server` on port `8080`.
The pre-deployed model is:
`/srv/models/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`

### Permanent Resolution
OpenCode was directed to use the OpenAI-compatible HTTP endpoint exposed by `llama-server`:
- Base URL: `http://127.0.0.1:8080/v1`
- Model Name: `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf`
- Offload: `-ngl 99` (all layers on Blackwell GB10 GPU, consuming ~8.03 GB RSS memory).

---

## 4. Incident 4: Declarative Permission Schema Contract Error

### Symptom
When configuring `opencode.json`, attempts to use array-based permission rules caused configuration parse errors:
```json
// INCORRECT SYNTAX (Throws error)
"permission": {
  "read": {
    "deny": [".env", "secretos/**"]
  }
}
```

### Root Cause
OpenCode's internal Zod schema validator (`PermissionActionConfig`) expects a key-value dictionary mapping the file glob pattern to the action string:

### Correct Syntax
```json
// CORRECT SYNTAX
"permission": {
  "read": {
    ".env": "deny",
    ".env.*": "deny",
    "secretos/**": "deny"
  },
  "edit": {
    "pedidos.csv": "deny"
  },
  "bash": {
    "*cat .env*": "deny",
    "*curl*": "deny"
  }
}
```

---

## 5. Incident 5: Table Cross-Referencing in Executive Reports

### Observation
During preliminary reviews, auditors requested explicit proof for statements like *"P04 is the worst supplier"* or *"P06 claim letters need modification"*.

### Correction Implemented
All generated documentation now uses explicit table and row cross-referencing:
- *"Referencing Table 4 (Quarantined Rows, Row 305), the duplicate clone PO-1303 reduced P06 claims from 4 to 3 orders."*
- *"Referencing Table 1 (Supplier Failure Ranking, Row 1), P04 concentrates 43.2% of company overdue debt."*
This eliminated ambiguity and satisfied audit requirements.
