"""Motor de búsqueda: consulta tiendas en paralelo, pagina, filtra y ordena."""
import concurrent.futures as cf
import re
import threading
import time

from . import ajustes, bd, fetch, extract, descubre, importar, navegador, progreso, tiendas as cfg

DESAFIO_SIN_RESOLVER = ("pide demostrar que eres humano (captcha): se abrió una ventana de Chrome, pero no se resolvió en 90 s. "
                        "Resuélvelo en esa ventana en la próxima búsqueda y la sesión quedará guardada")
DESAFIO = "pide demostrar que eres humano (captcha). Para resolverlo tú, activa en Ajustes → Navegador la opción de abrir una ventana"
SIN_COINCIDENCIAS = "no tiene nada que coincida con la búsqueda"     # la tienda respondió, pero sin ese producto
MIN_HISTORIAL = 3
PAUSA = 0.6                 # segundos entre dos peticiones seguidas a la misma tienda (para no parecer un ataque)
MAX_INTENTOS = 4            # direcciones de búsqueda que se prueban en una tienda cuyo buscador no se conoce
REINTENTO_CAIDA = 600       # segundos sin volver a llamar a una tienda que no ha respondido a la conexión (la 1.ª vez)
MAX_CAIDA = 86400           # …y cada vez que vuelve a fallar se espera 6 veces más (10 min, 1 h, 6 h), hasta 24 h
RECHAZOS_PARA_ESPERAR = 2   # 403 seguidos antes de dejar de llamarla un tiempo (un 429 basta con uno)
BLOQUEO_FALLOS = 3          # esperas seguidas por rechazo tras las que se da por bloqueada (se prueba solo su portada)
_rechazos = {}   # {host: 403/401 seguidos}
# Rechazo en una página siguiente durante la consulta en curso. Cada tienda se consulta entera en un mismo hilo
# (_tienda_viva → _intenta), así que la marca es de ese hilo: búsquedas simultáneas no se mezclan.
_hilo_rechazo = threading.local()


_caidas = {}     # {host: cuándo dejó de responder} (lo que queda en memoria; lo que manda está en la tabla «caidas»)


def espera_caida(fallos):
    return min(REINTENTO_CAIDA * 6 ** max(fallos - 1, 0), MAX_CAIDA)


def caida_hasta(h):
    """Hasta cuándo no se llama a una tienda que no conecta (0 si se puede). Insistir contra una web que ha cortado
    tu conexión alarga el bloqueo (Dungeon Marvels bloqueó la IP de casa el 9/11/2026 tras una ráfaga de pruebas)."""
    with bd.conecta() as c:
        f = c.execute("SELECT desde, fallos FROM caidas WHERE host=?", (h,)).fetchone()
    return f["desde"] + espera_caida(f["fallos"]) if f else 0


def marca_caida(h):
    with bd.conecta() as c:
        c.execute("INSERT INTO caidas(host, desde, fallos) VALUES(?,?,1) ON CONFLICT(host) DO UPDATE SET desde=excluded.desde, fallos=fallos+1",
                  (h, time.time()))
    _caidas[h] = time.time()


def limpia_caida(h):
    if _caidas.pop(h, None) is not None or caida_hasta(h):
        with bd.conecta() as c:
            c.execute("DELETE FROM caidas WHERE host=?", (h,))


def es_rechazo(err):
    """La tienda respondió, pero rechazando la consulta (403/401) o pidiendo esperar (429)."""
    return bool(err) and any(f"(error {c})" in err for c in (401, 403, 429))


def bloquea(h):
    """Desactiva una tienda que sigue rechazando tus consultas: desde ahí no recibe ninguna petición (ritmo.py) hasta que
    la reactives tú con su chip. Lo que pegues de ella sigue contando."""
    with cfg.cerrojo:
        lista = cfg.carga()
        t = next((t for t in lista if t["host"] == h), None)
        if not t or t.get("bloqueo"):
            return
        t["activa"] = False
        antes = bool(t.get("manual"))
        t["manual"] = True             # ninguna petición más (ni para ver si vuelve): la reactivas tú cuando te desbloquee
        t["bloqueo"] = {"desde": time.time(), "manual": antes}      # cómo la tenías, para devolvérsela al reactivarla
        cfg.guarda(lista)
    with bd.conecta() as c:
        c.execute("DELETE FROM caidas WHERE host=?", (h,))
    _caidas.pop(h, None)
    _rechazos.pop(h, None)
    # Sin aviso por Telegram: allí solo van los cambios de límites y objetivos de tus juegos. El bloqueo se ve en
    # Ajustes → Estado de las tiendas.


def registra_rechazo(h, err):
    """Un 429, o varios 403 seguidos, hacen esperar a la tienda como si no respondiera; si sigue igual, se bloquea."""
    n = _rechazos[h] = _rechazos.get(h, 0) + 1
    if "(error 429)" not in err and n < RECHAZOS_PARA_ESPERAR:
        return
    marca_caida(h)
    with bd.conecta() as c:
        f = c.execute("SELECT fallos FROM caidas WHERE host=?", (h,)).fetchone()
    if f and f["fallos"] >= BLOQUEO_FALLOS:
        bloquea(h)


def _cuando(segundos):
    m = int(segundos / 60) + 1
    return f"{m} min" if m < 90 else f"{round(m / 60)} h"


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
        if st in (401, 403):
            return [], f"rechaza las consultas automáticas (error {st})"     # no se insiste con otras direcciones
        if st != 200:
            err = ("no encuentra la página de búsqueda" if st == 404 else "su web no responde bien") + f" (error {st})"
            continue
        items, sig = extract.analiza(html, url, consulta, con_estado=con_estado)
        if items and (t.get("envio") is None or t.get("envio_gratis") is None):
            _apunta_envio(t["host"], html)
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
            if st2 in (401, 403, 429):
                registra_rechazo(t["host"], f"rechazó la página siguiente (error {st2})")
                _hilo_rechazo.hubo = True            # que el éxito de la primera página no lo borre
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


JUEGO = re.compile(r"\b(juegos?|games?|cartas|expansion|tablero|boardgame|lcg|cooperativo|miniaturas|rol)\b")


# Lo que seguro que NO es un juego de mesa, en cualquier tienda. Solo cosas inequívocas (ropa, calzado, herramientas, jardín): un
# juego no tiene que decir «juego» para valer, así que lo que no se reconoce se queda.
NO_JUEGO = re.compile(r"\b(zapatillas?|deportivas|camisetas?|sudaderas?|calcetines|gorras?|pantalon(?:es)?|chaquetas?|talla\s+\d+|rociador|protector(?:es)? de pantalla|correas?|pulseras?|coche de juguete|"
                      r"pulverizador|manguera|taladro|cortacesped|desbrozadora|guantes|"
                      r"figuras?\s+(?:de\s+)?\d+\s*cm|marvel\s+legends|funko)\b")      # figuras de colección («Marvel Legends figura 15cm … Civil Warrior»)
TIPOS = ("juego", "expansion", "complemento", "accesorio", "lote")
# Varios productos juntos («Pack 3 expansiones», «Lote Marvel Champions + Civil War», «Bundle»): no es el juego suelto
LOTE = re.compile(r"\b(lote|bundle|megapack)\b|\b(?:[2-9]|1\d)\s+expansiones\b|\bpack\s+(?:de\s+)?(?:[2-9]|1\d)\s+(?:juegos|cajas|productos)\b|\bpack\s+(?:de\s+)?expansiones\b")
ACCESORIO = re.compile(r"\b(fundas?|sleeves?|tapetes?|playmat|game ?mat|mat|neopreno|organizador|inserto|insert|deck ?box|portacartas|protectores|dividers?|separadores|divisores)\b")
COMPLEMENTO = re.compile(r"\b(add ?on|addon|character|promos?|mini ?expansion)\b")
# Los packs de héroe, villano, escenario o campaña son expansiones oficiales (Marvel Champions…), digan o no «expansión».
EXPANSION = re.compile(r"\b(expansion|expansiones|ampliacion|(?:pack|paquete)s? (?:de )?(?:heroe|villano|escenario|escenico|campana|personajes?)|(?:hero|villain|scenario|campaign) pack)\b")


def es_no_juego(titulo):
    return bool(NO_JUEGO.search(extract.normaliza(titulo)))


def tipo_de(titulo):
    """Qué es, por su título: 'accesorio' (fundas, tapetes, organizadores), 'complemento' (add-on, personaje, promo),
    'expansion' (también los packs de héroe, escenario o campaña) o, si no dice nada de eso, 'juego' (el juego base o cualquier cosa que no se reconozca: nunca se descarta por no
    decir que es un juego)."""
    # «Dune Imperium: Linajes (+ Promo)» es la expansión que trae una promo de regalo, no la promo
    n = extract.normaliza(re.sub(r"(?i)[+]\s*promos?|con promos?", " ", titulo))
    for tipo, rx in (("lote", LOTE), ("accesorio", ACCESORIO), ("complemento", COMPLEMENTO), ("expansion", EXPANSION)):
        if rx.search(n):
            return tipo
    return "juego"


def exige_juego(consulta):
    """Con una sola palabra de búsqueda, las tiendas generalistas devuelven de todo: solo valen los juegos."""
    return len(extract.normaliza(consulta).split()) == 1


def solo_juego(tienda, titulo, consulta):
    """¿Este resultado vale? Falso si es de una tienda generalista, la búsqueda es de una sola palabra y el título no parece el de
    un juego («Talla: 45 - Under Armour Zapatillas Charged Vantage 2», «Rociador Berthoud Vantage»)."""
    return not (tienda in cfg.GENERALISTAS and exige_juego(consulta) and not JUEGO.search(extract.normaliza(titulo)))


def _tienda(t, consulta, nav=None, paginas=1):
    """La tienda y, si tiene búsqueda de repaso (cfg.REPASO: Amazon en todas sus secciones), lo que esta añada."""
    h, items, err = _tienda_base(t, consulta, nav, paginas)
    repaso = cfg.REPASO.get(h)
    if repaso and not es_caida(err):
        vistas = {x["url"] for x in items}
        nuevos = [x for x in _repaso(t, repaso, consulta, nav) if x["url"] not in vistas]
        if nuevos:
            items, err = items + nuevos, None
    return h, items, err


def _repaso(t, plantilla, consulta, nav):
    """Una página de la búsqueda de repaso, solo con lo que por su título es un juego. Sirve para los juegos que la tienda
    tiene mal clasificados (Eternal Decks no está en «Juguetes y juegos» de Amazon) sin traer relojes ni zapatillas."""
    url = cfg.url_busqueda(plantilla, consulta)
    try:
        time.sleep(PAUSA)
        if nav and t.get("js"):
            st, html = navegador.get(url, visible=nav["visible"], esperar_humano=90 if nav["visible"] else 0)
        else:
            st, html = fetch.get(url)
    except Exception:                               # el repaso nunca estropea lo ya encontrado
        return []
    if st != 200:
        return []
    return [x for x in extract.analiza(html, url, consulta)[0] if JUEGO.search(extract.normaliza(x["titulo"]))]


def _tienda_base(t, consulta, nav=None, paginas=1):
    """nav: None (sin navegador) o {'visible': bool}. Orden: método rápido y, si falla, navegador."""
    h = t["host"]
    estados = t.get("tipo") == "segunda_mano"
    hasta = caida_hasta(h)
    if hasta > time.time():                                  # no insistir contra una web que no responde
        return h, [], f"no responde; se volverá a probar dentro de {_cuando(hasta - time.time())}"
    try:
        return _tienda_viva(t, consulta, nav, paginas, estados)
    except navegador.Desafio:
        marca_caida(h)                 # sin insistir: como una tienda caída, se vuelve a probar cada vez más tarde
        return h, [], DESAFIO
    except Exception as e:
        if isinstance(e, OSError) and "navegador" not in str(e):   # tiempo agotado, conexión rechazada… (no la cola de Chrome)
            marca_caida(h)
        return h, [], f"no se pudo conectar ({str(e)[:60]})"


def _tienda_viva(t, consulta, nav, paginas, estados):
    h = t["host"]
    _hilo_rechazo.hubo = False
    r = _tienda_consulta(t, consulta, nav, paginas, estados)
    if es_rechazo(r[2]):                                     # responde, pero rechazándote: no insistir
        registra_rechazo(h, r[2])
    elif _hilo_rechazo.hubo:
        pass                                                 # respondió, pero rechazó una página siguiente: no se olvida
    else:
        _rechazos.pop(h, None)
        limpia_caida(h)                                      # ha respondido: se olvida que estuvo caída
    return r


def _tienda_consulta(t, consulta, nav, paginas, estados):
    h = t["host"]
    if not (nav and t.get("js")):
        try:
            r, err = _intenta(t, consulta, fetch.get, paginas, estados)
        except OSError as e:
            # A Python le falta a veces el certificado intermedio de una web (Comic Stores, Generación X…) que Chrome sí resuelve: no es
            # un bloqueo, así que se lee con el navegador. Cualquier otro fallo de conexión sigue siendo «no responde».
            if not (nav and "CERTIFICATE_VERIFY_FAILED" in str(e)):
                raise
            r, err = [], None
        if r:
            return h, r, None
        if es_rechazo(err):
            return h, [], err          # nos ha rechazado: pedírselo enseguida con Chrome es insistir
    if nav is None:
        return h, [], (err or SIN_COINCIDENCIAS) + " (quizá solo la lea un navegador: activa «Usar Chrome» en Ajustes)"
    leida = not t.get("js") and err == SIN_COINCIDENCIAS          # su página se leyó bien, solo que sin ese producto
    if leida and _sin_chrome.get(h, 0) > time.time():
        return h, [], err
    visible = nav["visible"]
    get = lambda u: navegador.get(u, visible=visible, esperar_humano=90 if visible else 0)
    plant = t.get("plantilla")
    r, err = _intenta(t, consulta, get, paginas, estados)
    if r:
        t["js"] = True
        return h, r, None
    if plant is None:
        t["plantilla"] = None
    if leida and (err or SIN_COINCIDENCIAS) == SIN_COINCIDENCIAS:
        # Chrome tampoco encontró nada: la lectura directa ya bastaba. Unos días sin repetirlo con Chrome, que es uno solo
        # para todas las tiendas y con 70 la cola de páginas hacía caducar las consultas de las demás.
        _sin_chrome[h] = time.time() + SIN_CHROME_DIAS * 86400
    return h, [], err or SIN_COINCIDENCIAS


_sin_chrome = {}
SIN_CHROME_DIAS = 3


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
    if not _ficha_permitida(t, x):
        return None                                       # «solo enlace», caída o bloqueada: su ficha no se consulta
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
FICHA_FALLO_HORAS = 2     # una ficha que no se pudo leer no se vuelve a pedir hasta pasado este tiempo


def _ficha_permitida(t, x):
    """¿Se puede leer la ficha de un producto de esta tienda? No si es «solo enlace» (o de las que nunca se consultan),
    está bloqueada o está esperando tras no responder o rechazarnos."""
    h = t.get("host") or x.get("tienda") or ""
    return not (t.get("manual") or cfg.nunca(h) or t.get("bloqueo") or caida_hasta(h) > time.time())


def ficha(x, lista=None):
    """Lo que dice la ficha del producto: {'idioma': 'es'|'en'|'otro'|None, 'agotado': bool|None, 'preventa': bool|None}.
    None = no se pudo saber. Sirve para no avisar de algo que en su ficha está agotado, en preventa o en otro idioma
    (el listado de algunas tiendas no lo dice). Se guarda unas horas para no repetir la consulta."""
    nada = {"idioma": None, "agotado": None, "preventa": None}
    t = next((t for t in (lista or cfg.carga()) if t["host"] == x.get("tienda")), {})
    if "btitem=" in x["url"] or x.get("importado") or not _ficha_permitida(t, x):
        return nada         # pegado a mano, tienda «solo enlace», caída o bloqueada: su ficha no se consulta
    with bd.conecta() as c:
        f = c.execute("SELECT idioma, agotado, preventa, ts FROM fichas WHERE url=?", (x["url"],)).fetchone()
    if f and time.time() - f["ts"] < FICHA_HORAS * 3600:
        return {"idioma": f["idioma"] if f["idioma"] in ("es", "en", "otro") else None,
                "agotado": None if f["agotado"] is None else bool(f["agotado"]),
                "preventa": None if f["preventa"] is None else bool(f["preventa"])}
    try:
        if t.get("js") and navegador.disponible() and ajustes.carga()["usar_navegador"]:
            st, html = navegador.get(x["url"], visible=False)
        else:
            st, html = fetch.get(x["url"], timeout=20)
    except Exception:
        st = None
    if st != 200:                 # se recuerda el fallo un rato: si no, se pediría otra vez en cada búsqueda
        with bd.conecta() as c:
            c.execute("INSERT INTO fichas(url, idioma, agotado, preventa, ts) VALUES(?,?,?,?,?) "     # el idioma ya leído se conserva
                      "ON CONFLICT(url) DO UPDATE SET agotado=NULL, preventa=NULL, ts=excluded.ts",
                      (x["url"], "", None, None, time.time() - (FICHA_HORAS - FICHA_FALLO_HORAS) * 3600))
        return nada
    datos = extract.datos_producto(html, x["url"]) or {}
    r = {"idioma": extract.codigo_idioma(extract.idioma_pagina(html)),
         "agotado": datos.get("agotado") if datos else None, "preventa": datos.get("preventa") if datos else None}
    if r["agotado"] is None and not r["preventa"]:     # los datos no lo dicen: lo que pone la ficha («Avisadme cuando…»)
        r["agotado"] = extract.sin_stock_pagina(html)
    if r["idioma"] is None and "amazon." in x["url"]:  # sin campo «Idioma»: de dónde son sus opiniones
        r["idioma"] = extract.idioma_por_resenas(html)
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


FICHAS_POR_BUSQUEDA = 3   # fichas que se leen por tienda en cada búsqueda para saber su stock (las más baratas; cada
                          # una espera su turno del ritmo por tienda)


def stock_de_fichas(urls):
    """{url: (agotado, preventa)} de las fichas leídas hace menos de FICHA_HORAS que lo dicen (None = no lo dice)."""
    urls, r = list(dict.fromkeys(urls)), {}
    with bd.conecta() as c:
        for i in range(0, len(urls), 500):
            trozo = urls[i:i + 500]
            for f in c.execute("SELECT url, agotado, preventa FROM fichas WHERE ts > ? AND (agotado IS NOT NULL OR preventa IS NOT NULL) "
                               "AND url IN (%s)" % ",".join("?" * len(trozo)), [time.time() - FICHA_HORAS * 3600] + trozo):
                r[f["url"]] = (None if f["agotado"] is None else bool(f["agotado"]), None if f["preventa"] is None else bool(f["preventa"]))
    return r


def corrige_stock(res, lista):
    """El listado de algunas tiendas no dice si queda stock: manda lo que ya se leyó en las fichas y, en las tiendas de
    cfg.STOCK_EN_FICHA, se leen las fichas de sus resultados más baratos (pocas y al ritmo de la tienda)."""
    stock = stock_de_fichas([x["url"] for x in res])
    pedir = {}
    for x in sorted(res, key=lambda x: x["precio"]):
        if x["url"] not in stock and x.get("tienda") in cfg.STOCK_EN_FICHA and len(pedir.setdefault(x["tienda"], [])) < FICHAS_POR_BUSQUEDA:
            pedir[x["tienda"]].append(x)
    for xs in pedir.values():
        for x in xs:
            f = ficha(x, lista)
            stock[x["url"]] = (f["agotado"], f["preventa"])
    for x in res:
        agotado, preventa = stock.get(x["url"], (None, None))
        if agotado is not None:
            x["agotado"] = agotado
        if preventa:
            x["preventa"] = True


def idiomas_de_fichas(urls):
    """{url: 'es'|'en'|'otro'} de las fichas ya leídas que dicen su idioma."""
    urls, r = list(dict.fromkeys(urls)), {}
    with bd.conecta() as c:
        for i in range(0, len(urls), 500):
            trozo = urls[i:i + 500]
            r.update({u: idi for u, idi in c.execute(
                "SELECT url, idioma FROM fichas WHERE idioma IN ('es','en','otro') AND url IN (%s)" % ",".join("?" * len(trozo)), trozo)})
    return r


def idioma_con_tienda(titulo, prior):
    cod, seguro = idioma_de(titulo)
    if cod == "?" and prior == "es":
        return "es", False
    return cod, seguro


def en_otro_idioma(titulo):
    """True si el título indica claramente otro idioma y no menciona el castellano."""
    cod, seguro = idioma_de(titulo)
    return cod in ("en", "otro") and seguro


_envio_visto = {}          # host → lo que anuncia su página de resultados (se guarda en la tienda al acabar la búsqueda)
_cerrojo_envio = threading.Lock()


def _apunta_envio(host, html):
    try:
        d = extract.detecta_envio(html)
    except Exception:          # noqa: BLE001  (es solo una pista)
        return
    if d.get("coste") is not None or d.get("gratis_desde") is not None:
        with _cerrojo_envio:
            _envio_visto[host] = d


def guarda_envios_vistos():
    """Guarda en cada tienda el envío que anuncia su web (campo «envio_auto»), sin tocar lo que hayas puesto tú."""
    if not _envio_visto:
        return
    with _cerrojo_envio:
        vistos = dict(_envio_visto)
        _envio_visto.clear()
    with cfg.cerrojo:
        lista = cfg.carga()
        cambia = False
        for t in lista:
            d = vistos.get(t["host"])
            if d:            # lo que no diga esta página se conserva
                nuevo = {**(t.get("envio_auto") or {}), **{k: d[k] for k in ("coste", "gratis_desde") if d.get(k) is not None}}
                if nuevo != t.get("envio_auto"):
                    t["envio_auto"], cambia = nuevo, True
        if cambia:
            cfg.guarda(lista)


def envio_de(t, precio):
    """Gastos de envío de la tienda (0 si supera el mínimo gratuito; None si no se conocen). Lo que pongas tú manda;
    si no hay nada, lo que anuncia su propia web («envio_auto»)."""
    auto = t.get("envio_auto") or {}
    gratis = t["envio_gratis"] if t.get("envio_gratis") is not None else auto.get("gratis_desde")      # cada dato por separado
    coste = t["envio"] if t.get("envio") is not None else auto.get("coste")
    if gratis is not None and precio >= gratis:
        return 0.0
    return coste


def historial_previo(urls):
    """{url: (precio_mínimo, observaciones, precio_máximo)} de lo ya guardado para esos artículos."""
    urls, out = list(urls), {}
    with bd.conecta() as c:
        for i in range(0, len(urls), 500):
            trozo = urls[i:i + 500]
            q = "SELECT url, MIN(precio) mn, COUNT(*) n, MAX(precio) mx FROM precios WHERE agotado=0 AND url IN (%s) GROUP BY url" % ",".join("?" * len(trozo))
            for r in c.execute(q, trozo):
                out[r["url"]] = (r["mn"], r["n"], r["mx"])
    return out


# Palabras que no distinguen un producto de otro (editorial, tipo de producto, idioma, relleno de la tienda).
RUIDO = {"asmodee", "fantasy", "flight", "games", "ffg", "lcg", "el", "la", "los", "las", "de", "del", "al", "the", "of", "a", "y", "en",
         "card", "game", "cards", "juego", "juegos", "cartas", "expansion", "exp", "castellano", "espanol", "espanola", "edicion",
         "comprar", "barato", "producto", "agotado", "preventa", "nuevo", "nueva", "living", "eng", "es", "esp", "spanish"}
# Palabras que describen el juego en general, no cuál es («Eternal Decks: juego de cartas cooperativo y estratégico»):
# con ellas, el mismo juego salía como otro producto en las tiendas que añaden una descripción al título.
DESCRIPCION = {"cooperativo", "cooperativa", "cooperativos", "competitivo", "competitiva", "estrategico", "estrategica",
               "estrategia", "mesa", "adulto", "adultos", "nino",
               "ninos", "jugador", "jugadores", "version", "oficial", "original", "divertido", "divertida", "ideal", "regalo",
               "oferta", "novedad", "para", "con", "por", "un", "una", "o", "u", "e", "and", "for", "cooperative",
               "strategy", "strategic", "edad", "anos", "partir", "desde", "recomendada"}
RUIDO |= DESCRIPCION
# Tiendas y editoriales que se cuelan en el título («Eternal Decks - Gigamesh», «… Salt and Pepper Games», «ugi games
# toys …», «Oferta Online …») y abreviaturas de idioma («SPA»).
RUIDO |= {"gigamesh", "devir", "ludonova", "tranjis", "maldito", "zacatrus",
          "ugi", "toys", "online", "spa", "envio", "gratis", "stock", "disponible"}
# Mismo producto con su nombre en inglés o en castellano según la tienda: se cuenta como la misma palabra
SINONIMOS = {"avispa": "wasp", "tormenta": "storm", "mercurio": "quicksilver", "tapete": "mat", "playmat": "mat",
             "funda": "sleeve", "protector": "sleeve", "protectore": "sleeve"}


# Coletillas de ficha que algunas tiendas añaden al título (Dynos: «Juego De Mesa … 60 Cartas Pegi 14»): con ellas, la misma
# expansión no se agrupaba con las demás tiendas y quedaba fuera de los más baratos.
COLETILLAS = re.compile(r"\bsalt\s+(?:and\s+|y\s+)?pepper\s+games\b|\bedge\s+entertainment\b|\bjuegos?\s+de\s+mesa\b|\bpegi\s+\d+|\bedad\s+recomendada\s+\d+(\s+anos?)?|\b\d+\s+cartas\b|\b\d+\s+anos?\b")


def clave_producto(titulo):
    """Identificador de un producto independiente de la tienda: sus palabras significativas, sin orden ni ruido.
    «Asmodee Marvel Champions: La Era de Apocalipsis» y «La Era de Apocalípsis - Marvel Champions» dan la misma clave."""
    palabras = set()
    for w in COLETILLAS.sub(" ", extract.normaliza(titulo)).split():
        if w in RUIDO or (re.search(r"\d", w) and re.search(r"[a-z]", w) and len(w) >= 5):    # referencias como ASM631069
            continue
        w = w[:-1] if len(w) > 4 and w.endswith("s") else w                                      # «apocalipsis» = «apocalipsi», plurales
        palabras.add(SINONIMOS.get(w, w))
    if LOTE.search(extract.normaliza(titulo)):
        palabras.add("[lote]")          # un lote nunca se agrupa con el juego suelto
    if not palabras:                    # un título hecho solo de palabras comunes: mejor su título entero que una clave vacía
        palabras = set(extract.normaliza(titulo).split())
    return " ".join(sorted(palabras))


def grupo_de(titulo, frases=()):
    """Con el filtro «al menos una de estas», el producto es la frase que encaja (más fiable); si no, su clave."""
    n = extract.normaliza(titulo)
    for f in frases:
        if extract.encaja(n, f) and tipo_de(titulo) not in ("accesorio", "lote"):     # sus fundas o un lote no son el juego
            return "f:" + f
    return "c:" + clave_producto(titulo)


# Lo que una tienda añade al nombre sin cambiar de producto: se puede ignorar para juntar dos grupos. Cualquier otra palabra
# de más puede ser otro producto («Black Panther» y «Black Panther Shuri» son dos packs), así que no se junta.
RELLENO = {"cinco", "escenario", "color", "cueva", "roja", "precintado", "unico", "completo"}


def fusiona_grupos(gs, consulta, tipos=None):
    """{grupo: grupo con el que se junta}. El mismo juego con una coletilla en una tienda («… | Cinco escenarios», «… juego
    de cartas») da una clave con palabras de más: si las de otro grupo de la misma búsqueda están todas en ella, es ese
    juego. Solo si ese otro grupo ya dice algo más que la búsqueda (al menos 2 palabras propias: «Marvel Champions» a secas
    no se traga sus expansiones), si los dos son del mismo tipo (un inserto no es el juego) y si lo que sobra es solo
    RELLENO («Héroes Reunidos 2» no es «Héroes Reunidos»). tipos: {grupo: tipo}."""
    base = set(clave_producto(consulta).split()) if consulta else set()
    claves = {g: set(g[2:].split()) for g in set(gs) if g.startswith("c:")}
    claves.update({a: set(a[2:].split()) for g, a in _alias().items() if g in claves and a not in claves})
    tipos = tipos or {}
    clase = lambda g: tipos.get(g) if tipos.get(g) in ("accesorio", "lote") else "juego"     # una expansión también es el juego
    out = {}
    for g, pal in claves.items():
        cand = [(len(p), o) for o, p in claves.items() if o != g and p < pal and len(p - base) >= 2
                and pal - p <= RELLENO and clase(o) == clase(g)]
        if cand:
            out[g] = max(cand)[1]
    conocidos = _alias()
    for g in claves:                     # lo que ya se juntó otra vez sigue junto aunque hoy no venga su pareja
        if g not in out and g in conocidos:
            out[g] = conocidos[g]
    for g in list(out):                  # en cadena: A→B→C acaba en C
        vistos = {g}
        while out[g] in out and out[g] not in vistos:
            vistos.add(out[g])
            out[g] = out[out[g]]
    nuevos = {g: a for g, a in out.items() if conocidos.get(g) != a} if base else {}      # ya resueltas; sin búsqueda no se aprende
    if nuevos:
        with bd.conecta() as c:
            c.executemany("INSERT OR REPLACE INTO alias_grupos(de, a, ts) VALUES(?,?,?)", [(g, a, time.time()) for g, a in nuevos.items()])
        with _alias_cerrojo:
            _alias_cache.update(nuevos)
    return out


_alias_cache = {}
_alias_leido = [None]
_alias_cerrojo = threading.Lock()


def _alias():
    """Las fusiones ya hechas (grupo largo → grupo con el que se juntó), de la base de datos. Devuelve una copia: varios
    hilos agrupan a la vez (búsqueda, revisión y la página)."""
    with _alias_cerrojo:
        if _alias_leido[0] != bd.RUTA:
            with bd.conecta() as c:
                _alias_cache.clear()
                _alias_cache.update({r["de"]: r["a"] for r in c.execute("SELECT de, a FROM alias_grupos")})
            _alias_leido[0] = bd.RUTA
        return dict(_alias_cache)


def grupos(titulos, consulta, alguna=""):
    """El producto (grupo) de cada título con las reglas de ahora: la página lo usa para reagrupar una búsqueda guardada
    o lo pegado a mano sin repetir la búsqueda."""
    frases = [f for f in (extract.normaliza(x).strip() for x in (alguna or "").split(",")) if f]
    palabras = set(extract.normaliza(consulta).split())
    frases = [f for f in frases if not set(f.split()) <= palabras]
    out = [{"grupo": grupo_de(t, frases), "clave": clave_producto(t), "tipo": tipo_de(t)} for t in titulos]
    junta = fusiona_grupos([o["grupo"] for o in out], consulta, {o["grupo"]: o["tipo"] for o in out})
    for o in out:
        o["grupo"] = junta.get(o["grupo"], o["grupo"])
    return out


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


def clave_objetivo(x, objs):
    """La clave del objetivo que se aplica a este producto (su grupo, su clave o la frase de una campaña); None si no hay."""
    if x.get("grupo") in objs:
        return x["grupo"]
    c = "c:" + (x.get("clave") or clave_producto(x["titulo"]))
    if c in objs:
        return c
    grupo = x.get("grupo") or c
    k = next((d for d, a in _alias().items() if d in objs and (a == grupo or a == c)), None)     # el 🎯 de una variante que se juntó con él
    if k:
        return k
    if tipo_de(x["titulo"]) in ("accesorio", "lote"):
        return None
    n = extract.normaliza(x["titulo"])
    return next((k for k in objs if k.startswith("f:") and extract.encaja(n, k[2:])), None)


def objetivo_para(x, objs):
    """El objetivo que el usuario puso a este producto (por su grupo, su clave o, si se puso desde una campaña, por la frase)."""
    if not objs:
        return None
    k = clave_objetivo(x, objs)
    return objs[k]["precio"] if k else None


VERSION_CLAVES = 7      # súbela al cambiar clave_producto (RUIDO, DESCRIPCION, COLETILLAS): se recalcula todo lo guardado


def rellena_claves():
    """Al arrancar: pone la clave de producto a los precios que no la tienen y, si cambió la forma de calcularla, la
    recalcula en todo lo guardado (historial, «No me interesa» y objetivos 🎯), para que nada pierda su historial ni deje
    de aplicarse."""
    hecha = int(ajustes.carga().get("version_claves") or 0)
    if hecha < VERSION_CLAVES:           # las fusiones se hicieron con las claves de antes: se vuelven a aprender
        with _alias_cerrojo, bd.conecta() as c:
            c.execute("DELETE FROM alias_grupos")
            _alias_cache.clear()
            _alias_leido[0] = None
    with bd.conecta() as c:
        sql = "SELECT DISTINCT titulo FROM precios" + ("" if hecha < VERSION_CLAVES else " WHERE clave IS NULL")
        titulos = [r[0] for r in c.execute(sql)]
    for i in range(0, len(titulos), 200):       # por tandas: no bloquea la base a una revisión que empiece a la vez
        with bd.conecta() as c:
            c.executemany("UPDATE precios SET clave=? WHERE titulo=?", [(clave_producto(t), t) for t in titulos[i:i + 200]])
    with bd.conecta() as c:
        if hecha < VERSION_CLAVES:
            for tabla in ("ignorados", "objetivos", "vinculos_amazon"):
                filas = [dict(r) for r in c.execute(f"SELECT * FROM {tabla} ORDER BY ts")]
                c.execute(f"DELETE FROM {tabla}")
                for f in filas:                  # de la más antigua a la más nueva: con la misma clave, queda la última
                    if f["titulo"] and not f["clave"].startswith("f:"):
                        f["clave"] = ("c:" if f["clave"].startswith("c:") else "") + clave_producto(f["titulo"])
                    c.execute(f"INSERT OR REPLACE INTO {tabla}({','.join(f)}) VALUES({','.join('?' * len(f))})", list(f.values()))
    if hecha < VERSION_CLAVES:
        ajustes.guarda({"version_claves": VERSION_CLAVES})
    return len(titulos)


def historial_producto(grupo):
    """El mejor precio del producto en cualquier tienda (nuevo, con stock, sin preventas), hora a hora. Por horas y no por
    búsqueda: una búsqueda parcial (p. ej. al pegar resultados se consulta solo esa tienda) no debe parecer una subida."""
    segunda = {t["host"] for t in cfg.carga() if t.get("tipo") == "segunda_mano"}
    with bd.conecta() as c:
        if grupo.startswith("f:"):
            f = grupo[2:]
            titulos = [t for (t,) in c.execute("SELECT DISTINCT titulo FROM precios")
                       if extract.encaja(extract.normaliza(t), f)]
            filas = []
            for i in range(0, len(titulos), 500):
                trozo = titulos[i:i + 500]
                filas += [dict(r) for r in c.execute("SELECT ts, precio, titulo, tienda, url FROM precios WHERE agotado=0 AND preventa=0 AND titulo IN (%s)"
                                                     % ",".join("?" * len(trozo)), trozo)]
        else:
            g = grupo if grupo.startswith("c:") else "c:" + grupo
            al = _alias()

            def fin(a):                  # a dónde acaba una fusión (las antiguas pueden ir en cadena)
                vistos = set()
                while a in al and a not in vistos:
                    vistos.add(a)
                    a = al[a]
                return a
            claves = [g[2:]] + [d[2:] for d, a in al.items() if fin(a) == g]       # y las variantes que se juntaron con él
            filas = [dict(r) for r in c.execute("SELECT ts, precio, titulo, tienda, url FROM precios WHERE agotado=0 AND preventa=0 AND clave IN (%s)"
                                                % ",".join("?" * len(claves)), claves)]
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
        vigiladas = [(r["nombre"], r["consulta"]) for r in c.execute("SELECT nombre, consulta FROM seguimientos WHERE activo=1")]
    salta = {}                      # tienda → vigiladas en las que se la salta (no tiene ese juego)
    for nombre, consulta in vigiladas:
        for h in tiendas_sin(consulta):
            salta.setdefault(h, []).append(nombre)
    with bd.conecta() as c:
        for h, t in lista.items():
            filas = [dict(r) for r in c.execute("SELECT ts, encontrados, error FROM estado_tiendas WHERE host=? ORDER BY ts DESC LIMIT ?", (h, ultimas))]
            con = sum(1 for f in filas if f["encontrados"])
            ult_ok = next((f["ts"] for f in filas if f["encontrados"]), None)
            ult_err = next((f["error"] for f in filas if f["error"]), "")
            manual_envio = t.get("envio") is not None or t.get("envio_gratis") is not None
            envio = {"coste": t.get("envio"), "gratis_desde": t.get("envio_gratis"), "suyo": False} if manual_envio else \
                {**(t.get("envio_auto") or {}), "suyo": True} if t.get("envio_auto") else None
            out.append({"host": h, "nombre": t.get("nombre") or h, "activa": t.get("activa", True), "manual": bool(t.get("manual")),
                        "bloqueada": bool(t.get("bloqueo")), "salta_en": salta.get(h, []), "envio": envio,
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


VECES_SIN = 4          # consultas seguidas sin el juego para saltarse esa tienda en las revisiones
VUELVE_A_MIRAR = 7     # días: entonces se vuelve a consultar una vez, por si lo han traído


def tiendas_sin(consulta, ahora=None):
    """Tiendas que en sus últimas VECES_SIN consultas de esta búsqueda respondieron sin el juego (y nunca lo tuvieron en
    40 días). Las revisiones automáticas se las saltan hasta que pasen VUELVE_A_MIRAR días desde la última vez: menos
    tiempo y menos peticiones. Las búsquedas que haces tú las consultan siempre."""
    ahora = ahora or time.time()
    out = set()
    with bd.conecta() as c:
        filas = c.execute("SELECT host, ts, encontrados, error FROM estado_tiendas WHERE consulta=? AND ts>? ORDER BY ts DESC",
                          (consulta, ahora - 40 * 86400)).fetchall()
    por = {}
    for f in filas:
        por.setdefault(f["host"], []).append(f)
    for h, fs in por.items():
        if any(f["encontrados"] for f in fs):
            continue
        ultimas = fs[:VECES_SIN]
        if len(ultimas) == VECES_SIN and all((f["error"] or "").startswith(SIN_COINCIDENCIAS) for f in ultimas) \
                and ahora - ultimas[0]["ts"] < VUELVE_A_MIRAR * 86400:
            out.add(h)
    return out


def buscar(consulta, incluir="", excluir="", ocultar_agotados=True, hosts=None, pmin=None, pmax=None, seg_id=None,
           castellano=True, preventas=False, con_envio=False, segunda_mano=False, abierta=False, region="es", paginas=None, idioma=None, alguna=""):
    """Devuelve (resultados ordenados por precio, informe por tienda).
    preventas: incluir productos en preventa · con_envio: ordenar por precio + envío · segunda_mano: incluir
    Vinted, Milanuncios… · abierta: buscar también en webs que no están en la lista (region: es | ue | mundo)."""
    lista = cfg.carga()
    aprendido = {t["host"]: (t.get("plantilla"), bool(t.get("js"))) for t in lista}    # para guardar luego solo lo que cambie
    aj = ajustes.carga()
    try:
        paginas = min(max(int(paginas or aj.get("paginas") or 1), 1), 6)    # nunca más de 6: muchas páginas seguidas parecen un ataque
    except (TypeError, ValueError):
        paginas = 1
    modo = modo_idioma(castellano, idioma)
    # bloqueada: nunca se consulta, ni aunque la pida una página abierta desde antes; si va como «solo enlace», cuenta lo pegado
    activas = [t for t in lista if (t["host"] in hosts if hosts is not None else t.get("activa", True) or t.get("bloqueo"))
               and not (t.get("bloqueo") and not t.get("manual"))]
    if not segunda_mano:
        activas = [t for t in activas if t.get("tipo") != "segunda_mano"]
    # «solo enlace» aunque no tenga dirección de búsqueda (su enlace es la portada): si no, se consultaba igual
    manuales = [t for t in activas if t.get("manual") or cfg.nunca(t["host"])]
    activas = [t for t in activas if t not in manuales]
    if seg_id is not None:            # revisión de una vigilada: sin las tiendas que nunca tienen este juego
        sin_el = tiendas_sin(consulta)
        activas = [t for t in activas if t["host"] not in sin_el]
    por_host = {t["host"]: t for t in lista}
    inc = extract.normaliza(incluir).split()
    frases = [f for f in (extract.normaliza(x).strip() for x in (alguna or "").split(",")) if f]   # basta con una (p. ej. nombres de campañas)
    exc = extract.normaliza(excluir).split()
    nav = {"visible": False} if aj["usar_navegador"] and navegador.disponible() else None   # siempre en segundo plano
    ocultos = set(ignorados())                                       # «ya lo tengo / no me interesa»

    idioma_ficha = {}           # lo que ya se leyó en la ficha de cada producto manda sobre lo que sugiere su título

    sin_stock = []              # lo que solo se descarta por agotado: no se enseña, pero se apunta para saber cuándo vuelve

    def pasa(x, prior=None):
        x["idioma"], x["idioma_seguro"] = idioma_con_tienda(x["titulo"], prior)
        if x.get("url") in idioma_ficha:      # Amazon: «Versión ES» en el título y la ficha dice francés
            x["idioma"], x["idioma_seguro"] = idioma_ficha[x["url"]], True
        n = extract.normaliza(x["titulo"])
        if frases and not any(extract.encaja(n, f) for f in frases):
            return False
        vale = (all(extract.encaja(n, w) for w in inc) and not any(extract.encaja(n, w) for w in exc)
                and not (x.get("preventa") and not preventas)
                and permite(x["idioma"], x["idioma_seguro"], modo)
                and clave_producto(x["titulo"]) not in ocultos)
        if vale and ocultar_agotados and x["agotado"]:
            sin_stock.append(x)
            return False
        return vale

    res, informe = [], {}
    ahora = time.time()
    # Con el ritmo por tienda cada una espera su turno, así que se consultan más a la vez (cada hilo, una tienda distinta).
    # Una tienda que acaba de volver de un bloqueo se consulta unos días con una sola página.
    pags = lambda t: 1 if t.get("suave_hasta", 0) > ahora else paginas
    prog = progreso.actual()          # la barra de carga de la página: tiendas hechas de cuántas
    progreso.total(prog, len(activas))

    def una(t):
        try:
            return _tienda(t, consulta, nav, pags(t))
        finally:
            progreso.avanza(prog)
    with cf.ThreadPoolExecutor(12) as ex:
        resultados = list(ex.map(una, activas))
    progreso.fase(prog, "Revisando lo encontrado")
    if nav and aj["navegador_visible"]:
        # Solo las tiendas que piden comprobar que eres humano se reintentan con ventana, de una en una,
        # para que el usuario pueda resolverlo; el resto se consulta sin que salga nada en pantalla.
        for i, (host, items, err) in enumerate(resultados):
            if err == DESAFIO:
                r = _tienda(por_host[host], consulta, {"visible": True}, pags(por_host[host]))
                # La ventana ya se abrió y nadie resolvió la comprobación a tiempo: decir eso, no «activa la ventana».
                resultados[i] = (r[0], r[1], DESAFIO_SIN_RESOLVER if r[2] == DESAFIO else r[2])
    progreso.fase(prog, "Mirando el idioma en las fichas")
    idioma_ficha.update(idiomas_de_fichas([x["url"] for _, items, _ in resultados for x in items]))
    for host, items, err in resultados:
        kept = 0
        prior = prior_tienda(items)
        for x in items:
            x["tienda"] = host
            if pasa(x, prior) and solo_juego(host, x["titulo"], consulta) and not es_no_juego(x["titulo"]):
                x["tienda"], x["origen"], x["tipo"] = host, por_host[host].get("tipo", "tienda"), tipo_de(x["titulo"])
                res.append(x)
                kept += 1
        informe[host] = {"encontrados": kept, "error": err if not kept else None, "brutos": len(items), "error_tienda": err,
                         "caida": es_caida(err) and not kept}
    for t in manuales:
        enlace = cfg.url_busqueda(t["plantilla"], consulta) if t.get("plantilla") else f"https://{t['host']}/"
        informe[t["host"]] = {"encontrados": 0, "error": None, "manual": enlace}
        previos = [x for x in importar.vigentes(t["host"], consulta)                   # lo que el usuario pegó a mano
                   if pasa(x) and solo_juego(t["host"], x["titulo"], consulta) and not es_no_juego(x["titulo"])]
        for x in previos:
            x["tienda"], x["origen"], x["tipo"] = t["host"], t.get("tipo", "tienda"), tipo_de(x["titulo"])
            res.append(x)
        if previos:
            informe[t["host"]].update(importados=len(previos), importado_ts=max(x["importado"] for x in previos))
    if abierta:
        progreso.fase(prog, "Buscando en otras webs")
        from . import abierta as web
        conocidos = {t["host"].replace("www.", "") for t in lista}
        items, info = web.busca(consulta, region=region, excluir_hosts=conocidos, castellano=(modo != "todos"), nav=nav)
        kept = 0
        for x in items:
            if pasa(x):
                x["origen"], x["tipo"] = "web", tipo_de(x["titulo"])
                res.append(x)
                kept += 1
        informe["Búsqueda abierta"] = {"encontrados": kept, "error": info if not kept else None,
                                       "caida": bool(info) and info.startswith("no se pudo") and not kept}   # «no encontré precios» sí respondió
    cfg.aplica_descubiertas({t["host"]: (t.get("plantilla"), bool(t.get("js"))) for t in lista       # plantillas descubiertas
                             if (t.get("plantilla"), bool(t.get("js"))) != aprendido[t["host"]]})
    registra_estado({h: {"brutos": i.get("brutos", 0), "error": i.get("error_tienda")} for h, i in informe.items() if "brutos" in i}, consulta)
    guarda_envios_vistos()

    # producto (grupo) y PVP aproximado, con todas las tiendas; después, el filtro de precio
    # Una frase que no añade nada a la búsqueda («Vantage» buscando «Vantage») no distingue productos: juntaría en una sola
    # tarjeta todo lo que la contenga (el juego, un reloj Polar Vantage, un coche Aston Martin Vantage…).
    palabras_consulta = set(extract.normaliza(consulta).split())
    frases_grupo = [f for f in frases if not set(f.split()) <= palabras_consulta]
    precios_grupo = {}
    for x in res:
        x["grupo"] = grupo_de(x["titulo"], frases_grupo)
        x["clave"] = clave_producto(x["titulo"])
    junta = fusiona_grupos([x["grupo"] for x in res], consulta, {x["grupo"]: tipo_de(x["titulo"]) for x in res})
    for x in res:
        x["grupo"] = junta.get(x["grupo"], x["grupo"])
        if not x["agotado"] and x.get("origen") != "segunda_mano":            # la segunda mano no marca el precio de mercado
            precios_grupo.setdefault(x["grupo"], {})
            precios_grupo[x["grupo"]].setdefault(x["tienda"], x["precio"])          # una vez por tienda
    pvps = {g: pvp_de(list(p.values())) for g, p in precios_grupo.items()}
    for x in res:
        pvp = pvps.get(x["grupo"])
        x["pvp"] = pvp if pvp and pvp > x["precio"] else None
        x["descuento"] = round(100 * (1 - x["precio"] / pvp)) if x["pvp"] else None
    res = [x for x in res if not (pmin is not None and x["precio"] < pmin) and not (pmax is not None and x["precio"] > pmax)]
    progreso.fase(prog, "Comprobando el stock en las fichas")
    corrige_stock(res, lista)
    agotados = [x for x in res if x["agotado"] and ocultar_agotados]       # los que su ficha dice que están agotados…
    agotados += [x for x in sin_stock if x.get("tienda") and solo_juego(x["tienda"], x["titulo"], consulta)       # …y los del listado
                 and not es_no_juego(x["titulo"]) and (pmin is None or x["precio"] >= pmin) and (pmax is None or x["precio"] <= pmax)]
    for x in agotados:
        x["clave"] = clave_producto(x["titulo"])
    res = [x for x in res if not (ocultar_agotados and x["agotado"]) and not (x.get("preventa") and not preventas)]
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
        mn, n, mx = previo.get(x["url"], (None, 0, None))
        # Mínimo histórico: lo más barato que se le ha visto Y alguna vez estuvo más caro (si nunca cambia, no es noticia)
        x["n_hist"], x["minimo"] = n, bool(n >= MIN_HISTORIAL and x["precio"] <= mn and mx > x["precio"] + 0.005)
    res.sort(key=lambda x: (x["agotado"], x["total"] if con_envio else x["precio"]))
    ts = time.time()
    with bd.conecta() as c:
        c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      [(ts, consulta, x["tienda"], x["titulo"], x["url"], x["precio"], int(x["agotado"]), seg_id, int(x.get("preventa", False)), x["clave"])
                       for x in res + agotados if not x.get("importado")])    # lo pegado se apunta una vez, al pegarlo (importar.guarda)
    return res, informe
