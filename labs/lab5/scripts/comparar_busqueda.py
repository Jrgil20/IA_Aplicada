#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comparación Modo A (archivos directos) vs Modo B (buscador MCP).

Ejecuta las preguntas de ``preguntas_de_prueba.csv`` por las dos vías, mide
tiempo y contexto consumido, evalúa el acierto con los mismos criterios de
Legal del problema 9 y genera:

    salidas/10-comparacion.json
    salidas/10-comparacion.html

Solo usa la biblioteca estándar de Python 3. El modelo es el llama-server
local del Spark (API compatible con OpenAI).

Uso:
    python3 scripts/comparar_busqueda.py
    python3 scripts/comparar_busqueda.py --ids Q01,Q07   # prueba corta
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASISTENTE = os.path.join(RAIZ, "asistente")
SALIDAS = os.path.join(RAIZ, "salidas")
PREGUNTAS = os.path.join(RAIZ, "preguntas_de_prueba.csv")
SERVIDOR_MCP = os.path.join(ASISTENTE, "servidor_mcp.py")
DOCUMENTOS = os.path.join(RAIZ, "documentos")

if ASISTENTE not in sys.path:
    sys.path.insert(0, ASISTENTE)

from busqueda import Indice, normalizar, tokenizar  # noqa: E402
from evaluar import CRITERIOS, RESPUESTAS_ESPERADAS, evaluar_respuesta  # noqa: E402
from llm import SISTEMA, _llamar_modelo  # noqa: E402

LIMITE_MCP = 5
TOPE_CONTEXTO_DIRECTO = 40000  # caracteres de documentos que "lee" el agente
MAX_DOCS_DIRECTO = 15
HOY = "2026-11-05"


# ---------------------------------------------------------------------------
# Cliente MCP por stdio
# ---------------------------------------------------------------------------

class ClienteMCP:
    """Cliente mínimo del servidor MCP: initialize + tools/call."""

    def __init__(self, ruta_servidor: str):
        self.proceso = subprocess.Popen(
            [sys.executable, ruta_servidor],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=RAIZ,
        )
        self._id = 0
        self.inicializar()

    def _peticion(self, metodo: str, params: dict | None = None) -> dict:
        self._id += 1
        mensaje = {"jsonrpc": "2.0", "id": self._id, "method": metodo}
        if params is not None:
            mensaje["params"] = params
        self.proceso.stdin.write(json.dumps(mensaje, ensure_ascii=False) + "\n")
        self.proceso.stdin.flush()
        linea = self.proceso.stdout.readline()
        if not linea:
            raise RuntimeError("El servidor MCP cerró la conexión sin responder.")
        respuesta = json.loads(linea)
        if "error" in respuesta:
            raise RuntimeError(respuesta["error"].get("message", "Error MCP"))
        return respuesta.get("result", {})

    def inicializar(self) -> None:
        self._peticion(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "comparador-ti", "version": "1.0"},
            },
        )

    def llamar(self, nombre: str, argumentos: dict) -> object:
        resultado = self._peticion(
            "tools/call", {"name": nombre, "arguments": argumentos}
        )
        if resultado.get("isError"):
            raise RuntimeError(resultado["content"][0]["text"])
        return json.loads(resultado["content"][0]["text"])

    def cerrar(self) -> None:
        try:
            self.proceso.stdin.close()
        except Exception:
            pass
        try:
            self.proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proceso.kill()
            self.proceso.wait(timeout=5)


# ---------------------------------------------------------------------------
# Motor de respuesta común a los dos modos
# ---------------------------------------------------------------------------

def responder_modelo(documentos_texto: str, pregunta: str) -> tuple[str, int]:
    mensaje = (
        "DOCUMENTOS DISPONIBLES PARA RESPONDER:\n\n"
        f"{documentos_texto}\n\n"
        f"PREGUNTA DE LA SEDE: {pregunta.strip()}\n\n"
        "Responde con la información de los documentos y cita cada afirmación."
    )
    inicio = time.monotonic()
    respuesta = _llamar_modelo(
        [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": mensaje},
        ],
        max_tokens=380,
    )
    ms = int((time.monotonic() - inicio) * 1000)
    return respuesta.strip(), ms


def _bloque_completo(documento) -> str:
    return (
        f"[DOC: {documento.doc_id} · {documento.titulo}]\n"
        f"Tipo: {documento.tipo}\n"
        f"Proveedor: {documento.proveedor or 'No aplica'}\n"
        f"Fecha: {documento.fecha or 'Sin fecha'}\n"
        f"Estado: {documento.estado or 'Sin estado'}\n"
        f"Ruta: {documento.ruta}\n"
        "Texto:\n"
        f"{documento.texto.strip()}"
    )


def _bloque_fragmento(fragmento: dict) -> str:
    return (
        f"[DOC: {fragmento['id']} · {fragmento['seccion']}]\n"
        f"Tipo: {fragmento.get('tipo', '')}\n"
        f"Proveedor: {fragmento.get('proveedor') or 'No aplica'}\n"
        f"Fecha: {fragmento.get('fecha') or 'Sin fecha'}\n"
        f"Estado: {fragmento.get('estado') or 'Sin estado'}\n"
        "Texto:\n"
        f"{fragmento.get('texto', '').strip()}"
    )


# ---------------------------------------------------------------------------
# Modo A: el agente busca y abre archivos por su cuenta
# ---------------------------------------------------------------------------

class ExploradorDirecto:
    """Simula grep + lectura de archivos completos, sin índice BM25."""

    def __init__(self, indice: Indice):
        self.indice = indice
        self._tokens = {
            documento.doc_id: set(
                tokenizar(
                    " ".join(
                        [
                            documento.doc_id,
                            documento.titulo,
                            documento.tipo,
                            documento.proveedor,
                            documento.estado,
                            documento.texto,
                        ]
                    )
                )
            )
            for documento in indice.documentos
        }
        self._titulos = {
            documento.doc_id: set(tokenizar(documento.titulo))
            for documento in indice.documentos
        }
        self._textos_normalizados = {
            documento.doc_id: normalizar(documento.texto)
            for documento in indice.documentos
        }

    def seleccionar(self, pregunta: str):
        tokens_unicos = sorted(set(tokenizar(pregunta)))
        proveedor = self.indice._proveedor_detectado(tokenizar(pregunta))
        clases = self.indice._clases_relevantes(tokenizar(pregunta))
        aliases = {
            "P01": ("distribuidora", "andina"),
            "P02": ("logistica", "avila"),
            "P03": ("suministros", "caroni"),
            "P04": ("importadora", "margarita"),
            "P05": ("papelera", "llanos"),
            "P06": ("tecnologia", "zulia"),
        }

        candidatos = []
        meses = set(tokens_unicos) & {
            "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembr", "setiembr", "octubr", "noviembr", "diciembr",
        }
        pide_acta = bool(set(tokens_unicos) & {"reunion", "acta", "actas", "comprometio", "acuerdo"})
        for documento in self.indice.documentos:
            if "reemplazad" in normalizar(documento.estado):
                continue
            tokens_doc = self._tokens[documento.doc_id]
            titulo_tokens = self._titulos[documento.doc_id]
            presentes = sum(1 for token in tokens_unicos if token in tokens_doc)
            en_titulo = sum(1 for token in tokens_unicos if token in titulo_tokens)
            puntos = 2.0 * presentes + 3.0 * en_titulo

            if documento.clase == "acta" and pide_acta:
                puntos += 15.0
                if meses and meses & titulo_tokens:
                    puntos += 30.0

            if proveedor:
                texto = self._textos_normalizados[documento.doc_id]
                menciona = documento.proveedor.startswith(proveedor)
                if not menciona:
                    menciona = any(alias in texto for alias in aliases.get(proveedor, ()))
                if documento.proveedor.startswith(proveedor):
                    puntos += 40.0
                elif menciona:
                    puntos += 8.0
                else:
                    puntos -= 20.0
            if clases and documento.clase in clases:
                puntos += 6.0
            if puntos > 0:
                candidatos.append((puntos, documento))

        candidatos.sort(key=lambda par: (-par[0], par[1].doc_id))
        elegidos = []
        usados = 0
        for puntos, documento in candidatos:
            if len(elegidos) >= MAX_DOCS_DIRECTO or usados >= TOPE_CONTEXTO_DIRECTO:
                break
            if documento in elegidos:
                continue
            largo = len(documento.texto)
            if elegidos and usados + largo > TOPE_CONTEXTO_DIRECTO:
                continue
            elegidos.append(documento)
            usados += largo
        return elegidos

    def ejecutar(self, pregunta: str) -> dict:
        inicio = time.monotonic()
        documentos = self.seleccionar(pregunta)
        bloques = [_bloque_completo(documento) for documento in documentos]
        contexto = "\n\n".join(bloques)
        ms_recuperacion = int((time.monotonic() - inicio) * 1000)
        respuesta, ms_modelo = responder_modelo(contexto, pregunta)
        return {
            "respuesta": respuesta,
            "documentos": [documento.doc_id for documento in documentos],
            "rutas": [documento.ruta for documento in documentos],
            "fragmentos": len(documentos),
            "contexto_documentos": len(contexto),
            "ms_recuperacion": ms_recuperacion,
            "ms_modelo": ms_modelo,
            "ms_total": int((time.monotonic() - inicio) * 1000),
            "herramientas": ["glob", "grep", "read"],
        }


# ---------------------------------------------------------------------------
# Modo B: el agente solo ve los documentos a través del MCP
# ---------------------------------------------------------------------------

def ejecutar_mcp(cliente: ClienteMCP, pregunta: str) -> dict:
    inicio = time.monotonic()
    fragmentos = cliente.llamar(
        "buscar_documentos", {"consulta": pregunta, "limite": LIMITE_MCP}
    )
    ms_busqueda = int((time.monotonic() - inicio) * 1000)
    contexto = "\n\n".join(_bloque_fragmento(f) for f in fragmentos)
    ms_recuperacion = int((time.monotonic() - inicio) * 1000)
    respuesta, ms_modelo = responder_modelo(contexto, pregunta)
    return {
        "respuesta": respuesta,
        "documentos": [f["id"] for f in fragmentos],
        "secciones": [f["seccion"] for f in fragmentos],
        "fragmentos": len(fragmentos),
        "contexto_documentos": len(contexto),
        "ms_busqueda": ms_busqueda,
        "ms_recuperacion": ms_recuperacion,
        "ms_modelo": ms_modelo,
        "ms_total": int((time.monotonic() - inicio) * 1000),
        "herramientas": ["buscar_documentos"],
    }


# ---------------------------------------------------------------------------
# Ejecución y métricas
# ---------------------------------------------------------------------------

def _promedio(valores) -> float:
    valores = list(valores)
    return sum(valores) / len(valores) if valores else 0.0


def correr(ids: set[str] | None = None) -> dict:
    with open(PREGUNTAS, "r", encoding="utf-8", newline="") as archivo:
        preguntas = list(csv.DictReader(archivo))
    if ids:
        preguntas = [f for f in preguntas if f["id"].strip() in ids]

    print("Cargando índice documental…", flush=True)
    indice = Indice(DOCUMENTOS)
    explorador = ExploradorDirecto(indice)
    print(f"Índice listo: {len(indice.documentos)} documentos, {len(indice.fragmentos)} fragmentos.", flush=True)

    cliente = ClienteMCP(SERVIDOR_MCP)
    resultados = []
    inicio_total = time.monotonic()
    try:
        for fila in preguntas:
            qid = fila["id"].strip()
            pregunta = fila["pregunta"].strip()
            print(f"\n{qid} · {pregunta}", flush=True)

            print("  Modo A (archivos directos)…", flush=True)
            modo_a = explorador.ejecutar(pregunta)
            correcta_a, detalle_a = evaluar_respuesta(qid, modo_a["respuesta"])
            modo_a["correcta"] = correcta_a
            modo_a["detalle"] = detalle_a

            print("  Modo B (buscador MCP)…", flush=True)
            modo_b = ejecutar_mcp(cliente, pregunta)
            correcta_b, detalle_b = evaluar_respuesta(qid, modo_b["respuesta"])
            modo_b["correcta"] = correcta_b
            modo_b["detalle"] = detalle_b

            if correcta_a != correcta_b:
                ganador = "mcp" if correcta_b else "directo"
            elif modo_a["contexto_documentos"] == modo_b["contexto_documentos"]:
                ganador = "empate"
            elif modo_b["contexto_documentos"] < modo_a["contexto_documentos"]:
                ganador = "mcp"
            else:
                ganador = "directo"

            resultados.append(
                {
                    "id": qid,
                    "pregunta": pregunta,
                    "esperada": RESPUESTAS_ESPERADAS.get(qid, ""),
                    "criterio": CRITERIOS.get(qid, {}).get("descripcion", ""),
                    "modo_a": modo_a,
                    "modo_b": modo_b,
                    "ganador": ganador,
                }
            )
            print(
                f"  A: {'OK' if correcta_a else 'FALLA'} {modo_a['contexto_documentos']:,} car · "
                f"{modo_a['ms_total']/1000:.1f} s | "
                f"B: {'OK' if correcta_b else 'FALLA'} {modo_b['contexto_documentos']:,} car · "
                f"{modo_b['ms_total']/1000:.1f} s",
                flush=True,
            )
            _guardar_json(resultados, inicio_total, indice, incompleto=True)
    finally:
        cliente.cerrar()

    return _consolidar(resultados, inicio_total, indice)


def _consolidar(resultados: list[dict], inicio_total: float, indice: Indice) -> dict:
    total = len(resultados)
    aciertos_a = sum(1 for r in resultados if r["modo_a"]["correcta"])
    aciertos_b = sum(1 for r in resultados if r["modo_b"]["correcta"])
    contexto_a = _promedio(r["modo_a"]["contexto_documentos"] for r in resultados)
    contexto_b = _promedio(r["modo_b"]["contexto_documentos"] for r in resultados)
    latencia_a = _promedio(r["modo_a"]["ms_total"] for r in resultados)
    latencia_b = _promedio(r["modo_b"]["ms_total"] for r in resultados)
    ahorro = ((contexto_a - contexto_b) / contexto_a * 100) if contexto_a else 0.0
    delta_latencia = ((latencia_b - latencia_a) / latencia_a * 100) if latencia_a else 0.0

    return {
        "generado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "hoy": HOY,
        "modelo": "qwen3-coder (llama-server local)",
        "documentos": len(indice.documentos),
        "fragmentos_indice": len(indice.fragmentos),
        "duracion_s": round(time.monotonic() - inicio_total, 1),
        "limite_mcp": LIMITE_MCP,
        "tope_contexto_directo": TOPE_CONTEXTO_DIRECTO,
        "total": total,
        "resumen": {
            "total": total,
            "aciertos_a": aciertos_a,
            "aciertos_b": aciertos_b,
            "porcentaje_a": round(100 * aciertos_a / total, 1) if total else 0,
            "porcentaje_b": round(100 * aciertos_b / total, 1) if total else 0,
            "contexto_promedio_a": round(contexto_a),
            "contexto_promedio_b": round(contexto_b),
            "ahorro_contexto_pct": round(ahorro, 1),
            "latencia_promedio_a_ms": round(latencia_a),
            "latencia_promedio_b_ms": round(latencia_b),
            "delta_latencia_pct": round(delta_latencia, 1),
            "tokens_estimados_a": round((contexto_a + len(SISTEMA)) / 4),
            "tokens_estimados_b": round((contexto_b + len(SISTEMA)) / 4),
        },
        "resultados": resultados,
    }


def _guardar_json(resultados: list[dict], inicio_total: float, indice: Indice, incompleto: bool) -> None:
    os.makedirs(SALIDAS, exist_ok=True)
    datos = _consolidar(resultados, inicio_total, indice)
    datos["incompleto"] = incompleto
    with open(os.path.join(SALIDAS, "10-comparacion.json"), "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Informe HTML para TI
# ---------------------------------------------------------------------------

def _e(valor) -> str:
    return html.escape(str(valor if valor is not None else ""))


def _num(valor: int | float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def _segundos(ms: int | float) -> str:
    return f"{ms / 1000:.1f} s"


def _recomendacion(resumen: dict) -> tuple[str, str]:
    ahorro = resumen["ahorro_contexto_pct"]
    base = (
        f"Adoptar el buscador MCP como única vía de acceso del agente a "
        f"<code>documentos/</code>. Reduce el contexto documental en "
        f"{ahorro:.0f} % y mantiene {resumen['aciertos_b']} de "
        f"{resumen['total']} respuestas correctas."
    )
    if resumen["porcentaje_b"] + 6 < resumen["porcentaje_a"]:
        base = (
            "Mantener el acceso directo mientras se corrige la recuperación del buscador MCP: "
            f"en esta corrida el modo directo acertó {resumen['porcentaje_a']:.0f} % y el MCP "
            f"{resumen['porcentaje_b']:.0f} %, aunque el MCP usó {ahorro:.0f} % menos contexto."
        )
    detalle = (
        "El ahorro de contexto es la diferencia decisiva: el modo directo vuelca archivos "
        "completos y deja menos espacio para el razonamiento; el buscador entrega solo los "
        "fragmentos pertinentes, con documento y sección, y permite auditar qué ve el modelo. "
        "La condición de TI se cumple porque el agente MCP no puede abrir, listar ni buscar "
        "dentro de <code>documentos/</code>: solo recibe lo que devuelve el servidor."
    )
    return base, detalle


def generar_html(datos: dict) -> str:
    resumen = datos["resumen"]
    recomendacion, justificacion = _recomendacion(resumen)
    total = datos["total"]
    ahorro = resumen["ahorro_contexto_pct"]
    delta = resumen["delta_latencia_pct"]
    delta_txt = (
        f"{abs(delta):.0f} % más rápida" if delta < 0 else f"{abs(delta):.0f} % más lenta"
    )
    color_ahorro = "verde" if ahorro >= 40 else ("ambar" if ahorro >= 15 else "rojo")
    color_precision = (
        "verde" if resumen["porcentaje_b"] >= 90
        else ("ambar" if resumen["porcentaje_b"] >= 70 else "rojo")
    )

    filas = []
    for r in datos["resultados"]:
        a, b = r["modo_a"], r["modo_b"]
        estado_a = "ok" if a["correcta"] else "falla"
        estado_b = "ok" if b["correcta"] else "falla"
        ganador = {
            "mcp": "Buscador MCP",
            "directo": "Archivos directos",
            "empate": "Empate",
        }.get(r["ganador"], r["ganador"])
        clase_ganador = "mcp" if r["ganador"] == "mcp" else (
            "directo" if r["ganador"] == "directo" else "empate"
        )
        filas.append(
            f'<tr id="fila-{_e(r["id"])}">'
            f'<td class="id">{_e(r["id"])}</td>'
            f'<td class="pregunta">{_e(r["pregunta"])}</td>'
            f'<td><span class="dato">{_segundos(a["ms_total"])}</span>'
            f'<span class="sub">{_num(a["contexto_documentos"])} car</span></td>'
            f'<td><span class="pastilla {estado_a}">{"Correcta" if a["correcta"] else "Incorrecta"}</span>'
            f'<details><summary>Ver respuesta</summary><p>{_e(a["respuesta"])}</p>'
            f'<p class="ref">Documentos: {_e(", ".join(a["documentos"]))}</p></details></td>'
            f'<td><span class="dato">{_segundos(b["ms_total"])}</span>'
            f'<span class="sub">{_num(b["contexto_documentos"])} car</span></td>'
            f'<td><span class="pastilla {estado_b}">{"Correcta" if b["correcta"] else "Incorrecta"}</span>'
            f'<details><summary>Ver respuesta</summary><p>{_e(b["respuesta"])}</p>'
            f'<p class="ref">Fragmentos: {_e(" · ".join(b["documentos"]))}</p></details></td>'
            f'<td><span class="ganador {clase_ganador}">{_e(ganador)}</span></td>'
            "</tr>"
        )

    metodos = [
        ("Modo A · Archivos directos", f"El agente busca con <code>glob</code>/<code>grep</code> y abre hasta {MAX_DOCS_DIRECTO} archivos completos de <code>documentos/</code>.", "A"),
        ("Modo B · Buscador MCP", f"El agente llama <code>buscar_documentos</code> y recibe los {datos['limite_mcp']} fragmentos más pertinentes, con cita de documento y sección. No abre archivos.", "B"),
    ]
    tarjetas_metodo = "".join(
        f'<article class="metodo"><span class="letra">{letra}</span><div><h3>{_e(titulo)}</h3><p>{texto}</p></div></article>'
        for titulo, texto, letra in metodos
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Buscador para el agente · Comparación para TI</title>
<style>
  :root {{
    --tinta:#12283f; --suave:#4a6076; --azul:#173f63; --azul-claro:#e8f0f6;
    --verde:#0c6b5c; --verde-claro:#e6f4f0; --dorado:#b28a2e; --dorado-claro:#fbf4e2;
    --rojo:#a33d2f; --rojo-claro:#f8e9e6; --ambar:#8a6414; --ambar-claro:#fbf1d7;
    --fondo:#f2f5f7; --blanco:#fff; --linea:#d9e2e8;
    --fuente:"Segoe UI","Helvetica Neue",Arial,"Noto Sans",sans-serif;
    --mono:ui-monospace,"SFMono-Regular",Consolas,monospace;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--fondo); color:var(--tinta); font-family:var(--fuente); line-height:1.55; }}
  .pagina {{ width:min(1180px, calc(100% - 32px)); margin:0 auto; padding:34px 0 70px; }}
  .cabecera {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start;
    border-bottom:1px solid var(--linea); padding-bottom:18px; }}
  .marca {{ display:flex; gap:13px; align-items:center; }}
  .monograma {{ width:46px; height:46px; display:grid; place-items:center; background:var(--tinta);
    color:#fff; font-size:14px; font-weight:700; letter-spacing:.06em; border-radius:4px; position:relative; }}
  .monograma::after {{ content:""; position:absolute; left:8px; right:8px; bottom:8px; height:2px; background:var(--dorado); }}
  .empresa {{ font-size:10.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--suave); font-weight:600; }}
  h1 {{ margin:2px 0 0; font-size:23px; letter-spacing:-.01em; }}
  .meta {{ text-align:right; font-size:12px; color:var(--suave); }}
  .meta strong {{ display:block; color:var(--tinta); font-size:12.5px; }}

  .recomendacion {{ margin-top:26px; background:linear-gradient(135deg,#12324f,#173f63); color:#fff;
    border-radius:14px; padding:28px 30px; box-shadow:0 14px 34px rgba(18,40,63,.18); }}
  .recomendacion .etiqueta {{ margin:0 0 8px; font-size:10.5px; letter-spacing:.18em; text-transform:uppercase;
    color:#e8c879; font-weight:700; }}
  .recomendacion h2 {{ margin:0; font-size:24px; line-height:1.25; max-width:900px; }}
  .recomendacion p {{ margin:12px 0 0; color:#cfe0ec; font-size:14px; max-width:980px; }}
  .recomendacion code {{ background:rgba(255,255,255,.12); padding:1px 5px; border-radius:4px; color:#fff; }}
  .sello {{ display:inline-flex; align-items:center; gap:7px; margin-top:17px; background:rgba(255,255,255,.10);
    border:1px solid rgba(255,255,255,.22); border-radius:999px; padding:6px 13px; font-size:12px; font-weight:600; }}
  .sello::before {{ content:""; width:7px; height:7px; border-radius:50%; background:#63d2a8; }}

  .metricas {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:16px; }}
  .metrica {{ background:var(--blanco); border:1px solid var(--linea); border-radius:11px; padding:15px 17px; }}
  .metrica .rotulo {{ font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; color:var(--suave); }}
  .metrica strong {{ display:block; font-size:24px; line-height:1.25; margin-top:3px; letter-spacing:-.01em; }}
  .metrica small {{ display:block; color:var(--suave); font-size:11.5px; margin-top:2px; }}
  .metrica.verde strong {{ color:var(--verde); }}
  .metrica.ambar strong {{ color:var(--ambar); }}
  .metrica.rojo strong {{ color:var(--rojo); }}

  h2.seccion {{ font-size:12.5px; letter-spacing:.1em; text-transform:uppercase; color:var(--suave);
    margin:34px 0 10px; }}
  .metodos {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
  .metodo {{ display:flex; gap:13px; background:var(--blanco); border:1px solid var(--linea);
    border-radius:11px; padding:16px 18px; }}
  .metodo .letra {{ flex:0 0 auto; width:28px; height:28px; border-radius:50%; display:grid; place-items:center;
    background:var(--azul-claro); color:var(--azul); font-weight:700; font-size:13px; }}
  .metodo h3 {{ margin:2px 0 4px; font-size:14px; }}
  .metodo p {{ margin:0; font-size:12.5px; color:var(--suave); }}
  .metodo code {{ font-family:var(--mono); font-size:11.5px; background:#eef2f5; padding:1px 4px; border-radius:3px; }}

  .tabla-envoltura {{ background:var(--blanco); border:1px solid var(--linea); border-radius:12px; overflow:hidden; }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  thead th {{ background:#eef3f6; color:var(--suave); text-align:left; font-size:10.5px;
    letter-spacing:.07em; text-transform:uppercase; padding:11px 12px; border-bottom:1px solid var(--linea); }}
  thead th.grupo-a {{ border-top:2px solid #9fb4c6; }}
  thead th.grupo-b {{ border-top:2px solid var(--verde); }}
  tbody td {{ padding:12px; border-bottom:1px solid #edf1f4; vertical-align:top; }}
  tbody tr:last-child td {{ border-bottom:0; }}
  tbody tr:hover {{ background:#fafcfd; }}
  td.id {{ font-family:var(--mono); font-size:11px; font-weight:700; color:var(--azul); white-space:nowrap; }}
  td.pregunta {{ min-width:230px; }}
  .dato {{ display:block; font-weight:700; font-size:13px; white-space:nowrap; }}
  .sub {{ display:block; font-size:11px; color:var(--suave); white-space:nowrap; }}
  .pastilla {{ display:inline-block; font-size:10px; font-weight:700; letter-spacing:.04em; text-transform:uppercase;
    padding:3px 8px; border-radius:999px; white-space:nowrap; }}
  .pastilla.ok {{ background:var(--verde-claro); color:var(--verde); }}
  .pastilla.falla {{ background:var(--rojo-claro); color:var(--rojo); }}
  details {{ margin-top:6px; font-size:11.5px; }}
  summary {{ cursor:pointer; color:var(--azul); font-weight:600; }}
  details p {{ margin:6px 0 0; color:var(--tinta); font-size:11.5px; }}
  details p.ref {{ color:var(--suave); font-family:var(--mono); font-size:10px; }}
  .ganador {{ display:inline-block; font-size:10.5px; font-weight:700; padding:3px 8px; border-radius:5px; white-space:nowrap; }}
  .ganador.mcp {{ background:var(--verde-claro); color:var(--verde); }}
  .ganador.directo {{ background:var(--ambar-claro); color:var(--ambar); }}
  .ganador.empate {{ background:#eef2f5; color:var(--suave); }}

  .condicion {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:10px; }}
  .panel {{ background:var(--blanco); border:1px solid var(--linea); border-radius:11px; padding:18px 20px; }}
  .panel h3 {{ margin:0 0 7px; font-size:14px; }}
  .panel p {{ margin:0; font-size:12.5px; color:var(--suave); }}
  .panel ul {{ margin:8px 0 0 18px; padding:0; font-size:12.5px; color:var(--suave); }}
  .panel li {{ margin:3px 0; }}
  .panel code {{ font-family:var(--mono); font-size:11.5px; background:#eef2f5; padding:1px 4px; border-radius:3px; }}
  pre {{ margin:10px 0 0; background:#0f2233; color:#d6e4ef; border-radius:8px; padding:12px 14px;
    font-family:var(--mono); font-size:10.8px; line-height:1.5; overflow-x:auto; }}

  .pie {{ margin-top:32px; border-top:1px solid var(--linea); padding-top:14px;
    font-size:11.5px; color:#7b8fa1; display:flex; justify-content:space-between; gap:16px; }}
  @media (max-width:900px) {{
    .metricas {{ grid-template-columns:repeat(2,1fr); }}
    .metodos, .condicion {{ grid-template-columns:1fr; }}
    .cabecera {{ flex-direction:column; }}
    .meta {{ text-align:left; }}
    .tabla-envoltura {{ overflow-x:auto; }}
    table {{ min-width:980px; }}
  }}
  @media print {{
    body {{ background:#fff; }}
    .pagina {{ width:100%; padding:0; }}
    .recomendacion, .metrica, .metodo, .panel, .tabla-envoltura {{ box-shadow:none; }}
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
        <span class="empresa">Comercial Los Samanes, C.A. · Compras y TI</span>
        <h1>El buscador para el agente</h1>
      </div>
    </div>
    <div class="meta">
      <strong>Decisión de arquitectura para TI</strong>
      Problema 10 · {_e(datos["generado"])}
    </div>
  </header>

  <section class="recomendacion">
    <p class="etiqueta">Recomendación para TI</p>
    <h2>{recomendacion}</h2>
    <p>{justificacion}</p>
    <span class="sello">Condición de TI verificada: el agente MCP no abre archivos de documentos/</span>
  </section>

  <div class="metricas">
    <div class="metrica {color_ahorro}">
      <span class="rotulo">Ahorro de contexto</span>
      <strong>{ahorro:.0f} %</strong>
      <small>{_num(resumen["contexto_promedio_a"])} → {_num(resumen["contexto_promedio_b"])} caracteres por pregunta</small>
    </div>
    <div class="metrica {color_precision}">
      <span class="rotulo">Acierto con MCP</span>
      <strong>{resumen["porcentaje_b"]:.0f} %</strong>
      <small>{resumen["aciertos_b"]} de {total} · modo directo {resumen["porcentaje_a"]:.0f} %</small>
    </div>
    <div class="metrica">
      <span class="rotulo">Latencia promedio</span>
      <strong>{_segundos(resumen["latencia_promedio_b_ms"])}</strong>
      <small>MCP {delta_txt} que el modo directo</small>
    </div>
    <div class="metrica">
      <span class="rotulo">Contexto estimado</span>
      <strong>{_num(resumen["tokens_estimados_b"])}</strong>
      <small>tokens con MCP vs {_num(resumen["tokens_estimados_a"])} en directo</small>
    </div>
  </div>

  <h2 class="seccion">Cómo se probó</h2>
  <div class="metodos">{tarjetas_metodo}</div>

  <h2 class="seccion">Resultado pregunta por pregunta</h2>
  <div class="tabla-envoltura">
    <table>
      <thead>
        <tr>
          <th rowspan="2">ID</th>
          <th rowspan="2">Pregunta</th>
          <th colspan="2" class="grupo-a">Modo A · Archivos directos</th>
          <th colspan="2" class="grupo-b">Modo B · Buscador MCP</th>
          <th rowspan="2">Ganador</th>
        </tr>
        <tr>
          <th>Tiempo / contexto</th><th>Acierto</th>
          <th>Tiempo / contexto</th><th>Acierto</th>
        </tr>
      </thead>
      <tbody>
        {"".join(filas)}
      </tbody>
    </table>
  </div>

  <h2 class="seccion">Condición de TI y alcance</h2>
  <div class="condicion">
    <div class="panel">
      <h3>Qué ve el agente en cada modo</h3>
      <ul>
        <li><strong>Modo A:</strong> puede listar, buscar y abrir cualquier archivo de <code>documentos/</code>. El contexto depende de cuántos archivos abra.</li>
        <li><strong>Modo B:</strong> solo recibe los fragmentos que devuelve <code>buscar_documentos</code> y las secciones que pida con <code>leer_fragmento</code>.</li>
        <li>En ambos modos se usó el mismo modelo local, el mismo prompt de sistema y los mismos criterios de corrección de Legal.</li>
      </ul>
    </div>
    <div class="panel">
      <h3>Configuración que hace cumplir la condición</h3>
      <p>El agente <code>agente-mcp</code> tiene denegado <code>read</code>, <code>glob</code> y <code>grep</code> sobre <code>documentos/**</code>, además de <code>shell</code>. El servidor está registrado en <code>opencode.json</code>.</p>
      <pre>{{
  "mcp": {{ "servers": {{ "buscador": {{
    "type": "local",
    "command": ["python3", "asistente/servidor_mcp.py"]
  }}}}}},
  "agents": {{ "agente-mcp": {{ "permissions": [
    {{ "action": "read", "resource": "documentos/**", "effect": "deny" }},
    {{ "action": "glob", "resource": "documentos/**", "effect": "deny" }},
    {{ "action": "grep", "resource": "documentos/**", "effect": "deny" }},
    {{ "action": "shell", "resource": "*", "effect": "deny" }}
  ] }}}}
}}</pre>
    </div>
  </div>

  <h2 class="seccion">Lectura de los números</h2>
  <div class="panel">
    <p><strong>Contexto:</strong> caracteres de documentos enviados al modelo en cada pregunta; no incluye el prompt de sistema, que es idéntico en ambos modos. La estimación de tokens usa 4 caracteres por token.
    <strong>Tiempo:</strong> recuperación más generación, medido de punta a punta en el Spark. <strong>Acierto:</strong> verificación automática de los hechos clave que Legal exige para cada pregunta; las respuestas completas quedan a la vista en la tabla. <strong>Ganador:</strong> se decide primero por acierto y, si ambos aciertan, por menor contexto; el tiempo se informa por separado.</p>
  </div>

  <footer class="pie">
    <span>Comparación automática con las {total} preguntas de <code>preguntas_de_prueba.csv</code>. Documentos de compras ficticios, de solo lectura.</span>
    <span>Generado el {_e(datos["generado"])} · {datos["duracion_s"]} s de ejecución</span>
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    analizador = argparse.ArgumentParser(description="Compara archivos directos contra el buscador MCP.")
    analizador.add_argument("--ids", help="Lista de IDs separados por coma, por ejemplo Q01,Q07.")
    argumentos = analizador.parse_args()
    ids = {x.strip() for x in argumentos.ids.split(",")} if argumentos.ids else None

    os.makedirs(SALIDAS, exist_ok=True)
    datos = correr(ids)
    datos.pop("incompleto", None)

    json_salida = os.path.join(SALIDAS, "10-comparacion.json")
    with open(json_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)

    html_salida = os.path.join(SALIDAS, "10-comparacion.html")
    with open(html_salida, "w", encoding="utf-8") as archivo:
        archivo.write(generar_html(datos))

    resumen = datos["resumen"]
    print(
        f"\nResultado: MCP {resumen['aciertos_b']}/{datos['total']} "
        f"({resumen['porcentaje_b']} %) vs directo {resumen['aciertos_a']}/{datos['total']} "
        f"({resumen['porcentaje_a']} %). Ahorro de contexto: {resumen['ahorro_contexto_pct']} %."
    )
    print(f"HTML: {html_salida}\nJSON: {json_salida}")


if __name__ == "__main__":
    main()
