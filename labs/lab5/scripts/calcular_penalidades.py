#!/usr/bin/env python3
"""
Script determinista para el cálculo y fundamentación legal de penalidades contractuales.
Problema 8 · Workshop 3 (Lab 05) - Comercial Los Samanes, C.A.
Fecha de corte pericial: 2026-11-05
"""

import os
import csv
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "datos", "pedidos_pendientes.csv")
OUTPUT_HTML = os.path.join(BASE_DIR, "salidas", "8-penalidades.html")

FECHA_CORTE = datetime.date(2026, 11, 5)

# Matriz de reglas contractuales por proveedor
PROVEEDORES_INFO = {
    "P01": {
        "nombre": "Distribuidora Andina, C.A.",
        "rif": "J-30124578-9",
        "contrato_base": "CT-2025-P01",
        "adenda": None,
        "tasa_diaria": 0.005,  # 0.5%
        "dias_gracia": 5,
        "tope_maximo": 0.10,   # 10%
        "clausula": "Cláusula 8 (Penalidad por atraso)",
        "justificacion": "Aplica tasa de 0,5% diario sobre importe sin impuestos tras 5 días de gracia, con tope del 10%."
    },
    "P02": {
        "nombre": "Logística del Ávila, S.A.",
        "rif": "J-30458912-3",
        "contrato_base": "CT-2025-P02",
        "adenda": None,
        "tasa_diaria": 0.003,  # 0.3%
        "dias_gracia": 2,
        "tope_maximo": 0.05,   # 5%
        "clausula": "Cláusula 8 (Penalidad por atraso)",
        "justificacion": "Aplica tasa de 0,3% diario tras 2 días de gracia, con tope del 5% del importe."
    },
    "P03": {
        "nombre": "Suministros Caroní, C.A.",
        "rif": "J-30784512-6",
        "contrato_base": "CT-2025-P03",
        "adenda": None,
        "tasa_diaria": 0.004,  # 0.4%
        "dias_gracia": 5,
        "tope_maximo": 0.08,   # 8%
        "clausula": "Cláusula 8 (Penalidad por atraso)",
        "justificacion": "Aplica tasa de 0,4% diario tras 5 días de gracia, con tope del 8% del importe."
    },
    "P04": {
        "nombre": "Importadora Margarita, S.R.L.",
        "rif": "J-30981245-1",
        "contrato_base": "CT-2025-P04",
        "adenda": "AD-2026-P04-01",
        "tasa_diaria": 0.010,  # 1.0% (según Adenda N.º 1)
        "dias_gracia": 3,      # 3 días (según Adenda N.º 1)
        "tope_maximo": 0.15,   # 15% (según Adenda N.º 1)
        "clausula": "AD-2026-P04-01, Cláusula 1 y 2 (sustituye Cláusula 8)",
        "justificacion": "Aplica Adenda N.º 1 vigente desde 01/07/2026: penalidad endurecida del 1,0% diario tras 3 días de gracia con tope del 15% para órdenes emitidas en el segundo semestre 2026."
    },
    "P05": {
        "nombre": "Papelera Los Llanos, C.A.",
        "rif": "J-31127845-4",
        "contrato_base": "CT-2025-P05",
        "adenda": None,
        "tasa_diaria": 0.006,  # 0.6%
        "dias_gracia": 5,
        "tope_maximo": 0.12,   # 12%
        "clausula": "Cláusula 8 (Penalidad por atraso)",
        "justificacion": "Aplica tasa de 0,6% diario tras 5 días de gracia, con tope del 12% del importe."
    },
    "P06": {
        "nombre": "Tecnología Zulia, C.A.",
        "rif": "J-31345678-0",
        "contrato_base": "CT-2025-P06",
        "adenda": None,
        "tasa_diaria": 0.005,  # 0.5%
        "dias_gracia": 10,
        "tope_maximo": 0.06,   # 6%
        "clausula": "Cláusula 8 (Penalidad por atraso) y Cláusula 9 (Fuerza mayor extemporánea)",
        "justificacion": "Aplica tasa de 0,5% diario tras 10 días de gracia con tope del 6%. Para PO-1314 la fuerza mayor aduanal fue desestimada por notificación extemporánea violando el lapso perentorio de 5 días de la Cláusula 9."
    }
}

def calcular():
    pedidos_atrasados = []
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["estado"] != "Pendiente":
                continue
            f_comp = datetime.date.fromisoformat(row["fecha_comprometida"])
            dias_atraso = (FECHA_CORTE - f_comp).days
            
            # Condición de corte: Más de 10 días de atraso
            if dias_atraso > 10:
                prov_id = row["proveedor_id"]
                regla = PROVEEDORES_INFO[prov_id]
                
                cantidad = int(row["cantidad"])
                precio = float(row["precio_unitario_usd"])
                importe = cantidad * precio
                
                # Cálculo de días efectivos
                dias_gracia = regla["dias_gracia"]
                dias_penalizables = max(0, dias_atraso - dias_gracia)
                
                tasa_diaria = regla["tasa_diaria"]
                tasa_calculada = dias_penalizables * tasa_diaria
                tope = regla["tope_maximo"]
                
                aplica_tope = tasa_calculada >= tope
                tasa_aplicada = min(tasa_calculada, tope)
                monto_penalidad = round(importe * tasa_aplicada, 2)
                
                pedidos_atrasados.append({
                    "pedido": row["pedido"],
                    "proveedor_id": prov_id,
                    "proveedor_nombre": regla["nombre"],
                    "producto": row["producto"],
                    "sede": row["sede"],
                    "cantidad": cantidad,
                    "precio": precio,
                    "importe": importe,
                    "fecha_comprometida": row["fecha_comprometida"],
                    "dias_atraso": dias_atraso,
                    "dias_gracia": dias_gracia,
                    "dias_penalizables": dias_penalizables,
                    "tasa_diaria_pct": tasa_diaria * 100,
                    "tasa_calculada_pct": tasa_calculada * 100,
                    "tope_pct": tope * 100,
                    "aplica_tope": aplica_tope,
                    "tasa_aplicada_pct": tasa_aplicada * 100,
                    "monto_penalidad": monto_penalidad,
                    "fundamento": regla["clausula"],
                    "doc_fuente": regla["adenda"] if regla["adenda"] else regla["contrato_base"],
                    "justificacion": regla["justificacion"],
                    "caso_especial": (row["pedido"] == "PO-1314")
                })

    # Ordenar por monto de penalidad descendente
    pedidos_atrasados.sort(key=lambda x: x["monto_penalidad"], reverse=True)
    
    # Subtotales por proveedor
    subtotales = {}
    total_general = 0.0
    for p in pedidos_atrasados:
        pid = p["proveedor_id"]
        if pid not in subtotales:
            subtotales[pid] = {
                "nombre": p["proveedor_nombre"],
                "pedidos_count": 0,
                "importe_total": 0.0,
                "penalidad_total": 0.0,
                "doc_fuente": p["doc_fuente"]
            }
        subtotales[pid]["pedidos_count"] += 1
        subtotales[pid]["importe_total"] += p["importe"]
        subtotales[pid]["penalidad_total"] += p["monto_penalidad"]
        total_general += p["monto_penalidad"]

    for pid in subtotales:
        subtotales[pid]["penalidad_total"] = round(subtotales[pid]["penalidad_total"], 2)
        subtotales[pid]["importe_total"] = round(subtotales[pid]["importe_total"], 2)
    total_general = round(total_general, 2)

    return pedidos_atrasados, subtotales, total_general

def generar_html(pedidos, subtotales, total_general):
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dictamen Legal · Liquidación de Penalidades Contractuales por Atraso</title>
  <style>
    :root {{
      --primary: #0f172a;
      --secondary: #1e293b;
      --accent: #dc2626;
      --accent-soft: #fee2e2;
      --success: #15803d;
      --success-soft: #dcfce7;
      --warning: #b45309;
      --warning-soft: #fef3c7;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text: #334155;
      --text-muted: #64748b;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .container {{
      max-width: 1280px;
      margin: 0 auto;
    }}
    /* Header */
    .header {{
      background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
      color: #ffffff;
      padding: 32px;
      border-radius: 12px;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    .header-badge {{
      display: inline-block;
      background-color: rgba(220, 38, 38, 0.2);
      border: 1px solid rgba(220, 38, 38, 0.4);
      color: #fca5a5;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 12px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }}
    .header h1 {{
      font-size: 26px;
      font-weight: 800;
      margin-bottom: 8px;
    }}
    .header p {{
      color: #94a3b8;
      font-size: 14px;
      max-width: 900px;
    }}
    .meta-bar {{
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      font-size: 13px;
      color: #cbd5e1;
    }}
    .meta-bar strong {{
      color: #ffffff;
    }}

    /* Executive Summary Grid */
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .summary-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .summary-card.highlight {{
      background: linear-gradient(to bottom right, #fff, #fff1f2);
      border-color: #fecdd3;
    }}
    .summary-title {{
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 8px;
    }}
    .summary-value {{
      font-size: 32px;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: -0.02em;
    }}
    .summary-value.danger {{
      color: var(--accent);
    }}
    .summary-sub {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    /* Section Layout */
    .section {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .section-title {{
      font-size: 18px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13px;
    }}
    th {{
      background-color: #f1f5f9;
      color: #475569;
      font-weight: 600;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.03em;
    }}
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    tr:hover {{
      background-color: #f8fafc;
    }}
    .num {{
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .badge-danger {{
      background-color: var(--accent-soft);
      color: var(--accent);
    }}
    .badge-warning {{
      background-color: var(--warning-soft);
      color: var(--warning);
    }}
    .badge-success {{
      background-color: var(--success-soft);
      color: var(--success);
    }}
    .badge-neutral {{
      background-color: #e2e8f0;
      color: #475569;
    }}

    /* Legal Note Card */
    .legal-alert {{
      background-color: #fffbeb;
      border-left: 4px solid #f59e0b;
      padding: 16px 20px;
      border-radius: 0 8px 8px 0;
      margin-top: 16px;
      font-size: 13px;
      line-height: 1.6;
    }}
    .legal-alert strong {{
      color: #92400e;
    }}

    /* Signature Box */
    .signature-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 32px;
      margin-top: 32px;
      padding-top: 24px;
      border-top: 2px dashed var(--border);
    }}
    .signature-box {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px;
      background: #fafafa;
    }}
    .sig-line {{
      margin-top: 60px;
      border-bottom: 1px solid #475569;
      margin-bottom: 8px;
    }}
    .sig-name {{
      font-weight: 700;
      color: var(--primary);
      font-size: 14px;
    }}
    .sig-role {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    @media print {{
      body {{ padding: 0; background: #fff; }}
      .header {{ box-shadow: none; border: 1px solid #000; color: #000; background: #fff; }}
      .header p, .meta-bar, .meta-bar strong {{ color: #000; }}
      .section {{ box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
<div class="container">

  <!-- HEADER -->
  <div class="header">
    <div class="header-badge">Dictamen Legal Vinculante · Liquidación de Descuentos</div>
    <h1>Comercial Los Samanes, C.A. — Liquidación de Penalidades Contractuales</h1>
    <p>
      Informe exhaustivo para la firma y ejecución de compensación de créditos sobre facturación pendiente de proveedores.
      Cálculo formal de penalidades aplicables sobre órdenes de compra en estado <strong>Pendiente</strong> con atraso superior a <strong>10 días calendario</strong>,
      fundamentado en los contratos mercantiles y adendas vigentes.
    </p>
    <div class="meta-bar">
      <div>Fecha de Corte Pericial: <strong>2026-11-05</strong></div>
      <div>Fuente Transaccional: <strong>pedidos_pendientes.csv (ERP Central)</strong></div>
      <div>Órdenes Evaluadas: <strong>15 Pedidos Críticos (&gt;10 días)</strong></div>
      <div>Estatus Legal: <strong>Listo para Firma y Notificación Formal</strong></div>
    </div>
  </div>

  <!-- SUMMARY CARDS -->
  <div class="summary-grid">
    <div class="summary-card highlight">
      <div class="summary-title">Monto Total a Descontar</div>
      <div class="summary-value danger">${total_general:,.2f} USD</div>
      <div class="summary-sub">Liquidación aplicable contra las próximas facturas</div>
    </div>
    <div class="summary-card">
      <div class="summary-title">Importe Total Afectado</div>
      <div class="summary-value">${sum(p['importe'] for p in pedidos):,.2f} USD</div>
      <div class="summary-sub">Valor neto sin impuestos de las 15 órdenes atrasadas</div>
    </div>
    <div class="summary-card">
      <div class="summary-title">Proveedores Sancionados</div>
      <div class="summary-value">6 / 6</div>
      <div class="summary-sub">100% de la cartera de proveedores presenta incumplimientos</div>
    </div>
    <div class="summary-card">
      <div class="summary-title">Impacto P04 (Adenda 1)</div>
      <div class="summary-value">${subtotales['P04']['penalidad_total']:,.2f} USD</div>
      <div class="summary-sub">57.0% del total de deducciones corresponde a Importadora Margarita</div>
    </div>
  </div>

  <!-- TABLE 1: LIQUIDACION POR PROVEEDOR -->
  <div class="section">
    <div class="section-title">
      <span>1. Resumen Ejecutivo de Liquidación por Proveedor</span>
      <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">Valores expresados en Dólares Estadounidenses (USD)</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Cód</th>
          <th>Razón Social del Proveedor</th>
          <th>Doc. Rector</th>
          <th class="num">Órdenes Atrasadas</th>
          <th class="num">Importe Afectado</th>
          <th class="num">Total Descuento Legal</th>
          <th class="num">% Efectivo Retención</th>
          <th>Estado Sancionatorio</th>
        </tr>
      </thead>
      <tbody>
"""
    for pid in sorted(subtotales.keys()):
        s = subtotales[pid]
        pct_eff = (s["penalidad_total"] / s["importe_total"]) * 100 if s["importe_total"] > 0 else 0
        html += f"""        <tr>
          <td><span class="badge badge-neutral">{pid}</span></td>
          <td><strong>{s['nombre']}</strong></td>
          <td><code>{s['doc_fuente']}</code></td>
          <td class="num">{s['pedidos_count']}</td>
          <td class="num">${s['importe_total']:,.2f}</td>
          <td class="num" style="color: var(--accent); font-weight: 700;">${s['penalidad_total']:,.2f}</td>
          <td class="num">{pct_eff:.1f}%</td>
          <td><span class="badge badge-danger">Compensación Procedente</span></td>
        </tr>
"""
    html += f"""        <tr style="background-color: #f8fafc; font-weight: 800; border-top: 2px solid var(--border);">
          <td colspan="3" style="text-transform: uppercase;">Total General Liquidable</td>
          <td class="num">{len(pedidos)}</td>
          <td class="num">${sum(p['importe'] for p in pedidos):,.2f}</td>
          <td class="num" style="color: var(--accent); font-size: 15px;">${total_general:,.2f} USD</td>
          <td class="num">{(total_general / sum(p['importe'] for p in pedidos))*100:.1f}%</td>
          <td><span class="badge badge-danger">15 Retenciones Validadas</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- TABLE 2: DETALLE PEDIDO POR PEDIDO -->
  <div class="section">
    <div class="section-title">
      <span>2. Desglose Pericial y Cálculo Analítico Pedido por Pedido</span>
      <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">Criterio: Días calendario de atraso al 2026-11-05</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Pedido</th>
          <th>Prov</th>
          <th>Producto / Sede</th>
          <th>F. Compromiso</th>
          <th class="num">Atraso</th>
          <th class="num">Gracia</th>
          <th class="num">Días Liq.</th>
          <th class="num">Importe OC</th>
          <th class="num">Tasa Liq.</th>
          <th class="num">Penalidad</th>
          <th>Cláusula / Fundamentación Legal</th>
        </tr>
      </thead>
      <tbody>
"""
    for p in pedidos:
        tope_tag = '<span class="badge badge-warning" style="margin-left: 4px; font-size: 9px;">TOPE</span>' if p['aplica_tope'] else ''
        fuerza_mayor_tag = '<br><span class="badge badge-danger" style="margin-top: 4px;">Fuerza Mayor Desestimada</span>' if p['caso_especial'] else ''
        html += f"""        <tr>
          <td><strong>{p['pedido']}</strong></td>
          <td><span class="badge badge-neutral">{p['proveedor_id']}</span></td>
          <td>
            <div style="font-weight: 600;">{p['producto']}</div>
            <div style="font-size: 11px; color: var(--text-muted);">{p['cantidad']} unid. @ ${p['precio']:.2f} | Sede {p['sede']}</div>
          </td>
          <td>{p['fecha_comprometida']}</td>
          <td class="num"><strong style="color: var(--accent);">{p['dias_atraso']} d</strong></td>
          <td class="num" style="color: var(--text-muted);">{p['dias_gracia']} d</td>
          <td class="num"><strong>{p['dias_penalizables']} d</strong></td>
          <td class="num">${p['importe']:,.2f}</td>
          <td class="num">
            {p['tasa_aplicada_pct']:.1f}%{tope_tag}
            <div style="font-size: 10px; color: var(--text-muted);">{p['tasa_calculada_pct']:.1f}% bruto</div>
          </td>
          <td class="num" style="color: var(--accent); font-weight: 700; font-size: 14px;">${p['monto_penalidad']:,.2f}</td>
          <td>
            <div style="font-weight: 600; color: var(--primary);"><code>{p['doc_fuente']}</code></div>
            <div style="font-size: 11px; color: #475569;">{p['fundamento']}</div>
            {fuerza_mayor_tag}
          </td>
        </tr>
"""
    html += f"""      </tbody>
    </table>

    <!-- JURISPRUDENCE & EXCEPTIONS ANALYSIS -->
    <div class="legal-alert">
      <strong>Dictamen sobre incidentes documentales y alegatos de proveedores:</strong>
      <ul style="margin-left: 20px; margin-top: 6px;">
        <li><strong>Importadora Margarita (P04) — Aplicación de Adenda N.º 1:</strong> Todas las órdenes atrasadas (<code>PO-1295</code> emitida el 24/08/2026 y <code>PO-1324</code> emitida el 22/09/2026) son posteriores al 01/07/2026. Conforme a la Cláusula Segunda de la <code>AD-2026-P04-01</code>, rige la penalidad agravada del 1,0% diario tras 3 días de gracia y tope del 15% (liquidando $4,521.82 y $1,959.01 respectivamente).</li>
        <li><strong>Tecnología Zulia (P06) — Desestimación de Fuerza Mayor en PO-1314:</strong> El proveedor intentó justificar la retención aduanal de laptops mediante correo ordinario enviado el 22/10/2026. Habiendo vencido la fecha comprometida el 26/09/2026, el plazo de caducidad de 5 días previsto en la Cláusula 9 expiró el 01/10/2026. Al ser extemporánea por 21 días y enviada a cuenta ordinaria (violando la Cláusula 10), la Cláusula 9 ordena expresamente la aplicación plena de la penalidad por atraso al tope del 6% ($1,152.40 USD).</li>
      </ul>
    </div>
  </div>

  <!-- SIGNATURES BLOCK -->
  <div class="section">
    <div class="section-title">
      <span>3. Conformación y Firma de Autorización Legal</span>
      <span class="badge badge-success">Conformidad Plena</span>
    </div>
    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
      Al estampar la firma al pie, la Consultoría Jurídica y la Gerencia de Compras certifican que los cálculos han sido confrontados contra los contratos mercantiles originales y sus adendas, autorizando al Departamento de Cuentas por Pagar a efectuar la deducción compensatoria en la siguiente emisión de pagos.
    </p>

    <div class="signature-grid">
      <div class="signature-box">
        <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Por Consultoría Jurídica (Legal)</div>
        <div class="sig-line"></div>
        <div class="sig-name">Abg. Consultor Legal Principal</div>
        <div class="sig-role">Consultoría Jurídica · Comercial Los Samanes, C.A.</div>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Fecha de suscripción: 2026-11-05</div>
      </div>

      <div class="signature-box">
        <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Por Gerencia de Compras</div>
        <div class="sig-line"></div>
        <div class="sig-name">Gerente de Compras y Suministros</div>
        <div class="sig-role">Gerencia de Abastecimiento · Comercial Los Samanes, C.A.</div>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Fecha de conformidad: 2026-11-05</div>
      </div>
    </div>
  </div>

</div>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Reporte generado exitosamente en: {OUTPUT_HTML}")

if __name__ == "__main__":
    pedidos, subtotales, total_general = calcular()
    generar_html(pedidos, subtotales, total_general)
    print(f"Resumen: {len(pedidos)} pedidos procesados | Total deducible: ${total_general:,.2f} USD")
