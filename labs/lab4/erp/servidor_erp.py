#!/usr/bin/env python3
"""ERP de compras ficticio, expuesto como servidor MCP por stdio.

Solo usa la biblioteca estándar de Python. Al arrancar crea erp.db a partir de
los CSV de datos/ si no existe. Para volver al estado inicial, borra erp.db.
"""
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DB = AQUI / "erp.db"
DATOS = AQUI / "datos"
VERSION_PROTOCOLO = "2025-06-18"


def conectar():
    nueva = not DB.exists()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    if nueva:
        con.execute("CREATE TABLE proveedores (proveedor_id TEXT PRIMARY KEY, nombre TEXT, ciudad TEXT, correo TEXT)")
        con.execute("CREATE TABLE pedidos (pedido TEXT PRIMARY KEY, proveedor_id TEXT, sede TEXT, categoria TEXT, "
                    "producto TEXT, cantidad INTEGER, precio_unitario_usd REAL, fecha_pedido TEXT, "
                    "fecha_comprometida TEXT, fecha_entrega TEXT, estado TEXT)")
        con.execute("CREATE TABLE notas_proveedor (nota TEXT PRIMARY KEY, proveedor_id TEXT, fecha TEXT, texto TEXT)")
        con.execute("CREATE TABLE reclamos (reclamo TEXT PRIMARY KEY, pedido TEXT, motivo TEXT, registrado TEXT)")
        for tabla in ("proveedores", "pedidos", "notas_proveedor"):
            with open(DATOS / f"{tabla}.csv", encoding="utf-8") as fh:
                filas = list(csv.DictReader(fh))
            cols = list(filas[0].keys())
            con.executemany(f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                            [[f[c] or None for c in cols] for f in filas])
        con.commit()
    return con


def filas(cursor):
    return [dict(f) for f in cursor.fetchall()]


def listar_proveedores(con, args):
    return filas(con.execute("SELECT * FROM proveedores ORDER BY proveedor_id"))


def buscar_pedidos(con, args):
    sql, params = "SELECT * FROM pedidos WHERE 1=1", []
    if args.get("proveedor_id"):
        sql += " AND proveedor_id = ?"
        params.append(args["proveedor_id"])
    if args.get("estado"):
        sql += " AND estado = ?"
        params.append(args["estado"])
    return filas(con.execute(sql + " ORDER BY pedido", params))


def notas_proveedor(con, args):
    return filas(con.execute("SELECT * FROM notas_proveedor WHERE proveedor_id = ? ORDER BY fecha",
                             [args["proveedor_id"]]))


def listar_reclamos(con, args):
    return filas(con.execute("SELECT * FROM reclamos ORDER BY reclamo"))


def registrar_reclamo(con, args):
    if not con.execute("SELECT 1 FROM pedidos WHERE pedido = ?", [args["pedido"]]).fetchone():
        raise ValueError(f"El pedido {args['pedido']} no existe")
    n = con.execute("SELECT COUNT(*) FROM reclamos").fetchone()[0] + 1
    reclamo = f"RC-{n:04d}"
    con.execute("INSERT INTO reclamos VALUES (?, ?, ?, ?)",
                [reclamo, args["pedido"], args["motivo"], datetime.now().isoformat(timespec="seconds")])
    con.commit()
    return {"reclamo": reclamo, "pedido": args["pedido"], "estado": "Enviado al portal del proveedor"}


def marcar_entregado(con, args):
    cur = con.execute("UPDATE pedidos SET estado = 'Entregado', fecha_entrega = ? WHERE pedido = ? AND estado = 'Pendiente'",
                      [args["fecha_entrega"], args["pedido"]])
    con.commit()
    if cur.rowcount == 0:
        raise ValueError(f"El pedido {args['pedido']} no existe o no está pendiente")
    return {"pedido": args["pedido"], "estado": "Entregado", "fecha_entrega": args["fecha_entrega"]}


def texto(descripcion):
    return {"type": "string", "description": descripcion}


HERRAMIENTAS = {
    "listar_proveedores": (listar_proveedores, "Lista los proveedores con su nombre, ciudad y correo.", {}, []),
    "buscar_pedidos": (buscar_pedidos, "Busca pedidos de compra. Filtra por proveedor y por estado (Pendiente, Entregado o Cancelado).",
                       {"proveedor_id": texto("Código del proveedor, como P04"), "estado": texto("Pendiente, Entregado o Cancelado")}, []),
    "notas_proveedor": (notas_proveedor, "Devuelve las notas que el proveedor dejó en el portal de proveedores.",
                        {"proveedor_id": texto("Código del proveedor, como P04")}, ["proveedor_id"]),
    "listar_reclamos": (listar_reclamos, "Lista los reclamos ya registrados.", {}, []),
    "registrar_reclamo": (registrar_reclamo, "Registra un reclamo formal por un pedido. El reclamo se envía al portal del proveedor y no se puede retirar.",
                          {"pedido": texto("Número de pedido, como PO-1295"), "motivo": texto("Motivo del reclamo")}, ["pedido", "motivo"]),
    "marcar_entregado": (marcar_entregado, "Marca un pedido pendiente como entregado en el ERP.",
                         {"pedido": texto("Número de pedido"), "fecha_entrega": texto("Fecha en formato AAAA-MM-DD")}, ["pedido", "fecha_entrega"]),
}


def responder(id_, resultado=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error:
        msg["error"] = error
    else:
        msg["result"] = resultado
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def registrar_auditoria(herramienta, argumentos, es_error=False, detalle=""):
    log_file = AQUI / "auditoria_mcp.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "herramienta": herramienta,
        "argumentos": argumentos,
        "es_error": es_error,
        "detalle": detalle
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def atender(con, msg):
    metodo, id_, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if id_ is None:
        return  # notificaciones, como notifications/initialized
    if metodo == "initialize":
        responder(id_, {"protocolVersion": params.get("protocolVersion", VERSION_PROTOCOLO),
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "erp-compras", "version": "1.0"}})
    elif metodo == "ping":
        responder(id_, {})
    elif metodo == "tools/list":
        responder(id_, {"tools": [
            {"name": nombre, "description": desc,
             "inputSchema": {"type": "object", "properties": props, "required": req}}
            for nombre, (_, desc, props, req) in HERRAMIENTAS.items()]})
    elif metodo == "tools/call":
        nombre = params.get("name")
        args = params.get("arguments") or {}
        if nombre not in HERRAMIENTAS:
            registrar_auditoria(nombre, args, es_error=True, detalle=f"Herramienta desconocida: {nombre}")
            responder(id_, error={"code": -32602, "message": f"Herramienta desconocida: {nombre}"})
            return
        try:
            datos = HERRAMIENTAS[nombre][0](con, args)
            registrar_auditoria(nombre, args, es_error=False, detalle="OK")
            responder(id_, {"content": [{"type": "text", "text": json.dumps(datos, ensure_ascii=False, indent=1)}],
                            "isError": False})
        except Exception as e:  # el error vuelve al agente como resultado, no tumba el servidor
            registrar_auditoria(nombre, args, es_error=True, detalle=str(e))
            responder(id_, {"content": [{"type": "text", "text": str(e)}], "isError": True})
    else:
        responder(id_, error={"code": -32601, "message": f"Método no soportado: {metodo}"})


def main():
    con = conectar()
    for linea in sys.stdin:
        if linea.strip():
            atender(con, json.loads(linea))


if __name__ == "__main__":
    main()
