"""Motor de búsqueda: consulta tiendas en paralelo, pagina, filtra y ordena."""
import concurrent.futures as cf
import re
import time

from . import ajustes, bd, fetch, extract, descubre, importar, navegador, tiendas as cfg

DESAFIO = "pide comprobación humana (captcha): activa «Mostrar la ventana» en Ajustes y resuélvela una vez"
MIN_HISTORIAL = 3
PAUSA = 0.6                 # segundos entre dos peticiones seguidas a la misma tienda (para no parecer un ataque)
MAX_INTENTOS = 4            # direcciones de búsqueda que se prueban en una tienda cuyo buscador no se conoce
REINTENTO_CAIDA = 600       # segundos sin volver a llamar a una tienda que no ha respondido a la conexión
_caidas = {}     # observaciones previas necesarias para hablar de «mínimo histórico»


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
    for n, (pl, url) in enumerate(urls[:MAX_INTENTOS]):
        if n:
            time.sleep(PAUSA)
        st, html = get(url)
        if st == 429:
            return [], "limita las peticiones (429): vuelve a probar dentro de un rato"
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
            time.sleep(PAUSA)
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
    caida = _caidas.get(h)
    if caida and time.time() - caida < REINTENTO_CAIDA:     # no insistir contra una web que no responde
        return h, [], f"no responde (se vuelve a intentar en {int((caida + REINTENTO_CAIDA - time.time()) / 60) + 1} min)"
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
        return h, [], DESAFIO
    except Exception as e:
        if isinstance(e, OSError):                           # tiempo agotado, conexión rechazada…
            _caidas[h] = time.time()
        return h, [], f"error: {str(e)[:70]}"


OTROS_IDIOMAS = re.compile(r"\b(ingles|inglesa|english|frances|francesa|francais|aleman|alemana|deutsch|italiano|italiana|portugues|portuguesa|polaco|polaca|neerlandes|ruso|rusa|players|playing time|minutes)\b|\bages \d+")
ES = re.compile(r"\b(castellano|espanol|espanola)\b")


EN_EXPLICITO = re.compile(r"\b(ingles|inglesa|english|players|playing time|minutes)\b|\bages \d+")
ES_PALABRAS = {"el", "la", "los", "las", "del", "de", "al", "para", "con", "sin", "una", "uno", "juego", "juegos", "carta", "cartas", "heroe", "heroes",
               "escenario", "escenarios", "jugadores", "tapete", "fundas", "funda", "ampliacion", "caja", "dados", "tablero", "campana"}
EN_PALABRAS = {"the", "of", "and", "for", "with", "your", "players", "ages", "minutes", "playing", "time", "game", "card", "cards",
               "scenario", "scenarios", "campaign", "playmat", "official", "core"}
MODOS_IDIOMA = ("castellano", "estricto", "todos")


def idioma_de(titulo):
    """Idioma de un producto según su título: (código, seguro).
    código: 'es' | 'en' | 'otro' | '?' (no se sabe). seguro: el título lo dice expresamente (Castellano, Inglés, Français…);
    si no, es una deducción por las palabras (artículos y términos españoles frente a ingleses)."""
    n = extract.normaliza(titulo)
    if ES.search(n):
        return "es", True
    if OTROS_IDIOMAS.search(n):
        return ("en" if EN_EXPLICITO.search(n) else "otro"), True
    palabras = set(n.split())
    es = len(palabras & ES_PALABRAS) + (1 if re.search(r"[ñáéíóúü¿¡]", titulo.lower()) else 0)
    en = len(palabras & EN_PALABRAS)
    if es >= 1 and es >= en:
        return "es", False
    if es == 0 and en >= 2:
        return "en", False
    return "?", False


def permite(cod, seguro, modo):
    """castellano: oculta solo lo que dice expresamente otro idioma · estricto: deja solo lo que está o parece en castellano ·
    todos: no filtra."""
    if modo == "todos":
        return True
    if modo == "estricto":
        return cod == "es"
    return not (cod in ("en", "otro") and seguro)


def modo_idioma(castellano=True, idioma=None):
    return idioma if idioma in MODOS_IDIOMA else ("castellano" if castellano else "todos")


def verifica_idioma(x, lista=None):
    """El idioma REAL del producto, leyendo su ficha («Idioma: Francés»): el título no basta, porque algunas tiendas
    (Amazon) traducen los títulos de sus anuncios. Devuelve 'es' | 'en' | 'otro' | None (no se pudo saber).
    Guarda el resultado 30 días para no volver a pedir la ficha."""
    if "btitem=" in x["url"]:
        return None                                       # lo importado a mano no tiene ficha que consultar
    with bd.conecta() as c:
        f = c.execute("SELECT codigo, ts FROM idiomas WHERE url=?", (x["url"],)).fetchone()
    if f and time.time() - f["ts"] < 30 * 86400:
        return f["codigo"] or None
    t = next((t for t in (lista or cfg.carga()) if t["host"] == x.get("tienda")), {})
    try:
        if t.get("js") and navegador.disponible() and ajustes.carga()["usar_navegador"]:
            st, html = navegador.get(x["url"], visible=False)
        else:
            st, html = fetch.get(x["url"], timeout=20)
    except Exception:
        return None
    if st != 200:
        return None
    valor = extract.idioma_pagina(html)
    cod = extract.codigo_idioma(valor)
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO idiomas(url, valor, codigo, ts) VALUES(?,?,?,?)", (x["url"], valor or "", cod or "", time.time()))
    return cod


FICHA_HORAS = 6       # el stock cambia: la ficha se vuelve a leer pasado este tiempo


def ficha(x, lista=None):
    """Lo que dice la ficha del producto: {'idioma': 'es'|'en'|'otro'|None, 'agotado': bool|None, 'preventa': bool|None}.
    None = no se pudo saber. Sirve para no avisar de algo que en su ficha está agotado, en preventa o en otro idioma
    (el listado de algunas tiendas no lo dice). Se guarda unas horas para no repetir la consulta."""
    nada = {"idioma": None, "agotado": None, "preventa": None}
    if "btitem=" in x["url"]:
        return nada                                       # lo importado a mano no tiene ficha
    with bd.conecta() as c:
        f = c.execute("SELECT idioma, agotado, preventa, ts FROM fichas WHERE url=?", (x["url"],)).fetchone()
    if f and time.time() - f["ts"] < FICHA_HORAS * 3600:
        return {"idioma": f["idioma"] or None, "agotado": None if f["agotado"] is None else bool(f["agotado"]),
                "preventa": None if f["preventa"] is None else bool(f["preventa"])}
    t = next((t for t in (lista or cfg.carga()) if t["host"] == x.get("tienda")), {})
    try:
        if t.get("js") and navegador.disponible() and ajustes.carga()["usar_navegador"]:
            st, html = navegador.get(x["url"], visible=False)
        else:
            st, html = fetch.get(x["url"], timeout=20)
    except Exception:
        return nada
    if st != 200:
        return nada
    datos = extract.datos_producto(html, x["url"]) or {}
    r = {"idioma": extract.codigo_idioma(extract.idioma_pagina(html)),
         "agotado": datos.get("agotado") if datos else None, "preventa": datos.get("preventa") if datos else None}
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO fichas(url, idioma, agotado, preventa, ts) VALUES(?,?,?,?,?)",
                  (x["url"], r["idioma"] or "", None if r["agotado"] is None else int(r["agotado"]),
                   None if r["preventa"] is None else int(r["preventa"]), time.time()))
    return r


def pasa_idioma(titulo, modo):
    return permite(*idioma_de(titulo), modo)


def prior_tienda(items):
    """'es' si la mayoría de los títulos reconocibles de una tienda están en castellano (así los que no dicen nada se
    tratan como «parece castellano»); None si la tienda es mixta, como Amazon."""
    cods = [idioma_de(x["titulo"])[0] for x in items]
    es, otros = cods.count("es"), sum(1 for c in cods if c in ("en", "otro"))
    return "es" if es >= 3 and es >= 2 * otros else None


def idioma_con_tienda(titulo, prior):
    cod, seguro = idioma_de(titulo)
    if cod == "?" and prior == "es":
        return "es", False
    return cod, seguro


def en_otro_idioma(titulo):
    """True si el título indica claramente otro idioma y no menciona el castellano."""
    cod, seguro = idioma_de(titulo)
    return cod in ("en", "otro") and seguro


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
           castellano=True, preventas=False, con_envio=False, segunda_mano=False, abierta=False, region="es", paginas=None, idioma=None):
    """Devuelve (resultados ordenados por precio, informe por tienda).
    preventas: incluir productos en preventa · con_envio: ordenar por precio + envío · segunda_mano: incluir
    Vinted, Milanuncios… · abierta: buscar también en webs que no están en la lista (region: es | ue | mundo)."""
    lista = cfg.carga()
    aj = ajustes.carga()
    paginas = paginas or int(aj.get("paginas") or 1)
    modo = modo_idioma(castellano, idioma)
    activas = [t for t in lista if (t["host"] in hosts if hosts is not None else t.get("activa", True))]
    if not segunda_mano:
        activas = [t for t in activas if t.get("tipo") != "segunda_mano"]
    manuales = [t for t in activas if t.get("manual") and t.get("plantilla")]
    activas = [t for t in activas if t not in manuales]
    por_host = {t["host"]: t for t in lista}
    inc = extract.normaliza(incluir).split()
    exc = extract.normaliza(excluir).split()
    nav = {"visible": False} if aj["usar_navegador"] and navegador.disponible() else None   # siempre en segundo plano

    def pasa(x, prior=None):
        x["idioma"], x["idioma_seguro"] = idioma_con_tienda(x["titulo"], prior)
        n = extract.normaliza(x["titulo"])
        return (all(w in n for w in inc) and not any(w in n for w in exc)
                and not (ocultar_agotados and x["agotado"])
                and not (x.get("preventa") and not preventas)
                and permite(x["idioma"], x["idioma_seguro"], modo)
                and not (pmin is not None and x["precio"] < pmin) and not (pmax is not None and x["precio"] > pmax))

    res, informe = [], {}
    with cf.ThreadPoolExecutor(6) as ex:
        resultados = list(ex.map(lambda t: _tienda(t, consulta, nav, paginas), activas))
    if nav and aj["navegador_visible"]:
        # Solo las tiendas que piden comprobar que eres humano se reintentan con ventana, de una en una,
        # para que el usuario pueda resolverlo; el resto se consulta sin que salga nada en pantalla.
        for i, (host, items, err) in enumerate(resultados):
            if err == DESAFIO:
                resultados[i] = _tienda(por_host[host], consulta, {"visible": True}, paginas)
    for host, items, err in resultados:
        kept = 0
        prior = prior_tienda(items)
        for x in items:
            if pasa(x, prior):
                x["tienda"], x["origen"] = host, por_host[host].get("tipo", "tienda")
                res.append(x)
                kept += 1
        informe[host] = {"encontrados": kept, "error": err if not kept else None}
    for t in manuales:
        informe[t["host"]] = {"encontrados": 0, "error": None, "manual": cfg.url_busqueda(t["plantilla"], consulta)}
        previos = [x for x in importar.vigentes(t["host"], consulta) if pasa(x)]      # lo que el usuario pegó a mano
        for x in previos:
            x["tienda"], x["origen"] = t["host"], t.get("tipo", "tienda")
            res.append(x)
        if previos:
            informe[t["host"]].update(importados=len(previos), importado_ts=max(x["importado"] for x in previos))
    if abierta:
        from . import abierta as web
        conocidos = {t["host"].replace("www.", "") for t in lista}
        items, info = web.busca(consulta, region=region, excluir_hosts=conocidos, castellano=(modo != "todos"), nav=nav)
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
        if "idioma" not in x:
            x["idioma"], x["idioma_seguro"] = idioma_de(x["titulo"])
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
