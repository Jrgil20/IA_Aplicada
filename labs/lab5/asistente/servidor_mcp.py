#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Buscador documental del Asistente de Compras expuesto como servidor MCP.

Implementa el transporte stdio y el protocolo JSON-RPC 2.0 (estilo del
servidor ERP del lab 2). Reutiliza el índice BM25 de ``busqueda.py`` para que
el agente consulte los documentos sin abrir los archivos de ``documentos/``.

Solo usa la biblioteca estándar de Python 3.

Herramientas:
    buscar_documentos(consulta, limite=5)
    leer_fragmento(documento_id, seccion)

Prueba rápida:
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \\
        | python3 asistente/servidor_mcp.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from busqueda import Indice, normalizar  # noqa: E402

DOCUMENTOS = os.path.normpath(os.path.join(BASE, "..", "documentos"))
VERSION_PROTOCOLO = "2025-06-18"
NOMBRE_SERVIDOR = "buscador-compras"
VERSION_SERVIDOR = "1.0"

INSTRUCCIONES = (
    "Buscador de los documentos de compras de Comercial Los Samanes. "
    "Usa buscar_documentos para localizar cláusulas, políticas, actas y "
    "correos, y leer_fragmento para recuperar una sección completa. Cita "
    "siempre el documento y la sección que devuelve la herramienta."
)


# ---------------------------------------------------------------------------
# Índice documental
# ---------------------------------------------------------------------------

_indice: Indice | None = None
_indice_error: str = ""


def indice() -> Indice:
    """Carga el índice una sola vez, al arrancar el servidor."""
    global _indice, _indice_error
    if _indice is None:
        try:
            _indice = Indice(DOCUMENTOS)
            _indice_error = ""
        except Exception as error:  # se informa por la herramienta, no por stdout
            _indice_error = f"No se pudo cargar el índice documental: {error}"
            raise
    return _indice


def _cita(doc_id: str, seccion: str) -> str:
    return f"[DOC: {doc_id} · {seccion}]"


def buscar_documentos(args: dict) -> list[dict]:
    consulta = str(args.get("consulta") or "").strip()
    if not consulta:
        raise ValueError("El parámetro 'consulta' es obligatorio.")
    try:
        limite = int(args.get("limite", 5))
    except (TypeError, ValueError):
        raise ValueError("El parámetro 'limite' debe ser un número entero.")
    limite = max(1, min(limite, 20))

    resultados = indice().buscar(consulta, limite)
    salida = []
    for fragmento in resultados:
        salida.append(
            {
                "id": fragmento.doc_id,
                "titulo": fragmento.titulo,
                "tipo": fragmento.tipo,
                "proveedor": fragmento.proveedor,
                "fecha": fragmento.fecha,
                "estado": fragmento.estado,
                "seccion": fragmento.seccion,
                "score": fragmento.puntaje,
                "texto": fragmento.texto,
                "cita": _cita(fragmento.doc_id, fragmento.seccion),
            }
        )
    return salida


def leer_fragmento(args: dict) -> dict:
    doc_id = str(args.get("documento_id") or "").strip()
    seccion = str(args.get("seccion") or "").strip()
    if not doc_id:
        raise ValueError("El parámetro 'documento_id' es obligatorio.")
    if not seccion:
        raise ValueError("El parámetro 'seccion' es obligatorio.")

    documento = indice().documento(doc_id)
    if documento is None:
        # Se tolera una diferencia de mayúsculas o de separadores.
        buscado = normalizar(doc_id).replace(" ", "")
        for candidato in indice().documentos:
            if normalizar(candidato.doc_id).replace(" ", "") == buscado:
                documento = candidato
                break

    fragmentos = [
        f
        for f in indice().fragmentos
        if normalizar(f.doc_id) == normalizar(documento.doc_id if documento else doc_id)
    ]
    if not fragmentos:
        raise ValueError(f"No existe el documento '{doc_id}' en la base de compras.")

    seccion_normal = normalizar(seccion)
    coincidencias = [
        f
        for f in fragmentos
        if seccion_normal == normalizar(f.seccion)
        or seccion_normal in normalizar(f.seccion)
        or normalizar(f.seccion) in seccion_normal
    ]
    if not coincidencias:
        disponibles = sorted({f.seccion for f in fragmentos})
        raise ValueError(
            f"El documento '{documento.doc_id}' no tiene la sección '{seccion}'. "
            "Secciones disponibles: " + "; ".join(disponibles)
        )

    texto = "\n\n".join(f.texto.strip() for f in coincidencias)
    primera = coincidencias[0]
    return {
        "id": primera.doc_id,
        "titulo": primera.titulo,
        "tipo": primera.tipo,
        "proveedor": primera.proveedor,
        "fecha": primera.fecha,
        "estado": primera.estado,
        "seccion": primera.seccion,
        "texto": texto,
        "cita": _cita(primera.doc_id, primera.seccion),
    }


HERRAMIENTAS = {
    "buscar_documentos": {
        "funcion": buscar_documentos,
        "descripcion": (
            "Busca en los 436 documentos de compras (contratos, adendas, "
            "políticas, procedimientos, actas, correos, fichas y listas) y "
            "devuelve los fragmentos más pertinentes con su cita exacta "
            "[DOC: <id> · <sección>]."
        ),
        "propiedades": {
            "consulta": {
                "type": "string",
                "description": "Pregunta o términos de búsqueda en lenguaje natural.",
            },
            "limite": {
                "type": "integer",
                "description": "Cantidad máxima de fragmentos (1 a 20). Por defecto 5.",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
            },
        },
        "requeridos": ["consulta"],
    },
    "leer_fragmento": {
        "funcion": leer_fragmento,
        "descripcion": (
            "Devuelve el texto completo de una sección concreta de un "
            "documento, sin volcar el resto del archivo."
        ),
        "propiedades": {
            "documento_id": {
                "type": "string",
                "description": "Identificador del documento, por ejemplo CT-2025-P04 o PR-COM-03.",
            },
            "seccion": {
                "type": "string",
                "description": "Título de la sección, por ejemplo 'Cláusula 8 · Penalidad por atraso'.",
            },
        },
        "requeridos": ["documento_id", "seccion"],
    },
}


# ---------------------------------------------------------------------------
# Protocolo JSON-RPC / MCP por stdio
# ---------------------------------------------------------------------------

def responder(id_, resultado=None, error=None) -> None:
    mensaje = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        mensaje["error"] = error
    else:
        mensaje["result"] = resultado
    sys.stdout.write(json.dumps(mensaje, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _resultado_texto(datos) -> dict:
    return {
        "content": [
            {"type": "text", "text": json.dumps(datos, ensure_ascii=False, indent=1)}
        ],
        "isError": False,
    }


def atender(mensaje: dict) -> None:
    metodo = mensaje.get("method")
    id_ = mensaje.get("id")
    params = mensaje.get("params") or {}

    # Notificaciones (initialized, cancelled, ...): no llevan respuesta.
    if id_ is None:
        return

    if metodo == "initialize":
        pedida = params.get("protocolVersion") or VERSION_PROTOCOLO
        responder(
            id_,
            {
                "protocolVersion": pedida if pedida in {
                    "2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"
                } else VERSION_PROTOCOLO,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": NOMBRE_SERVIDOR,
                    "version": VERSION_SERVIDOR,
                },
                "instructions": INSTRUCCIONES,
            },
        )
    elif metodo == "ping":
        responder(id_, {})
    elif metodo == "tools/list":
        responder(
            id_,
            {
                "tools": [
                    {
                        "name": nombre,
                        "description": datos["descripcion"],
                        "inputSchema": {
                            "type": "object",
                            "properties": datos["propiedades"],
                            "required": datos["requeridos"],
                            "additionalProperties": False,
                        },
                    }
                    for nombre, datos in HERRAMIENTAS.items()
                ]
            },
        )
    elif metodo == "tools/call":
        nombre = params.get("name")
        if nombre not in HERRAMIENTAS:
            responder(
                id_,
                error={"code": -32602, "message": f"Herramienta desconocida: {nombre}"},
            )
            return
        argumentos = params.get("arguments") or {}
        if not isinstance(argumentos, dict):
            responder(
                id_,
                error={"code": -32602, "message": "Los argumentos deben ser un objeto."},
            )
            return
        try:
            datos = HERRAMIENTAS[nombre]["funcion"](argumentos)
            responder(id_, _resultado_texto(datos))
        except Exception as error:  # el error vuelve al agente como resultado
            responder(
                id_,
                {
                    "content": [{"type": "text", "text": str(error)}],
                    "isError": True,
                },
            )
    elif metodo in ("resources/list", "resources/templates/list", "prompts/list"):
        clave = {
            "resources/list": "resources",
            "resources/templates/list": "resourceTemplates",
            "prompts/list": "prompts",
        }[metodo]
        responder(id_, {clave: []})
    elif metodo == "logging/setLevel":
        responder(id_, {})
    else:
        responder(
            id_,
            error={"code": -32601, "message": f"Método no soportado: {metodo}"},
        )


def main() -> None:
    # El índice se carga antes de atender para fallar temprano si falta la
    # carpeta de documentos. Cualquier traza va a stderr: stdout es solo JSON.
    try:
        indice()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return

    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        try:
            mensaje = json.loads(linea)
        except json.JSONDecodeError as error:
            responder(
                None,
                error={"code": -32700, "message": f"JSON inválido: {error.msg}"},
            )
            continue
        if not isinstance(mensaje, dict):
            responder(
                None,
                error={"code": -32600, "message": "La solicitud debe ser un objeto JSON."},
            )
            continue
        try:
            atender(mensaje)
        except Exception as error:  # nunca tumbar el servidor por una solicitud
            traceback.print_exc(file=sys.stderr)
            if mensaje.get("id") is not None:
                responder(
                    mensaje.get("id"),
                    error={"code": -32603, "message": f"Error interno: {error}"},
                )


if __name__ == "__main__":
    main()
