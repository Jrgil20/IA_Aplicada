# Reglas del proyecto (lab 2)

- Los datos son ficticios. Para cualquier cálculo de fechas, hoy es 2026-10-28.
- Un pedido lleva atraso cuando está Pendiente y hoy supera su fecha_comprometida.
- Los datos de pedidos y proveedores salen del ERP vía MCP, no de archivos sueltos.
- Los entregables van en la carpeta salidas/.
- No envíes correos ni publiques nada.

## Condiciones de Gobernanza de TI (Seguridad MCP)
1. **Inmutabilidad de Estados:** El agente tiene prohibido invocar `marcar_entregado` (`deny`). Nunca puede cambiar el estado de un pedido en el ERP.
2. **Aprobación Humana de Reclamos:** Ningún reclamo formal puede registrarse mediante `registrar_reclamo` sin que un analista humano lo apruebe explícitamente en el momento (`ask`).
3. **Contraste de Veracidad:** En cualquier informe ejecutivo, el agente debe contrastar lo alegado por el proveedor en `notas_proveedor` con la realidad comprobada de los registros en `pedidos`.
