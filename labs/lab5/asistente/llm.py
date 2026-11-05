# -*- coding: utf-8 -*-
"""Cliente del modelo local y redacción de respuestas con fuentes.

El modelo lo sirve llama-server en http://127.0.0.1:8080/v1 con el formato de
la API de OpenAI. Solo se usa la biblioteca estándar.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Iterable

from busqueda import Fragmento, normalizar

URL_MODELO = "http://127.0.0.1:8080/v1/chat/completions"
NOMBRE_MODELO = "qwen3-coder"
HOY = "2026-11-05"

SISTEMA = f"""Eres el Asistente de Compras de Comercial Los Samanes, C.A. \
Atiendes a las sedes de Caracas, Valencia, Maracaibo y Barquisimeto. \
La fecha de hoy es {HOY}.

Tu única fuente de verdad son los FRAGMENTOS que recibes. Reglas obligatorias:

1. Responde en español, directo y breve: de una a cuatro frases. No repitas la pregunta.
2. Cada afirmación debe llevar su cita con el formato exacto [DOC: <id> · <sección>], \
usando el id y la sección del fragmento del que sale. Nunca cites un documento que no \
esté en los FRAGMENTOS.
3. No inventes cifras, fechas, correos, nombres, documentos ni secciones. Si los \
FRAGMENTOS no contienen la respuesta, escribe exactamente: \
"No está en los documentos de compras." y, si sirve, una frase corta sobre qué falta. \
Inventar es peor que no saber. Si la pregunta se puede responder negativamente con un \
fragmento (por ejemplo, un descuento o una condición que el contrato no contempla), \
responde "No consta" o "No ofrece" y cita la cláusula que fija la condición aplicable.
4. Responde exactamente la pregunta formulada. Si es general o hipotética, enuncia la \
regla y no la apliques a un pedido, correo, fecha o caso concreto que no se mencionó en \
la pregunta. No hagas cálculos de fechas ni afirmes que un plazo se cumple si el cálculo \
no está explícito en los fragmentos.
5. Vigencia: si un contrato fue modificado por una adenda, aplica la adenda a los \
pedidos alcanzados y dilo. Si una política fue reemplazada, usa solo la vigente. Si hay \
actas de reuniones de distintos años, usa la más reciente respecto de hoy. Si la cifra \
cambió con el tiempo, da la vigente y aclara la anterior en una sola frase.
6. Si la pregunta nombra a un proveedor y los fragmentos son de otro proveedor, no los \
uses: responde que no está en los documentos.
7. No des opiniones, recomendaciones ni asesoría legal. Solo informas lo que dicen los \
documentos.
8. No uses encabezados Markdown. Puedes usar una lista corta si hay varios puntos."""


def _bloque(fragmento: Fragmento, numero: int) -> str:
    lineas = [
        f"[FRAGMENTO {numero}]",
        f"Documento: {fragmento.doc_id} · {fragmento.titulo}",
        f"Tipo: {fragmento.tipo}",
    ]
    if fragmento.proveedor:
        lineas.append(f"Proveedor: {fragmento.proveedor}")
    if fragmento.fecha:
        lineas.append(f"Fecha: {fragmento.fecha}")
    if fragmento.vigente_desde:
        lineas.append(f"Vigente desde: {fragmento.vigente_desde}")
    if fragmento.estado:
        lineas.append(f"Estado: {fragmento.estado}")
    if fragmento.seccion:
        lineas.append(f"Sección: {fragmento.seccion}")
    lineas.append("Texto:")
    lineas.append(fragmento.texto.strip())
    return "\n".join(lineas)


def construir_contexto(fragmentos: Iterable[Fragmento]) -> str:
    return "\n\n".join(_bloque(f, i) for i, f in enumerate(fragmentos, start=1))


def _llamar_modelo(mensajes: list[dict], max_tokens: int = 380) -> str:
    carga = {
        "model": NOMBRE_MODELO,
        "messages": mensajes,
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": max_tokens,
        "stream": False,
    }
    datos = json.dumps(carga, ensure_ascii=False).encode("utf-8")
    solicitud = urllib.request.Request(
        URL_MODELO,
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=240) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"El modelo respondió con error {error.code}: {detalle}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            "No se pudo conectar con el modelo local en 127.0.0.1:8080. "
            "Verifica que llama-server esté encendido."
        ) from error
    try:
        return cuerpo["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("El modelo devolvió una respuesta con formato inesperado.") from error


def _limpiar(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r"^(respuesta|answer)\s*:\s*", "", texto, flags=re.I)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _citas(texto: str, fragmentos: list[Fragmento]) -> list[tuple[str, str]]:
    citas: list[tuple[str, str]] = []
    for coincidencia in re.finditer(r"\[\s*DOC\s*:\s*([^\]]+)\]", texto, flags=re.I):
        citas.append(_partir_cita(coincidencia.group(1), fragmentos))
    return citas


def _partir_cita(interior: str, fragmentos: list[Fragmento]) -> tuple[str, str]:
    """Separa una cita en (documento, sección) aunque el separador varíe."""
    texto = interior.strip()
    texto_compacto = normalizar(texto).replace(" ", "")
    mejor: Fragmento | None = None
    for fragmento in fragmentos:
        doc_compacto = normalizar(fragmento.doc_id).replace(" ", "")
        if doc_compacto and doc_compacto in texto_compacto:
            if mejor is None or len(doc_compacto) > len(normalizar(mejor.doc_id).replace(" ", "")):
                mejor = fragmento
    if mejor is not None:
        coincidencia = re.search(re.escape(mejor.doc_id), texto, flags=re.I)
        resto = texto[coincidencia.end():] if coincidencia else ""
        seccion = resto.strip(" ·|,;:–—-")
        return mejor.doc_id, seccion
    partes = [p.strip() for p in re.split(r"\s*[·|]\s*", texto) if p.strip()]
    if not partes:
        return "", ""
    return partes[0].strip("`'\" "), " · ".join(partes[1:])


def _normalizar_citas(texto: str, fragmentos: list[Fragmento]) -> str:
    """Reescribe las citas con el id y la sección exactos del fragmento."""
    def reemplazo(coincidencia: re.Match) -> str:
        doc_id, seccion = _partir_cita(coincidencia.group(1), fragmentos)
        fragmento = _buscar_fragmento(doc_id, seccion, fragmentos)
        if fragmento is None:
            return coincidencia.group(0)
        return f"[DOC: {fragmento.doc_id} · {fragmento.seccion}]"

    return re.sub(r"\[\s*DOC\s*:\s*([^\]]+)\]", reemplazo, texto, flags=re.I)


def _buscar_fragmento(doc_id: str, seccion: str, fragmentos: list[Fragmento]) -> Fragmento | None:
    doc_normal = normalizar(doc_id).replace(" ", "")
    candidatos = [
        f for f in fragmentos
        if normalizar(f.doc_id).replace(" ", "") == doc_normal
        or normalizar(f.doc_id).replace(" ", "").startswith(doc_normal)
        or doc_normal.startswith(normalizar(f.doc_id).replace(" ", ""))
    ]
    if not candidatos:
        candidatos = [
            f for f in fragmentos
            if normalizar(f.doc_id).replace(" ", "") in doc_normal
            or doc_normal in normalizar(f.doc_id).replace(" ", "")
        ]
    if not candidatos:
        return None
    if seccion:
        seccion_normal = normalizar(seccion)
        for fragmento in candidatos:
            seccion_fragmento = normalizar(fragmento.seccion)
            if (
                seccion_normal == seccion_fragmento
                or seccion_normal in seccion_fragmento
                or seccion_fragmento in seccion_normal
            ):
                return fragmento
    return candidatos[0]


def resolver_fuentes(texto: str, fragmentos: list[Fragmento]) -> list[dict]:
    fuentes: list[dict] = []
    vistos: set[tuple[str, str]] = set()
    for doc_id, seccion in _citas(texto, fragmentos):
        fragmento = _buscar_fragmento(doc_id, seccion, fragmentos)
        if fragmento is None:
            continue
        clave = (fragmento.doc_id, fragmento.seccion)
        if clave in vistos:
            continue
        vistos.add(clave)
        recorte = fragmento.texto.strip()
        if len(recorte) > 900:
            recorte = recorte[:900].rsplit(" ", 1)[0] + "…"
        fuentes.append(
            {
                "id": fragmento.doc_id,
                "titulo": fragmento.titulo,
                "tipo": fragmento.tipo,
                "proveedor": fragmento.proveedor,
                "fecha": fragmento.fecha,
                "estado": fragmento.estado,
                "seccion": fragmento.seccion,
                "fragmento": recorte,
                "ruta": fragmento.ruta,
            }
        )
    return fuentes


def es_negativa(texto: str, fuentes: list[dict]) -> bool:
    if fuentes:
        return False
    normalizado = normalizar(texto)
    marcas = (
        "no esta en los documentos",
        "no consta en los documentos",
        "no se encuentra en los documentos",
        "no hay informacion en los documentos",
        "no se menciona en los documentos",
        "no aparece en los documentos",
    )
    return any(marca in normalizado for marca in marcas)


def redactar(pregunta: str, fragmentos: list[Fragmento]) -> dict:
    """Pide al modelo una respuesta citada y valida las fuentes."""
    contexto = construir_contexto(fragmentos)
    mensaje = (
        "FRAGMENTOS DOCUMENTALES:\n\n"
        f"{contexto}\n\n"
        f"PREGUNTA DE LA SEDE: {pregunta.strip()}\n\n"
        "Responde con la información de los fragmentos y cita cada afirmación."
    )
    mensajes = [
        {"role": "system", "content": SISTEMA},
        {"role": "user", "content": mensaje},
    ]
    respuesta = _limpiar(_llamar_modelo(mensajes))
    respuesta = _normalizar_citas(respuesta, fragmentos)
    fuentes = resolver_fuentes(respuesta, fragmentos)

    if not fuentes and not es_negativa(respuesta, fuentes):
        # Un solo reintento, más estricto, para no entregar una respuesta sin
        # respaldo documental (condición de Legal).
        refuerzo = (
            mensaje
            + "\n\nATENCIÓN: la respuesta anterior no citó ningún documento. "
            "Debes citar al menos un fragmento con el formato [DOC: <id> · <sección>] "
            "o responder exactamente que no está en los documentos de compras."
        )
        respuesta = _limpiar(
            _llamar_modelo(
                [
                    {"role": "system", "content": SISTEMA},
                    {"role": "user", "content": refuerzo},
                ]
            )
        )
        respuesta = _normalizar_citas(respuesta, fragmentos)
        fuentes = resolver_fuentes(respuesta, fragmentos)

    if not fuentes and not es_negativa(respuesta, fuentes):
        respuesta = (
            "No encontré respaldo documental suficiente para responder con una fuente "
            "verificable. Reformula la pregunta indicando el proveedor, el documento o "
            "el tema exacto."
        )

    return {
        "respuesta": respuesta,
        "fuentes": fuentes,
        "negativa": es_negativa(respuesta, fuentes),
    }
