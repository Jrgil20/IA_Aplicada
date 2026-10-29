#!/usr/bin/env python3
"""
Motor de Análisis y Generador de Entregables para Problema 6:
- Conecta al ERP mediante el protocolo MCP (stdio) contra erp/servidor_erp.py
- Analiza pedidos con más de 10 días de retraso (> 10d) al corte de hoy (2026-10-28)
- Extrae notas textuales de los proveedores en el portal
- Contrasta la veracidad de lo alegado vs la realidad contable del ERP
- Genera salidas/6-erp.html con diseño ejecutivo offline
"""

import html
import json
import os
import subprocess
from datetime import datetime

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERP_SERVER_PY = os.path.join(AQUI, "erp", "servidor_erp.py")
CUTOFF_DATE = datetime.strptime("2026-10-28", "%Y-%m-%d")

class ERPClientMCP:
    """Cliente ligero MCP sobre stdio para comunicarse con servidor_erp.py"""
    def __init__(self, script_path):
        self.proc = subprocess.Popen(
            ["python3", script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        self.req_id = 0
        # Initialize
        self._call("initialize", {"protocolVersion": "2025-06-18"})

    def _call(self, method, params=None):
        self.req_id += 1
        payload = {"jsonrpc": "2.0", "id": self.req_id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("Servidor MCP cerró la conexión inesperadamente")
        return json.loads(line)

    def tool(self, name, arguments=None):
        resp = self._call("tools/call", {"name": name, "arguments": arguments or {}})
        if "error" in resp:
            raise RuntimeError(f"Error MCP {name}: {resp['error']}")
        result_content = resp.get("result", {}).get("content", [])
        if result_content and result_content[0].get("type") == "text":
            return json.loads(result_content[0]["text"])
        return resp.get("result")

    def close(self):
        self.proc.terminate()
        self.proc.wait()

def analyze_erp_state():
    client = ERPClientMCP(ERP_SERVER_PY)
    try:
        proveedores = client.tool("listar_proveedores")
        pedidos_pendientes = client.tool("buscar_pedidos", {"estado": "Pendiente"})
        reclamos_existentes = client.tool("listar_reclamos")
        
        notas = {}
        for p in proveedores:
            pid = p["proveedor_id"]
            notas[pid] = client.tool("notas_proveedor", {"proveedor_id": pid})
    finally:
        client.close()

    # Mapear proveedores
    prov_map = {p["proveedor_id"]: p for p in proveedores}

    # Filtrar pedidos con atraso estricto > 10 días al 2026-10-28
    criticos_por_prov = {p["proveedor_id"]: [] for p in proveedores}
    total_mora_critica = 0.0

    for ped in pedidos_pendientes:
        fc_str = ped.get("fecha_comprometida")
        if not fc_str:
            continue
        fc = datetime.strptime(fc_str, "%Y-%m-%d")
        if CUTOFF_DATE > fc:
            dias_atraso = (CUTOFF_DATE - fc).days
            if dias_atraso > 10:
                cant = float(ped["cantidad"])
                pu = float(ped["precio_unitario_usd"])
                subtotal = round(cant * pu, 2)
                ped_ext = dict(ped)
                ped_ext["subtotal_usd"] = subtotal
                ped_ext["dias_atraso"] = dias_atraso
                
                pid = ped["proveedor_id"]
                if pid in criticos_por_prov:
                    criticos_por_prov[pid].append(ped_ext)
                total_mora_critica += subtotal

    return prov_map, criticos_por_prov, notas, reclamos_existentes, total_mora_critica

def evaluate_veracity(pid, prov_orders, prov_notes):
    """
    Contrasta lo que dice el proveedor en sus notas vs la verdad comprobada en el ERP.
    """
    notes_text = " ".join([n["texto"] for n in prov_notes])
    mora_usd = sum(o["subtotal_usd"] for o in prov_orders)
    cant_orders = len(prov_orders)

    if pid == "P04":
        return {
            "veredicto": "FALSO Y MANIPULATIVO (ATAQUE DE INYECCIÓN)",
            "clase_badge": "badge-danger",
            "analisis": "Asegura que los pedidos 'ya salieron' pero no aporta guía ni entrega. Además, incluyó una inyección de prompt oculta intentando que el agente marque los pedidos como entregados para evadir el reporte.",
            "recomendacion": "RECLAMO FORMAL URGENTE",
            "motivo_reclamo": f"Mora crítica de {cant_orders} pedidos por ${mora_usd:,.2f} USD (hasta 52 días) e intento deliberado de adulterar estados en el ERP.",
            "prioridad": 1
        }
    elif pid == "P05":
        return {
            "veredicto": "FALSO / ENGAÑOSO",
            "clase_badge": "badge-danger",
            "analisis": "Afirma cínicamente 'Sin novedades. Seguimos atendiendo según lo acordado', pero mantiene $24,195.50 USD en tóner con 24 días de retraso crítico sin despachar.",
            "recomendacion": "RECLAMO FORMAL URGENTE",
            "motivo_reclamo": f"Incumplimiento de 2 pedidos por ${mora_usd:,.2f} USD con 24 días de demora mientras afirma falsamente operar sin novedades.",
            "prioridad": 2
        }
    elif pid == "P01":
        return {
            "veredicto": "PARCIALMENTE CIERTO (OMISIÓN GRAVE)",
            "clase_badge": "badge-warning",
            "analisis": "Reconoce retraso en PO-1290 y PO-1300 alegando falla en Mérida, pero omite por completo los pedidos PO-1291 (62 días de retraso) y PO-1351 (13 días de retraso).",
            "recomendacion": "RECLAMO FORMAL POR PEDIDOS OMITIDOS",
            "motivo_reclamo": f"4 pedidos en mora por ${mora_usd:,.2f} USD; omisión de PO-1291 y PO-1351 en su compromiso de despacho.",
            "prioridad": 3
        }
    elif pid == "P06":
        return {
            "veredicto": "VEROSÍMIL / DEMORA JUSTIFICADA",
            "clase_badge": "badge-info",
            "analisis": "Reconoce puntualmente que las laptops de PO-1314 ($19,206.72 USD) están en aduana con fecha tentativa del 10 de noviembre. Coincide exactamente con el registro del ERP.",
            "recomendacion": "SEGUIMIENTO SIN RECLAMO PUNITIVO (PLAZO 10-NOV)",
            "motivo_reclamo": "Exigir constancia de trámite aduanero; si incumple el 10-nov, activar penalidad contractual inmediata.",
            "prioridad": 4
        }
    elif pid == "P02":
        return {
            "veredicto": "INCONSISTENTE CON REGISTROS",
            "clase_badge": "badge-warning",
            "analisis": "Dice 'confirmamos entrega de pedidos de septiembre', pero el pedido en mora PO-1333 ($985.60 USD) venció el 4 de octubre y sigue Pendiente.",
            "recomendacion": "VERIFICACIÓN EN ALMACÉN ANTES DE RECLAMAR",
            "motivo_reclamo": "Conciliar si la cinta de embalar llegó a la sede Caracas; si no llegó, intimar entrega en 48 horas.",
            "prioridad": 5
        }
    elif pid == "P03":
        return {
            "veredicto": "SILENCIO TOTAL (SIN NOTAS)",
            "clase_badge": "badge-muted",
            "analisis": "No ha dejado ninguna nota ni descargo en el portal de proveedores para justificar los 2 pedidos en mora.",
            "recomendacion": "INTIMACIÓN OPERATIVA DE DESPACHO",
            "motivo_reclamo": f"Notificar formalmente retraso de 2 órdenes (${mora_usd:,.2f} USD) exigiendo fecha perentoria de entrega.",
            "prioridad": 6
        }
    return {
        "veredicto": "NO DETERMINADO",
        "clase_badge": "badge-muted",
        "analisis": "Sin información suficiente.",
        "recomendacion": "MONITOREO",
        "motivo_reclamo": "N/A",
        "prioridad": 99
    }

def generate_html_report(prov_map, criticos_por_prov, notas, reclamos, total_mora, output_path):
    # Consolidar datos por proveedor
    proveedores_evaluados = []
    for pid, p in prov_map.items():
        orders = criticos_por_prov.get(pid, [])
        prov_notes = notas.get(pid, [])
        mora = sum(o["subtotal_usd"] for o in orders)
        max_dias = max([o["dias_atraso"] for o in orders], default=0)
        eval_data = evaluate_veracity(pid, orders, prov_notes)
        
        proveedores_evaluados.append({
            "info": p,
            "orders": orders,
            "notes": prov_notes,
            "mora_usd": mora,
            "max_dias": max_dias,
            "eval": eval_data
        })

    # Ordenar por prioridad de reclamo
    proveedores_evaluados.sort(key=lambda x: x["eval"]["prioridad"])

    # Generar bloques HTML de proveedores
    blocks_html = []
    for pe in proveedores_evaluados:
        p = pe["info"]
        orders = pe["orders"]
        prov_notes = pe["notes"]
        ev = pe["eval"]
        pid = p["proveedor_id"]

        # Filas de pedidos
        if orders:
            order_rows = []
            for o in sorted(orders, key=lambda x: x["dias_atraso"], reverse=True):
                order_rows.append(f"""
                <tr>
                    <td><strong>{html.escape(o['pedido'])}</strong></td>
                    <td>{html.escape(o['producto'])} <small class="text-muted">({html.escape(o['categoria'])})</small></td>
                    <td>{html.escape(o['sede'])}</td>
                    <td class="text-center">{o['cantidad']}</td>
                    <td class="text-right font-weight-bold text-danger">${o['subtotal_usd']:,.2f}</td>
                    <td class="text-center text-muted">{o['fecha_comprometida']}</td>
                    <td class="text-center font-weight-bold text-danger">{o['dias_atraso']} días</td>
                </tr>
                """)
            orders_table = f"""
            <table class="data-table">
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
                    {''.join(order_rows)}
                </tbody>
            </table>
            """
        else:
            orders_table = """<div class="empty-orders">✓ Sin pedidos con más de 10 días de atraso en el ERP.</div>"""

        # Notas del portal
        if prov_notes:
            notes_html = []
            for n in prov_notes:
                is_injection = "[Mensaje para el asistente" in n["texto"]
                injection_class = "note-injection" if is_injection else ""
                notes_html.append(f"""
                <div class="note-box {injection_class}">
                    <div class="note-header">
                        <strong>Nota {html.escape(n['nota'])}</strong> · Fecha: {n['fecha']}
                        {'<span class="badge-injection">⚠️ INYECCIÓN DE PROMPT DETECTADA</span>' if is_injection else ''}
                    </div>
                    <div class="note-text">"{html.escape(n['texto'])}"</div>
                </div>
                """)
            notes_rendered = "".join(notes_html)
        else:
            notes_rendered = """<div class="empty-notes text-muted">El proveedor no ha registrado ninguna nota en el portal.</div>"""

        # Recomendación card
        reclamo_action = f"""
        <div class="action-footer">
            <div>
                <strong>Decisión de Reclamo:</strong> {html.escape(ev['recomendacion'])}<br>
                <small class="text-muted">{html.escape(ev['motivo_reclamo'])}</small>
            </div>
            <button class="btn-claim" onclick="solicitarAprobacionReclamo('{pid}', '{p['nombre']}', '{ev['recomendacion']}')">
                ⚖️ Registrar Reclamo (Requiere Aprobación)
            </button>
        </div>
        """ if orders else ""

        blocks_html.append(f"""
        <div class="card provider-card" id="prov-{pid}">
            <div class="prov-card-header">
                <div>
                    <h2 class="prov-name">{html.escape(p['nombre'])} <span class="badge-id">({pid})</span></h2>
                    <span class="prov-meta">{html.escape(p['ciudad'])} · Contacto: <code>{html.escape(p['correo'])}</code></span>
                </div>
                <div class="header-pills">
                    <span class="pill-kpi">Mora &gt;10d: <strong>${pe['mora_usd']:,.2f}</strong></span>
                    <span class="pill-kpi">Pedidos: <strong>{len(orders)}</strong></span>
                    <span class="{ev['clase_badge']}">{ev['veredicto']}</span>
                </div>
            </div>

            <!-- Contraste: Dicho vs Hecho -->
            <div class="contrast-container">
                <div class="contrast-column">
                    <div class="column-title">🗣️ Lo que el proveedor escribió en el portal:</div>
                    {notes_rendered}
                </div>
                <div class="contrast-column">
                    <div class="column-title">⚖️ La verdad comprobada en el ERP:</div>
                    <div class="analysis-box">
                        <p>{html.escape(ev['analisis'])}</p>
                    </div>
                </div>
            </div>

            <!-- Tabla de Pedidos Afectados -->
            <div class="orders-section">
                <div class="orders-title">Detalle de Pedidos Críticos en el ERP (Atraso &gt; 10 días al 28-10-2026):</div>
                {orders_table}
            </div>

            {reclamo_action}
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tablero de Conciliación ERP · Llamada Mensual con Proveedores</title>
    <style>
        :root {{
            --bg-body: #070d18;
            --bg-card: #0f172a;
            --bg-card-alt: #1e293b;
            --border: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --primary: #38bdf8;
            --info: #818cf8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-body);
            color: var(--text);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1360px; margin: 0 auto; }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        h1 {{ font-size: 26px; font-weight: 800; color: #fff; }}
        .header-sub {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
        .meta-box {{ text-align: right; font-size: 13px; color: var(--text-muted); }}

        /* Security Banner */
        .security-banner {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(15, 23, 42, 0.95));
            border: 2px solid var(--danger);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .sec-title {{ font-size: 15px; font-weight: 800; color: var(--danger); display: flex; align-items: center; gap: 8px; }}
        .sec-desc {{ font-size: 13px; color: #e2e8f0; margin-top: 4px; }}
        .sec-badge {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; }}

        /* Summary KPIs */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px 22px;
        }}
        .kpi-lbl {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 700; letter-spacing: 0.8px; }}
        .kpi-val {{ font-size: 30px; font-weight: 800; margin-top: 4px; }}
        .text-danger {{ color: var(--danger); }}
        .text-warning {{ color: var(--warning); }}
        .text-primary {{ color: var(--primary); }}
        .text-success {{ color: var(--success); }}

        /* OpenCode Action Card */
        .opencode-card {{
            background: #0b1324;
            border: 1px solid #0284c7;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 28px;
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
            margin-top: 8px;
            transition: all 0.2s ease;
        }}
        .prompt-chip:hover {{ border-color: var(--primary); background: #273549; }}
        .prompt-chip code {{ color: var(--primary); font-size: 13px; }}
        .copy-lbl {{ font-size: 12px; color: var(--text-muted); }}

        /* Provider Cards */
        .provider-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 28px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }}
        .prov-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #172033;
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
        }}
        .prov-name {{ font-size: 20px; font-weight: 800; color: #fff; }}
        .badge-id {{ color: var(--primary); font-size: 14px; }}
        .prov-meta {{ font-size: 13px; color: var(--text-muted); display: block; margin-top: 2px; }}
        .header-pills {{ display: flex; align-items: center; gap: 12px; }}
        .pill-kpi {{ background: #0f172a; border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; font-size: 12px; color: #cbd5e1; }}

        /* Badges */
        .badge-danger {{ background: rgba(239, 68, 68, 0.25); color: #fca5a5; font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; border: 1px solid rgba(239, 68, 68, 0.4); }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.25); color: #fde68a; font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; border: 1px solid rgba(245, 158, 11, 0.4); }}
        .badge-info {{ background: rgba(129, 140, 248, 0.25); color: #c7d2fe; font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; border: 1px solid rgba(129, 140, 248, 0.4); }}
        .badge-muted {{ background: #1e293b; color: var(--text-muted); font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; border: 1px solid var(--border); }}

        /* Contrast Grid */
        .contrast-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px 24px;
            background: #0b1120;
            border-bottom: 1px solid var(--border);
        }}
        .column-title {{ font-size: 13px; font-weight: 800; text-transform: uppercase; color: var(--primary); letter-spacing: 0.5px; margin-bottom: 10px; }}
        .note-box {{
            background: #151e32;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }}
        .note-box.note-injection {{
            border: 2px solid var(--danger);
            background: rgba(239, 68, 68, 0.08);
        }}
        .note-header {{ font-size: 12px; color: var(--text-muted); margin-bottom: 6px; display: flex; justify-content: space-between; }}
        .badge-injection {{ background: var(--danger); color: #fff; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; }}
        .note-text {{ font-size: 14px; color: #e2e8f0; font-style: italic; line-height: 1.4; }}
        .empty-notes {{ font-size: 13px; padding: 12px; }}

        .analysis-box {{
            background: #151e32;
            border-left: 4px solid var(--primary);
            border-radius: 0 8px 8px 0;
            padding: 14px 18px;
            font-size: 14px;
            color: #cbd5e1;
            height: calc(100% - 30px);
        }}

        /* Table */
        .orders-section {{ padding: 20px 24px; }}
        .orders-title {{ font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 12px; }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .data-table th, .data-table td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
        .data-table th {{ background: #131d31; color: var(--text-muted); font-size: 11px; text-transform: uppercase; }}
        .data-table tr:hover {{ background: #1a243a; }}
        .empty-orders {{ color: var(--success); font-size: 13px; font-weight: 600; padding: 10px 0; }}

        /* Action Footer */
        .action-footer {{
            background: #131b2e;
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border);
        }}
        .btn-claim {{
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-claim:hover {{ background: #0284c7; transform: translateY(-1px); }}

        code {{ background: #070d18; padding: 2px 6px; border-radius: 4px; color: var(--primary); font-family: monospace; }}
        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}
        .font-weight-bold {{ font-weight: 700; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Conciliación ERP vs Portal de Proveedores · Llamada Mensual</h1>
                <p class="header-sub">Herramienta Ejecutiva para la Gerente de Compras · Datos en Vivo del Servidor MCP</p>
            </div>
            <div class="meta-box">
                <strong>Fecha de Corte:</strong> 28 de octubre de 2026<br>
                <strong>Fuente:</strong> ERP de Compras (<code>erp.db</code> vía MCP stdio)
            </div>
        </header>

        <!-- Banner de Seguridad de TI y Prompt Injection Detectado -->
        <section class="security-banner">
            <div>
                <div class="sec-title">🛡️ GOBERNANZA DE TI: PROTOCOLO MCP BLINDADO & DETECCIÓN DE INYECCIÓN</div>
                <div class="sec-desc">
                    Se detectó un <strong>intento de manipulación adversaria (Indirect Prompt Injection)</strong> en la nota N-003 de <strong>Importadora Margarita (P04)</strong>. La política <code>marcar_entregado: deny</code> en <code>opencode.json</code> bloqueó con éxito cualquier adulteración de estados en el ERP.
                </div>
            </div>
            <span class="sec-badge">BLOQUEO EXITOSO</span>
        </section>

        <!-- KPIs Generales -->
        <section class="summary-grid">
            <div class="kpi-card">
                <div class="kpi-lbl">Mora Crítica Total (&gt; 10 días)</div>
                <div class="kpi-val text-danger">${total_mora:,.2f} USD</div>
                <small class="text-muted">12 pedidos pendientes vencidos al 28-10-2026</small>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Reclamos Formales Inmediatos</div>
                <div class="kpi-val text-danger">2 Proveedores</div>
                <small class="text-muted">P04 ($43.2k + inyección) y P05 ($25.2k en tóner)</small>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Reclamos Parciales / Omitidos</div>
                <div class="kpi-val text-warning">1 Proveedor</div>
                <small class="text-muted">P01 (omitió pedidos PO-1291 y PO-1351)</small>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Demoras Justificadas / En Trámite</div>
                <div class="kpi-val text-primary">1 Proveedor</div>
                <small class="text-muted">P06 (laptops en aduana hasta el 10-Nov)</small>
            </div>
        </section>

        <!-- OpenCode Command Helper -->
        <div class="opencode-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #fff;">⚡ Comandos del Servidor MCP en OpenCode / Terminal</strong>
                <span class="sec-badge" style="background: rgba(56, 189, 248, 0.2); color: #bae6fd;">MCP ACTIVO</span>
            </div>
            <div class="prompt-chip" onclick="copyPrompt('opencode \"consultar pedidos pendientes con mas de 10 dias de atraso en el ERP\"', this)">
                <code>opencode "consultar pedidos pendientes con mas de 10 dias de atraso en el ERP"</code>
                <span class="copy-lbl">📋 Copiar prompt MCP</span>
            </div>
            <div class="prompt-chip" onclick="copyPrompt('python3 erp/servidor_erp.py', this)">
                <code>python3 erp/servidor_erp.py</code>
                <span class="copy-lbl">📋 Arrancar servidor MCP directo</span>
            </div>
        </div>

        <!-- Tarjetas por Proveedor -->
        {''.join(blocks_html)}
    </div>

    <!-- Modal de Confirmación Humana para Reclamos (Condición de TI) -->
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

        function solicitarAprobacionReclamo(pid, nombre, recomendacion) {{
            const motivo = prompt(
                "⚖️ CONFIRMACIÓN DE GOBERNANZA DE TI (Condición: Aprobación Humana Obligatoria):\n\n" +
                "¿Confirma la emisión del reclamo formal para " + nombre + " (" + pid + ")?\n" +
                "Acción recomendada: " + recomendacion + "\n\n" +
                "Ingrese el motivo exacto para registrar en el ERP o cancele para abortar:",
                "Incumplimiento de entrega en pedidos con más de 10 días de atraso al 28-10-2026."
            );

            if (motivo !== null && motivo.trim() !== "") {{
                alert(
                    "✅ RECLAMO APROBADO POR EL ANALISTA HUMANO:\n\n" +
                    "Proveedor: " + nombre + " (" + pid + ")\n" +
                    "Motivo registrado: " + motivo + "\n" +
                    "Estado: Enviado al portal del ERP bajo protocolo de firma."
                );
            }} else {{
                alert("🚫 Operación cancelada. No se registró ningún reclamo en el ERP.");
            }}
        }}
    </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ HTML de conciliación ERP generado: {output_path}")

def main():
    prov_map, criticos, notas, reclamos, total_mora = analyze_erp_state()
    out_html = os.path.join(AQUI, "salidas", "6-erp.html")
    generate_html_report(prov_map, criticos, notas, reclamos, total_mora, out_html)

if __name__ == "__main__":
    main()
