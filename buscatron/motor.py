"""Motor de búsqueda: consulta tiendas en paralelo, pagina, filtra y ordena."""
import concurrent.futures as cf
import re
import time

from . import ajustes, bd, fetch, extract, descubre, navegador, tiendas as cfg

MIN_HISTORIAL = 3     # observaciones previas necesarias para hablar de «mínimo histórico»


def _candidatas(t, consulta, get):
    """URLs de búsqueda a probar, de más a menos fiable."""
    base = "https://" + t["host"]
    if t.get("plantilla"):
        return [(t["plantilla"], cfg.url_busqueda(t["plantilla"], consulta))], None
    st, home = get(base + "/")
    if st != 200:
        return [], f"portada HTTP {st}"
    pl = descubre.plantilla(home, base + "/")
    urls = [(pl, cfg.url_busqueda(pl, consulta))] if pl else []
    urls += [(base + p, cfg.url_busqueda(base + p, consulta)) for p in cfg.PLANTILLAS]
    return urls, None


def _intenta(t, consulta, get, paginas=1, con_estado=False):
    urls, err = _candidatas(t, consulta, get)
    if err:
        return [], err
    for pl, url in urls:
        st, html = get(url)
        if st != 200:
            err = f"HTTP {st}"
            continue
        items, sig = extract.analiza(html, url, consulta, con_estado=con_estado)
        if not items:
            err = "sin resultados"
            continue
        t["plantilla"] = pl
        paginas_vistas, urls_vistas = {url}, {x["url"] for x in items}
        for _ in range(max(paginas, 1) - 1):          # páginas siguientes, mientras aporten productos nuevos
            if not sig or sig in paginas_vistas:
                break
            paginas_vistas.add(sig)
            try:
                st2, html2 = get(sig)
            except Exception:
                break
            if st2 != 200:
                break
            mas, sig2 = extract.analiza(html2, sig, consulta, con_estado=con_estado)
            nuevos = [x for x in mas if x["url"] not in urls_vistas]
            if not nuevos:
                break
            items += nuevos
            urls_vistas |= {x["url"] for x in nuevos}
            sig = sig2
        return items, None
    return [], err or "sin buscador detectable"


def _tienda(t, consulta, nav=None, paginas=1):
    """nav: None (sin navegador) o {'visible': bool}. Orden: método rápido y, si falla, navegador."""
    h = t["host"]
    estados = t.get("tipo") == "segunda_mano"
    try:
        if not (nav and t.get("js")):
            r, err = _intenta(t, consulta, fetch.get, paginas, estados)
            if r:
                return h, r, None
        if nav is None:
            return h, [], (err or "sin resultados") + " (puede cargar con JavaScript: activa el navegador en Ajustes)"
        visible = nav["visible"]
        get = lambda u: navegador.get(u, visible=visible, esperar_humano=90 if visible else 0)
        plant = t.get("plantilla")
        r, err = _intenta(t, consulta, get, paginas, estados)
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


def envio_de(t, precio):
    """Gastos de envío configurados para la tienda (0 si supera el mínimo gratuito; None si no se conocen)."""
    gratis, coste = t.get("envio_gratis"), t.get("envio")
    if gratis is not None and precio >= gratis:
        return 0.0
    return coste


def historial_previo(urls):
    """{url: (precio_mínimo, observaciones)} de lo ya guardado para esos artículos."""
    urls, out = list(urls), {}
    with bd.conecta() as c:
        for i in range(0, len(urls), 500):
            trozo = urls[i:i + 500]
            q = "SELECT url, MIN(precio) mn, COUNT(*) n FROM precios WHERE agotado=0 AND url IN (%s) GROUP BY url" % ",".join("?" * len(trozo))
            for r in c.execute(q, trozo):
                out[r["url"]] = (r["mn"], r["n"])
    return out


def historial_de(url):
    """Precios guardados de un artículo (uno por revisión, el más bajo si hay varios) y datos para la gráfica."""
    with bd.conecta() as c:
        filas = [dict(r) for r in c.execute("SELECT ts, precio, titulo, tienda FROM precios WHERE url=? AND agotado=0 ORDER BY ts", (url,))]
    puntos = {}
    for f in filas:
        puntos[f["ts"]] = min(f["precio"], puntos.get(f["ts"], f["precio"]))
    pts = [{"ts": t, "precio": p} for t, p in sorted(puntos.items())]
    if len(pts) > 240:                                      # para que la gráfica no se sature
        paso = len(pts) / 240
        pts = [pts[int(i * paso)] for i in range(240)] + [pts[-1]]
    return {"url": url, "titulo": filas[-1]["titulo"] if filas else "", "tienda": filas[-1]["tienda"] if filas else "", "puntos": pts}


def buscar(consulta, incluir="", excluir="", ocultar_agotados=True, hosts=None, pmin=None, pmax=None, seg_id=None,
           castellano=True, preventas=False, con_envio=False, segunda_mano=False, abierta=False, region="es", paginas=None):
    """Devuelve (resultados ordenados por precio, informe por tienda).
    preventas: incluir productos en preventa · con_envio: ordenar por precio + envío · segunda_mano: incluir
    Vinted, Milanuncios… · abierta: buscar también en webs que no están en la lista (region: es | ue | mundo)."""
    lista = cfg.carga()
    aj = ajustes.carga()
    paginas = paginas or int(aj.get("paginas") or 1)
    activas = [t for t in lista if (t["host"] in hosts if hosts is not None else t.get("activa", True))]
    if not segunda_mano:
        activas = [t for t in activas if t.get("tipo") != "segunda_mano"]
    manuales = [t for t in activas if t.get("manual") and t.get("plantilla")]
    activas = [t for t in activas if t not in manuales]
    por_host = {t["host"]: t for t in lista}
    inc = extract.normaliza(incluir).split()
    exc = extract.normaliza(excluir).split()
    nav = {"visible": bool(aj["navegador_visible"])} if aj["usar_navegador"] and navegador.disponible() else None

    def pasa(x):
        n = extract.normaliza(x["titulo"])
        return (all(w in n for w in inc) and not any(w in n for w in exc)
                and not (ocultar_agotados and x["agotado"])
                and not (x.get("preventa") and not preventas)
                and not (castellano and en_otro_idioma(x["titulo"]))
                and not (pmin is not None and x["precio"] < pmin) and not (pmax is not None and x["precio"] > pmax))

    res, informe = [], {}
    with cf.ThreadPoolExecutor(6) as ex:
        for host, items, err in ex.map(lambda t: _tienda(t, consulta, nav, paginas), activas):
            kept = 0
            for x in items:
                if pasa(x):
                    x["tienda"], x["origen"] = host, por_host[host].get("tipo", "tienda")
                    res.append(x)
                    kept += 1
            informe[host] = {"encontrados": kept, "error": err if not kept else None}
    for t in manuales:
        informe[t["host"]] = {"encontrados": 0, "error": None, "manual": cfg.url_busqueda(t["plantilla"], consulta)}
    if abierta:
        from . import abierta as web
        conocidos = {t["host"].replace("www.", "") for t in lista}
        items, info = web.busca(consulta, region=region, excluir_hosts=conocidos, castellano=castellano, nav=nav)
        kept = 0
        for x in items:
            if pasa(x):
                x["origen"] = "web"
                res.append(x)
                kept += 1
        informe["Búsqueda abierta"] = {"encontrados": kept, "error": info if not kept else None}
    cfg.guarda(lista)  # persiste las plantillas descubiertas

    previo = historial_previo({x["url"] for x in res})
    for x in res:
        t = por_host.get(x["tienda"], {})
        x["envio"] = envio_de(t, x["precio"])
        x["total"] = round(x["precio"] + (x["envio"] or 0), 2)
        mn, n = previo.get(x["url"], (None, 0))
        x["n_hist"], x["minimo"] = n, bool(n >= MIN_HISTORIAL and x["precio"] <= mn)
    res.sort(key=lambda x: (x["agotado"], x["total"] if con_envio else x["precio"]))
    ts = time.time()
    with bd.conecta() as c:
        c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa) VALUES(?,?,?,?,?,?,?,?,?)",
                      [(ts, consulta, x["tienda"], x["titulo"], x["url"], x["precio"], int(x["agotado"]), seg_id, int(x.get("preventa", False))) for x in res])
    return res, informe
