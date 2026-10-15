#!/usr/bin/env python3
"""
Portal Maestro Unificado — Workshop Agentes de Código en el Trabajo
Integra de forma organizada los 5 problemas en una única interfaz ejecutiva:
- Tab 1: 🏢 Tablero de Dirección General (Problema 5 - Kraljic, Pareto, KPIs)
- Tab 2: 🤝 Reunión con Proveedores (Problema 1 - Criterio de Falla, P04)
- Tab 3: 📅 Operación Semanal de los Lunes (Problema 2 - Atrasos >10d y Borradores)
- Tab 4: 🛡️ Auditoría de Seguridad TI (Problema 3 - Red-Teaming, Permisos OS)
- Tab 5: ⚖️ Calidad de Datos Finanzas (Problema 4 - Cuarentena 7 filas, 5 Reglas)
Incluye una Barra de Consulta Ejecutiva interactiva respaldada por Qwen 30B en Spark.
"""

import html
import os
import re

def build_master_index(salidas_dir, output_path):
    # Leer contenidos generados previamente
    def read_body(filepath):
        if not os.path.exists(filepath):
            return f"<p class='text-muted'>Entregable no encontrado en {filepath}</p>"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            m = re.search(r'<div class="container">(.*?)</div>\s*</body>', content, re.DOTALL)
            if m:
                return m.group(1).strip()
            b = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
            if b:
                return b.group(1).strip()
            return content

    body_p5 = read_body(os.path.join(salidas_dir, "5-tablero-gerente.html"))
    body_p1 = read_body(os.path.join(salidas_dir, "1-reunion-proveedores.html"))
    body_p2 = read_body(os.path.join(salidas_dir, "2-lunes", "estado-pedidos-jefe.html"))
    body_p3 = read_body(os.path.join(salidas_dir, "3-auditoria.html"))
    body_p4 = read_body(os.path.join(salidas_dir, "4-calidad-datos.html"))

    master_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal Ejecutivo Unificado · Cadena de Suministro y Gobernanza de Agentes</title>
    <style>
        :root {{
            --bg-body: #050811;
            --bg-nav: #0d1527;
            --bg-card: #111c33;
            --border: #233454;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --purple: #c084fc;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-body);
            color: var(--text);
            padding: 0;
            line-height: 1.5;
        }}
        
        /* Top Navigation Header */
        .top-navbar {{
            background: var(--bg-nav);
            border-bottom: 2px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
        }}
        .nav-inner {{
            max-width: 1440px;
            margin: 0 auto;
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .brand-logo {{
            background: linear-gradient(135deg, var(--primary), #6366f1);
            color: #fff;
            font-weight: 900;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 16px;
        }}
        .brand-text h1 {{ font-size: 18px; font-weight: 800; color: #fff; }}
        .brand-text p {{ font-size: 12px; color: var(--text-muted); }}

        /* Tabs Menu */
        .tabs-menu {{
            display: flex;
            gap: 8px;
            background: #080d1a;
            padding: 4px;
            border-radius: 8px;
            border: 1px solid var(--border);
            flex-wrap: wrap;
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .tab-btn:hover {{ color: #fff; background: rgba(255, 255, 255, 0.05); }}
        .tab-btn.active {{
            background: var(--primary);
            color: #050811;
            font-weight: 800;
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.4);
        }}

        /* Executive Query Assistant Bar */
        .assistant-section {{
            background: linear-gradient(180deg, #0d172e 0%, #080d1a 100%);
            border-bottom: 1px solid var(--border);
            padding: 16px 24px;
        }}
        .assistant-inner {{
            max-width: 1440px;
            margin: 0 auto;
        }}
        .assistant-bar {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        .query-input-wrapper {{
            flex: 1;
            position: relative;
        }}
        .query-input {{
            width: 100%;
            padding: 12px 18px;
            background: #050811;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .query-input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
        }}
        .query-btn {{
            background: linear-gradient(135deg, var(--primary), #2563eb);
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .query-btn:hover:not(:disabled) {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        .query-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .chips-row {{
            display: flex;
            gap: 8px;
            margin-top: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .chips-label {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .chip {{
            background: #111c33;
            border: 1px solid var(--border);
            color: var(--primary);
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .chip:hover {{
            background: rgba(56, 189, 248, 0.15);
            border-color: var(--primary);
        }}
        .status-badge {{
            font-size: 11px;
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 6px;
            margin-left: auto;
        }}
        .status-badge.safe {{
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        .status-badge.warning {{
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .status-badge.danger {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }}

        /* Assistant Response Card */
        .assistant-response-box {{
            display: none;
            margin-top: 14px;
            background: #090e1c;
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 16px 20px;
            animation: fadeIn 0.3s ease;
        }}
        .assistant-response-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
        }}
        .assistant-response-text {{
            font-size: 14px;
            color: #e2e8f0;
            line-height: 1.6;
            white-space: pre-wrap;
        }}

        /* Content Area */
        .content-area {{
            max-width: 1440px;
            margin: 0 auto;
            padding: 24px;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; animation: fadeIn 0.3s ease; }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Shared Dashboard CSS */
        .card, .kpi-card, .metric-card, .section-box, .provider-block, .exigencia-card {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 12px; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #0c1424; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; }}
        tr:hover {{ background: rgba(255, 255, 255, 0.03); }}
        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}
        .font-weight-bold {{ font-weight: 700; }}
        .text-danger {{ color: var(--danger); }}
        .text-warning {{ color: var(--warning); }}
        .text-success {{ color: var(--success); }}
        .text-primary {{ color: var(--primary); }}
        .text-muted {{ color: var(--text-muted); }}

        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: #fde68a; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; }}
        .badge-success {{ background: rgba(16, 185, 129, 0.2); color: #a7f3d0; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; }}
        .badge-primary {{ background: rgba(56, 189, 248, 0.2); color: #bae6fd; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; }}
        code {{ background: #060a14; padding: 2px 6px; border-radius: 4px; color: var(--primary); font-family: monospace; }}
    </style>
</head>
<body>
    <!-- Top Navigation Bar -->
    <nav class="top-navbar">
        <div class="nav-inner">
            <div class="brand">
                <span class="brand-logo">DGX SPARK</span>
                <div class="brand-text">
                    <h1>Portal Ejecutivo de Cadena de Suministro</h1>
                    <p>Tablero Centralizado Multi-Rol · Workshop Agentes de Código (Soutec · UCAB)</p>
                </div>
            </div>
            <div class="tabs-menu">
                <button class="tab-btn active" onclick="switchTab('tab-p5', this)">🏢 Dirección General</button>
                <button class="tab-btn" onclick="switchTab('tab-p1', this)">🤝 Reunión Proveedores</button>
                <button class="tab-btn" onclick="switchTab('tab-p2', this)">📅 Informe de los Lunes</button>
                <button class="tab-btn" onclick="switchTab('tab-p3', this)">🛡️ Auditoría de TI</button>
                <button class="tab-btn" onclick="switchTab('tab-p4', this)">⚖️ Calidad Finanzas</button>
            </div>
        </div>
    </nav>

    <!-- Executive Query Assistant Bar -->
    <section class="assistant-section">
        <div class="assistant-inner">
            <div class="assistant-bar">
                <div class="query-input-wrapper">
                    <input type="text" id="userQuery" class="query-input" placeholder="Pregunta ejecutiva al modelo (ej. '¿Quién es el peor proveedor?', '¿Qué anomalías hay en cuarentena?')..." onkeydown="if(event.key==='Enter') executeQuery();" />
                </div>
                <button id="btnQuery" class="query-btn" onclick="executeQuery()">Consultar Modelo</button>
            </div>
            <div class="chips-row">
                <span class="chips-label">Consultas Rápidas:</span>
                <span class="chip" onclick="setQuery('¿Quién es el peor proveedor y por qué abrir la reunión con él?')">🎯 Peor proveedor (P04)</span>
                <span class="chip" onclick="setQuery('¿Cuáles son las 7 anomalías de datos puestas en cuarentena?')">⚖️ 7 Anomalías Cuarentena</span>
                <span class="chip" onclick="setQuery('¿Qué pedidos tienen más de 10 días de atraso en el informe de los lunes?')">📅 Mora > 10d (Lunes)</span>
                <span class="chip" onclick="setQuery('¿Cómo quedó la clasificación de proveedores en la Matriz de Kraljic?')">📊 Matriz de Kraljic</span>
                <span class="chip" onclick="setQuery('¿Qué reveló el Red-Teaming de seguridad de TI?')">🛡️ Red-Teaming TI</span>
                <span id="strikeBadge" class="status-badge safe">🛡️ 3 intentos restantes</span>
            </div>
            <div id="responseBox" class="assistant-response-box">
                <div class="assistant-response-header">
                    <span id="responseStatus">🤖 RESPUESTA EJECUTIVA (QWEN 30B / SPARK)</span>
                    <span id="responseTimer"></span>
                </div>
                <div id="responseText" class="assistant-response-text"></div>
            </div>
        </div>
    </section>

    <!-- Contenido Dinámico Organizado -->
    <main class="content-area">
        <!-- Tab 1: Dirección General (Problema 5) -->
        <div id="tab-p5" class="tab-content active">
            {body_p5}
        </div>

        <!-- Tab 2: Reunión con Proveedores (Problema 1) -->
        <div id="tab-p1" class="tab-content">
            {body_p1}
        </div>

        <!-- Tab 3: Operación de los Lunes (Problema 2) -->
        <div id="tab-p2" class="tab-content">
            {body_p2}
        </div>

        <!-- Tab 4: Auditoría de TI (Problema 3) -->
        <div id="tab-p3" class="tab-content">
            {body_p3}
        </div>

        <!-- Tab 5: Calidad de Finanzas (Problema 4) -->
        <div id="tab-p4" class="tab-content">
            {body_p4}
        </div>
    </main>

    <script>
        function switchTab(tabId, btn) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function setQuery(text) {{
            const input = document.getElementById('userQuery');
            input.value = text;
            input.focus();
        }}

        let sessionId = localStorage.getItem('lab3_session_id');
        if (!sessionId) {{
            sessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
            localStorage.setItem('lab3_session_id', sessionId);
        }}

        async function executeQuery() {{
            const input = document.getElementById('userQuery');
            const btn = document.getElementById('btnQuery');
            const box = document.getElementById('responseBox');
            const textEl = document.getElementById('responseText');
            const badge = document.getElementById('strikeBadge');
            const timer = document.getElementById('responseTimer');
            const query = input.value.trim();

            if (!query) return;

            btn.disabled = true;
            btn.innerText = "Consultando...";
            box.style.display = "block";
            box.style.borderLeftColor = "var(--primary)";
            textEl.innerText = "Procesando inferencia ejecutiva contra el modelo en DGX Spark...";
            const startTime = performance.now();

            try {{
                const res = await fetch('/api/consulta', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ pregunta: query, session_id: sessionId }})
                }});

                const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
                timer.innerText = elapsed + "s";

                if (res.ok) {{
                    const data = await res.json();
                    textEl.innerText = data.respuesta;
                    
                    if (data.bloqueado) {{
                        badge.className = "status-badge danger";
                        badge.innerText = "🚫 SESIÓN BLOQUEADA";
                        box.style.borderLeftColor = "var(--danger)";
                        input.disabled = true;
                        input.placeholder = "Sesión bloqueada por superar intentos inválidos.";
                        btn.innerText = "Bloqueado";
                        return;
                    }} else if (data.intentos_restantes < 3) {{
                        badge.className = "status-badge warning";
                        badge.innerText = "⚠️ " + data.intentos_restantes + " intentos restantes";
                    }} else {{
                        badge.className = "status-badge safe";
                        badge.innerText = "🛡️ " + data.intentos_restantes + " intentos restantes";
                    }}
                }} else {{
                    textEl.innerText = "Aviso: El endpoint de consulta (/api/consulta) no está activo en este puerto estático. Para consultar al modelo, asegúrese de iniciar 'python3 scripts/servidor_asistente.py' en Spark.";
                }}
            }} catch (err) {{
                textEl.innerText = "Error de conexión con el backend de inferencia local. Asegúrese de que 'servidor_asistente.py' está corriendo en la máquina.";
            }} finally {{
                if (!input.disabled) {{
                    btn.disabled = false;
                    btn.innerText = "Consultar Modelo";
                }}
            }}
        }}
    </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(master_html)
    print(f"✅ Portal unificado con barra ejecutiva generado en: {output_path}")

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    salidas_dir = os.path.join(base, "salidas")
    out_index = os.path.join(salidas_dir, "index.html")
    build_master_index(salidas_dir, out_index)

if __name__ == "__main__":
    main()
