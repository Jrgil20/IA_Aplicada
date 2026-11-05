# Auditoría del problema 8 · «Lo que dice el contrato»

- **Artefacto auditado:** `salidas/8-penalidades.html` y el generador `scripts/calcular_penalidades.py`
- **Fecha de auditoría:** 2026-11-05
- **Alcance:** laboratorio local del workshop 3; datos ficticios de Comercial Los Samanes, C.A.
- **Veredicto:** **remediado el 2026-11-05.** El error material de $19,30 y las brechas de endurecimiento fueron corregidos en el generador y el HTML fue regenerado. La página sigue siendo un **borrador** que requiere revisión y firma humana. Ver §8.

---

## Resumen para mesa (2 hallazgos en 2 minutos)

1. **Tasa de Tecnología Zulia (P06) equivocada.** El contrato dice **0,2 % diario**; el script aplicaba **0,5 %**. El pedido PO-1365 quedaba en **$32,17** cuando corresponde **$12,87**, y el total pasaba de **$11.343,33** a **$11.362,63**. La página se declaraba «Listo para Firma».
2. **Inyección de HTML desde el CSV.** Los campos del ERP se insertaban en la página sin escapar. Un `producto` con `<b>HOLA</b>` se renderizaba como etiqueta, no como texto. Cualquiera que controle el export del ERP podía alterar el documento que firma Legal.

Estos dos hallazgos ya están corregidos; el estado final está en **§8**. Prioridad que se siguió: **H1 → H3 → H4 → H2 → H5/H6**.

---

## 0. Alcance y autorización

| Campo | Valor |
|---|---|
| App | Generador determinista de un informe legal en HTML. No hay servidor ni LLM en tiempo de ejecución. |
| URL / puerto | No aplica: el entregable es un archivo local. |
| Versión | Árbol de trabajo sin commit; `HEAD` del repositorio: `4a8b028`. |
| Modelo | Ninguno en runtime. El script se produjo con el agente/qwen3-coder local, pero la página final no invoca un modelo. |
| Dueño / autorización | Equipo del laboratorio; auditoría solicitada por el usuario. |
| Datos permitidos | `datos/pedidos_pendientes.csv` y `documentos/` (ficticios). |
| Datos prohibidos | Red UCAB, servicios externos, datos reales de proveedores. |
| Acciones permitidas | Lectura de `documentos/` y del CSV; escritura solo en `scripts/` y `salidas/`; pruebas en copias en `/tmp`. |
| Acciones realizadas | Se corrigió `scripts/calcular_penalidades.py` y se regeneró `salidas/8-penalidades.html`. `documentos/` y el CSV no se modificaron. Ver §8. |
| Ventana | 2026-11-05. |
| Criterio de parada | Encontrar y reproducir los fallos de mayor impacto; no tumbar ni alterar el entregable. |

> **Nota de alcance:** el problema 8 no es una app conversacional. Las pruebas de fuga de system prompt, inyección directa, imagen y agencia no tienen superficie en runtime. Sí aplican la revisión de código, el manejo de salida HTML, la integridad de las reglas y la exactitud legal.

---

## 1. Inventario

| Pieza | Hallazgo |
|---|---|
| Modelo | No hay modelo en runtime. El HTML es estático. |
| System prompt | No hay prompt en el artefacto. `AGENTS.md` contiene reglas del proyecto, sin secretos. |
| Entradas | `datos/pedidos_pendientes.csv` (pedido, proveedor, producto, cantidades, precios, fechas, estado). No hay entrada de usuario en la página. |
| Ensamblado | El script lee el CSV con `csv.DictReader` y concatena valores en un `f-string` HTML. |
| Salida | `salidas/8-penalidades.html`, abierto en navegador. Sin JavaScript ni recursos externos. |
| Agencia | Ninguna: el script solo escribe un archivo. No ejecuta comandos, SQL ni acciones externas. |
| Datos | Nombres de proveedores, precios, importes y penalidades. Datos comerciales; no hay PII de personas en la salida. |
| Logs | No hay logging. |
| Dependencias | Solo biblioteca estándar: `os`, `csv`, `datetime`. Sin `pip`. |
| Límites | Sin límite de tamaño ni validación de esquema del CSV. |

---

## 2. Superficie

| Punto | Riesgo | Estado |
|---|---|---|
| CSV del ERP → HTML | Inyección de HTML/script si un campo trae marcado | **Vulnerable** (H3) |
| Reglas contractuales hardcodeadas | Tasa, gracia o tope desactualizados | **Vulnerable** (H1, H2) |
| Fechas de vigencia de adendas | Aplicar una adenda a pedidos anteriores | **Latente** (H2) |
| Texto de cierre y certificación | La página se autodeclara lista para firma | **Vulnerable** (H4) |
| Salida a disco | Permisos del archivo con datos comerciales | **Bajo** (H6) |
| Ejecución de la salida | `eval`, `exec`, shell, SQL | **Sin hallazgos** |
| Secretos | Claves, tokens, contraseñas | **Sin hallazgos** |
| Recursos externos | CDNs, fuentes, imágenes, JS | **Sin hallazgos** |

---

## 3. Matriz de pruebas

### 3.1 Pruebas de comportamiento LLM

| # | Prueba | Resultado |
|---|---|---|
| 1 | Fuga del system prompt | **N/A.** No hay prompt ni LLM en runtime. |
| 2 | Inyección directa | **N/A.** No hay chat ni entrada de usuario. |
| 3 | Inyección indirecta por dato | **N/A en runtime.** Se revisó el corpus: no se encontraron marcadores de inyección en `documentos/` (`ignora las instrucciones`, `system prompt`, `responde solo`, etc.). Riesgo residual solo en la fase de generación con el agente. |
| 4 | Salida sin escapar | **Ejecutada.** `<b>HOLA</b>` en el CSV se renderiza como HTML crudo. Ver H3. |
| 5 | Agencia | **N/A.** El script no ejecuta acciones; solo escribe el HTML. |
| 6 | Inyección por imagen | **N/A.** No hay VLM ni cámara. |
| 7 | Imagen cambia formato | **N/A.** No hay VLM. |
| 8 | Contraste con alucinación | **Equivalente de exactitud:** se contrastaron tasas, gracias, topes y totales contra los contratos. Ver H1 y H2. |

### 3.2 Pruebas de código y datos

| # | Qué se revisó | Resultado |
|---|---|---|
| 1 | Secretos en código/HTML | Sin `api_key`, `token`, `password` ni secretos. |
| 2 | Salida del modelo a sink peligroso | Sin `eval`, `exec`, `os.system`, `subprocess`, SQL. |
| 3 | Entrada externa sin validar | **Hallazgo H3:** el CSV se interpola sin escapar. **H5:** sin validación de esquema. |
| 4 | Salida mostrada sin escapar | **Hallazgo H3:** `f-string` con `p['producto']`, `s['nombre']`, etc. |
| 5 | Datos sensibles en logs | Sin logs. **H6:** permisos `664` del HTML. |
| 6 | Dependencias | Solo stdlib; sin lockfile necesario. |
| 7 | Sin límites | CSV local pequeño; sin límite de tamaño, impacto bajo (H5). |

---

## 4. Hallazgos

### H1 · Tasa de penalidad de P06 incorrecta: 0,5 % en el código frente a 0,2 % en el contrato

| Campo | Detalle |
|---|---|
| **Qué probé** | Recalcular las 15 penalidades con las tasas leídas de cada contrato y comparar con la salida del script. |
| **Evidencia** | `scripts/calcular_penalidades.py:80` fija `"tasa_diaria": 0.005  # 0.5%` para P06. `documentos/contratos/CT-2025-P06_tecnologia-zulia.md:57` dice «penalidad del **0,2 %** del importe del pedido por cada día calendario». |
| **Resultado** | PO-1365: el script calcula **$32,17** (2,0 % de $1.608,40); lo correcto es **$12,87** (0,8 %). Total del informe: **$11.362,63** frente a **$11.343,33**; sobrestimación de **$19,30**. PO-1314 no cambia porque el tope del 6 % ya se alcanza con ambas tasas. |
| **Riesgo OWASP** | **LLM09 · Misinformation** (información legal/financiera incorrecta). |
| **MITRE ATLAS** | No es una cadena adversarial: es un fallo de integridad del dato con impacto financiero (`Impact`). |
| **Severidad** | **Alta.** Legal puede firmar y descontar $19,30 de más; el error es reproducible y afecta el total. |
| **Mitigación** | Cambiar la tasa de P06 a `0.002`. Añadir una prueba que compare la tabla de reglas contra los contratos y que fije el total esperado. |
| **Re-prueba** | **Remediado y verificado en el entregable:** total **$11.343,33** y PO-1365 **$12,87**. Ver §5 y §8. |

### H2 · Reglas hardcodeadas sin vigencia ni verificación contra los contratos

| Campo | Detalle |
|---|---|
| **Qué probé** | Revisar cómo se elige la regla de cada proveedor y si la adenda de P04 respeta la fecha de emisión. Comparar metadatos (RIF) con los contratos. |
| **Evidencia** | `scripts/calcular_penalidades.py:53-62` define la adenda P04 como si aplicara siempre; `:100-103` selecciona la regla solo por `proveedor_id`, sin mirar `fecha_pedido`. La adenda `documentos/contratos/AD-2026-P04-01_adenda-importadora-margarita.md` (Cláusula segunda) solo aplica a órdenes emitidas desde el 01/07/2026. Además, los seis RIF de `PROVEEDORES_INFO` (`:22,33,44,55,66,77`) no coinciden con los de los contratos (por ejemplo, P01: script `J-30124578-9`, contrato `J-40118273-5`). |
| **Resultado** | Con los datos actuales no hay error P04: PO-1295 y PO-1324 son posteriores al 01/07/2026. Prueba sintética con una orden P04 de junio: el script aplica 15 % (tope de la adenda) y da **$150,00**; la cláusula original (0,5 %, 7 días de gracia, tope 10 %) da **$100,00**. Diferencia: **$50,00**. |
| **Riesgo OWASP** | **LLM09 · Misinformation**. |
| **MITRE ATLAS** | `Impact` por integridad de la regla de negocio. |
| **Severidad** | **Media.** Hoy el output es correcto, pero el diseño falla en cuanto entre una orden antigua o cambie una adenda. Los RIF incorrectos indican que la tabla no se verificó contra la fuente. |
| **Mitigación** | Añadir `vigente_desde`/`vigente_hasta` a cada regla y elegir por `fecha_pedido`; derivar los metadatos de una fuente verificada; probar una orden P04 anterior a julio. |
| **Re-prueba** | **Remediado y verificado:** la orden sintética de junio pasa a **$100,00** con la cláusula original. Ver §5 y §8. |

### H3 · Inyección de HTML (XSS) desde campos del CSV

| Campo | Detalle |
|---|---|
| **Qué probé** | Insertar `<b>HOLA</b>` en el campo `producto` de una copia del CSV y abrir el HTML generado. |
| **Evidencia** | `scripts/calcular_penalidades.py:496` (`s['nombre']`), `:498` (`s['doc_fuente']`), `:545` (`p['pedido']`), `:548` (`p['producto']`), `:549` (`p['sede']`), `:562` (`p['doc_fuente']`) y `:563` (`p['fundamento']`) se interpolan sin `html.escape`. |
| **Resultado** | En la copia sin endurecer, el HTML contiene `<div style="font-weight: 600;"><b>HOLA</b></div>` (etiqueta cruda, línea 761 de la copia). En la copia con `html.escape`, contiene `&lt;b&gt;HOLA&lt;/b&gt;`. |
| **Riesgo OWASP** | **LLM05 · Improper Output Handling**. |
| **MITRE ATLAS** | `Execution` en el navegador de Legal → `Impact` sobre la integridad del documento firmado. |
| **Severidad** | **Media.** Requiere control del CSV/export del ERP, pero el impacto es un documento legal manipulado que se abre localmente. |
| **Mitigación** | Escapar todos los valores con `html.escape(..., quote=True)`; añadir CSP `default-src 'none'; style-src 'unsafe-inline'; script-src 'none'`; validar el esquema del CSV. |
| **Re-prueba** | **Remediado y verificado:** `<b>HOLA</b>` sale como `&lt;b&gt;HOLA&lt;/b&gt;`. Ver §5 y §8. |

### H4 · Auto-certificación y cifras hardcodeadas en la página

| Campo | Detalle |
|---|---|
| **Qué probé** | Revisar si los textos de cierre y los KPIs se derivan de los datos o están fijos. |
| **Evidencia** | `salidas/8-penalidades.html:258` («Dictamen Legal Vinculante»), `:268` («15 Pedidos Críticos»), `:269` («Listo para Firma y Notificación Formal»), `:287` («6 / 6»), `:293` («57.0%»); en el generador, `scripts/calcular_penalidades.py:431-442`, `:460-466` y `:585`. |
| **Resultado** | Las cifras coinciden hoy por casualidad, pero no se recalculan. Si cambia el CSV, la página sigue diciendo «15», «6/6» y «57.0%». Ejemplo concreto: al corregir H1, el peso real de P04 pasa a **57,1 %**, pero el HTML seguiría mostrando **57.0 %**. H1 demuestra que la página puede estar equivocada y aun así declararse lista para firma. |
| **Riesgo OWASP** | **LLM09 · Misinformation** y sesgo de automatización. |
| **MITRE ATLAS** | `Impact` (decisión legal basada en una salida no verificada). |
| **Severidad** | **Media.** No es explotable remotamente, pero favorece que Legal firme sin revisar. |
| **Mitigación** | Calcular conteos y porcentajes desde `pedidos`/`subtotales`; sustituir «Listo para Firma» por «Borrador generado automáticamente — requiere revisión legal»; incluir fecha de generación y hash del CSV; añadir una prueba de total. |
| **Re-prueba** | **Remediado:** se quitaron las auto-certificaciones y los KPIs se calculan desde los datos. Ver §8. |

### H5 · Robustez de entrada y salida (baja)

| Campo | Detalle |
|---|---|
| **Qué probé** | Revisar qué pasa con un proveedor desconocido, una fecha o un precio inválido, un CSV vacío o la carpeta `salidas/` ausente. |
| **Evidencia** | `scripts/calcular_penalidades.py:96` (`date.fromisoformat`), `:102` (`PROVEEDORES_INFO[prov_id]`), `:105` (`float`), `:465` (`subtotales['P04']`), `:510` (división por cero si no hay pedidos) y `:614` (no crea `salidas/`). |
| **Resultado** | Un proveedor nuevo lanza `KeyError`; una fecha o precio mal formado lanza excepción; un CSV sin P04 lanza `KeyError`; sin pedidos, división por cero. |
| **Riesgo OWASP** | Sin categoría directa; es robustez/higiene. |
| **Severidad** | **Baja.** El CSV es local y el fallo es ruidoso (no silencioso), pero puede dejar el informe sin generar. |
| **Mitigación** | Validar columnas y tipos; mensaje de error claro; `os.makedirs(..., exist_ok=True)`; proteger denominadores. |
| **Re-prueba** | No aplica para el cierre; se recomienda añadir pruebas unitarias. |

### H6 · Permisos del entregable (baja)

| Campo | Detalle |
|---|---|
| **Qué probé** | Revisar permisos de `salidas/8-penalidades.html`. |
| **Evidencia** | `stat -c '%a %n' salidas salidas/8-penalidades.html` → `775 salidas`, `664 salidas/8-penalidades.html`. |
| **Resultado** | El informe con importes y nombres de proveedores es legible por cualquier usuario local del Spark. |
| **Riesgo OWASP** | **LLM02 · Sensitive Information Disclosure** (datos comerciales, no PII). |
| **Severidad** | **Baja.** Depende de que el Spark sea multiusuario. |
| **Mitigación** | `chmod 750 salidas` y `chmod 640 salidas/8-penalidades.html`; o un grupo dedicado. |
| **Re-prueba** | **Remediado:** el generador aplica `640` al HTML y `750` a `salidas/`. Ver §8. |

---

## 5. Re-prueba de mitigaciones (antes / después; el entregable ya incorpora las correcciones)

| Falla | Corrección probada | Antes | Después | Estado |
|---|---|---|---|---|
| H1 | P06 `tasa_diaria = 0.002` | Total $11.362,63; PO-1365 $32,17 | Total **$11.343,33**; PO-1365 **$12,87** | **Aplicado y verificado** |
| H2 | Elegir cláusula P04 por `fecha_pedido < 2026-07-01` | Orden sintética de junio: $150,00 (15 %) | **$100,00** (10 %) | **Aplicado y verificado** |
| H3 | `html.escape` en todos los campos + CSP | `<b>HOLA</b>` crudo | `&lt;b&gt;HOLA&lt;/b&gt;` | **Aplicado y verificado** |
| H4 | Quitar auto-certificación y calcular KPIs | Textos fijos | KPIs dinámicos y página marcada como borrador | **Aplicado y verificado** |
| H5 | Validación de columnas, fechas, precios y proveedor | `KeyError`/traza críptica | Mensaje con número de fila | **Aplicado y verificado** |
| H6 | `chmod 640` / `750` | `664` / `775` | **`640` / `750`** | **Aplicado y verificado** |

Reproducciones:

```bash
# H1/H4: total actual del entregable ($11.343,33)
python3 scripts/calcular_penalidades.py

# H1: pruebas de regresión (total, PO-1365, P04, RIF, escape)
python3 scripts/probar_penalidades.py

# H3: la marca inofensiva sale cruda con el generador original y escapada con el actual
grep -n 'HOLA' /tmp/audit8-inj/salidas/8-penalidades.html
grep -n 'HOLA' /tmp/audit8-final-xss/salidas/8-penalidades.html

# H2: la orden P04 sintética de junio da $150 con la adenda y $100 con la cláusula original
grep -n -A 12 'PO-9998' /tmp/audit8-p04/salidas/8-penalidades.html | grep -E 'PO-9998|15\.0%'
grep -n -A 12 'PO-9998' /tmp/audit8-final-p04/salidas/8-penalidades.html | grep -E 'PO-9998|10\.0%'
```

---

## 6. Controles que sí pasan

- **Sin secretos** en el script ni en el HTML.
- **Sin sinks peligrosos:** no hay `eval`, `exec`, `os.system`, `subprocess`, SQL ni `innerHTML`.
- **Solo biblioteca estándar:** `os`, `csv`, `datetime`, `hashlib`, `html`, `unittest`.
- **Sin recursos externos:** el HTML no tiene `http://`, `https://`, `<script>`, `<iframe>`, fuentes ni imágenes externas.
- **`documentos/` intacto:** la auditoría solo leyó; no se movió, editó ni borró ningún documento.
- **Sin marcadores de inyección** en los 436 documentos (`ignora las instrucciones`, `system prompt`, `responde solo`, etc.).
- **Cálculo base correcto** en los otros cinco proveedores: P01 0,5 %/5 días/10 %; P02 0,3 %/2/5 %; P03 0,4 %/5/8 %; P04 adenda 1 %/3/15 % para pedidos desde julio; P05 0,6 %/5/12 %.
- **Filtro de corte correcto:** solo pedidos `Pendiente` con más de 10 días de atraso (15 pedidos).

---

## 7. Recomendación

1. **Revisar y firmar** `salidas/8-penalidades.html` como borrador humano. El total ahora es **$11.343,33**; la página ya no se autodeclara «lista para firma».
2. **Mantener las pruebas de regresión** con `python3 scripts/probar_penalidades.py` antes de cada regeneración.
3. **No volver a hardcodear** tasas, topes, conteos ni porcentajes: las reglas y los KPIs deben salir del CSV y de la tabla de reglas verificada.
4. **Revalidar** cualquier adenda o contrato nuevo contra `PROVEEDORES_INFO`/`P04_ORIGINAL` y añadir su prueba.
5. **Conservar** los permisos `640`/`750` si el Spark es multiusuario.

> La auditoría solo leyó `documentos/` y el CSV. Las correcciones se aplicaron al generador y el HTML fue regenerado; las pruebas previas se conservan en `/tmp/audit8*`.

---

## 8. Remediación aplicada (2026-11-05)

| Hallazgo | Cambio aplicado | Verificación |
|---|---|---|
| **H1** | P06 pasó de `0.005` a `0.002` en `PROVEEDORES_INFO` y en su justificación. | Total **$11.343,33**; PO-1365 **$12,87**; prueba `test_po_1365_usa_tasa_p06_de_0_2`. |
| **H2** | Se añadió `P04_ORIGINAL` y `regla_para()`: la adenda solo aplica desde `2026-07-01`. Se corrigieron los seis RIF contra los contratos. | Orden P04 sintética de junio: **$100,00** (10 %) en vez de $150,00; pruebas `test_regla_p04_*` y `test_rifs_de_los_contratos`. |
| **H3** | Se añadió `esc()` con `html.escape(..., quote=True)` en todos los campos de texto del CSV y una CSP `default-src 'none'`. | `<b>HOLA</b>` sale como `&lt;b&gt;HOLA&lt;/b&gt;`; prueba `test_escape_de_html`. |
| **H4** | Se quitaron «Dictamen Legal Vinculante», «Listo para Firma» y «Conformidad Plena». Los conteos, porcentajes y montos del análisis P04/P06 se calculan desde los datos. Se añadieron fecha de generación y huella SHA-256 del CSV. | El HTML dice «Borrador · Requiere revisión y firma humana»; P04 pesa **57,1 %**; no quedan hardcodes de KPIs en el generador. |
| **H5** | Validación de columnas, fechas, cantidades, precios y proveedor; mensajes de error con número de fila; `os.makedirs()` para `salidas/`; división protegida. | Proveedor `P99` produce «Fila 30: proveedor desconocido 'P99'» sin traza críptica. |
| **H6** | `os.chmod(OUTPUT_HTML, 0o640)` y `os.chmod(salidas_dir, 0o750)`. | `stat`: `640 salidas/8-penalidades.html`, `750 salidas`. |

**Verificación final ejecutada:**

```text
python3 -m py_compile scripts/calcular_penalidades.py scripts/probar_penalidades.py  -> OK
python3 scripts/calcular_penalidades.py                                              -> 15 pedidos | $11.343,33
python3 scripts/probar_penalidades.py                                                -> 10 pruebas OK
HTML parseado sin errores; sin <script>, <iframe>, recursos externos ni sinks peligrosos.
documentos/ y datos/pedidos_pendientes.csv sin modificaciones.
```

**Estado:** los seis hallazgos quedaron cerrados. El entregable sigue siendo un **borrador generado automáticamente** y requiere la revisión y firma de una persona.
