"""Motor de búsqueda: consulta tiendas en paralelo y ordena por precio."""
import concurrent.futures as cf
import sqlite3
import time
import os
from urllib.parse import quote_plus

from . import fetch, extract, descubre, tiendas as cfg

BD = os.path.join(cfg.RAIZ, "buscatron.db")


def _bd():
    c = sqlite3.connect(BD)
    c.execute("""CREATE TABLE IF NOT EXISTS precios(
        ts REAL, consulta TEXT, tienda TEXT, titulo TEXT, url TEXT, precio REAL, agotado INTEGER)""")
    return c


def _candidatas(t, consulta):
    """URLs de búsqueda a probar, de más a menos fiable."""
    q = quote_plus(consulta)
    base = "https://" + t["host"]
    if t.get("plantilla"):
        return [t["plantilla"].replace("{q}", q)], None
    st, home = fetch.get(base + "/")
    if st != 200:
        return [], f"portada HTTP {st}"
    pl = descubre.plantilla(home, base + "/")
    urls = ([(pl, pl.replace("{q}", q))] if pl else [])
    urls += [(base + p, base + p.format(q=q)) for p in cfg.PLANTILLAS]
    return urls, None


def _tienda(t, consulta):
    try:
        urls, err = _candidatas(t, consulta)
        if err:
            return t["host"], [], err
        for item in urls:
            pl, url = item if isinstance(item, tuple) else (t["plantilla"], item)
            st, html = fetch.get(url)
            if st != 200:
                err = f"HTTP {st}"
                continue
            r = extract.extrae(html, url, consulta)
            if r:
                t["plantilla"] = pl
                return t["host"], r, None
            err = "sin resultados (¿carga con JavaScript?)"
        return t["host"], [], err or "sin buscador detectable"
    except Exception as e:
        return t["host"], [], f"error: {str(e)[:60]}"


def buscar(consulta, incluir="", excluir="", ocultar_agotados=False, hosts=None, pmin=None, pmax=None):
    """Devuelve (resultados ordenados por precio, informe por tienda)."""
    lista = cfg.carga()
    activas = [t for t in lista if (t["host"] in hosts if hosts is not None else t.get("activa", True))]
    inc = extract.normaliza(incluir).split()
    exc = extract.normaliza(excluir).split()
    res, informe = [], {}
    with cf.ThreadPoolExecutor(6) as ex:
        for host, items, err in ex.map(lambda t: _tienda(t, consulta), activas):
            kept = 0
            for x in items:
                n = extract.normaliza(x["titulo"])
                if all(w in n for w in inc) and not any(w in n for w in exc):
                    if ocultar_agotados and x["agotado"]:
                        continue
                    if (pmin is not None and x["precio"] < pmin) or (pmax is not None and x["precio"] > pmax):
                        continue
                    x["tienda"] = host
                    res.append(x)
                    kept += 1
            informe[host] = {"encontrados": kept, "error": err if not kept else None}
    cfg.guarda(lista)  # persiste las plantillas descubiertas
    res.sort(key=lambda x: (x["agotado"], x["precio"]))
    ts = time.time()
    with _bd() as c:
        c.executemany("INSERT INTO precios VALUES(?,?,?,?,?,?,?)",
                      [(ts, consulta, x["tienda"], x["titulo"], x["url"], x["precio"], int(x["agotado"])) for x in res])
    return res, informe
