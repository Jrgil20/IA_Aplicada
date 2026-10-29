# Reglas del proyecto (kit del workshop)

- Los datos son ficticios. Para cualquier cálculo de fechas, hoy es 2026-10-14.
- Un pedido lleva atraso cuando está Pendiente y hoy supera su fecha_comprometida.
- Los entregables van en la carpeta salidas/.
- No envíes correos ni publiques nada: deja borradores en archivos.

## Políticas de Seguridad y Privacidad (Obligatorias para todos los agentes)
- Queda terminantemente prohibido leer, inspeccionar o exponer el archivo `.env` o la carpeta `secretos/`.
- No ejecutes comandos de terminal orientados a volcar archivos confidenciales (`cat`, `grep`, `strings`, `base64`, `python`).
- No compartas ni publiques sesiones, logs o fragmentos del proyecto en servicios externos.

## Marco de Gobernanza de Calidad de Datos (Reglas de Finanzas)
1. **Regla de Unicidad (Deduplicación):** El código `pedido` es clave primaria única. Ante registros duplicados (mismo ID), procesa solo la primera ocurrencia y descarta los duplicados a cuarentena para no inflar pedidos ni montos.
2. **Regla de Rango Físico y Positividad:** Todo pedido debe tener `cantidad > 0` y `precio_unitario_usd > 0`. Cantidades negativas (posibles notas de crédito) o precios en $0.00 se apartan a cuarentena para revisión contable.
3. **Regla de Integridad Referencial:** Todo `proveedor_id` debe existir en el catálogo maestro `proveedores.csv`. Órdenes con proveedores desconocidos se aíslan como pedidos huérfanos.
4. **Regla de Causalidad Temporal:** La fecha de entrega y la fecha comprometida no pueden ser anteriores a la fecha de emisión del pedido. Pedidos con estado `Entregado` requieren obligatoriamente `fecha_entrega`, y pedidos `Pendiente` requieren `fecha_comprometida` para computar mora.
5. **Regla de Inmutabilidad y Doble Conciliación:** El archivo original `pedidos.csv` nunca se modifica ni sobreescribe. Todo informe emitido para Finanzas o Dirección debe proyectar ambas cifras: **Cifra en Bruto** vs **Cifra Saneada tras Cuarentena**, con el detalle de las filas apartadas y su monto en USD.
