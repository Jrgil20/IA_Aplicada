---
name: informe-lunes
description: Ejecuta el procedimiento semanal de compras de los lunes. Genera el informe consolidado para el jefe y los borradores de correo para proveedores con mas de 10 dias de atraso.
---

# Procedimiento Semanal de Compras (Informe de los Lunes)

Usa esta skill cada lunes cuando cualquier usuario solicite el estado de pedidos atrasados o la preparación de notificaciones a proveedores.

## Instrucciones de Ejecución

1. Ejecuta el script unificado de la raíz del proyecto:
```bash
./informe-lunes.sh
```

2. Verifica que los entregables se hayan generado en `salidas/2-lunes/`:
   - `estado-pedidos-jefe.html`: Tablero ejecutivo con los pedidos críticos (> 10 días de atraso).
   - `correo-P01-distribuidora-andina.md`: Borrador formal de reclamo.
   - `correo-P02-logistica-del-avila.md`: Borrador formal de reclamo.
   - `correo-P04-importadora-margarita.md`: Borrador formal de reclamo.
   - `correo-P06-tecnologia-zulia.md`: Borrador formal de reclamo.
   - `seguridad-auditoria.md`: Reporte de validación de controles de TI.

## Reglas Inquebrantables de la Dirección
- **NO ENVIAR CORREOS:** Los correos quedan exclusivamente como borradores locales en Markdown. Nunca intentes enviarlos por SMTP o API externa.
- **NO PUBLICAR:** No compartas sesiones fuera del entorno local.
