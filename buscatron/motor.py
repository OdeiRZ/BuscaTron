"""Motor de búsqueda: consulta tiendas en paralelo, pagina, filtra y ordena."""
import concurrent.futures as cf
import re
import time

from . import ajustes, bd, fetch, extract, descubre, importar, navegador, tiendas as cfg

DESAFIO = "pide demostrar que eres humano (captcha). Para resolverlo tú, activa en Ajustes → Navegador la opción de abrir una ventana"
SIN_COINCIDENCIAS = "no tiene nada que coincida con la búsqueda"     # la tienda respondió, pero sin ese producto
MIN_HISTORIAL = 3
PAUSA = 0.6                 # segundos entre dos peticiones seguidas a la misma tienda (para no parecer un ataque)
MAX_INTENTOS = 4            # direcciones de búsqueda que se prueban en una tienda cuyo buscador no se conoce
REINTENTO_CAIDA = 600       # segundos sin volver a llamar a una tienda que no ha respondido a la conexión
_caidas = {}     # {host: cuándo dejó de responder}: no se le vuelve a llamar hasta pasado REINTENTO_CAIDA


def _candidatas(t, consulta, get):
    """URLs de búsqueda a probar, de más a menos fiable."""
    base = "https://" + t["host"]
    if t.get("plantilla"):
        return [(t["plantilla"], cfg.url_busqueda(t["plantilla"], consulta))], None
    st, home = get(base + "/")
    if st != 200:
        return [], f"su web no responde bien (error {st})"
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
            return [], "pide esperar por demasiadas consultas (error 429): vuelve a probar más tarde"
        if st != 200:
            err = ("rechaza las consultas automáticas" if st in (401, 403) else "no encuentra la página de búsqueda" if st == 404 else "su web no responde bien") + f" (error {st})"
            continue
        items, sig = extract.analiza(html, url, consulta, con_estado=con_estado)
        if not items:
            err = SIN_COINCIDENCIAS
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
    return [], err or "no encuentro su buscador: añade la dirección de búsqueda en «Editar la lista de tiendas»"


def _tienda(t, consulta, nav=None, paginas=1):
    """nav: None (sin navegador) o {'visible': bool}. Orden: método rápido y, si falla, navegador."""
    h = t["host"]
    estados = t.get("tipo") == "segunda_mano"
    caida = _caidas.get(h)
    if caida and time.time() - caida < REINTENTO_CAIDA:     # no insistir contra una web que no responde
        return h, [], f"no responde; se volverá a probar dentro de {int((caida + REINTENTO_CAIDA - time.time()) / 60) + 1} min"
    try:
        if not (nav and t.get("js")):
            r, err = _intenta(t, consulta, fetch.get, paginas, estados)
            if r:
                return h, r, None
        if nav is None:
            return h, [], (err or SIN_COINCIDENCIAS) + " (quizá solo la lea un navegador: activa «Usar Chrome» en Ajustes)"
        visible = nav["visible"]
        get = lambda u: navegador.get(u, visible=visible, esperar_humano=90 if visible else 0)
        plant = t.get("plantilla")
        r, err = _intenta(t, consulta, get, paginas, estados)
        if r:
            t["js"] = True
            return h, r, None
        if plant is None:
            t["plantilla"] = None
        return h, [], err or SIN_COINCIDENCIAS
    except navegador.Desafio:
        return h, [], DESAFIO
    except Exception as e:
        if isinstance(e, OSError):                           # tiempo agotado, conexión rechazada…
            _caidas[h] = time.time()
        return h, [], f"no se pudo conectar ({str(e)[:60]})"


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


# Palabras que no distinguen un producto de otro (editorial, tipo de producto, idioma, relleno de la tienda).
RUIDO = {"asmodee", "fantasy", "flight", "games", "ffg", "lcg", "el", "la", "los", "las", "de", "del", "al", "the", "of", "a", "y", "en",
         "card", "game", "cards", "juego", "juegos", "cartas", "expansion", "exp", "castellano", "espanol", "espanola", "edicion",
         "comprar", "barato", "producto", "agotado", "preventa", "nuevo", "nueva", "living", "eng", "es", "esp", "spanish"}


def clave_producto(titulo):
    """Identificador de un producto independiente de la tienda: sus palabras significativas, sin orden ni ruido.
    «Asmodee Marvel Champions: La Era de Apocalipsis» y «La Era de Apocalípsis - Marvel Champions» dan la misma clave."""
    palabras = set()
    for w in extract.normaliza(titulo).split():
        if w in RUIDO or (re.search(r"\d", w) and re.search(r"[a-z]", w) and len(w) >= 5):    # referencias como ASM631069
            continue
        palabras.add(w[:-1] if len(w) > 4 and w.endswith("s") else w)                            # «apocalipsis» = «apocalipsi», plurales
    return " ".join(sorted(palabras))


def grupo_de(titulo, frases=()):
    """Con el filtro «al menos una de estas», el producto es la frase que encaja (más fiable); si no, su clave."""
    n = extract.normaliza(titulo)
    for f in frases:
        if f in n or f.replace(" ", "") in n.replace(" ", ""):
            return "f:" + f
    return "c:" + clave_producto(titulo)


def pvp_de(precios):
    """PVP aproximado de un producto: el precio (redondeado al euro) que más se repite entre tiendas, con al menos 3
    tiendas; si hay empate, el más alto. None si no hay datos suficientes."""
    if len(precios) < 3:
        return None
    cuenta = {}
    for p in precios:
        cuenta.setdefault(round(p), []).append(p)
    mejor = max(cuenta.values(), key=lambda v: (len(v), max(v)))
    return round(max(mejor), 2) if len(mejor) >= 2 else None


def ignorados():
    with bd.conecta() as c:
        return {r["clave"]: dict(r) for r in c.execute("SELECT clave, titulo, ts FROM ignorados ORDER BY ts DESC")}


def ignora(titulo):
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO ignorados(clave, titulo, ts) VALUES(?,?,?)", (clave_producto(titulo), titulo, time.time()))


def deja_de_ignorar(clave):
    with bd.conecta() as c:
        c.execute("DELETE FROM ignorados WHERE clave=?", (clave,))


def objetivos():
    """Precio objetivo por producto: {grupo: {grupo, titulo, precio, ts}}. El grupo es el del motor («f:civil war» o «c:<clave>»)."""
    with bd.conecta() as c:
        return {r["clave"]: dict(r, grupo=r["clave"]) for r in c.execute("SELECT clave, titulo, precio, ts FROM objetivos ORDER BY titulo")}


def pon_objetivo(grupo, titulo, precio):
    if not grupo or precio is None or precio <= 0:
        raise ValueError("falta el producto o el precio")
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO objetivos(clave, titulo, precio, ts) VALUES(?,?,?,?)", (grupo, titulo, round(precio, 2), time.time()))


def quita_objetivo(grupo):
    with bd.conecta() as c:
        c.execute("DELETE FROM objetivos WHERE clave=?", (grupo,))


def objetivo_para(x, objs):
    """El objetivo que el usuario puso a este producto (por su grupo, su clave o, si se puso desde una campaña, por la frase)."""
    if not objs:
        return None
    o = objs.get(x.get("grupo")) or objs.get("c:" + (x.get("clave") or clave_producto(x["titulo"])))
    if o:
        return o["precio"]
    n = extract.normaliza(x["titulo"])
    for g, o in objs.items():
        f = g[2:] if g.startswith("f:") else None
        if f and (f in n or f.replace(" ", "") in n.replace(" ", "")):
            return o["precio"]
    return None


def rellena_claves():
    """Pone la clave de producto a los precios guardados antes de que existiera la columna (una vez; luego no hay nada que hacer)."""
    with bd.conecta() as c:
        titulos = [r[0] for r in c.execute("SELECT DISTINCT titulo FROM precios WHERE clave IS NULL")]
        c.executemany("UPDATE precios SET clave=? WHERE titulo=? AND clave IS NULL", [(clave_producto(t), t) for t in titulos])
    return len(titulos)


def historial_producto(grupo):
    """El mejor precio del producto en cualquier tienda (nuevo, con stock, sin preventas), hora a hora. Por horas y no por
    búsqueda: una búsqueda parcial (p. ej. al pegar resultados se consulta solo esa tienda) no debe parecer una subida."""
    segunda = {t["host"] for t in cfg.carga() if t.get("tipo") == "segunda_mano"}
    with bd.conecta() as c:
        if grupo.startswith("f:"):
            f = grupo[2:]
            titulos = [t for (t,) in c.execute("SELECT DISTINCT titulo FROM precios")
                       if f in extract.normaliza(t) or f.replace(" ", "") in extract.normaliza(t).replace(" ", "")]
            filas = []
            for i in range(0, len(titulos), 500):
                trozo = titulos[i:i + 500]
                filas += [dict(r) for r in c.execute("SELECT ts, precio, titulo, tienda, url FROM precios WHERE agotado=0 AND preventa=0 AND titulo IN (%s)"
                                                     % ",".join("?" * len(trozo)), trozo)]
        else:
            filas = [dict(r) for r in c.execute("SELECT ts, precio, titulo, tienda, url FROM precios WHERE agotado=0 AND preventa=0 AND clave=?",
                                                (grupo[2:] if grupo.startswith("c:") else grupo,))]
    puntos = {}
    for f in filas:
        if f["tienda"] in segunda:
            continue
        h = int(f["ts"] // 3600)
        if h not in puntos or f["precio"] < puntos[h]["precio"]:
            puntos[h] = {"ts": f["ts"], "precio": f["precio"], "tienda": f["tienda"]}
    pts = [puntos[t] for t in sorted(puntos)]
    if len(pts) > 240:
        paso = len(pts) / 240
        pts = [pts[int(i * paso)] for i in range(240)] + [pts[-1]]
    tiendas = len({f["tienda"] for f in filas if f["tienda"] not in segunda})
    return {"grupo": grupo, "titulo": grupo[2:] if grupo.startswith("f:") else (filas[-1]["titulo"] if filas else ""),
            "tienda": f"{tiendas} tiendas" if tiendas != 1 else "1 tienda", "puntos": pts, "por_producto": True}


def es_caida(err):
    """True si la tienda no respondió (red, captcha, error HTTP…); «no tiene nada que coincida» es una respuesta."""
    return bool(err) and not err.startswith(SIN_COINCIDENCIAS)


def registra_estado(informe, consulta):
    ts = time.time()
    filas = [(h, ts, consulta, i.get("brutos", i.get("encontrados", 0)), i.get("error") or "") for h, i in informe.items()
             if not i.get("manual") and h != "Búsqueda abierta"]
    with bd.conecta() as c:
        c.executemany("INSERT INTO estado_tiendas(host, ts, consulta, encontrados, error) VALUES(?,?,?,?,?)", filas)


def estado_tiendas(ultimas=10):
    """Por tienda: sus últimas consultas, cuántas dieron resultados y el último fallo; sugiere desactivar las que nunca dan nada."""
    lista = {t["host"]: t for t in cfg.carga()}
    out = []
    with bd.conecta() as c:
        for h, t in lista.items():
            filas = [dict(r) for r in c.execute("SELECT ts, encontrados, error FROM estado_tiendas WHERE host=? ORDER BY ts DESC LIMIT ?", (h, ultimas))]
            con = sum(1 for f in filas if f["encontrados"])
            ult_ok = next((f["ts"] for f in filas if f["encontrados"]), None)
            ult_err = next((f["error"] for f in filas if f["error"]), "")
            out.append({"host": h, "nombre": t.get("nombre") or h, "activa": t.get("activa", True), "manual": bool(t.get("manual")),
                        "consultas": len(filas), "con_resultados": con, "ultimo_ok": ult_ok, "ultimo_error": ult_err,
                        "sugerir_desactivar": bool(t.get("activa", True) and not t.get("manual") and len(filas) >= 6 and con == 0)})
    return sorted(out, key=lambda x: (not x["sugerir_desactivar"], x["manual"], -x["con_resultados"], x["nombre"]))


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
           castellano=True, preventas=False, con_envio=False, segunda_mano=False, abierta=False, region="es", paginas=None, idioma=None, alguna=""):
    """Devuelve (resultados ordenados por precio, informe por tienda).
    preventas: incluir productos en preventa · con_envio: ordenar por precio + envío · segunda_mano: incluir
    Vinted, Milanuncios… · abierta: buscar también en webs que no están en la lista (region: es | ue | mundo)."""
    lista = cfg.carga()
    aprendido = {t["host"]: (t.get("plantilla"), bool(t.get("js"))) for t in lista}    # para guardar luego solo lo que cambie
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
    frases = [f for f in (extract.normaliza(x).strip() for x in (alguna or "").split(",")) if f]   # basta con una (p. ej. nombres de campañas)
    exc = extract.normaliza(excluir).split()
    nav = {"visible": False} if aj["usar_navegador"] and navegador.disponible() else None   # siempre en segundo plano
    ocultos = set(ignorados())                                       # «ya lo tengo / no me interesa»

    def pasa(x, prior=None):
        x["idioma"], x["idioma_seguro"] = idioma_con_tienda(x["titulo"], prior)
        n = extract.normaliza(x["titulo"])
        if frases and not any(f in n or f.replace(" ", "") in n.replace(" ", "") for f in frases):
            return False
        return (all(w in n for w in inc) and not any(w in n for w in exc)
                and not (ocultar_agotados and x["agotado"])
                and not (x.get("preventa") and not preventas)
                and permite(x["idioma"], x["idioma_seguro"], modo)
                and clave_producto(x["titulo"]) not in ocultos)

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
        informe[host] = {"encontrados": kept, "error": err if not kept else None, "brutos": len(items), "error_tienda": err,
                         "caida": es_caida(err) and not kept}
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
        informe["Búsqueda abierta"] = {"encontrados": kept, "error": info if not kept else None,
                                       "caida": bool(info) and info.startswith("no se pudo") and not kept}   # «no encontré precios» sí respondió
    cfg.aplica_descubiertas({t["host"]: (t.get("plantilla"), bool(t.get("js"))) for t in lista       # plantillas descubiertas
                             if (t.get("plantilla"), bool(t.get("js"))) != aprendido[t["host"]]})
    registra_estado({h: {"brutos": i.get("brutos", 0), "error": i.get("error_tienda")} for h, i in informe.items() if "brutos" in i}, consulta)

    # producto (grupo) y PVP aproximado, con todas las tiendas; después, el filtro de precio
    precios_grupo = {}
    for x in res:
        x["grupo"] = grupo_de(x["titulo"], frases)
        x["clave"] = clave_producto(x["titulo"])
        if not x["agotado"] and x.get("origen") != "segunda_mano":            # la segunda mano no marca el precio de mercado
            precios_grupo.setdefault(x["grupo"], {})
            precios_grupo[x["grupo"]].setdefault(x["tienda"], x["precio"])          # una vez por tienda
    pvps = {g: pvp_de(list(p.values())) for g, p in precios_grupo.items()}
    for x in res:
        pvp = pvps.get(x["grupo"])
        x["pvp"] = pvp if pvp and pvp > x["precio"] else None
        x["descuento"] = round(100 * (1 - x["precio"] / pvp)) if x["pvp"] else None
    res = [x for x in res if not (pmin is not None and x["precio"] < pmin) and not (pmax is not None and x["precio"] > pmax)]
    for h, i in informe.items():
        if "brutos" in i:
            i["encontrados"] = sum(1 for x in res if x["tienda"] == h)
            if not i["encontrados"] and not i["error"] and i["brutos"]:
                i["error"] = "tiene productos, pero ninguno pasa tus filtros"
            i.pop("brutos", None)
            i.pop("error_tienda", None)

    previo = historial_previo({x["url"] for x in res})
    objs = objetivos()
    for x in res:
        x["objetivo_producto"] = objetivo_para(x, objs)
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
        c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      [(ts, consulta, x["tienda"], x["titulo"], x["url"], x["precio"], int(x["agotado"]), seg_id, int(x.get("preventa", False)), x["clave"])
                       for x in res])
    return res, informe
