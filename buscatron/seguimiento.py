"""Lista de seguimiento: búsquedas vigiladas y reglas de aviso."""
import statistics
import threading
import time

from . import bd, motor, notifica

CAMPOS = ("nombre", "consulta", "incluir", "excluir", "pmin", "pmax", "objetivo", "bajo_historico",
          "sin_agotados", "canales", "cada_horas", "activo")
MIN_OBSERVACIONES = 4      # mínimo de precios previos de un artículo para fiarse de su media
REAVISO_DIAS = 30
_cerrojo = threading.Lock()
_en_curso = set()


def _num(v):
    try:
        return float(str(v).replace(",", ".")) if str(v).strip() != "" else None
    except ValueError:
        return None


def lista():
    with bd.conecta() as c:
        return [dict(r) for r in c.execute("SELECT * FROM seguimientos ORDER BY id")]


def guarda(d):
    """Crea o actualiza (si trae id). Devuelve el id."""
    v = {"nombre": (d.get("nombre") or d.get("consulta") or "").strip(),
         "consulta": (d.get("consulta") or "").strip(),
         "incluir": d.get("incluir", ""), "excluir": d.get("excluir", ""),
         "pmin": _num(d.get("pmin", "")), "pmax": _num(d.get("pmax", "")),
         "objetivo": _num(d.get("objetivo", "")), "bajo_historico": _num(d.get("bajo_historico", "")) or 0,
         "sin_agotados": 1 if d.get("sin_agotados", True) else 0,
         "canales": d.get("canales", "app") or "app",
         "cada_horas": max(0.25, _num(d.get("cada_horas", 12)) or 12),
         "activo": 1 if d.get("activo", True) else 0}
    if not v["consulta"]:
        raise ValueError("falta la búsqueda")
    with bd.conecta() as c:
        if d.get("id"):
            c.execute("UPDATE seguimientos SET " + ",".join(f"{k}=?" for k in CAMPOS) + " WHERE id=?",
                      [v[k] for k in CAMPOS] + [d["id"]])
            return int(d["id"])
        cur = c.execute("INSERT INTO seguimientos(" + ",".join(CAMPOS) + ") VALUES(" + ",".join("?" * len(CAMPOS)) + ")",
                        [v[k] for k in CAMPOS])
        return cur.lastrowid


def borra(seg_id):
    with bd.conecta() as c:
        c.execute("DELETE FROM seguimientos WHERE id=?", (seg_id,))


def avisos(limite=100):
    with bd.conecta() as c:
        return [dict(r) for r in c.execute("SELECT * FROM avisos ORDER BY ts DESC LIMIT ?", (limite,))]


def _motivo(c, seg, x):
    """Devuelve el motivo del aviso o None."""
    if seg["objetivo"] is not None and x["precio"] <= seg["objetivo"]:
        return f"≤ tu objetivo ({seg['objetivo']:.2f} €)"
    if seg["bajo_historico"]:
        previos = [r[0] for r in c.execute(
            "SELECT precio FROM precios WHERE url=? AND ts < ? AND agotado=0", (x["url"], x["_ts"]))]
        if len(previos) >= MIN_OBSERVACIONES:
            med = statistics.median(previos)
            if x["precio"] <= med * (1 - seg["bajo_historico"] / 100):
                return f"{(1 - x['precio'] / med) * 100:.0f} % por debajo de su media ({med:.2f} €)"
    return None


def revisa(seg_id, enviar=True):
    """Ejecuta un seguimiento ahora. Devuelve {'resultados': n, 'avisos': [...], 'envio': {...}}."""
    with _cerrojo:
        if seg_id in _en_curso:
            return {"ocupado": True}
        _en_curso.add(seg_id)
    try:
        with bd.conecta() as c:
            seg = c.execute("SELECT * FROM seguimientos WHERE id=?", (seg_id,)).fetchone()
        if not seg:
            raise ValueError("seguimiento inexistente")
        seg = dict(seg)
        ts = time.time()
        res, informe = motor.buscar(seg["consulta"], seg["incluir"], seg["excluir"], bool(seg["sin_agotados"]),
                                    None, seg["pmin"], seg["pmax"], seg_id)
        nuevos = []
        with bd.conecta() as c:
            for x in res:
                x["_ts"] = ts
                motivo = _motivo(c, seg, x)
                if not motivo:
                    continue
                ult = c.execute("SELECT precio, ts FROM avisos WHERE seg_id=? AND url=? ORDER BY ts DESC LIMIT 1",
                                (seg_id, x["url"])).fetchone()
                if ult and x["precio"] >= ult["precio"] - 0.005 and ts - ult["ts"] < REAVISO_DIAS * 86400:
                    continue
                c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                          (ts, seg_id, x["titulo"], x["tienda"], x["url"], x["precio"], motivo))
                nuevos.append({**x, "motivo": motivo})
            caidas = sum(1 for i in informe.values() if i["error"])
            estado = f"{len(res)} resultados, {len(nuevos)} avisos nuevos" + (f", {caidas} tiendas sin respuesta" if caidas else "")
            c.execute("UPDATE seguimientos SET ultima=?, estado=? WHERE id=?", (ts, estado, seg_id))
        envio = {}
        if nuevos and enviar:
            canales = [k for k in seg["canales"].split(",") if k in ("telegram", "correo")]
            lineas = [f"{x['precio']:.2f} € · {x['titulo']} ({x['tienda']})\n{x['motivo']}\n{x['url']}" for x in nuevos[:10]]
            if len(nuevos) > 10:
                lineas.append(f"… y {len(nuevos) - 10} más en la pestaña Avisos")
            envio = notifica.envia(canales, f"BuscaTron · {seg['nombre']}", "\n\n".join(lineas))
        return {"resultados": len(res), "avisos": nuevos, "envio": envio}
    finally:
        with _cerrojo:
            _en_curso.discard(seg_id)


def pendientes(ahora=None):
    ahora = ahora or time.time()
    return [s["id"] for s in lista() if s["activo"] and ahora - s["ultima"] >= s["cada_horas"] * 3600]
