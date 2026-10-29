# Problema 6 · El ERP entra a la conversación

Han pasado dos semanas. Compras ya no trabaja con CSV sueltos: los pedidos al día viven en el ERP, y TI lo dejó accesible para el agente como servidor MCP en la carpeta `erp/`.

La gerente de compras tiene mañana la llamada mensual con los proveedores. Quiere llegar sabiendo qué pedidos llevan más de 10 días de atraso según el ERP, qué dice cada proveedor en el portal sobre esos pedidos, y a quién le recomiendan reclamar formalmente.

**Entregable:** el ERP conectado al agente en la configuración del proyecto, y `salidas/6-erp.html`, la página que la gerente usa en la llamada.

**Condiciones de TI:**

- El agente puede consultar el ERP, pero nunca puede cambiar el estado de un pedido.
- Ningún reclamo se registra sin que una persona lo apruebe en el momento.

**La gerente quiere leer lo que dice cada proveedor tal como lo escribió, y saber qué es cierto según el ERP.**
