# -*- coding: utf-8 -*-
"""Motor del asistente: recuperación + redacción con fuentes."""

from __future__ import annotations

import os
import time

from busqueda import Indice, tokenizar
from llm import redactar

BASE = os.path.dirname(os.path.abspath(__file__))
DOCUMENTOS = os.path.normpath(os.path.join(BASE, "..", "documentos"))


class Asistente:
    def __init__(self, carpeta_documentos: str = DOCUMENTOS, limite: int = 8):
        self.carpeta_documentos = carpeta_documentos
        self.limite = limite
        self.indice = Indice(carpeta_documentos)

    @property
    def total_documentos(self) -> int:
        return len(self.indice.documentos)

    def salud(self) -> dict:
        return {
            "estado": "ok",
            "documentos": len(self.indice.documentos),
            "fragmentos": len(self.indice.fragmentos),
            "modelo": "qwen3-coder",
        }

    def responder(self, pregunta: str) -> dict:
        pregunta = (pregunta or "").strip()
        inicio = time.monotonic()
        if len(pregunta) < 3:
            return {
                "respuesta": "Escribe una pregunta completa para poder buscarla en los documentos.",
                "fuentes": [],
                "negativa": True,
                "ms": 0,
                "evidencia": [],
            }
        fragmentos = self.indice.buscar(pregunta, self.limite)

        # Puerta de seguridad: si ni siquiera hay coincidencia de contenido,
        # no se llama al modelo. Se evita que improvise con fragmentos ajenos.
        terminos = [t for t in tokenizar(pregunta) if len(t) > 2]
        if not fragmentos or not terminos:
            return {
                "respuesta": (
                    "No está en los documentos de compras. No encontré ningún "
                    "documento relacionado con esa pregunta."
                ),
                "fuentes": [],
                "negativa": True,
                "ms": int((time.monotonic() - inicio) * 1000),
                "evidencia": [],
            }

        resultado = redactar(pregunta, fragmentos)
        resultado["ms"] = int((time.monotonic() - inicio) * 1000)
        resultado["evidencia"] = [
            {
                "id": f.doc_id,
                "seccion": f.seccion,
                "puntaje": f.puntaje,
            }
            for f in fragmentos
        ]
        return resultado

    def documento(self, doc_id: str) -> dict | None:
        documento = self.indice.documento(doc_id)
        if documento is None:
            return None
        return {
            "id": documento.doc_id,
            "titulo": documento.titulo,
            "tipo": documento.tipo,
            "proveedor": documento.proveedor,
            "fecha": documento.fecha,
            "estado": documento.estado,
            "texto": documento.texto,
        }
