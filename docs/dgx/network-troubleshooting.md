# Troubleshooting: DGX Spark Network Connectivity & Subnetting

Technical reference and post-mortem guide for resolving Layer 1 (Physical), Layer 2 (Data Link), and Layer 3 (Network Routing) connectivity issues between client workstations/laptops and the **NVIDIA DGX Spark** (`ucab-spark2`).

---

## 1. Network Topology & Baseline Parameters

| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **DGX Spark IP** | `192.168.6.42` / `192.168.6.34` | Primary workstation IPs observed in lab |
| **Subnet Mask** | `/26` (`255.255.255.192`) | **CRITICAL:** Not a standard `/24` |
| **Valid Host Range** | `192.168.6.1` – `192.168.6.62` | Usable IP range for client and Spark |
| **Default Gateway** | `192.168.6.1` | Expected upstream router |
| **NVIDIA MAC OUI** | `dc:04:5a:...` | Hardware identifier in ARP tables |
| **Spark Physical Interfaces** | `enp7s7` (PCIe onboard), `enxdc045a73a5a7` (USB/dongle) | Physical Ethernet interfaces on Spark |

```
Subnet: 192.168.6.0/26 (Mask: 255.255.255.192)
[192.168.6.1] ---------- [192.168.6.42] ---------- [192.168.6.50]
 Gateway Router            DGX Spark                 Client Laptop
```

---

## 2. Issues Encountered, Root Causes & Diagnoses

### Issue A: Layer 1 — Dead Jack / Cable Disconnected (`NO-CARRIER`)

#### Symptom
The Ethernet link does not come up; physical RJ-45 LEDs are completely dark. Running `ping` immediately returns `Network is unreachable`.

#### Diagnostic Command
```bash
cat /sys/class/net/<interface>/carrier
# Output: 0

ip link show <interface>
# Output: <NO-CARRIER,BROADCAST,MULTICAST,UP> state DOWN
```

#### Root Cause
The wall outlet or patch panel is disconnected, or the RJ-45 connector did not latch firmly into the port.

#### Fix
1. Inspect physical link LEDs on laptop and switch.
2. Re-seat connector firmly until it clicks.
3. Switch to an active switch port until `carrier` returns `1`.

---

### Issue B: Layer 2 ARP Resolution vs. Layer 3 Timeouts

#### Symptom
ARP successfully discovers the MAC address (`dc:04:5a:73:a5:a7 REACHABLE`), but all Layer 3 (ICMP `ping`) and Layer 4 (TCP port 22 / 11434) attempts result in `Connection timed out`.

#### Diagnostic Command
```bash
ip neigh show dev <interface>
# Output: 192.168.6.42 lladdr dc:04:5a:73:a5:a7 REACHABLE

ping -c 3 192.168.6.42
# Output: 100% packet loss
```

#### Root Cause
ARP works via Layer 2 broadcast (`ff:ff:ff:ff:ff:ff`), so the Spark correctly acknowledges "I am 192.168.6.42". However, when the Spark attempts to send unicast IP response packets back to the client, **Layer 3 routing fails**.

---

### Issue C: Subnet Mask Mismatch (`/26` vs `/24`) — [Root Cause]

#### Symptom
When the client workstation was configured with IP `192.168.6.100/24`, it could not communicate with the Spark (`192.168.6.42`).

#### Technical Explanation
Inspecting the Spark routing table via `ip route` revealed:
```text
default via 192.168.6.1 dev enxdc045a73a5a7 proto dhcp src 192.168.6.42 metric 20100
192.168.6.0/26 dev enxdc045a73a5a7 proto kernel scope link src 192.168.6.42 metric 100
```

1. The Spark is configured in a **/26 subnet** (`255.255.255.192`).
2. A `/26` subnet on `192.168.6.0` only spans from `192.168.6.0` to `192.168.6.63`.
3. Client IP `192.168.6.100` belongs to `192.168.6.64/26` (a completely different subnet).
4. When the Spark received packets from `.100`, its routing table evaluated that `.100` was **not local**, forwarding all replies to default gateway `192.168.6.1`. Since `192.168.6.1` was unreachable on the direct lab switch, all response packets were silently dropped.

#### Fix
Assign the client workstation a static IP strictly inside the valid range (`.2` to `.62`):
- **Client IP:** `192.168.6.50/26` (Subnet mask `255.255.255.192`)

---

## 3. Operational Playbook

### Step 1: Configure Client Laptop (Ubuntu / Linux NetworkManager)

Configure static IP while preserving default WiFi Internet route (`ipv4.never-default yes`):

```bash
# 1. Apply static IP inside /26 range
nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.6.50/26 \
  ipv4.method manual \
  ipv4.never-default yes

# 2. Activate connection
nmcli connection up "Wired connection 1"
```

### Direct Peer-to-Peer Cable Setup (No Switch / No DHCP)
When connecting client laptop directly to the Spark via Ethernet cable:
1. On the Spark terminal, assign the static IP to its active PCIe interface (`enp7s7`):
   ```bash
   sudo ip addr add 192.168.6.34/26 dev enp7s7
   sudo ip link set enp7s7 up
   ```
2. On client laptop (`eno2`), verify link carrier is 1 and IP is `192.168.6.50/26`.

### Step 2: Verification

```bash
# Verify Layer 3 ICMP ping (< 1ms expected)
ping -c 3 192.168.6.34
# (or 192.168.6.42 depending on assigned IP)

# Verify Layer 4 SSH port 22 open
nc -zv -w 2 192.168.6.42 22

# Verify SSH authentication prompt
ssh -o StrictHostKeyChecking=accept-new ucab-spark2@192.168.6.42
```

### Step 3: Rollback Procedure (Restore Standard DHCP)

When the laboratory session ends, revert the Ethernet interface to automatic DHCP:

```bash
# 1. Reset IPv4 settings to DHCP auto
nmcli connection modify "Wired connection 1" \
  ipv4.method auto \
  ipv4.addresses "" \
  ipv4.never-default no

# 2. Deactivate connection
nmcli connection down "Wired connection 1"
```

---

## 4. Quick Diagnostic Matrix

| Symptom | Diagnostic Command | Typical Root Cause | Action |
| :--- | :--- | :--- | :--- |
| **No carrier** | `cat /sys/class/net/<iface>/carrier` | Dead wall jack / loose cable | Change port or re-seat cable |
| **ARP FAILED** | `ip neigh show dev <iface>` | Wrong subnet / different VLAN | Verify physical switch segment |
| **ARP OK, Ping timeout** | `ip route` (on Spark) | Subnet mismatch (`/26` vs `/24`) | Use IP between `.2` and `.62` |
| **Port 22 refused** | `nc -zv <spark_ip> 22` | SSH service down / wrong port | Start `sshd` on Spark |
| **Port 11434 refused** | `nc -zv <spark_ip> 11434` | Ollama listening on 127.0.0.1 | Run `OLLAMA_HOST=0.0.0.0:11434 ollama serve` |
