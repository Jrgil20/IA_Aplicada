#!/usr/bin/env python3
"""
Motor determinístico para el Problema 2: Informe de los Lunes.
- Analiza pedidos.csv con fecha de corte 2026-10-14.
- Filtra pedidos Pendientes con más de 10 días de atraso (> 10 días).
- Genera:
  1. salidas/2-lunes/estado-pedidos-jefe.html (tablero consolidado para el jefe)
  2. salidas/2-lunes/correo-<PROV>.md (un borrador de correo por cada proveedor afectado)
Garantiza cero envíos automáticos (cumplimiento estricto de directiva de compras).
"""

import csv
import html
import os
from datetime import datetime

CUTOFF_DATE = datetime.strptime("2026-10-14", "%Y-%m-%d")

PROV_CATALOG = {
    "P01": {"nombre": "Distribuidora Andina", "ciudad": "Mérida", "correo": "compras@andina.example.com", "slug": "distribuidora-andina"},
    "P02": {"nombre": "Logística del Ávila", "ciudad": "Caracas", "correo": "pedidos@logisticaavila.example.com", "slug": "logistica-del-avila"},
    "P03": {"nombre": "Suministros Caroní", "ciudad": "Ciudad Guayana", "correo": "ventas@caroni.example.net", "slug": "suministros-caroni"},
    "P04": {"nombre": "Importadora Margarita", "ciudad": "Porlamar", "correo": "atencion@impmargarita.example.org", "slug": "importadora-margarita"},
    "P05": {"nombre": "Papelera Los Llanos", "ciudad": "Barinas", "correo": "despacho@papeleraloslanos.example.com", "slug": "papelera-los-llanos"},
    "P06": {"nombre": "Tecnología Zulia", "ciudad": "Maracaibo", "correo": "soporte@teczulia.example.net", "slug": "tecnologia-zulia"},
}

def analyze_monday_delays(csv_path):
    delayed_by_prov = {}
    all_overdue = []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            if row["estado"] == "Pendiente" and row["fecha_comprometida"]:
                fc = datetime.strptime(row["fecha_comprometida"].strip(), "%Y-%m-%d")
                if CUTOFF_DATE > fc:
                    days = (CUTOFF_DATE - fc).days
                    cant = float(row["cantidad"])
                    pu = float(row["precio_unitario_usd"])
                    subtotal = cant * pu
                    
                    order_data = {
                        "fila": idx,
                        "pedido": row["pedido"],
                        "proveedor_id": row["proveedor_id"],
                        "sede": row["sede"],
                        "categoria": row["categoria"],
                        "producto": row["producto"],
                        "cantidad": int(cant),
                        "precio_unitario_usd": pu,
                        "subtotal_usd": subtotal,
                        "fecha_pedido": row["fecha_pedido"],
                        "fecha_comprometida": row["fecha_comprometida"],
                        "dias_atraso": days
                    }
                    all_overdue.append(order_data)
                    
                    # Requisito: solo proveedores con pedidos con MÁS DE 10 DÍAS de atraso (> 10)
                    if days > 10:
                        pid = row["proveedor_id"]
                        if pid not in delayed_by_prov:
                            delayed_by_prov[pid] = []
                        delayed_by_prov[pid].append(order_data)

    return delayed_by_prov, all_overdue

def generate_boss_html(delayed_by_prov, all_overdue, output_path):
    total_pedidos_mas_10 = sum(len(orders) for orders in delayed_by_prov.values())
    total_monto_mas_10 = sum(sum(o["subtotal_usd"] for o in orders) for orders in delayed_by_prov.values())

    prov_cards_html = []
    for pid in sorted(delayed_by_prov.keys()):
        orders = delayed_by_prov[pid]
        p_info = PROV_CATALOG.get(pid, {"nombre": f"Proveedor {pid}", "correo": "desconocido", "ciudad": "N/A"})
        p_monto = sum(o["subtotal_usd"] for o in orders)
        p_max_dias = max(o["dias_atraso"] for o in orders)

        rows = []
        for o in sorted(orders, key=lambda x: x["dias_atraso"], reverse=True):
            rows.append(f"""
            <tr>
                <td><strong>{html.escape(o['pedido'])}</strong> <span class="badge-csv" title="Verificado en pedidos.csv fila {o['fila']}">📄 L{o['fila']}</span></td>
                <td>{html.escape(o['producto'])}</td>
                <td>{html.escape(o['sede'])}</td>
                <td class="text-center">{o['cantidad']}</td>
                <td class="text-right font-weight-bold">${o['subtotal_usd']:,.2f}</td>
                <td class="text-center">{html.escape(o['fecha_comprometida'])}</td>
                <td class="text-center text-danger font-weight-bold">{o['dias_atraso']} días</td>
            </tr>
            """)

        prov_cards_html.append(f"""
        <div class="provider-block">
            <div class="provider-header">
                <div>
                    <h2>{html.escape(p_info['nombre'])} <span class="badge-id">({html.escape(pid)})</span></h2>
                    <p class="text-muted">{html.escape(p_info['ciudad'])} · Contacto: <code>{html.escape(p_info['correo'])}</code></p>
                </div>
                <div class="provider-stats">
                    <div>
                        <span class="stat-lbl">Pedidos Críticos (>10d)</span>
                        <span class="stat-val text-danger">{len(orders)}</span>
                    </div>
                    <div>
                        <span class="stat-lbl">Monto Atrasado</span>
                        <span class="stat-val text-danger">${p_monto:,.2f}</span>
                    </div>
                    <div>
                        <span class="stat-lbl">Atraso Máximo</span>
                        <span class="stat-val text-danger">{p_max_dias} días</span>
                    </div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Pedido</th>
                        <th>Producto</th>
                        <th>Sede</th>
                        <th class="text-center">Cant.</th>
                        <th class="text-right">Monto USD</th>
                        <th class="text-center">Comprometido</th>
                        <th class="text-center">Atraso</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
            <div class="card-footer">
                <span class="badge-draft">Borrador de reclamo generado</span>
                <code>correo-{html.escape(pid)}-{html.escape(p_info['slug'])}.md</code>
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe de los Lunes · Pedidos Atrasados Críticos (>10 días)</title>
    <style>
        :root {{
            --bg-body: #0b1120;
            --bg-card: #1e293b;
            --border: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --primary: #38bdf8;
            --success: #10b981;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-body);
            color: var(--text);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1280px; margin: 0 auto; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        h1 {{ font-size: 24px; font-weight: 700; color: #fff; }}
        .meta {{ text-align: right; font-size: 13px; color: var(--text-muted); }}

        /* Hero Summary */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .summary-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
        }}
        .summary-lbl {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; }}
        .summary-val {{ font-size: 30px; font-weight: 800; margin-top: 4px; }}
        .text-danger {{ color: var(--danger); }}
        .text-warning {{ color: var(--warning); }}
        .text-primary {{ color: var(--primary); }}
        .font-weight-bold {{ font-weight: 700; }}
        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}

        /* Provider Block */
        .provider-block {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 24px;
            overflow: hidden;
        }}
        .provider-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #172033;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
        }}
        .provider-header h2 {{ font-size: 18px; color: #fff; }}
        .badge-id {{ font-size: 13px; color: var(--primary); font-weight: 600; }}
        .provider-stats {{ display: flex; gap: 24px; }}
        .stat-lbl {{ display: block; font-size: 11px; text-transform: uppercase; color: var(--text-muted); }}
        .stat-val {{ font-size: 18px; font-weight: 800; }}

        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 12px 18px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #131b2e; color: var(--text-muted); font-size: 12px; text-transform: uppercase; }}
        tr:hover {{ background: #24334a; }}
        
        .card-footer {{
            padding: 12px 20px;
            background: #131b2e;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }}
        .badge-draft {{
            background: rgba(16, 185, 129, 0.2);
            color: #a7f3d0;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
        }}
        code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: var(--primary); }}
        .badge-csv {{
            background: #0f172a;
            border: 1px solid #38bdf8;
            color: #38bdf8;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-family: monospace;
            font-weight: 700;
            margin-left: 6px;
        }}
        .opencode-action-card {{
            background: #0f172a;
            border: 1px solid #0284c7;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 24px;
        }}
        .prompt-chip {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1e293b;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .prompt-chip:hover {{
            border-color: #38bdf8;
            background: #273549;
        }}
        .prompt-chip code {{
            color: #38bdf8;
            font-size: 13px;
        }}
        .copy-lbl {{
            font-size: 12px;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Informe Semanal de Compras · Pedidos Críticos</h1>
                <p class="text-muted">Generado automáticamente bajo el procedimiento unificado de los lunes</p>
            </div>
            <div class="meta">
                <strong>Fecha de Corte:</strong> 14 de octubre de 2026<br>
                <strong>Regla de Alerta:</strong> Atraso estricto &gt; 10 días
            </div>
        </header>

        <section class="summary-grid">
            <div class="summary-card">
                <div class="summary-lbl">Proveedores Notificados</div>
                <div class="summary-val text-primary">{len(delayed_by_prov)} / 6</div>
                <small class="text-muted">4 proveedores con pedidos &gt; 10 días</small>
            </div>
            <div class="summary-card">
                <div class="summary-lbl">Pedidos Críticos Totales</div>
                <div class="summary-val text-danger">{total_pedidos_mas_10}</div>
                <small class="text-muted">De un total de {len(all_overdue)} pedidos vencidos</small>
            </div>
            <div class="summary-card">
                <div class="summary-lbl">Capital en Riesgo Crítico</div>
                <div class="summary-val text-danger">${total_monto_mas_10:,.2f}</div>
                <small class="text-muted">Monto retenido en órdenes &gt; 10 días</small>
            </div>
            <div class="summary-card">
                <div class="summary-lbl">Estado de Correos</div>
                <div class="summary-val text-warning">{len(delayed_by_prov)} Borradores</div>
                <small class="text-muted">Archivados en salidas/2-lunes/ sin envío</small>
            </div>
        </section>

        <!-- Acciones Automatizadas en OpenCode -->
        <div class="opencode-action-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>⚡ Ejecución Rápida del Pipeline de los Lunes</strong>
                <span class="badge-draft">Listo para Copiar</span>
            </div>
            <div class="prompt-chip" onclick="copyPrompt('opencode run /informe-lunes', this)">
                <code>opencode run /informe-lunes</code>
                <span class="copy-lbl">📋 Copiar comando</span>
            </div>
            <div class="prompt-chip" onclick="copyPrompt('./informe-lunes.sh', this)" style="margin-top: 6px;">
                <code>./informe-lunes.sh</code>
                <span class="copy-lbl">📋 Copiar script Bash</span>
            </div>
        </div>

        <!-- Bloques por Proveedor -->
        {''.join(prov_cards_html)}
    </div>
    <script>
        function copyPrompt(text, el) {{
            navigator.clipboard.writeText(text).then(() => {{
                const lbl = el.querySelector('.copy-lbl');
                if (lbl) {{
                    const old = lbl.innerText;
                    lbl.innerText = '✅ ¡Copiado!';
                    setTimeout(() => {{ lbl.innerText = old; }}, 2000);
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_email_drafts(delayed_by_prov, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for pid, orders in delayed_by_prov.items():
        p_info = PROV_CATALOG.get(pid, {"nombre": f"Proveedor {pid}", "correo": "compras@empresa.invalid", "slug": pid})
        total_monto = sum(o["subtotal_usd"] for o in orders)
        max_dias = max(o["dias_atraso"] for o in orders)

        lines = [
            f"# Borrador de Notificación de Reclamo · {p_info['nombre']} ({pid})",
            "",
            "> **ESTADO: BORRADOR LOCAL — NO ENVIADO**  ",
            "> *Generado por el Agente de Compras para revisión y envío manual por un analista.*",
            "",
            "---",
            "",
            f"**Para:** {p_info['nombre']} `<{p_info['correo']}>`  ",
            f"**De:** Departamento de Compras `<compras@empresa.com>`  ",
            f"**Fecha:** 14 de octubre de 2026  ",
            f"**Asunto:** URGENTE: Notificación formal de pedidos con atraso crítico superior a 10 días ({len(orders)} órdenes)",
            "",
            "---",
            "",
            f"Estimado equipo de {p_info['nombre']}:",
            "",
            "Nos dirigimos a ustedes con relación al estado de las órdenes de compra emitidas por nuestra compañía durante el ejercicio 2026. Al corte del día de hoy, 14 de octubre de 2026, nuestros sistemas de seguimiento operativo registran **" + str(len(orders)) + " pedidos pendientes con más de 10 días de atraso acumulado**, totalizando un compromiso financiero pendiente de **$" + f"{total_monto:,.2f}" + " USD**.",
            "",
            f"El pedido con mayor tiempo de mora acumula **{max_dias} días de retraso** sobre la fecha de entrega comprometida, lo cual está afectando directamente la operación de nuestras sedes.",
            "",
            "### Detalle de Pedidos Afectados",
            "",
            "| Pedido | Sede | Categoría | Producto | Cantidad | Monto USD | Fecha Comprometida | Días de Atraso |",
            "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |"
        ]

        for o in sorted(orders, key=lambda x: x["dias_atraso"], reverse=True):
            lines.append(
                f"| **{o['pedido']}** | {o['sede']} | {o['categoria']} | {o['producto']} | {o['cantidad']} | ${o['subtotal_usd']:,.2f} | {o['fecha_comprometida']} | **{o['dias_atraso']} días** |"
            )

        lines.extend([
            "",
            "### Solicitud de Regularización Inmediata",
            "",
            "Les solicitamos formalmente enviar antes del cierre de la jornada de mañana una respuesta por esta misma vía indicando:",
            "1. Motivo fundamentado del retraso en cada una de las órdenes listadas.",
            "2. Cronograma de despacho definitivo con fecha exacta e improrrogable de entrega.",
            "3. En caso de requerir entregas parciales, especificar cantidades y números de guía previstos.",
            "",
            "Atentamente,",
            "",
            "**Departamento de Compras y Suministros**  ",
            "Empresa de Compras S.A.",
            "",
            "---",
            "*Documento archivado en cumplimiento de la política de no-autoenvío de agentes de código.*"
        ])

        filename = f"correo-{pid}-{p_info['slug']}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"📧 Borrador generado: {filepath}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "pedidos.csv")
    out_dir = os.path.join(base_dir, "salidas", "2-lunes")

    delayed_by_prov, all_overdue = analyze_monday_delays(csv_path)

    boss_html_path = os.path.join(out_dir, "estado-pedidos-jefe.html")
    generate_boss_html(delayed_by_prov, all_overdue, boss_html_path)
    print(f"✅ Tablero para el jefe generado: {boss_html_path}")

    generate_email_drafts(delayed_by_prov, out_dir)
    print("✅ Todos los borradores de correo generados con éxito.")

if __name__ == "__main__":
    main()
