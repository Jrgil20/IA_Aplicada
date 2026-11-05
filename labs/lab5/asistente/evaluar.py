# -*- coding: utf-8 -*-
"""Evaluación del asistente con las preguntas de Legal.

Ejecuta las preguntas de `preguntas_de_prueba.csv`, comprueba hechos clave en
cada respuesta y genera `salidas/9-evaluacion.html` y el JSON de respaldo.
"""

from __future__ import annotations

import csv
import html
import json
import os
import re
import time
from datetime import datetime

from busqueda import sin_acentos
from motor import Asistente

BASE = os.path.dirname(os.path.abspath(__file__))
PREGUNTAS = os.path.normpath(os.path.join(BASE, "..", "preguntas_de_prueba.csv"))
SALIDAS = os.path.normpath(os.path.join(BASE, "..", "salidas"))

# Hechos que debe contener la respuesta para considerarla correcta. Los
# patrones se aplican al texto normalizado (sin acentos, minúsculas).
CRITERIOS = {
    "Q01": {
        "patrones": [r"\b5\b", r"gracia"],
        "descripcion": "Debe indicar 5 días calendario de gracia.",
    },
    "Q02": {
        "patrones": [r"15\s*%", r"penalidad|atraso"],
        "descripcion": "Debe indicar el tope vigente del 15 % (adenda).",
    },
    "Q03": {
        "patrones": [r"3[.,]?\s?000|tres mil", r"cotizacion"],
        "descripcion": "Debe indicar el umbral de USD 3.000 para tres cotizaciones.",
    },
    "Q04": {
        "patrones": [r"\b45\b", r"dia|pago|factura"],
        "descripcion": "Debe indicar 45 días calendario.",
    },
    "Q05": {
        "patrones": [r"fuerza mayor", r"aduan", r"\b5\b", r"no se|no aplica|no corre|no se cobra"],
        "descripcion": "Debe explicar la fuerza mayor aduanal, el plazo de 5 días y que no se cobra si se notifica bien.",
        "espera_negativa": True,
    },
    "Q06": {
        "patrones": [r"gerencia general", r"finanzas"],
        "descripcion": "Debe nombrar a la Gerencia General y a la Gerencia de Finanzas.",
    },
    "Q07": {
        "patrones": [r"transporte[s]? gu[aá]rico", r"\b5\b", r"caja|carton"],
        "descripcion": "Debe indicar Transportes Guárico, las cajas de cartón y el máximo de 5 días.",
    },
    "Q08": {
        "patrones": [r"no consta|no ofrece|no menciona|no preve|no contempla", r"pronto pago"],
        "descripcion": "Debe responder que no ofrece descuento por pronto pago, no evadir la pregunta.",
        "espera_negativa": True,
    },
    "Q09": {
        "patrones": [r"\b5\b", r"dia|calendario", r"responder|respuesta|reclamo"],
        "descripcion": "Debe indicar 5 días calendario desde la notificación.",
    },
    "Q10": {
        "patrones": [r"reclamos@impmargarita\.example\.org"],
        "descripcion": "Debe indicar el correo de reclamos de Importadora Margarita.",
    },
    "Q11": {
        "patrones": [r"1\s*%", r"penalidad|atraso|dia"],
        "descripcion": "Debe indicar el 1 % diario vigente (adenda).",
    },
    "Q12": {
        "patrones": [r"no esta en los documentos|no consta|no se menciona|no se encuentra|no hay informacion"],
        "prohibidos": [r"\b\d+\s+empleados"],
        "descripcion": "Debe decir que el dato no está en los documentos y no inventar una cifra.",
        "espera_negativa": True,
    },
}

RESPUESTAS_ESPERADAS = {
    "Q01": "5 días calendario de gracia; después corre la penalidad del 0,4 % diario (CT-2025-P03, cláusula 8).",
    "Q02": "15 % del importe del pedido, para órdenes emitidas desde el 01/07/2026. Antes de la adenda era 10 % (AD-2026-P04-01, cláusula primera).",
    "Q03": "Desde USD 3.000 se necesitan al menos tres cotizaciones de proveedores distintos (POL-COM-2026, Cotizaciones).",
    "Q04": "45 días calendario desde la recepción de la factura (CT-2025-P05, cláusula 7).",
    "Q05": "La retención aduanal es fuerza mayor si no se debe a errores de documentación del proveedor; debe notificarse por escrito dentro de 5 días calendario con la constancia. Si se notifica tarde, se aplica la penalidad por todos los días de atraso (CT-2025-P06, cláusulas 8 y 9).",
    "Q06": "La Gerencia General y la Gerencia de Finanzas, en ese orden (PR-COM-03, Quién aprueba el reclamo).",
    "Q07": "Cambiar de transportista a Transportes Guárico desde el 1 de octubre y entregar las cajas de cartón a las cuatro sedes en un máximo de 5 días calendario desde la orden (ACT-2026-09, P02).",
    "Q08": "No ofrece descuento por pronto pago; el contrato fija el pago a 30 días y no prevé descuento (CT-2025-P06, cláusula 7).",
    "Q09": "5 días calendario desde la notificación del reclamo (PR-COM-03, Plazo de respuesta del proveedor).",
    "Q10": "reclamos@impmargarita.example.org, con copia al representante (CT-2025-P04, cláusula 10).",
    "Q11": "1 % del importe por cada día calendario de atraso, para órdenes emitidas desde el 01/07/2026. Antes era 0,5 % (AD-2026-P04-01, cláusula primera).",
    "Q12": "No está en los documentos: ningún documento de compras indica cuántos empleados tiene Distribuidora Andina.",
}


def normalizar(texto: str) -> str:
    texto = sin_acentos(texto or "").lower()
    return re.sub(r"\s+", " ", texto).strip()


def evaluar_respuesta(qid: str, respuesta: str, fuentes=None) -> tuple[bool, str]:
    criterio = CRITERIOS[qid]
    texto = normalizar(respuesta)

    # Una respuesta positiva sin fuente no puede considerarse correcta: Legal
    # exige documento y sección en cada afirmación.
    if fuentes is not None and not fuentes:
        marcas_negativas = (
            "no esta en los documentos",
            "no consta en los documentos",
            "no se encuentra en los documentos",
            "no hay informacion en los documentos",
        )
        if not any(marca in texto for marca in marcas_negativas):
            return False, "Sin fuente documental: la respuesta positiva no cita un documento."

    # Las negaciones no cumplen un criterio que espera un dato positivo.
    if not criterio.get("espera_negativa") and re.match(r"^(no|sin|nunca|ningun[oa]?)\b", texto):
        return False, "La respuesta empieza con una negación y el criterio espera un dato positivo."

    faltantes = [p for p in criterio["patrones"] if not re.search(p, texto)]
    prohibidos = [p for p in criterio.get("prohibidos", []) if re.search(p, texto)]
    if faltantes:
        return False, "Faltó: " + ", ".join(faltantes)
    if prohibidos:
        return False, "Aparece un dato prohibido: " + ", ".join(prohibidos)
    return True, "Cumple los hechos clave."


def correr() -> dict:
    asistente = Asistente()
    with open(PREGUNTAS, "r", encoding="utf-8", newline="") as archivo:
        preguntas = list(csv.DictReader(archivo))

    resultados = []
    inicio = time.monotonic()
    for fila in preguntas:
        qid = fila["id"].strip()
        pregunta = fila["pregunta"].strip()
        print(f"Evaluando {qid}…", flush=True)
        respuesta = asistente.responder(pregunta)
        correcta, detalle = evaluar_respuesta(qid, respuesta["respuesta"], respuesta.get("fuentes"))
        resultados.append(
            {
                "id": qid,
                "pregunta": pregunta,
                "respuesta": respuesta["respuesta"],
                "fuentes": respuesta["fuentes"],
                "negativa": respuesta["negativa"],
                "ms": respuesta["ms"],
                "correcta": correcta,
                "detalle": detalle,
                "esperada": RESPUESTAS_ESPERADAS[qid],
                "criterio": CRITERIOS[qid]["descripcion"],
                "evidencia": respuesta.get("evidencia", []),
            }
        )

    total = len(resultados)
    aciertos = sum(1 for r in resultados if r["correcta"])
    return {
        "generado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "modelo": "qwen3-coder (llama-server local)",
        "documentos": asistente.total_documentos,
        "fragmentos": len(asistente.indice.fragmentos),
        "duracion_s": round(time.monotonic() - inicio, 1),
        "total": total,
        "aciertos": aciertos,
        "porcentaje": round(100 * aciertos / total, 1) if total else 0,
        "resultados": resultados,
    }


def _e(valor) -> str:
    return html.escape(str(valor if valor is not None else ""))


def _fuentes_html(fuentes: list[dict], negativa: bool = False) -> str:
    if not fuentes:
        if negativa:
            return (
                '<p class="sin-fuente negativa">Respuesta negativa: el dato no está en '
                "los documentos, por eso no se cita una fuente.</p>"
            )
        return '<p class="sin-fuente">Sin fuentes citadas. La respuesta no se apoya en un documento.</p>'
    tarjetas = []
    for fuente in fuentes:
        tarjetas.append(
            '<article class="fuente">'
            f'<div class="fuente-cabecera"><span class="fuente-id">{_e(fuente["id"])}</span>'
            f'<span class="fuente-tipo">{_e(fuente.get("tipo", "Documento"))}</span></div>'
            f'<p class="fuente-titulo">{_e(fuente.get("titulo", ""))}</p>'
            f'<p class="fuente-seccion">{_e(fuente.get("seccion", ""))}</p>'
            f'<blockquote>{_e(fuente.get("fragmento", ""))}</blockquote>'
            f'<p class="fuente-ruta">{_e(fuente.get("ruta", ""))}</p>'
            "</article>"
        )
    return '<div class="lista-fuentes">' + "".join(tarjetas) + "</div>"


def generar_html(datos: dict) -> str:
    filas_indice = []
    tarjetas = []
    for r in datos["resultados"]:
        estado = "correcta" if r["correcta"] else "revisar"
        etiqueta = "Correcta" if r["correcta"] else "Revisar"
        filas_indice.append(
            f'<a class="indice-fila" href="#{_e(r["id"])}">'
            f'<span class="indice-id">{_e(r["id"])}</span>'
            f'<span class="indice-pregunta">{_e(r["pregunta"])}</span>'
            f'<span class="pastilla {estado}">{etiqueta}</span></a>'
        )
        fuentes = _fuentes_html(r["fuentes"], r.get("negativa", False))
        tiempo = f'{r["ms"] / 1000:.1f} s' if r.get("ms") else ""
        tarjetas.append(
            f'<article class="pregunta {estado}" id="{_e(r["id"])}">'
            '<div class="pregunta-cabecera">'
            f'<div><span class="pregunta-id">{_e(r["id"])}</span>'
            f'<h3>{_e(r["pregunta"])}</h3></div>'
            f'<span class="pastilla {estado}">{etiqueta}</span>'
            "</div>"
            '<div class="bloque">'
            '<h4>Respuesta del asistente</h4>'
            f'<div class="respuesta">{_e(r["respuesta"])}</div>'
            "</div>"
            '<div class="bloque">'
            f'<h4>Fuentes citadas <span class="conteo">{len(r["fuentes"])}</span></h4>'
            f"{fuentes}"
            "</div>"
            '<div class="bloque referencia">'
            "<details>"
            "<summary>Respuesta de referencia y criterio de corrección</summary>"
            f'<p><strong>Referencia:</strong> {_e(r["esperada"])}</p>'
            f'<p><strong>Criterio automático:</strong> {_e(r["criterio"])}</p>'
            f'<p><strong>Resultado:</strong> {_e(r["detalle"])}</p>'
            f'<p><strong>Tiempo de respuesta:</strong> {_e(tiempo)}</p>'
            "</details>"
            "</div>"
            "</article>"
        )

    aciertos = datos["aciertos"]
    total = datos["total"]
    porcentaje = datos["porcentaje"]
    porcentaje_txt = f"{porcentaje:g}"
    color = "verde" if porcentaje >= 90 else ("ambar" if porcentaje >= 70 else "rojo")
    resumen = (
        "Las respuestas coinciden con los hechos clave, pero Legal debe revisar "
        "las fuentes y el texto antes de aprobar."
        if aciertos == total
        else f"{total - aciertos} pregunta(s) requieren revisión antes de la aprobación."
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'">
<title>Evaluación preliminar del Asistente de Compras · Legal</title>
<style>
  :root {{
    --tinta:#12283f; --suave:#4a6076; --azul:#173f63; --azul-claro:#e8f0f6;
    --verde:#0c6b5c; --verde-claro:#e6f4f0; --dorado:#b28a2e;
    --rojo:#a33d2f; --rojo-claro:#f8e9e6; --ambar:#8a6414; --ambar-claro:#fbf1d7;
    --fondo:#f2f5f7; --blanco:#fff; --linea:#d9e2e8;
    --fuente:"Segoe UI","Helvetica Neue",Arial,"Noto Sans",sans-serif;
    --mono:ui-monospace,"SFMono-Regular",Consolas,monospace;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--fondo); color:var(--tinta); font-family:var(--fuente); line-height:1.55; }}
  .pagina {{ width:min(1040px, calc(100% - 32px)); margin:0 auto; padding:34px 0 70px; }}
  .cabecera {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start;
    border-bottom:1px solid var(--linea); padding-bottom:18px; }}
  .marca {{ display:flex; gap:13px; align-items:center; }}
  .monograma {{ width:44px; height:44px; display:grid; place-items:center; background:var(--tinta);
    color:#fff; font-size:14px; font-weight:700; letter-spacing:.06em; border-radius:4px; position:relative; }}
  .monograma::after {{ content:""; position:absolute; left:8px; right:8px; bottom:8px; height:2px; background:var(--dorado); }}
  .empresa {{ font-size:10.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--suave); font-weight:600; }}
  h1 {{ margin:2px 0 0; font-size:22px; letter-spacing:-.01em; }}
  .meta {{ text-align:right; font-size:12px; color:var(--suave); }}
  .meta strong {{ display:block; color:var(--tinta); font-size:12.5px; }}
  .hero {{ display:grid; grid-template-columns:1.1fr 1fr; gap:22px; margin-top:26px;
    background:var(--blanco); border:1px solid var(--linea); border-radius:14px; padding:26px 28px;
    box-shadow:0 10px 30px rgba(18,40,63,.07); }}
  .hero-etiqueta {{ margin:0 0 8px; font-size:10.5px; letter-spacing:.17em; text-transform:uppercase;
    color:var(--dorado); font-weight:700; }}
  .hero h2 {{ margin:0; font-size:18px; line-height:1.3; }}
  .hero p {{ margin:9px 0 0; color:var(--suave); font-size:13.5px; }}
  .marcador {{ text-align:right; }}
  .nota {{ font-size:12.5px; font-weight:650; }}
  .nota.verde {{ color:var(--verde); }} .nota.ambar {{ color:var(--ambar); }} .nota.rojo {{ color:var(--rojo); }}
  .barra {{ height:8px; background:#e7edf1; border-radius:999px; overflow:hidden; margin-top:12px; }}
  .barra span {{ display:block; height:100%; width:{porcentaje_txt}%; border-radius:999px;
    background:linear-gradient(90deg, var(--verde), #1d9a72); }}
  .metricas {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:16px; }}
  .metrica {{ background:var(--blanco); border:1px solid var(--linea); border-radius:10px; padding:13px 15px; }}
  .metrica strong {{ display:block; font-size:19px; line-height:1.2; }}
  .metrica span {{ font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--suave); }}
  h2.seccion {{ font-size:13px; letter-spacing:.1em; text-transform:uppercase; color:var(--suave);
    margin:34px 0 10px; }}
  .indice {{ background:var(--blanco); border:1px solid var(--linea); border-radius:12px; overflow:hidden; }}
  .indice-fila {{ display:grid; grid-template-columns:52px 1fr auto; gap:12px; align-items:center;
    padding:11px 16px; text-decoration:none; color:inherit; border-bottom:1px solid #edf1f4; font-size:13px; }}
  .indice-fila:last-child {{ border-bottom:0; }}
  .indice-fila:hover {{ background:#f8fafb; }}
  .indice-id {{ font-family:var(--mono); font-size:11.5px; font-weight:700; color:var(--azul); }}
  .pastilla {{ display:inline-block; font-size:10.5px; font-weight:700; letter-spacing:.05em; text-transform:uppercase;
    padding:3px 9px; border-radius:999px; white-space:nowrap; }}
  .pastilla.correcta {{ background:var(--verde-claro); color:var(--verde); }}
  .pastilla.revisar {{ background:var(--rojo-claro); color:var(--rojo); }}
  .pregunta {{ background:var(--blanco); border:1px solid var(--linea); border-left:3px solid var(--verde);
    border-radius:10px; padding:20px 22px; margin-top:14px; break-inside:avoid; }}
  .pregunta.revisar {{ border-left-color:var(--rojo); }}
  .pregunta-cabecera {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start;
    border-bottom:1px solid #edf1f4; padding-bottom:12px; }}
  .pregunta-id {{ font-family:var(--mono); font-size:11.5px; font-weight:700; color:var(--azul);
    background:var(--azul-claro); padding:2px 6px; border-radius:4px; }}
  .pregunta h3 {{ margin:6px 0 0; font-size:15.5px; line-height:1.35; }}
  .bloque {{ margin-top:14px; }}
  .bloque h4 {{ margin:0 0 7px; font-size:11px; letter-spacing:.08em; text-transform:uppercase;
    color:var(--suave); }}
  .conteo {{ background:#eef2f5; color:var(--suave); border-radius:999px; padding:0 7px; font-size:10.5px; }}
  .respuesta {{ font-size:14px; white-space:pre-wrap; }}
  .lista-fuentes {{ display:grid; gap:9px; }}
  .fuente {{ border:1px solid var(--linea); border-radius:9px; padding:12px 13px; background:#fbfcfd; }}
  .fuente-cabecera {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:4px; }}
  .fuente-id {{ font-family:var(--mono); font-size:11px; font-weight:700; color:var(--azul);
    background:var(--azul-claro); padding:2px 6px; border-radius:4px; }}
  .fuente-tipo {{ font-size:10px; letter-spacing:.06em; text-transform:uppercase; color:var(--suave); }}
  .fuente-titulo {{ margin:0; font-size:13px; font-weight:650; }}
  .fuente-seccion {{ margin:2px 0 7px; font-size:12px; color:var(--verde); font-weight:650; }}
  .fuente blockquote {{ margin:0; padding:7px 10px; border-left:2px solid var(--linea);
    color:var(--suave); font-size:12px; white-space:pre-wrap; }}
  .fuente-ruta {{ margin:6px 0 0; font-family:var(--mono); font-size:10px; color:#8798a6; }}
  .sin-fuente {{ margin:0; font-size:12.5px; color:var(--rojo); }}
  .sin-fuente.negativa {{ color:var(--ambar); }}
  details {{ font-size:12.5px; color:var(--suave); }}
  summary {{ cursor:pointer; font-weight:650; color:var(--azul); }}
  details p {{ margin:8px 0 0; }}
  .pie {{ margin-top:32px; border-top:1px solid var(--linea); padding-top:14px;
    font-size:11.5px; color:#7b8fa1; display:flex; justify-content:space-between; gap:16px; }}
  @media (max-width:760px) {{
    .hero {{ grid-template-columns:1fr; }}
    .marcador {{ text-align:left; }}
    .metricas {{ grid-template-columns:repeat(2,1fr); }}
    .cabecera {{ flex-direction:column; }}
    .meta {{ text-align:left; }}
    .indice-fila {{ grid-template-columns:44px 1fr auto; }}
  }}
  @media print {{
    body {{ background:#fff; }}
    .pagina {{ width:100%; padding:0; }}
    .hero, .metrica, .pregunta, .indice {{ box-shadow:none; }}
    .pregunta {{ page-break-inside:avoid; }}
    details {{ display:block; }}
    details > * {{ display:block; }}
  }}
</style>
</head>
<body>
<div class="pagina">
  <header class="cabecera">
    <div class="marca">
      <div class="monograma" aria-hidden="true">LS</div>
      <div>
        <span class="empresa">Comercial Los Samanes, C.A. · Compras</span>
        <h1>Evaluación del Asistente de Compras</h1>
      </div>
    </div>
    <div class="meta">
      <strong>Preparado para la Gerencia de Legal</strong>
      Problema 9 · {_e(datos["generado"])}
    </div>
  </header>

  <section class="hero">
    <div>
      <p class="hero-etiqueta">Resultado de la evaluación</p>
      <h2>{aciertos} de {total} coincidencias automáticas · revisión humana pendiente</h2>
      <p>{_e(resumen)} Se evaluaron las {total} preguntas de <code>preguntas_de_prueba.csv</code>
         contra los documentos de compras vigentes al 05/11/2026.</p>
    </div>
    <div class="marcador">
      <div style="font-size:42px;font-weight:700;line-height:1;letter-spacing:-.03em;">{porcentaje_txt} %</div>
      <div class="nota {color}">{"Evaluación automática preliminar" if aciertos == total else "Requiere revisión"}</div>
      <div class="barra" aria-hidden="true"><span></span></div>
      <div style="font-size:11.5px;color:var(--suave);margin-top:7px;">{aciertos} aciertos · {total - aciertos} por revisar</div>
    </div>
  </section>

  <div class="metricas">
    <div class="metrica"><strong>{datos["documentos"]}</strong><span>Documentos indexados</span></div>
    <div class="metrica"><strong>{total}</strong><span>Preguntas de Legal</span></div>
    <div class="metrica"><strong>{_e(datos["modelo"])}</strong><span>Modelo local</span></div>
    <div class="metrica"><strong>{datos["duracion_s"]} s</strong><span>Duración de la prueba</span></div>
  </div>

  <h2 class="seccion">Índice de preguntas</h2>
  <nav class="indice" aria-label="Índice de preguntas">
    {"".join(filas_indice)}
  </nav>

  <h2 class="seccion">Detalle pregunta por pregunta</h2>
  {"".join(tarjetas)}

  <footer class="pie">
    <span>Evaluación automática contra hechos clave; las respuestas y sus fuentes quedan a la vista para la revisión humana de Legal.</span>
    <span>Generado el {_e(datos["generado"])}</span>
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    os.makedirs(SALIDAS, exist_ok=True)
    datos = correr()
    json_salida = os.path.join(SALIDAS, "9-evaluacion.json")
    with open(json_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    html_salida = os.path.join(SALIDAS, "9-evaluacion.html")
    with open(html_salida, "w", encoding="utf-8") as archivo:
        archivo.write(generar_html(datos))
    for ruta in (json_salida, html_salida):
        try:
            os.chmod(ruta, 0o640)
        except OSError:
            pass
    print(
        f"\nResultado: {datos['aciertos']}/{datos['total']} "
        f"({datos['porcentaje']} %).\nHTML: {html_salida}\nJSON: {json_salida}"
    )


if __name__ == "__main__":
    main()
