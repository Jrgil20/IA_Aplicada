# -*- coding: utf-8 -*-
"""Servidor web del Asistente de Compras.

Sirve la interfaz y expone la API de preguntas. Solo biblioteca estándar.
Escucha en 0.0.0.0:8501 (equipo 1) o 8502 (equipo 2).
"""

from __future__ import annotations

import argparse
import base64
import hmac
import json
import mimetypes
import os
import posixpath
import sys
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from llm import intento_de_inyeccion, sanitizar_texto
from motor import Asistente

BASE = os.path.dirname(os.path.abspath(__file__))
ESTATICOS = os.path.join(BASE, "estaticos")

ASISTENTE: Asistente | None = None
USUARIO = os.environ.get("ASISTENTE_USUARIO", "").strip()
CLAVE = os.environ.get("ASISTENTE_CLAVE", "")

LIMITE_POR_MINUTO = 30
MAX_CONCURRENTES = 4
_SEMAFORO = threading.BoundedSemaphore(MAX_CONCURRENTES)
_HISTORIAL: dict[str, deque] = defaultdict(deque)
_HISTORIAL_LOCK = threading.Lock()


def _permitir_solicitud(ip: str) -> bool:
    ahora = time.monotonic()
    with _HISTORIAL_LOCK:
        cola = _HISTORIAL[ip]
        while cola and ahora - cola[0] > 60:
            cola.popleft()
        if len(cola) >= LIMITE_POR_MINUTO:
            return False
        cola.append(ahora)
        return True


class Manejador(BaseHTTPRequestHandler):
    server_version = "AsistenteCompras/1.1"
    sys_version = ""
    protocol_version = "HTTP/1.1"

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
        try:
            with open(ruta, "rb") as archivo:
                cuerpo = archivo.read()
        except OSError:
            self._json({"error": "No se pudo leer el archivo"}, 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", (tipo or "application/octet-stream") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
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

    def _autorizado(self) -> bool:
        if not USUARIO:
            return True
        cabecera = self.headers.get("Authorization", "")
        if not cabecera.startswith("Basic "):
            return False
        try:
            decodificado = base64.b64decode(cabecera[6:]).decode("utf-8")
            usuario, clave = decodificado.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return False
        return hmac.compare_digest(
            usuario.encode("utf-8"), USUARIO.encode("utf-8")
        ) and hmac.compare_digest(clave.encode("utf-8"), CLAVE.encode("utf-8"))

    def _no_autorizado(self) -> None:
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Asistente de Compras"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    # -- rutas --------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        if not self._autorizado():
            self._no_autorizado()
            return
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
        if not self._autorizado():
            self._no_autorizado()
            return
        ruta = urlparse(self.path).path
        if ruta != "/api/preguntar":
            self._json({"error": "Ruta no encontrada"}, 404)
            return

        tipo = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if tipo != "application/json":
            self.close_connection = True
            self._json({"error": "Content-Type no soportado; use application/json"}, 415)
            return

        if not _permitir_solicitud(self.client_address[0]):
            self.close_connection = True
            self._json({"error": "Demasiadas solicitudes; intenta de nuevo en un minuto."}, 429)
            return

        try:
            largo = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            largo = 0
        if largo <= 0 or largo > 20000:
            self.close_connection = True
            self._json({"error": "Solicitud inválida"}, 400)
            return
        try:
            datos = json.loads(self.rfile.read(largo).decode("utf-8"))
            if not isinstance(datos, dict):
                self._json({"error": "Solicitud inválida"}, 400)
                return
            pregunta = sanitizar_texto(str(datos.get("pregunta", "")))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json({"error": "Solicitud inválida"}, 400)
            return
        if not pregunta:
            self._json({"error": "La pregunta está vacía"}, 400)
            return
        if len(pregunta) > 1000:
            self._json({"error": "La pregunta es demasiado larga"}, 400)
            return
        if intento_de_inyeccion(pregunta):
            self._json(
                {"error": "La consulta contiene instrucciones no permitidas."},
                400,
            )
            return

        if ASISTENTE is None:
            self._json({"error": "El asistente todavía está cargando."}, 503)
            return

        if not _SEMAFORO.acquire(blocking=False):
            self._json({"error": "El asistente está ocupado; intenta de nuevo."}, 503)
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
        finally:
            _SEMAFORO.release()

        respuesta["pregunta"] = pregunta
        respuesta.pop("evidencia", None)
        self._json(respuesta)

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._autorizado():
            self._no_autorizado()
            return
        ruta = urlparse(self.path).path
        if ruta in ("/", "/index.html", "/api/salud"):
            self.send_response(200)
            if ruta == "/api/salud":
                self.send_header("Content-Type", "application/json; charset=utf-8")
            else:
                self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> None:
    global ASISTENTE
    analizador = argparse.ArgumentParser(description="Asistente de Compras")
    analizador.add_argument("--host", default=os.environ.get("ASISTENTE_HOST", "0.0.0.0"))
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
