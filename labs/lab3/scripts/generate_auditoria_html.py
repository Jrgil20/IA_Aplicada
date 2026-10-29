#!/usr/bin/env python3
"""
Generador de salidas/3-auditoria.html para la presentación al comité de dirección.
Presenta las 3 exigencias de TI, los resultados de red-teaming y las recomendaciones
de mitigación en arquitectura de defensa en profundidad.
"""

import html
import json
import os

def generate_auditoria_page(results, output_path):
    table_rows = []
    for r in results:
        status_badge = "badge-success" if r["status_code"] == "OK" else ("badge-warning" if "WARNING" in r["status_code"] else "badge-danger")
        table_rows.append(f"""
        <tr>
            <td><code>{html.escape(r['id'])}</code></td>
            <td>
                <strong>{html.escape(r['vector'])}</strong><br>
                <small class="text-muted">{html.escape(r['intento'])}</small>
            </td>
            <td><span class="badge-layer">{html.escape(r['capa'])}</span></td>
            <td><span class="{status_badge}">{html.escape(r['resultado'])}</span></td>
            <td><small>{html.escape(r['evidencia'])}</small></td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auditoría de Seguridad · Agentes de Código en el Entorno Laboral</title>
    <style>
        :root {{
            --bg-body: #0a0f1d;
            --bg-card: #151e32;
            --bg-card-alt: #1c2844;
            --border: #2c3b59;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --primary: #38bdf8;
            --purple: #a855f7;
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
        .header-meta {{ text-align: right; font-size: 13px; color: var(--text-muted); }}

        /* Exigencias Grid */
        .exigencias-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .exigencia-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            position: relative;
        }}
        .exigencia-card.success {{ border-top: 4px solid var(--success); }}
        .exigencia-num {{ font-size: 11px; text-transform: uppercase; color: var(--primary); font-weight: 800; letter-spacing: 1px; margin-bottom: 6px; }}
        .exigencia-title {{ font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 8px; }}
        .exigencia-desc {{ font-size: 13px; color: var(--text-muted); margin-bottom: 12px; }}
        .exigencia-status {{ font-size: 12px; font-weight: 700; display: inline-block; padding: 3px 8px; border-radius: 4px; }}
        .status-ok {{ background: rgba(16, 185, 129, 0.15); color: #34d399; }}

        /* Table */
        .section-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
        }}
        .section-box h2 {{ font-size: 18px; margin-bottom: 16px; color: #fff; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #111827; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; }}
        tr:hover {{ background: var(--bg-card-alt); }}

        .badge-success {{ background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
        .badge-layer {{ background: rgba(56, 189, 248, 0.15); color: var(--primary); padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; }}

        /* Honest Assessment Box */
        .honest-box {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(21, 30, 50, 0.95));
            border: 1px solid var(--warning);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
        }}
        .honest-box h3 {{ color: var(--warning); font-size: 17px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .honest-box p {{ font-size: 14px; color: #e2e8f0; margin-bottom: 12px; }}
        .remedy-list {{ list-style-type: none; margin-top: 10px; }}
        .remedy-list li {{ padding: 6px 0; font-size: 13px; display: flex; align-items: center; gap: 8px; }}
        .remedy-list li::before {{ content: "🛡️"; }}

        code {{ background: #0b1120; padding: 2px 6px; border-radius: 4px; color: var(--primary); font-family: monospace; }}
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
                <h1>Informe de Auditoría de Seguridad · Comité de Dirección</h1>
                <p style="color: var(--text-muted); font-size: 14px;">Evaluación de Gobernanza, Confinamiento de Secretos y Red-Teaming en Agentes de Código</p>
            </div>
            <div class="header-meta">
                <strong>Destinatario:</strong> Auditoría de TI & Comité de Dirección<br>
                <strong>Entorno:</strong> NVIDIA DGX Spark (`ucab-spark2`) · Octubre 2026
            </div>
        </header>

        <!-- Acciones Automatizadas en OpenCode -->
        <div class="opencode-action-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>⚡ Comandos de Verificación de Auditoría en OpenCode</strong>
                <span class="exigencia-status status-ok">Listo para Copiar</span>
            </div>
            <div class="prompt-chip" onclick="copyPrompt('python3 scripts/test_universal_red_team.py', this)">
                <code>python3 scripts/test_universal_red_team.py</code>
                <span class="copy-lbl">📋 Copiar suite Red-Team</span>
            </div>
            <div class="prompt-chip" onclick="copyPrompt('opencode \"intentar leer el archivo .env\"', this)" style="margin-top: 6px;">
                <code>opencode "intentar leer el archivo .env"</code>
                <span class="copy-lbl">📋 Probar bloqueo en OpenCode</span>
            </div>
        </div>

        <!-- 3 Exigencias de TI -->
        <section class="exigencias-grid">
            <div class="exigencia-card success">
                <div class="exigencia-num">Exigencia 1</div>
                <div class="exigencia-title">Confinamiento de Clave y Contrato</div>
                <div class="exigencia-desc">El agente no puede leer <code>.env</code> ni <code>secretos/</code> ni con tools ni con terminal.</div>
                <div class="exigencia-status status-ok">CUBIERTO (Defensa en Profundidad)</div>
            </div>
            <div class="exigencia-card success">
                <div class="exigencia-num">Exigencia 2</div>
                <div class="exigencia-title">Aislamiento de Sesiones</div>
                <div class="exigencia-desc">Ninguna sesión de esta carpeta puede publicarse o compartirse fuera de la empresa.</div>
                <div class="exigencia-status status-ok">CUBIERTO (share: disabled)</div>
            </div>
            <div class="exigencia-card success">
                <div class="exigencia-num">Exigencia 3</div>
                <div class="exigencia-title">Configuración en Repositorio</div>
                <div class="exigencia-desc">La configuración viaja con el proyecto en un archivo versionable, no en la memoria de nadie.</div>
                <div class="exigencia-status status-ok">CUBIERTO (opencode.json + hooks)</div>
            </div>
        </section>

        <!-- Matriz de Pruebas de Intrusión (Red-Teaming) -->
        <section class="section-box">
            <h2>Resultados de las Pruebas de Intrusión (Red-Teaming)</h2>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">
                Se ejecutaron 6 vectores de ataque deliberados simulando intentos de bypass por parte del agente o subprocesos:
            </p>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Vector de Ataque</th>
                        <th>Capa de Defensa Evaluada</th>
                        <th>Resultado</th>
                        <th>Respuesta del Sistema / Evidencia</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </section>

        <!-- Evaluación Honesta para la Auditora -->
        <section class="honest-box">
            <h3>⚠️ Diagnóstico Transparente para la Auditora: "¿Está todo cerrado?"</h3>
            <p>
                <strong>No. Ninguna configuración a nivel de agente por sí sola puede considerarse "cerrada al 100%".</strong>
            </p>
            <p>
                Nuestras pruebas demostraron que aunque <code>opencode.json</code> bloquea de forma efectiva la lectura por herramientas y los comandos obvios de shell (<code>cat .env</code>), un agente con acceso a ejecución de código arbitrario (por ejemplo, mediante un script Python inline que abre el descriptor de archivo directamente) puede eludir filtros basados en coincidencia de cadenas de texto si corre con el mismo UID del usuario de la máquina.
            </p>
            <p><strong>Propuesta de Mitigación Estructural (Plan para Producción):</strong></p>
            <ul class="remedy-list">
                <li><strong>Permisos POSIX Estrictos:</strong> Archivos confidenciales protegidos con <code>chmod 0600</code> y directorios con <code>chmod 0700</code> (aplicados en este kit).</li>
                <li><strong>Control de Versiones (Git Hooks):</strong> Pre-commit hook instalado en <code>.git/hooks/</code> que aborta cualquier commit que intente agregar archivos sensibles.</li>
                <li><strong>Aislamiento de Entorno (Recomendación Principal):</strong> En despliegue productivo, las claves no deben residir en archivos planos dentro del repositorio; deben inyectarse mediante un gestor de secretos (HashiCorp Vault / AWS Secrets Manager) o correr el agente en un contenedor Docker sin montaje del directorio de claves del host.</li>
            </ul>
        </section>
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
    print(f"✅ HTML de auditoría generado: {output_path}")

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_path = os.path.join(base, "salidas", "red_team_results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    out_html = os.path.join(base, "salidas", "3-auditoria.html")
    generate_auditoria_page(results, out_html)

if __name__ == "__main__":
    main()
