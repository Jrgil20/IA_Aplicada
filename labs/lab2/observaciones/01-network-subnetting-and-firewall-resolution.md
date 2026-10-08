# Observación 01: Subnetting (/26) y Resolución de Firewall Ingress (UFW)

> **Contexto:** Establecimiento del canal de red privado entre la laptop del estudiante (`eno2`) y la estación supercomputadora NVIDIA DGX Spark (`ucab-spark1`, IP `192.168.6.42`).

---

## 1. Problema A: La Trampa de la Máscara de Red (`/26` vs `/24`)

### Síntoma
La laptop intentaba conectarse a la Spark con la IP `192.168.6.100/24`. La tabla ARP en la laptop resolvía la dirección física de la Spark (`192.168.6.42 lladdr dc:04:5a:73:a5:a7 REACHABLE`), pero cualquier intento de ping o conexión TCP a los puertos 22 u 8080 terminaba en `Connection timed out`.

### Causa Raíz
Al inspeccionar la tabla de rutas de la Spark mediante `ip route`:
```text
192.168.6.0/26 dev enxdc045a73a5a7 proto kernel scope link src 192.168.6.42 metric 100
default via 192.168.6.1 dev enxdc045a73a5a7 proto dhcp src 192.168.6.42 metric 20100
```

Se descubrió que la Spark opera bajo una máscara **/26** (`255.255.255.192`), cuyo rango útil va únicamente de **`192.168.6.1` a `192.168.6.62`**.
- La IP asignada a la laptop (`.100`) pertenecía a otra subred (`192.168.6.64/26`).
- Por tanto, la Spark evaluaba que la laptop no era un host local y enviaba todas las respuestas al gateway `192.168.6.1`, el cual no existía en el switch del laboratorio, descartando los paquetes de vuelta.

### Solución
Se reconfiguró la placa Ethernet de la laptop a una IP válida dentro del rango:
```bash
nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.6.50/26 \
  ipv4.method manual \
  ipv4.never-default yes
nmcli connection up "Wired connection 1"
```
**Resultado:** Ping con 0% packet loss y latencia `< 1 ms` (`0.897 ms`), y puerto SSH 22 accesible de inmediato.

---

## 2. Problema B: Bloqueo de Tráfico Ingress en la Laptop por UFW

### Síntoma
Una vez que `app.py` arrancó en la Spark, la interfaz web reportaba `Camera: Disconnected`. En la Spark, OpenCV arrojaba:
```text
[tcp @ 0x40f275c0] Connection to tcp://192.168.6.50:8080 failed: Connection timed out
```

### Causa Raíz
El servidor de video `stream_camera.py` corría en `0.0.0.0:8080` en la laptop, pero el firewall de Ubuntu Desktop (`/etc/ufw/ufw.conf`, `ENABLED=yes`) descartaba por política por defecto todas las conexiones TCP entrantes al puerto 8080 que se originaban desde la Spark por el cable Ethernet.

### Solución
Se habilitó el tráfico entrante sobre la interfaz cableada:
```bash
sudo ufw allow in on eno2
```
**Resultado:** Inmediatamente la Spark pudo leer los cuadros del stream y el estado en la interfaz web cambió a `Camera: Connected`.
