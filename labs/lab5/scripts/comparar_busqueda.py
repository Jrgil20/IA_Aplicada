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
import hashlib
import html
import json
import math
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
CONDICION = os.path.join(SALIDAS, "10-condicion-ti.json")

if ASISTENTE not in sys.path:
    sys.path.insert(0, ASISTENTE)

from busqueda import Fragmento, Indice, normalizar, tokenizar  # noqa: E402
from evaluar import CRITERIOS, RESPUESTAS_ESPERADAS, evaluar_respuesta  # noqa: E402
from llm import SISTEMA, construir_contexto, redactar, sanitizar_texto  # noqa: E402

LIMITE_MCP = 5
TOPE_CONTEXTO_DIRECTO = 40000  # caracteres de documentos que "lee" el agente
MAX_DOCS_DIRECTO = 6
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

def _fragmento_desde_documento(documento) -> Fragmento:
    """Convierte un documento completo en un fragmento citable."""
    return Fragmento(
        fragmento_id=documento.doc_id,
        doc_id=documento.doc_id,
        titulo=documento.titulo,
        tipo=documento.tipo,
        clase=documento.clase,
        proveedor=documento.proveedor,
        fecha=documento.fecha,
        vigente_desde=documento.vigente_desde,
        estado=documento.estado,
        seccion="Documento completo",
        texto=documento.texto,
        ruta=documento.ruta,
    )


def _fragmento_desde_mcp(datos: dict) -> Fragmento:
    """Convierte la respuesta de la herramienta MCP en un fragmento citable."""
    return Fragmento(
        fragmento_id=f"{datos.get('id', '')}#{datos.get('seccion', '')}",
        doc_id=datos.get("id", ""),
        titulo=datos.get("titulo", ""),
        tipo=datos.get("tipo", ""),
        clase="",
        proveedor=datos.get("proveedor", ""),
        fecha=datos.get("fecha", ""),
        vigente_desde="",
        estado=datos.get("estado", ""),
        seccion=datos.get("seccion", ""),
        texto=datos.get("texto", ""),
        ruta="",
    )


def _contexto_total(pregunta: str, contexto_documentos: str) -> int:
    """Caracteres exactos del mensaje enviado al modelo, incluido el sistema."""
    envoltorio = (
        "FRAGMENTOS DOCUMENTALES:\n\n"
        "<untrusted_document_context>\n"
        f"{contexto_documentos}\n"
        "</untrusted_document_context>\n\n"
        "<user_query>\n"
        f"{sanitizar_texto(pregunta)}\n"
        "</user_query>\n\n"
        "Responde con la información de los fragmentos y cita cada afirmación."
    )
    return len(SISTEMA) + len(envoltorio)


def responder(fragmentos: list[Fragmento], pregunta: str) -> dict:
    """Usa el mismo pipeline endurecido del asistente en ambos modos."""
    contexto = construir_contexto(fragmentos)
    inicio = time.monotonic()
    salida = redactar(pregunta, fragmentos)
    ms = int((time.monotonic() - inicio) * 1000)
    salida["contexto_documentos"] = len(contexto)
    salida["contexto_total"] = _contexto_total(pregunta, contexto)
    salida["ms_modelo"] = ms
    return salida


# ---------------------------------------------------------------------------
# Modo A: el agente busca y abre archivos por su cuenta
# ---------------------------------------------------------------------------

class ExploradorDirecto:
    """Simula `grep` por el término más específico y lectura de archivos.

    No usa el índice BM25: reproduce lo que haría un agente que busca
    coincidencias literales y luego abre los archivos candidatos completos.
    """

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
        self._postings: dict[str, set[str]] = {}
        for doc_id, tokens in self._tokens.items():
            for token in tokens:
                self._postings.setdefault(token, set()).add(doc_id)
        self._proveedor_doc = {
            documento.doc_id: Indice._proveedor_detectado(tokenizar(documento.proveedor))
            for documento in indice.documentos
        }

    def _idf(self, token: str) -> float:
        df = len(self._postings.get(token, ()))
        total = len(self.indice.documentos)
        if not df:
            return 0.0
        return math.log(1 + (total - df + 0.5) / (df + 0.5))

    def seleccionar(self, pregunta: str):
        tokens_unicos = sorted(set(tokenizar(pregunta)))
        if not tokens_unicos:
            return []

        proveedor = self.indice._proveedor_detectado(tokens_unicos)
        pregunta_normal = normalizar(pregunta)
        menciona_historia = bool(
            re.search(
                r"\b(2024|2025|anterior(?:es)?|antes|historic[oa]s?|reemplazad[oa]s?|"
                r"derogad[oa]s?|viej[oa]s?|antigu[oa]s?)\b",
                pregunta_normal,
            )
        )

        # `grep` encuentra los archivos que contienen los términos. El agente
        # los ordena por especificidad (IDF) y por coincidencia en el título, y
        # abre los primeros. No se usa el índice BM25 del buscador MCP.
        ranking = []
        for documento in self.indice.documentos:
            if not menciona_historia and "reemplazad" in normalizar(documento.estado):
                continue
            tokens_doc = self._tokens[documento.doc_id]
            titulo_tokens = self._titulos[documento.doc_id]
            puntos = sum(self._idf(token) for token in tokens_unicos if token in tokens_doc)
            puntos += 2.0 * sum(
                self._idf(token) for token in tokens_unicos if token in titulo_tokens
            )
            if proveedor and self._proveedor_doc.get(documento.doc_id) == proveedor:
                puntos += 3.0
            if puntos > 0:
                ranking.append((puntos, documento))

        ranking.sort(key=lambda par: (-par[0], par[1].doc_id))
        elegidos = []
        usados = 0
        for _puntos, documento in ranking:
            if len(elegidos) >= MAX_DOCS_DIRECTO or usados >= TOPE_CONTEXTO_DIRECTO:
                break
            largo = len(documento.texto)
            if elegidos and usados + largo > TOPE_CONTEXTO_DIRECTO:
                continue
            elegidos.append(documento)
            usados += largo
        return elegidos

    def ejecutar(self, pregunta: str) -> dict:
        inicio = time.monotonic()
        documentos = self.seleccionar(pregunta)
        fragmentos = [_fragmento_desde_documento(documento) for documento in documentos]
        ms_recuperacion = int((time.monotonic() - inicio) * 1000)
        salida = responder(fragmentos, pregunta)
        return {
            "respuesta": salida["respuesta"],
            "fuentes": salida.get("fuentes", []),
            "negativa": salida.get("negativa", False),
            "documentos": [documento.doc_id for documento in documentos],
            "rutas": [documento.ruta for documento in documentos],
            "fragmentos": len(fragmentos),
            "contexto_documentos": salida["contexto_documentos"],
            "contexto_total": salida["contexto_total"],
            "ms_recuperacion": ms_recuperacion,
            "ms_modelo": salida["ms_modelo"],
            "ms_total": int((time.monotonic() - inicio) * 1000),
            "herramientas": ["grep", "read"],
        }


# ---------------------------------------------------------------------------
# Modo B: el agente solo ve los documentos a través del MCP
# ---------------------------------------------------------------------------

def ejecutar_mcp(cliente: ClienteMCP, pregunta: str) -> dict:
    inicio = time.monotonic()
    datos = cliente.llamar(
        "buscar_documentos", {"consulta": pregunta, "limite": LIMITE_MCP}
    )
    ms_busqueda = int((time.monotonic() - inicio) * 1000)
    fragmentos = [_fragmento_desde_mcp(f) for f in datos]
    ms_recuperacion = int((time.monotonic() - inicio) * 1000)
    salida = responder(fragmentos, pregunta)
    return {
        "respuesta": salida["respuesta"],
        "fuentes": salida.get("fuentes", []),
        "negativa": salida.get("negativa", False),
        "documentos": [f["id"] for f in datos],
        "secciones": [f["seccion"] for f in datos],
        "fragmentos": len(fragmentos),
        "contexto_documentos": salida["contexto_documentos"],
        "contexto_total": salida["contexto_total"],
        "ms_busqueda": ms_busqueda,
        "ms_recuperacion": ms_recuperacion,
        "ms_modelo": salida["ms_modelo"],
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
            correcta_a, detalle_a = evaluar_respuesta(
                qid, modo_a["respuesta"], modo_a.get("fuentes")
            )
            modo_a["correcta"] = correcta_a
            modo_a["detalle"] = detalle_a

            print("  Modo B (buscador MCP)…", flush=True)
            modo_b = ejecutar_mcp(cliente, pregunta)
            correcta_b, detalle_b = evaluar_respuesta(
                qid, modo_b["respuesta"], modo_b.get("fuentes")
            )
            modo_b["correcta"] = correcta_b
            modo_b["detalle"] = detalle_b

            if correcta_a != correcta_b:
                ganador = "mcp" if correcta_b else "directo"
            elif modo_a["contexto_total"] == modo_b["contexto_total"]:
                ganador = "empate"
            elif modo_b["contexto_total"] < modo_a["contexto_total"]:
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
                f"  A: {'OK' if correcta_a else 'FALLA'} {modo_a['contexto_total']:,} car total "
                f"({modo_a['contexto_documentos']:,} docs) · {modo_a['ms_total']/1000:.1f} s | "
                f"B: {'OK' if correcta_b else 'FALLA'} {modo_b['contexto_total']:,} car total "
                f"({modo_b['contexto_documentos']:,} docs) · {modo_b['ms_total']/1000:.1f} s",
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
    contexto_doc_a = _promedio(r["modo_a"]["contexto_documentos"] for r in resultados)
    contexto_doc_b = _promedio(r["modo_b"]["contexto_documentos"] for r in resultados)
    contexto_a = _promedio(r["modo_a"]["contexto_total"] for r in resultados)
    contexto_b = _promedio(r["modo_b"]["contexto_total"] for r in resultados)
    latencia_a = _promedio(r["modo_a"]["ms_total"] for r in resultados)
    latencia_b = _promedio(r["modo_b"]["ms_total"] for r in resultados)
    ahorro_doc = (
        ((contexto_doc_a - contexto_doc_b) / contexto_doc_a * 100) if contexto_doc_a else 0.0
    )
    ahorro_total = ((contexto_a - contexto_b) / contexto_a * 100) if contexto_a else 0.0
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
        "max_docs_directo": MAX_DOCS_DIRECTO,
        "prompt_sistema_caracteres": len(SISTEMA),
        "total": total,
        "codigo": _huellas(),
        "resumen": {
            "total": total,
            "aciertos_a": aciertos_a,
            "aciertos_b": aciertos_b,
            "porcentaje_a": round(100 * aciertos_a / total, 1) if total else 0,
            "porcentaje_b": round(100 * aciertos_b / total, 1) if total else 0,
            "contexto_documental_promedio_a": round(contexto_doc_a),
            "contexto_documental_promedio_b": round(contexto_doc_b),
            "contexto_promedio_a": round(contexto_a),
            "contexto_promedio_b": round(contexto_b),
            "ahorro_contexto_documental_pct": round(ahorro_doc, 1),
            "ahorro_contexto_pct": round(ahorro_total, 1),
            "latencia_promedio_a_ms": round(latencia_a),
            "latencia_promedio_b_ms": round(latencia_b),
            "delta_latencia_pct": round(delta_latencia, 1),
            "tokens_estimados_a": round(contexto_a / 4),
            "tokens_estimados_b": round(contexto_b / 4),
        },
        "resultados": resultados,
    }


def _huellas() -> dict:
    """Hash corto de los archivos que determinan el resultado."""
    rutas = {
        "opencode": os.path.join(RAIZ, "opencode.json"),
        "servidor_mcp": os.path.join(ASISTENTE, "servidor_mcp.py"),
        "busqueda": os.path.join(ASISTENTE, "busqueda.py"),
        "evaluar": os.path.join(ASISTENTE, "evaluar.py"),
        "llm": os.path.join(ASISTENTE, "llm.py"),
        "comparador": os.path.abspath(__file__),
    }
    huellas = {}
    for nombre, ruta in rutas.items():
        try:
            with open(ruta, "rb") as archivo:
                huellas[nombre] = hashlib.sha256(archivo.read()).hexdigest()[:12]
        except OSError:
            huellas[nombre] = "no-disponible"
    return huellas


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


def _estado_condicion() -> tuple[str, str]:
    """Lee el resultado de las pruebas de la condición de TI, si existen."""
    try:
        with open(CONDICION, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return (
            "pendiente",
            "Pruebas de condición pendientes: ejecutar "
            "<code>python3 scripts/probar_condicion_ti.py</code>.",
        )
    if datos.get("aprobado"):
        return (
            "ok",
            f"Pruebas ejecutadas: {datos.get('aprobados', 0)}/{datos.get('total', 0)} "
            "aprobadas. Ninguna herramienta ajena al buscador se completó.",
        )
    return (
        "falla",
        f"Pruebas ejecutadas: {datos.get('aprobados', 0)}/{datos.get('total', 0)} "
        "aprobadas. Revisar <code>salidas/10-condicion-ti.json</code>.",
    )


def _recomendacion(resumen: dict) -> tuple[str, str]:
    ahorro = resumen["ahorro_contexto_pct"]
    ahorro_doc = resumen["ahorro_contexto_documental_pct"]
    base = (
        f"Adoptar el buscador MCP como única vía de acceso del agente a "
        f"<code>documentos/</code>. Reduce el contexto total enviado al modelo "
        f"(documentos + sistema + pregunta) en {ahorro:.0f} % —el contexto "
        f"documental baja {ahorro_doc:.0f} %— y mantiene "
        f"{resumen['aciertos_b']} de {resumen['total']} respuestas correctas."
    )
    if resumen["porcentaje_b"] < resumen["porcentaje_a"]:
        base = (
            "Mantener el acceso directo mientras se corrige la recuperación del buscador MCP: "
            f"en esta corrida el modo directo acertó {resumen['porcentaje_a']:.0f} % y el MCP "
            f"{resumen['porcentaje_b']:.0f} %, aunque el MCP usó {ahorro:.0f} % menos contexto total."
        )
    detalle = (
        "El ahorro de contexto es la diferencia decisiva: el modo directo abre archivos "
        "completos y deja menos espacio para el razonamiento; el buscador entrega solo los "
        "fragmentos pertinentes, con documento y sección, y permite auditar qué ve el modelo. "
        "La condición de TI se cumple con una lista blanca: el agente MCP solo tiene las "
        "herramientas <code>buscar_documentos</code> y <code>leer_fragmento</code>; no puede "
        "usar <code>read</code>, <code>glob</code>, <code>grep</code>, <code>shell</code>, "
        "<code>subagent</code>, <code>webfetch</code> ni <code>websearch</code>."
    )
    return base, detalle


def generar_html(datos: dict) -> str:
    resumen = datos["resumen"]
    recomendacion, justificacion = _recomendacion(resumen)
    total = datos["total"]
    ahorro = resumen["ahorro_contexto_pct"]
    ahorro_doc = resumen["ahorro_contexto_documental_pct"]
    delta = resumen["delta_latencia_pct"]
    delta_txt = (
        f"{abs(delta):.0f} % más rápida" if delta < 0 else f"{abs(delta):.0f} % más lenta"
    )
    color_ahorro = "verde" if ahorro >= 40 else ("ambar" if ahorro >= 15 else "rojo")
    color_precision = (
        "verde" if resumen["porcentaje_b"] >= 90
        else ("ambar" if resumen["porcentaje_b"] >= 70 else "rojo")
    )
    estado_cond, texto_cond = _estado_condicion()
    sello = (
        "Condición de TI verificada: el agente MCP solo puede usar las dos herramientas del buscador"
        if estado_cond == "ok"
        else "Condición de TI configurada; pruebas del agente pendientes"
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
            f'<span class="sub">{_num(a["contexto_total"])} car total · '
            f'{_num(a["contexto_documentos"])} de documentos</span></td>'
            f'<td><span class="pastilla {estado_a}">{"Correcta" if a["correcta"] else "Incorrecta"}</span>'
            f'<details><summary>Ver respuesta</summary><p>{_e(a["respuesta"])}</p>'
            f'<p class="ref">Documentos: {_e(", ".join(a["documentos"]))}</p></details></td>'
            f'<td><span class="dato">{_segundos(b["ms_total"])}</span>'
            f'<span class="sub">{_num(b["contexto_total"])} car total · '
            f'{_num(b["contexto_documentos"])} de documentos</span></td>'
            f'<td><span class="pastilla {estado_b}">{"Correcta" if b["correcta"] else "Incorrecta"}</span>'
            f'<details><summary>Ver respuesta</summary><p>{_e(b["respuesta"])}</p>'
            f'<p class="ref">Fragmentos: {_e(" · ".join(b["documentos"]))}</p></details></td>'
            f'<td><span class="ganador {clase_ganador}">{_e(ganador)}</span></td>'
            "</tr>"
        )

    metodos = [
        ("Modo A · Archivos directos", f"El agente simula <code>grep</code> por el término más específico y abre hasta {MAX_DOCS_DIRECTO} archivos completos de <code>documentos/</code>.", "A"),
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
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'">
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
  .condicion-estado {{ margin:9px 0 0; padding:8px 10px; border-radius:7px; font-size:12px; font-weight:650; }}
  .condicion-estado.ok {{ background:var(--verde-claro); color:var(--verde); }}
  .condicion-estado.falla {{ background:var(--rojo-claro); color:var(--rojo); }}
  .condicion-estado.pendiente {{ background:var(--ambar-claro); color:var(--ambar); }}
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
    <span class="sello">{sello}</span>
  </section>

  <div class="metricas">
    <div class="metrica {color_ahorro}">
      <span class="rotulo">Ahorro de contexto total</span>
      <strong>{ahorro:.0f} %</strong>
      <small>documental {ahorro_doc:.0f} % · {_num(resumen["contexto_promedio_a"])} → {_num(resumen["contexto_promedio_b"])} caracteres por pregunta</small>
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
      <small>tokens totales con MCP vs {_num(resumen["tokens_estimados_a"])} en directo</small>
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
        <li><strong>Modo A:</strong> simula <code>grep</code> por el término más específico y abre hasta {datos["max_docs_directo"]} archivos completos de <code>documentos/</code>.</li>
        <li><strong>Modo B:</strong> solo recibe los fragmentos que devuelve <code>buscar_documentos</code> y las secciones que pida con <code>leer_fragmento</code>.</li>
        <li>En ambos modos se usó el mismo modelo local, el mismo prompt de sistema, la misma validación de citas y los mismos criterios de corrección de Legal.</li>
      </ul>
    </div>
    <div class="panel">
      <h3>Configuración que hace cumplir la condición</h3>
      <p>El agente <code>agente-mcp</code> tiene una lista blanca: solo las herramientas <code>buscador_buscar_documentos</code> y <code>buscador_leer_fragmento</code>. Todo lo demás está denegado, incluidos <code>read</code>, <code>glob</code>, <code>grep</code>, <code>shell</code>, <code>subagent</code>, <code>webfetch</code> y <code>websearch</code>. El servidor está registrado en <code>opencode.json</code>.</p>
      <p class="condicion-estado {estado_cond}">{texto_cond}</p>
      <pre>{{
  "mcp": {{ "servers": {{ "buscador": {{
    "type": "local",
    "command": ["python3", "asistente/servidor_mcp.py"],
    "cwd": ".",
    "codemode": false
  }}}}}},
  "agents": {{ "agente-mcp": {{ "permissions": [
    {{ "action": "*", "resource": "*", "effect": "deny" }},
    {{ "action": "buscador_buscar_documentos", "resource": "*", "effect": "allow" }},
    {{ "action": "buscador_leer_fragmento", "resource": "*", "effect": "allow" }}
  ] }}}}
}}</pre>
    </div>
  </div>

  <h2 class="seccion">Lectura de los números</h2>
  <div class="panel">
    <p><strong>Contexto total:</strong> caracteres del mensaje completo que recibe el modelo en cada pregunta: prompt de sistema, documentos, pregunta y delimitadores. <strong>Contexto documental:</strong> solo los documentos; se informa aparte porque es la parte que cambia entre modos. La estimación de tokens usa 4 caracteres por token.
    <strong>Tiempo:</strong> recuperación, redacción y validación de citas, medido de punta a punta en el Spark. <strong>Acierto:</strong> verificación automática de los hechos clave que Legal exige para cada pregunta, con la misma validación de citas del asistente; las respuestas completas quedan a la vista en la tabla y Legal debe revisarlas. <strong>Ganador:</strong> se decide primero por acierto y, si ambos aciertan, por menor contexto total; el tiempo se informa por separado.</p>
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
        f"({resumen['porcentaje_a']} %). Ahorro de contexto total: "
        f"{resumen['ahorro_contexto_pct']} % (documental "
        f"{resumen['ahorro_contexto_documental_pct']} %)."
    )
    print(f"HTML: {html_salida}\nJSON: {json_salida}")


if __name__ == "__main__":
    main()
