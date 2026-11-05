# -*- coding: utf-8 -*-
"""Índice documental y búsqueda léxica (BM25) para el asistente de Compras.

Solo usa la biblioteca estándar de Python. Lee documentos Markdown de
`documentos/`, los parte por secciones y recupera los fragmentos más
pertinentes para una pregunta en español.
"""

from __future__ import annotations

import math
import os
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable


# ---------------------------------------------------------------------------
# Normalización de texto
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a", "al", "algo", "algun", "alguna", "algunas", "alguno", "algunos",
    "ante", "antes", "asi", "bajo", "bien", "cabe", "cada", "como", "con",
    "contra", "cual", "cuales", "cuando", "cuanto", "cuanta", "cuantos",
    "cuantas", "de", "del", "desde", "donde", "dos", "durante", "e", "el",
    "ella", "ellas", "ellos", "en", "entre", "era", "es", "esa", "esas",
    "ese", "eso", "esos", "esta", "estan", "estar", "estas", "este", "esto",
    "estos", "fue", "ha", "hace", "hacen", "hacer", "hacia", "hasta", "hay",
    "la", "las", "le", "les", "lo", "los", "mas", "me", "mediante", "mi",
    "mis", "mucho", "muy", "ni", "no", "nos", "o", "para", "pero", "por",
    "que", "quien", "quienes", "se", "segun", "ser", "si", "sin", "sobre",
    "su", "sus", "te", "tiene", "tienen", "todo", "todos", "tras", "tu",
    "tus", "u", "un", "una", "unas", "uno", "unos", "y", "ya", "yo",
    # Palabras de la pregunta que no aportan al contenido.
    "dime", "decir", "saber", "quisiera", "favor", "porfa", "puede",
    "podria", "hola", "gracias", "necesito", "consulta",
}

# Se incluyen las formas ya pasadas por `raiz` (p. ej. "septiembr"), porque
# la detección de intención se hace sobre los tokens del índice.
_MESES = {
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "setiembre", "octubre", "noviembre", "diciembre",
    "septiembr", "setiembr", "octubr", "noviembr", "diciembr",
}

# Equivalencias puntuales que BM25 no descubre solo (no hay paquetes externos).
_EXPANSIONES = {
    "aduana": {"aduanal", "aduanero"},
    "aduanero": {"aduanal", "aduana"},
    "aduanal": {"aduana"},
    "tope": {"superar", "limite", "maximo"},
    "responder": {"respuesta", "plazo"},
    "respuesta": {"responder", "plazo"},
    "descuento": {"factura", "pago"},
    "comprometio": {"acuerdo", "compromiso"},
    "cotizacion": {"cotizaciones", "cotizar"},
    "gracia": {"gracia"},
}

# Los nombres de proveedor son la señal más fuerte para desambiguar los
# contratos, que comparten casi todo el texto genérico.
_ALIAS_PROVEEDOR = {
    "P01": {"p01", "distribuidora", "andina"},
    "P02": {"p02", "logistica", "avila"},
    "P03": {"p03", "suministros", "caroni"},
    "P04": {"p04", "importadora", "margarita"},
    "P05": {"p05", "papelera", "llanos"},
    "P06": {"p06", "tecnologia", "zulia"},
}

_CLASE_POR_TIPO = {
    "contrato de suministro": "contrato",
    "adenda de contrato": "adenda",
    "política": "politica",
    "procedimiento": "procedimiento",
    "acta de reunión": "acta",
    "evaluación de proveedor": "evaluacion",
    "ficha técnica de producto": "ficha",
    "lista de precios": "lista",
    "correo recibido": "correo",
}


def sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    texto = sin_acentos(texto).lower()
    # Une cifras con separador de miles: 3.000 -> 3000
    texto = re.sub(r"(?<=\d)[.](?=\d)", "", texto)
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def raiz(palabra: str) -> str:
    """Raíz muy ligera para español; evita depender de paquetes externos."""
    if len(palabra) <= 3:
        return palabra
    if palabra.endswith("mente") and len(palabra) > 8:
        palabra = palabra[:-5]
    for sufijo, reemplazo in (
        ("aciones", "acion"), ("iciones", "icion"), ("uciones", "ucion"),
        ("idades", "idad"), ("dades", "dad"),
    ):
        if palabra.endswith(sufijo):
            palabra = palabra[: -len(sufijo)] + reemplazo
            break
    else:
        if palabra.endswith("es") and len(palabra) > 5:
            palabra = palabra[:-2]
        elif palabra.endswith("s") and len(palabra) > 4:
            palabra = palabra[:-1]
    return palabra


def tokenizar(texto: str, quitar_vacias: bool = True) -> list[str]:
    tokens = []
    for palabra in normalizar(texto).split():
        if quitar_vacias and palabra in _STOPWORDS:
            continue
        if len(palabra) == 1 and not palabra.isdigit():
            continue
        tokens.append(raiz(palabra))
    return tokens


# ---------------------------------------------------------------------------
# Documentos y fragmentos
# ---------------------------------------------------------------------------

@dataclass
class Documento:
    doc_id: str
    titulo: str
    tipo: str
    clase: str
    proveedor: str
    fecha: str
    vigente_desde: str
    estado: str
    ruta: str
    texto: str


@dataclass
class Fragmento:
    fragmento_id: str
    doc_id: str
    titulo: str
    tipo: str
    clase: str
    proveedor: str
    fecha: str
    vigente_desde: str
    estado: str
    seccion: str
    texto: str
    ruta: str
    tokens: Counter = field(default_factory=Counter)
    largo: int = 0
    puntaje: float = 0.0


def _leer_metadatos(texto: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for linea in texto.splitlines()[:24]:
        coincidencia = re.match(r"^-\s*([^:]+):\s*(.+?)\s*$", linea)
        if coincidencia:
            clave = normalizar(coincidencia.group(1))
            meta[clave] = coincidencia.group(2).strip()
    return meta


def _fecha_de(meta: dict[str, str]) -> str:
    for clave in ("fecha", "firmada", "vigente desde", "aprobada"):
        valor = meta.get(clave, "")
        coincidencia = re.search(r"\d{4}-\d{2}-\d{2}", valor)
        if coincidencia:
            return coincidencia.group(0)
    return ""


def _titulo_de(texto: str, nombre_archivo: str) -> str:
    for linea in texto.splitlines():
        if linea.startswith("# "):
            return linea[2:].strip()
    return os.path.splitext(nombre_archivo)[0]


def _id_de(meta: dict[str, str], nombre_archivo: str) -> str:
    if meta.get("documento"):
        return meta["documento"].strip()
    return os.path.splitext(nombre_archivo)[0]


def _secciones(texto: str) -> list[tuple[str, str]]:
    """Devuelve [(título de sección, cuerpo)] a partir de los encabezados ##."""
    lineas = texto.splitlines()
    secciones: list[tuple[str, str]] = []
    titulo = ""
    cuerpo: list[str] = []
    for linea in lineas:
        if linea.startswith("## "):
            if titulo or cuerpo:
                secciones.append((titulo or "Ficha del documento", "\n".join(cuerpo).strip()))
            titulo = linea[3:].strip()
            cuerpo = []
        elif linea.startswith("# "):
            continue
        else:
            cuerpo.append(linea)
    if titulo or cuerpo:
        secciones.append((titulo or "Ficha del documento", "\n".join(cuerpo).strip()))
    return [(t, c) for t, c in secciones if c]


_CLAVES_METADATA = {
    "documento", "tipo", "proveedor", "firmado", "vigente desde", "estado",
    "fecha", "aprobada", "modifica", "de", "para", "trimestre", "lugar",
    "categoria", "asistentes por la compradora", "reemplaza", "version",
}


def _solo_metadatos(cuerpo: str) -> bool:
    lineas = [linea.strip() for linea in cuerpo.splitlines() if linea.strip()]
    if not lineas:
        return False
    for linea in lineas:
        coincidencia = re.match(r"^-\s*([^:]+):", linea)
        if not coincidencia:
            return False
        if normalizar(coincidencia.group(1)) not in _CLAVES_METADATA:
            return False
    return True


def _cuerpo_sin_metadatos(texto: str) -> str:
    lineas = []
    for linea in texto.splitlines():
        if linea.startswith("# "):
            continue
        if re.match(r"^-\s*[^:]+:", linea):
            continue
        lineas.append(linea)
    return "\n".join(lineas).strip()


def _partir_cuerpo(cuerpo: str, maximo: int = 1500) -> list[str]:
    if len(cuerpo) <= maximo:
        return [cuerpo]
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", cuerpo) if p.strip()]
    partes: list[str] = []
    actual = ""
    for parrafo in parrafos:
        if actual and len(actual) + len(parrafo) + 2 > maximo:
            partes.append(actual)
            actual = parrafo
        else:
            actual = f"{actual}\n\n{parrafo}".strip() if actual else parrafo
    if actual:
        partes.append(actual)
    return partes


def cargar_documentos(carpeta: str) -> list[Documento]:
    documentos: list[Documento] = []
    for raiz, _dirs, archivos in os.walk(carpeta):
        for nombre in sorted(archivos):
            if not nombre.lower().endswith(".md"):
                continue
            ruta = os.path.join(raiz, nombre)
            try:
                with open(ruta, "r", encoding="utf-8") as archivo:
                    texto = archivo.read()
            except OSError:
                continue
            meta = _leer_metadatos(texto)
            tipo = meta.get("tipo", "")
            documentos.append(
                Documento(
                    doc_id=_id_de(meta, nombre),
                    titulo=_titulo_de(texto, nombre),
                    tipo=tipo,
                    clase=_CLASE_POR_TIPO.get(normalizar(tipo), "otro"),
                    proveedor=meta.get("proveedor", ""),
                    fecha=_fecha_de(meta),
                    vigente_desde=meta.get("vigente desde", ""),
                    estado=meta.get("estado", ""),
                    ruta=os.path.relpath(ruta, os.path.dirname(carpeta)),
                    texto=texto,
                )
            )
    return documentos


def construir_fragmentos(documentos: Iterable[Documento]) -> list[Fragmento]:
    fragmentos: list[Fragmento] = []
    for documento in documentos:
        secciones = _secciones(documento.texto)
        if not secciones:
            secciones = [("Documento", documento.texto)]
        elif "## " not in documento.texto:
            # Correos y documentos sin secciones: se cita el mensaje y se
            # excluyen los metadatos del texto visible.
            secciones = [("Mensaje", _cuerpo_sin_metadatos(documento.texto))]
        contador = 0
        for titulo, cuerpo in secciones:
            if _solo_metadatos(cuerpo):
                continue
            for parte in _partir_cuerpo(cuerpo):
                contador += 1
                # El texto que se muestra y se cita no repite los metadatos.
                texto_visible = parte.strip()
                if not texto_visible:
                    continue
                # El texto indexado incluye metadatos y título para que una
                # pregunta que nombra al proveedor encuentre sus documentos.
                texto_indice = " ".join(
                    [
                        documento.doc_id, documento.titulo, documento.tipo,
                        documento.proveedor, documento.estado, titulo,
                        texto_visible,
                    ]
                )
                tokens = Counter(tokenizar(texto_indice))
                fragmentos.append(
                    Fragmento(
                        fragmento_id=f"{documento.doc_id}#{contador}",
                        doc_id=documento.doc_id,
                        titulo=documento.titulo,
                        tipo=documento.tipo,
                        clase=documento.clase,
                        proveedor=documento.proveedor,
                        fecha=documento.fecha,
                        vigente_desde=documento.vigente_desde,
                        estado=documento.estado,
                        seccion=titulo,
                        texto=texto_visible,
                        ruta=documento.ruta,
                        tokens=tokens,
                        largo=max(1, len(tokens)),
                    )
                )
    return fragmentos


# ---------------------------------------------------------------------------
# Índice BM25
# ---------------------------------------------------------------------------

class Indice:
    def __init__(self, carpetas_documentos: str):
        self.documentos = cargar_documentos(carpetas_documentos)
        self.fragmentos = construir_fragmentos(self.documentos)
        self.por_id = {documento.doc_id: documento for documento in self.documentos}
        self._df: Counter = Counter()
        self._tf: list[Counter] = []
        self._largo: list[int] = []
        for fragmento in self.fragmentos:
            self._tf.append(fragmento.tokens)
            self._largo.append(fragmento.largo)
            self._df.update(fragmento.tokens.keys())
        self._total = len(self.fragmentos)
        self._promedio = (sum(self._largo) / self._total) if self._total else 0.0

    # -- utilidades de intención ------------------------------------------
    @staticmethod
    def _proveedor_detectado(tokens: list[str]) -> str:
        mejor, puntos = "", 0
        for proveedor, alias in _ALIAS_PROVEEDOR.items():
            encontrados = len(alias.intersection(tokens))
            if encontrados > puntos:
                mejor, puntos = proveedor, encontrados
        return mejor

    @staticmethod
    def _clases_relevantes(tokens: list[str]) -> set[str]:
        conjunto = set(tokens)
        clases: set[str] = set()
        if conjunto & {"penalidad", "gracia", "atraso", "contrato", "adenda",
                       "pago", "factura", "correo", "notificacion", "aduanal",
                       "fuerza", "mayor", "descuento", "pronto"}:
            clases.update({"contrato", "adenda"})
        if conjunto & {"politica", "cotizacion", "cotizaciones", "monto",
                       "aprobacion", "aprueba", "umbral", "fraccionamiento",
                       "compra", "compras", "cotizar"}:
            clases.add("politica")
        if conjunto & {"reclamo", "reclamos", "responder", "respuesta", "plazo",
                       "proveedor", "proveedores"}:
            clases.add("procedimiento")
        if conjunto & {"reunion", "acta", "actas", "septiembre", "setiembre",
                       "septiembr", "setiembr", "octubre", "octubr",
                       "noviembre", "noviembr", "comprometio", "acuerdo",
                       "asistentes"}:
            clases.add("acta")
        if conjunto & {"precio", "precios", "lista", "catalogo", "producto"}:
            clases.add("lista")
        if conjunto & {"evaluacion", "puntaje", "trimestre", "desempeno"}:
            clases.add("evaluacion")
        return clases

    @staticmethod
    def _anio(fecha: str) -> int:
        coincidencia = re.search(r"(\d{4})", fecha or "")
        return int(coincidencia.group(1)) if coincidencia else 0

    def _refuerzo(self, fragmento: Fragmento, tokens: list[str], proveedor: str,
                  clases: set[str]) -> float:
        refuerzo = 1.0
        if proveedor:
            if fragmento.proveedor.startswith(proveedor):
                refuerzo *= 2.4
            elif fragmento.proveedor:
                refuerzo *= 0.42
        if clases and fragmento.clase in clases:
            refuerzo *= 1.35
        if fragmento.clase == "adenda":
            refuerzo *= 1.30
        if "reemplazad" in normalizar(fragmento.estado):
            refuerzo *= 0.15
        anio = self._anio(fragmento.fecha)
        if anio >= 2026:
            refuerzo *= 1.18
        elif anio == 2025:
            refuerzo *= 1.04
        # Una pregunta con mes pero sin año se refiere a la reunión más
        # reciente; el acta de 2026 debe pesar más que la de 2025.
        if fragmento.clase == "acta" and set(tokens) & _MESES and anio >= 2026:
            refuerzo *= 1.55
        if fragmento.clase == "acta" and set(tokens) & _MESES and anio == 2025:
            refuerzo *= 0.70

        # El boilerplate legal (confidencialidad, seguros, jurisdicción...)
        # comparte muchas palabras con las preguntas y suele desplazar a las
        # cláusulas que sí responden. Se atenúa.
        seccion = normalizar(fragmento.seccion)
        if any(
            marca in seccion
            for marca in (
                "confidencialidad", "proteccion de datos", "conducta",
                "anticorrupcion", "seguros", "cesion", "jurisdiccion",
            )
        ):
            refuerzo *= 0.55
        if "plazo de respuesta" in seccion:
            refuerzo *= 1.35
        if set(tokens) & {"descuento", "pago", "factura", "pronto"} and any(
            marca in seccion for marca in ("facturacion", "pago", "precio", "condiciones")
        ):
            refuerzo *= 1.30

        # "Aprobación de una compra" y "aprobación de un reclamo" comparten
        # palabras pero viven en documentos distintos. Sin esta distinción,
        # el procedimiento de reclamos desplaza a la política de compras.
        conjunto = set(tokens)
        aprueba_compra = (
            "compra" in conjunto
            and bool(conjunto & {"aprueba", "aprobacion", "monto", "umbral", "cotizacion"})
            and not bool(conjunto & {"reclamo", "reclamos"})
        )
        if aprueba_compra:
            if fragmento.clase == "politica":
                refuerzo *= 2.0
            if fragmento.doc_id == "PR-COM-03":
                refuerzo *= 0.30
        return refuerzo

    def buscar(self, pregunta: str, limite: int = 8) -> list[Fragmento]:
        tokens = tokenizar(pregunta)
        if not tokens:
            return []
        proveedor = self._proveedor_detectado(tokens)
        clases = self._clases_relevantes(tokens)
        terminos = Counter(tokens)
        for token in list(tokens):
            for equivalente in _EXPANSIONES.get(token, ()):
                terminos[equivalente] = 0
        k1, b = 1.5, 0.75
        resultados: list[Fragmento] = []
        for posicion, tf in enumerate(self._tf):
            puntaje = 0.0
            for termino, frecuencia in tf.items():
                if termino not in terminos:
                    continue
                df = self._df.get(termino, 0)
                idf = math.log(1 + (self._total - df + 0.5) / (df + 0.5))
                denominador = frecuencia + k1 * (
                    1 - b + b * self._largo[posicion] / (self._promedio or 1)
                )
                puntaje += idf * (frecuencia * (k1 + 1) / denominador)
            if puntaje <= 0:
                continue
            fragmento = self.fragmentos[posicion]
            puntaje *= self._refuerzo(fragmento, tokens, proveedor, clases)
            copia = Fragmento(**{**fragmento.__dict__, "tokens": Counter()})
            copia.puntaje = round(puntaje, 4)
            resultados.append(copia)
        resultados.sort(key=lambda f: f.puntaje, reverse=True)
        return resultados[:limite]

    def documento(self, doc_id: str) -> Documento | None:
        return self.por_id.get(doc_id)
