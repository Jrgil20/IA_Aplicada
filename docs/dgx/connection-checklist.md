# DGX Spark Connection & Agent Onboarding Checklist

Operational step-by-step checklist to execute when physically connecting a client laptop/workstation to the **NVIDIA DGX Spark** (`ucab-spark2`).

---

## 1. Baseline Configuration & Network Scope

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Client Static IP** | `192.168.6.50/26` | Host IP assigned to laptop Ethernet interface |
| **Subnet Mask** | `255.255.255.192` (`/26`) | Mandatory subnet range (`.1` to `.62`) |
| **Primary Spark IP** | `192.168.6.42` | SSH Host alias: `dgx-spark` |
| **Alternative Spark IP**| `192.168.6.34` | SSH Host alias: `dgx-spark-alt` |
| **Remote User** | `ucab-spark2` | Default user on DGX OS |
| **SSH Key** | `~/.ssh/id_ed25519` | Local authentication key |

---

## 2. Step-by-Step Connection Procedure

### Step 1: Connect Physical Cable & Configure Static IP

Connect the Ethernet cable. Configure static IP within the `/26` subnet while preserving default internet routing on WiFi (`ipv4.never-default yes`):

```bash
# 1. Inspect exact interface name if different from default
nmcli connection show

# 2. Assign static IP and enable link
nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.6.50/26 \
  ipv4.method manual \
  ipv4.never-default yes

nmcli connection up "Wired connection 1"
```

> [!NOTE]
> If your connection name is not `"Wired connection 1"`, check the exact name in the `NAME` column of `nmcli connection show` and adjust the command accordingly.

---

### Step 2: Verify Layer 3 Connectivity (ICMP Ping)

Verify that the DGX Spark responds to ICMP echo requests:

```bash
ping -c 2 192.168.6.42
```

- If `192.168.6.42` responds: proceed with `dgx-spark`.
- If `192.168.6.42` does not respond: test alternate IP:
  ```bash
  ping -c 2 192.168.6.34
  ```
  If `192.168.6.34` responds, use SSH alias `dgx-spark-alt` for subsequent steps.

---

### Step 3: Install SSH Public Key (One-Time Setup)

Copy your local public key to the workstation authorized keys (requires entering the `ucab-spark2` password once):

```bash
ssh-copy-id dgx-spark
# Or for alternate host:
# ssh-copy-id dgx-spark-alt
```

---

### Step 4: Verify Passwordless SSH Login

Ensure authentication succeeds without prompting for a password:

```bash
ssh dgx-spark hostname
```

The command must return `ucab-spark2` immediately without requiring keyboard input.

---

### Step 5: Test Autonomous Agent Execution (`agy`)

1. Restart the `agy` agent session.
2. Delegate non-destructive commands to the agent:
   ```bash
   ssh dgx-spark nvidia-smi
   ```
   *Expected outcome:* The command runs cleanly and outputs GPU telemetry without blocking.
3. Test privileged / sensitive execution guardrail:
   ```bash
   ssh dgx-spark sudo reboot
   ```
   *Expected outcome:* The agent must halt and ask for explicit human confirmation before executing destructive/reboot operations.

---

## 3. Operational Guardrails & Reminders

> [!CAUTION]
> **Do not delegate SSH commands to the agent until Step 4 is fully verified.**
> If passwordless key authentication is not active, remote SSH commands executed by the autonomous agent will freeze indefinitely waiting for interactive password entry on stdin, which the agent cannot supply.

> [!TIP]
> **Diagnostic fallback:**
> If Step 2 fails even with the physical cable connected:
> 1. Run `ip -br a` and `nmcli connection show`.
> 2. Consult the [Network Troubleshooting Guide](./network-troubleshooting.md) to inspect link carrier status, ARP table resolution (`ip neigh`), and routing tables.
