# Lista de Pasos: Conexión a DGX Spark y Configuración del Agente

Guía operativa paso a paso a seguir al conectar físicamente un equipo cliente / laptop a la estación **NVIDIA DGX Spark** (`ucab-spark2`).

---

## 1. Parámetros de Red y Entorno

| Parámetro | Valor | Descripción |
| :--- | :--- | :--- |
| **IP Estática Cliente** | `192.168.6.50/26` | IP asignada a la interfaz Ethernet local |
| **Máscara de Subred** | `255.255.255.192` (`/26`) | Rango obligatorio de subred (`.1` a `.62`) |
| **IP Primaria Spark** | `192.168.6.42` | Alias SSH en config: `dgx-spark` |
| **IP Alternativa Spark** | `192.168.6.34` | Alias SSH en config: `dgx-spark-alt` |
| **Usuario Remoto** | `ucab-spark2` | Usuario en DGX OS |
| **Llave SSH** | `~/.ssh/id_ed25519` | Llave local de autenticación |

---

## 2. Procedimiento Paso a Paso

### Paso 1: Conectar el Cable Físico y Asignar IP Estática

Conectar el cable Ethernet. Configurar la IP estática dentro del rango `/26` preservando la ruta por defecto a Internet vía WiFi (`ipv4.never-default yes`):

```bash
# 1. Verificar nombre real de la conexión cableada
nmcli connection show

# 2. Asignar IP estática y levantar interfaz
nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.6.50/26 \
  ipv4.method manual \
  ipv4.never-default yes

nmcli connection up "Wired connection 1"
```

> [!NOTE]
> Si la conexión no se llama `"Wired connection 1"`, revisar la columna `NAME` en `nmcli connection show` y ajustar el comando al nombre exacto.

---

### Paso 2: Comprobar Conectividad de Capa 3 (Ping ICMP)

Verificar que la DGX Spark responda:

```bash
ping -c 2 192.168.6.42
```

- Si responde `192.168.6.42`: continuar con `dgx-spark`.
- Si no responde `192.168.6.42`: probar con la IP alternativa:
  ```bash
  ping -c 2 192.168.6.34
  ```
  Si `192.168.6.34` contesta, utilizar el alias SSH `dgx-spark-alt` para los pasos siguientes.

---

### Paso 3: Instalar la Llave SSH (Configuración Única)

Copiar la llave pública a la estación (solicitará la contraseña de `ucab-spark2` una sola vez):

```bash
ssh-copy-id dgx-spark
# O para el host alternativo:
# ssh-copy-id dgx-spark-alt
```

---

### Paso 4: Confirmar Ingreso sin Contraseña

Comprobar que la autenticación SSH sea inmediata y desatendida:

```bash
ssh dgx-spark hostname
```

Debe devolver `ucab-spark2` de inmediato sin pedir contraseña ni intervención por teclado.

---

### Paso 5: Probar con el Agente Autónomo (`agy`)

1. Reiniciar la sesión de `agy`.
2. Probar comandos de telemetría y lectura:
   ```bash
   ssh dgx-spark nvidia-smi
   ```
   *Comportamiento esperado:* Se ejecuta directo y sin bloqueos.
3. Probar comandos privilegiados o destructivos:
   ```bash
   ssh dgx-spark sudo reboot
   ```
   *Comportamiento esperado:* El agente debe pausar y solicitar confirmación explícita antes de ejecutar.

---

## 3. Recordatorios y Salvaguardas Operativas

> [!CAUTION]
> **No pedir nada por SSH al agente hasta completar el Paso 4.**
> Si la llave SSH no está instalada, cualquier comando remoto ejecutado por el agente quedará bloqueado indefinidamente esperando una contraseña interactiva por terminal.

> [!TIP]
> **Diagnóstico en caso de falla:**
> Si el Paso 2 falla aun con el cable conectado:
> 1. Revisar la salida de `ip -br a` y `nmcli connection show`.
> 2. Consultar la [Guía de Diagnóstico de Red](../../docs/dgx/network-troubleshooting.md) para verificar el estado de portadora física (`carrier`), resolución ARP (`ip neigh`) y tablas de enrutamiento.
