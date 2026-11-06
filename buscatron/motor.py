"""Motor de búsqueda: consulta tiendas en paralelo y ordena por precio."""
import concurrent.futures as cf
import re
import time
from urllib.parse import quote_plus

from . import ajustes, bd, fetch, extract, descubre, navegador, tiendas as cfg

def _candidatas(t, consulta, get):
    """URLs de búsqueda a probar, de más a menos fiable."""
    q = quote_plus(consulta)
    base = "https://" + t["host"]
    if t.get("plantilla"):
        return [(t["plantilla"], t["plantilla"].replace("{q}", q))], None
    st, home = get(base + "/")
    if st != 200:
        return [], f"portada HTTP {st}"
    pl = descubre.plantilla(home, base + "/")
    urls = [(pl, pl.replace("{q}", q))] if pl else []
    urls += [(base + p, base + p.format(q=q)) for p in cfg.PLANTILLAS]
    return urls, None


def _intenta(t, consulta, get):
    urls, err = _candidatas(t, consulta, get)
    if err:
        return [], err
    for pl, url in urls:
        st, html = get(url)
        if st != 200:
            err = f"HTTP {st}"
            continue
        r = extract.extrae(html, url, consulta)
        if r:
            t["plantilla"] = pl
            return r, None
        err = "sin resultados"
    return [], err or "sin buscador detectable"


def _tienda(t, consulta, nav=None):
    """nav: None (sin navegador) o {'visible': bool}. Orden: método rápido y, si falla, navegador."""
    h = t["host"]
    try:
        if not (nav and t.get("js")):
            r, err = _intenta(t, consulta, fetch.get)
            if r:
                return h, r, None
        if nav is None:
            return h, [], (err or "sin resultados") + " (puede cargar con JavaScript: activa el navegador en Ajustes)"
        visible = nav["visible"]
        get = lambda u: navegador.get(u, visible=visible, esperar_humano=90 if visible else 0)
        plant = t.get("plantilla")
        r, err = _intenta(t, consulta, get)
        if r:
            t["js"] = True
            return h, r, None
        if plant is None:
            t["plantilla"] = None
        return h, [], err or "sin resultados"
    except navegador.Desafio:
        return h, [], "pide comprobación humana (captcha): activa «navegador visible» en Ajustes y resuélvela una vez"
    except Exception as e:
        return h, [], f"error: {str(e)[:70]}"


OTROS_IDIOMAS = re.compile(r"\b(ingles|inglesa|english|frances|francesa|francais|aleman|alemana|deutsch|italiano|italiana|portugues|portuguesa|polaco|polaca|neerlandes|ruso|rusa)\b")
ES = re.compile(r"\b(castellano|espanol|espanola)\b")


def en_otro_idioma(titulo):
    """True si el título indica claramente otro idioma y no menciona el castellano."""
    n = extract.normaliza(titulo)
    return bool(OTROS_IDIOMAS.search(n)) and not ES.search(n)


def buscar(consulta, incluir="", excluir="", ocultar_agotados=True, hosts=None, pmin=None, pmax=None, seg_id=None, castellano=True):
    """Devuelve (resultados ordenados por precio, informe por tienda)."""
    lista = cfg.carga()
    activas = [t for t in lista if (t["host"] in hosts if hosts is not None else t.get("activa", True))]
    manuales = [t for t in activas if t.get("manual") and t.get("plantilla")]
    activas = [t for t in activas if t not in manuales]
    inc = extract.normaliza(incluir).split()
    exc = extract.normaliza(excluir).split()
    res, informe = [], {}
    aj = ajustes.carga()
    nav = {"visible": bool(aj["navegador_visible"])} if aj["usar_navegador"] and navegador.disponible() else None
    with cf.ThreadPoolExecutor(6) as ex:
        for host, items, err in ex.map(lambda t: _tienda(t, consulta, nav), activas):
            kept = 0
            for x in items:
                n = extract.normaliza(x["titulo"])
                if all(w in n for w in inc) and not any(w in n for w in exc):
                    if ocultar_agotados and x["agotado"]:
                        continue
                    if castellano and en_otro_idioma(x["titulo"]):
                        continue
                    if (pmin is not None and x["precio"] < pmin) or (pmax is not None and x["precio"] > pmax):
                        continue
                    x["tienda"] = host
                    res.append(x)
                    kept += 1
            informe[host] = {"encontrados": kept, "error": err if not kept else None}
    for t in manuales:
        informe[t["host"]] = {"encontrados": 0, "error": None, "manual": t["plantilla"].replace("{q}", quote_plus(consulta))}
    cfg.guarda(lista)  # persiste las plantillas descubiertas
    res.sort(key=lambda x: (x["agotado"], x["precio"]))
    ts = time.time()
    with bd.conecta() as c:
        c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id) VALUES(?,?,?,?,?,?,?,?)",
                      [(ts, consulta, x["tienda"], x["titulo"], x["url"], x["precio"], int(x["agotado"]), seg_id) for x in res])
    return res, informe
