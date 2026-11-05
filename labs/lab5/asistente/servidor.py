# -*- coding: utf-8 -*-
"""Servidor web del Asistente de Compras.

Sirve la interfaz y expone la API de preguntas. Solo biblioteca estándar.
Escucha en 0.0.0.0:8501 (equipo 1) o 8502 (equipo 2).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import posixpath
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from motor import Asistente

BASE = os.path.dirname(os.path.abspath(__file__))
ESTATICOS = os.path.join(BASE, "estaticos")

ASISTENTE: Asistente | None = None


class Manejador(BaseHTTPRequestHandler):
    server_version = "AsistenteCompras/1.0"

    # -- utilidades de respuesta -------------------------------------------
    def _json(self, datos: dict, estado: int = 200) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _archivo(self, ruta: str) -> None:
        if not os.path.isfile(ruta):
            self._json({"error": "No encontrado"}, 404)
            return
        tipo, _ = mimetypes.guess_type(ruta)
        with open(ruta, "rb") as archivo:
            cuerpo = archivo.read()
        self.send_response(200)
        self.send_header("Content-Type", (tipo or "application/octet-stream") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _estatico(self, nombre: str) -> None:
        nombre = posixpath.normpath(nombre).lstrip("/")
        if nombre in ("", "."):
            nombre = "index.html"
        ruta = os.path.realpath(os.path.join(ESTATICOS, nombre))
        if not ruta.startswith(os.path.realpath(ESTATICOS) + os.sep):
            self._json({"error": "Ruta no permitida"}, 403)
            return
        self._archivo(ruta)

    def log_message(self, formato: str, *args) -> None:
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), formato % args))
        sys.stdout.flush()

    # -- rutas --------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        partes = urlparse(self.path)
        ruta = partes.path
        if ruta in ("/", "/index.html"):
            self._estatico("index.html")
            return
        if ruta == "/api/salud":
            self._json({"estado": "ok", "asistente": ASISTENTE.salud() if ASISTENTE else {}})
            return
        if ruta == "/api/documento":
            identificador = parse_qs(partes.query).get("id", [""])[0]
            documento = ASISTENTE.documento(identificador) if ASISTENTE else None
            if documento is None:
                self._json({"error": "Documento no encontrado"}, 404)
                return
            self._json(documento)
            return
        if ruta.startswith("/api/"):
            self._json({"error": "Ruta no encontrada"}, 404)
            return
        self._estatico(ruta)

    def do_POST(self) -> None:  # noqa: N802
        ruta = urlparse(self.path).path
        if ruta != "/api/preguntar":
            self._json({"error": "Ruta no encontrada"}, 404)
            return
        try:
            largo = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            largo = 0
        if largo <= 0 or largo > 20000:
            self._json({"error": "Solicitud inválida"}, 400)
            return
        try:
            datos = json.loads(self.rfile.read(largo).decode("utf-8"))
            pregunta = str(datos.get("pregunta", "")).strip()
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json({"error": "Solicitud inválida"}, 400)
            return
        if not pregunta:
            self._json({"error": "La pregunta está vacía"}, 400)
            return
        if len(pregunta) > 1000:
            self._json({"error": "La pregunta es demasiado larga"}, 400)
            return
        try:
            respuesta = ASISTENTE.responder(pregunta)
        except RuntimeError as error:
            self._json({"error": str(error)}, 503)
            return
        except Exception as error:  # pragma: no cover - protección del servidor
            self.log_message("Error inesperado: %r", error)
            self._json({"error": "Ocurrió un error al consultar los documentos."}, 500)
            return
        respuesta["pregunta"] = pregunta
        self._json(respuesta)


def main() -> None:
    global ASISTENTE
    analizador = argparse.ArgumentParser(description="Asistente de Compras")
    analizador.add_argument("--host", default="0.0.0.0")
    analizador.add_argument("--puerto", type=int, default=8501)
    opciones = analizador.parse_args()

    print("Cargando documentos de compras…", flush=True)
    ASISTENTE = Asistente()
    print(
        f"Listo: {ASISTENTE.total_documentos} documentos, "
        f"{len(ASISTENTE.indice.fragmentos)} fragmentos indexados.",
        flush=True,
    )
    servidor = ThreadingHTTPServer((opciones.host, opciones.puerto), Manejador)
    servidor.daemon_threads = True
    print(
        f"Asistente de Compras escuchando en http://{opciones.host}:{opciones.puerto}",
        flush=True,
    )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando el asistente.", flush=True)
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
