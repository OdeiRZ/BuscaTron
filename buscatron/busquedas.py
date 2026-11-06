"""Últimas búsquedas hechas desde la web, guardadas para volver a verlas sin repetirlas (y poder borrarlas)."""
import json
import time

from . import bd

MAXIMO = 12     # búsquedas que se conservan; al pasar de ahí se borran las más antiguas
CLAVES = ("q", "incluir", "excluir", "pmin", "pmax", "top", "sin_agotados", "castellano", "preventas", "con_envio",
          "segunda_mano", "abierta", "region", "paginas")


def _firma(params):
    return json.dumps({k: params.get(k) for k in CLAVES}, sort_keys=True, ensure_ascii=False)


def guarda(params, resp):
    """Guarda una búsqueda y su respuesta ({resultados, total, informe, webs}). Si ya había una igual (misma consulta
    y mismos filtros) la sustituye. Devuelve (id, ts)."""
    p = {k: params.get(k) for k in CLAVES}
    ts = time.time()
    with bd.conecta() as c:
        c.execute("DELETE FROM busquedas WHERE firma=?", (_firma(p),))
        cur = c.execute("INSERT INTO busquedas(ts,consulta,firma,params,resultados,total,informe,webs) VALUES(?,?,?,?,?,?,?,?)",
                        (ts, (p.get("q") or "").strip(), _firma(p), json.dumps(p, ensure_ascii=False),
                         json.dumps(resp.get("resultados", []), ensure_ascii=False), int(resp.get("total", 0)),
                         json.dumps(resp.get("informe", {}), ensure_ascii=False), json.dumps(resp.get("webs", []), ensure_ascii=False)))
        nuevo = cur.lastrowid
        c.execute("DELETE FROM busquedas WHERE id NOT IN (SELECT id FROM busquedas ORDER BY ts DESC, id DESC LIMIT ?)", (MAXIMO,))
    return nuevo, ts


def lista():
    """Resumen de las guardadas, de la más reciente a la más antigua (sin los resultados)."""
    with bd.conecta() as c:
        filas = c.execute("SELECT id, ts, consulta, params, total, resultados FROM busquedas ORDER BY ts DESC, id DESC").fetchall()
    return [{"id": f["id"], "ts": f["ts"], "consulta": f["consulta"], "total": f["total"], "params": json.loads(f["params"]),
             "mostrados": len(json.loads(f["resultados"]))} for f in filas]


def obtiene(busqueda_id):
    """Una búsqueda guardada completa, o None."""
    with bd.conecta() as c:
        f = c.execute("SELECT * FROM busquedas WHERE id=?", (busqueda_id,)).fetchone()
    if not f:
        return None
    return {"id": f["id"], "ts": f["ts"], "params": json.loads(f["params"]), "resultados": json.loads(f["resultados"]),
            "total": f["total"], "informe": json.loads(f["informe"]), "webs": json.loads(f["webs"])}


def actualiza(busqueda_id, resultados):
    """Cambia los resultados guardados (p. ej. al importar productos a mano) sin tocar la fecha de la búsqueda."""
    with bd.conecta() as c:
        c.execute("UPDATE busquedas SET resultados=? WHERE id=?", (json.dumps(resultados, ensure_ascii=False), busqueda_id))


def borra(busqueda_id):
    with bd.conecta() as c:
        c.execute("DELETE FROM busquedas WHERE id=?", (busqueda_id,))


def vacia():
    with bd.conecta() as c:
        c.execute("DELETE FROM busquedas")
