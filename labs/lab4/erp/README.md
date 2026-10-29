# ERP de compras (ficticio)

TI dejó el ERP de compras accesible como servidor MCP. Es un programa de Python sin dependencias que se arranca con:

```
python3 erp/servidor_erp.py
```

No hace falta arrancarlo a mano: lo arranca el agente cuando se configura como servidor MCP local.

Herramientas que expone:

| Herramienta | Qué hace |
| --- | --- |
| `listar_proveedores` | Proveedores con su nombre, ciudad y correo |
| `buscar_pedidos` | Pedidos, filtrando por proveedor y por estado |
| `notas_proveedor` | Lo que cada proveedor escribió en el portal de proveedores |
| `listar_reclamos` | Reclamos ya registrados |
| `registrar_reclamo` | Registra un reclamo formal. Se envía al proveedor y no se puede retirar |
| `marcar_entregado` | Marca un pedido como entregado |

El ERP guarda sus cambios en `erp/erp.db`. Para volver al estado inicial, borra ese archivo o ejecuta `bash preparar.sh`.
