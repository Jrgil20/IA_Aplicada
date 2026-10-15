# Observation 01: SSH Environment, Binary Discoverability & OpenCode Execution Modes

> **Context:** Lab 03 execution on NVIDIA DGX Spark (`ucab-spark2`, IP `192.168.6.34`)  
> **Topic:** Troubleshooting SSH shell environments, `$PATH` resolution for OpenCode, and deterministic execution modes.

---

## 1. Technical Problem Analysis

During remote SSH access, users reported that typing `opencode` produced `command not found`, and custom slash commands defined in the project were not visible inside OpenCode.

### Root Cause 1: Unexported Binary Path in SSH Non-Login / Non-Interactive Shells
The OpenCode binary installs by default to:
```text
~/.opencode/bin/opencode
```
Standard Linux SSH sessions do not automatically include `~/.opencode/bin` in the default `$PATH` unless explicitly exported in `~/.bashrc` or symlinked to a standard user binary path like `~/.local/bin`.

### Root Cause 2: Current Working Directory Context for `opencode.json`
OpenCode resolves its declarative configuration, permissions, and custom slash commands by reading `./opencode.json` relative to the **current working directory** where the command was initiated.
- When launched from `~` (user home), OpenCode runs with default settings and will not load the project's custom commands (`/informe-lunes`) or security policies (`deny` on `.env` / `pedidos.csv`).
- When launched from `~/mesa-de-trabajo-equipo-1/lab3/`, OpenCode immediately discovers `opencode.json` and registers all project-specific commands and governance rules.

---

## 2. Permanent Fix & SSH Setup Protocol

### Shell Configuration
Add the path and symlink permanently on the DGX Spark environment:

```bash
# Symlink into standard local bin directory
mkdir -p ~/.local/bin
ln -sf ~/.opencode/bin/opencode ~/.local/bin/opencode

# Ensure PATH exports both directories permanently
cat << 'EOF' >> ~/.bashrc
export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
alias opencode="$HOME/.opencode/bin/opencode"
EOF

# Reload environment
source ~/.bashrc
```

---

## 3. The 3 Execution Paradigms

```
                      +---> 1. Direct Shell (./informe-lunes.sh) [Deterministic / Zero Token Cost]
                      |
SSH Session on Spark -+---> 2. Headless CLI (opencode run /informe-lunes) [Single-shot Agent Execution]
                      |
                      +---> 3. Interactive TUI (opencode -> /informe-lunes) [Live Inspection Mode]
```

### 1. Direct Shell Scripting
- **Command:** `./informe-lunes.sh`
- **Mechanism:** Executes native bash script invoking Python pipeline modules (`verificar_seguridad.py`, `validar_calidad_datos.py`, `generar_informe_lunes.py`).
- **Advantage:** Runs in < 1 second, zero GPU inference required, perfect for rapid live demonstration.

### 2. Headless Agent CLI (`opencode run`)
- **Command:** `opencode run /informe-lunes`
- **Mechanism:** Launches OpenCode non-interactively, loads `opencode.json`, expands the `/informe-lunes` template into an agent task, executes within permissions sandbox, and terminates.
- **Advantage:** Ideal for remote automation or CI/CD demonstration.

### 3. Interactive TUI Mode
- **Command:** `opencode`
- **Usage:** Inside the interactive prompt, type `/informe-lunes`. OpenCode uses fuzzy matching and command autocomplete to display declared commands.
