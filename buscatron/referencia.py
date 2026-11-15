"""Referencia de Amazon para tus productos: su equivalente en Amazon y lo que BuscaTron ha visto allí (precio actual,
mínimo y máximo). Todo sale de la base de datos: no consulta nada. Para el histórico de años están camelcamelcamel y
Keepa, que no se pueden leer automáticamente (camelcamelcamel lo bloquea y Keepa pide una clave de pago): se enlazan.
Hay fichas de Amazon cuyo título no dice qué es («Fantasy MC16ES Flight Games Marvel Champions» es Los Más Buscados de la
Galaxia): para esas se sugieren parecidas y se puede vincular a mano pegando su enlace (se recuerda)."""
import re
import time
import urllib.parse
import urllib.request

from . import bd, extract, historico, motor, seguimiento

AMAZON = "www.amazon.es"
COBERTURA = 0.75        # parte de las palabras del producto que tiene que tener el título de Amazon
COBERTURA_SUGERENCIA = 0.4


def asin(url):
    m = re.search(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})", url or "")
    return m.group(1) if m else None


def url_amazon(a):
    return f"https://www.amazon.es/dp/{a}"


def asin_de_enlace(enlace):
    """El ASIN de un enlace de Amazon (también los cortos amzn.eu/d/… o amzn.to/…, que se siguen) o de un ASIN suelto."""
    enlace = (enlace or "").strip()
    if re.fullmatch(r"[A-Za-z0-9]{10}", enlace) and not enlace.isdigit():
        return enlace.upper()
    a = asin(enlace)
    if a:
        return a
    if re.match(r"(https?://)?(amzn\.(eu|to)|a\.co)/", enlace):
        req = urllib.request.Request(enlace if enlace.startswith("http") else "https://" + enlace, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return asin(r.geturl())
        except OSError:
            return None
    return None


def vincula(clave, enlace, titulo=""):
    a = asin_de_enlace(enlace)
    if not a:
        raise ValueError("No encuentro el producto en ese enlace: pega el de su ficha de Amazon (amazon.es/dp/… o amzn.eu/d/…)")
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO vinculos_amazon(clave, asin, titulo, ts) VALUES(?,?,?,?)", (clave, a, titulo, time.time()))
    return a


def titulo_de_enlace(enlace):
    """El nombre que lleva un enlace de Amazon antes de «/dp/» («…/Marvel-Champions-Tiranía-Cráneo-Rojo/dp/B08VW72D4F»)."""
    m = re.search(r"amazon\.[a-z.]+/([^/?#]+)/(?:dp|gp/product)/", enlace or "")
    return urllib.parse.unquote(m.group(1)).replace("-", " ").strip() if m else ""


def anade_extra(enlace, titulo=""):
    """Añade a la referencia un producto de Amazon por su enlace, tenga o no stock: así tiene su bloque (y su histórico de
    camelcamelcamel) aunque ninguna de tus tiendas lo venda ahora."""
    a = asin_de_enlace(enlace)
    if not a:
        raise ValueError("No encuentro el producto en ese enlace: pega el de su ficha de Amazon (amazon.es/…/dp/… o amzn.eu/d/…)")
    titulo = (titulo or titulo_de_enlace(enlace) or a).strip()[:160]
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO ref_extra(asin, titulo, ts) VALUES(?,?,?)", (a, titulo, time.time()))
    return {"asin": a, "titulo": titulo}


def quita_extra(asin_):
    with bd.conecta() as c:
        c.execute("DELETE FROM ref_extra WHERE asin=?", (asin_,))


def desvincula(clave):
    with bd.conecta() as c:
        c.execute("DELETE FROM vinculos_amazon WHERE clave=?", (clave,))


def _palabras(titulo):
    return set(motor.clave_producto(titulo).split())


def _amazon(c):
    """{url: {asin, titulo, actual, visto, minimo, maximo, n, desde}} de lo visto en Amazon, nuevo y con stock."""
    d = {}
    for url, titulo, precio, ts in c.execute(
            "SELECT url, titulo, precio, ts FROM precios WHERE tienda=? AND url LIKE '%/dp/%' AND agotado=0 AND preventa=0 ORDER BY ts",
            (AMAZON,)):
        url = url_amazon(asin(url)) if asin(url) else url       # una ficha, un historial (había direcciones con ref=…)
        a = d.setdefault(url, {"url": url, "asin": asin(url), "precios": []})
        a["titulo"] = titulo
        a["precios"].append((ts, precio))
    for a in d.values():
        ps = [p for _, p in a["precios"]]
        a.update(actual=ps[-1], visto=a["precios"][-1][0], minimo=min(ps), maximo=max(ps), n=len(ps), desde=a["precios"][0][0],
                 palabras=_palabras(a["titulo"]))
        del a["precios"]
    return d


ESTADOS = {"activas": "s.activo=1", "pausa": "s.activo=0", "todas": "1=1"}


def _de_vigiladas(c, estado="activas"):
    """Lo que encontró cada vigilada en su última revisión Y cumple sus filtros de ahora: [(titulo, precio, tienda, url, ts, seg_id)].
    estado: activas | pausa | todas (la pestaña de Vigiladas desde la que se abre)."""
    filas = []
    for s in c.execute("SELECT s.*, MAX(p.ts) AS uts FROM seguimientos s JOIN precios p ON p.seg_id=s.id WHERE "
                       + ESTADOS.get(estado, ESTADOS["activas"]) + " GROUP BY s.id").fetchall():
        seg = dict(s)
        seg["opciones"] = seguimiento.opciones_de(seg)
        for r in c.execute("SELECT titulo, precio, tienda, url, ts, seg_id FROM precios WHERE seg_id=? AND ts=? AND agotado=0",
                           (seg["id"], seg["uts"])).fetchall():
            if seguimiento.cumple(seg, r["titulo"], r["precio"], r["tienda"]):
                filas.append(tuple(r))
    return filas


def _productos(c, ambito, estado="activas"):
    """Los productos de tus avisos o de lo que encuentran tus vigiladas (según la pestaña: activas, en pausa o todas), uno por
    producto (el más barato), siempre con los filtros que tienen ahora."""
    if ambito == "avisos":
        filas = c.execute("SELECT titulo, precio, tienda, url, ts, seg_id FROM avisos WHERE oculto=0").fetchall()
    else:
        filas = _de_vigiladas(c, estado)
    ocultos = set(motor.ignorados())
    grupos = {}
    for titulo, precio, tienda, url, ts, sid in filas:
        k = motor.clave_producto(titulo)
        if k in ocultos:
            continue
        g = grupos.get(k)
        if not g or precio < g["precio"]:
            grupos[k] = {"titulo": titulo, "precio": precio, "tienda": tienda, "url": url, "ts": ts, "seg_id": sid}
    return sorted(grupos.values(), key=lambda g: extract.normaliza(g["titulo"]))


# Palabras de otro tipo de artículo: si el título de Amazon las lleva y el del producto no, no es el mismo producto
# («Too Many Bones: Gasket Add-on Character» no es «Too Many Bones Edición Definitiva»).
OTRO_ARTICULO = {"character", "personaje", "add", "addon", "sleeve", "funda", "tapete", "playmat", "organizador", "inserto", "insert", "accesorio"}


def es_otro_articulo(w, a):
    return bool((a["palabras"] & OTRO_ARTICULO) - w)


def _candidatos(prod, amazon, excluir, idiomas):
    """Los productos de Amazon que parecen el mismo, del más probable al menos."""
    if prod["tienda"] == AMAZON and prod["url"] in amazon:
        return [amazon[prod["url"]]]
    w = _palabras(prod["titulo"])
    if not w:
        return []
    exc = extract.normaliza(excluir or "").split()
    r = []
    for a in amazon.values():
        comun = len(w & a["palabras"]) / len(w)
        if comun < COBERTURA or es_otro_articulo(w, a):
            continue
        n = extract.normaliza(a["titulo"])
        if any(extract.encaja(n, e) for e in exc):            # lo que descarta la vigilada (fundas, tapetes…)
            continue
        if len(w) == 1 and not motor.JUEGO.search(n):         # «Vantage» a secas: solo lo que se anuncia como juego
            continue
        if prod["precio"] and not 0.5 <= a["actual"] / prod["precio"] <= 2:
            continue                                          # un pack de varias, o una funda: no es el mismo producto
        r.append(((idiomas.get(a["url"]) in ("en", "otro"), -comun, len(a["palabras"] - w)), a))
    r.sort(key=lambda z: z[0])
    return [a for _, a in r[:3]]


def _sugerencias(prod, amazon, excluir, usadas):
    """Sin un equivalente seguro: fichas de Amazon que comparten parte del nombre, a un precio parecido y con un título
    que no dice gran cosa más (lo típico de una ficha mal titulada). Las confirmas tú con «Es este»."""
    w = _palabras(prod["titulo"])
    if len(w) < 2 or not prod["precio"]:
        return []
    exc = extract.normaliza(excluir or "").split()
    r = []
    for a in amazon.values():
        if a["url"] in usadas:
            continue
        comun = len(w & a["palabras"]) / len(w)
        ratio = a["actual"] / prod["precio"]
        if comun < COBERTURA_SUGERENCIA or not 0.75 <= ratio <= 1.5:
            continue
        if any(extract.encaja(extract.normaliza(a["titulo"]), e) for e in exc):
            continue
        r.append(((len(a["palabras"] - w), abs(1 - ratio), -comun), a))
    r.sort(key=lambda z: z[0])
    return [a for _, a in r[:3]]


def resumen(ambito="avisos", estado="activas"):
    """[{producto…, amazon: {…}|None, alternativas: [...]}] para la vista «Referencia de Amazon»."""
    with bd.conecta() as c:
        amazon = _amazon(c)
        prods = _productos(c, ambito, estado)
        excl = {sid: exc for sid, exc in c.execute("SELECT id, excluir FROM seguimientos")}
        vinculos = {k: a for k, a in c.execute("SELECT clave, asin FROM vinculos_amazon")}
        extras = [(a, t) for a, t in c.execute("SELECT asin, titulo FROM ref_extra ORDER BY ts")]
    idiomas = motor.idiomas_de_fichas(list(amazon) + [p["url"] for p in prods])
    prods = [p for p in prods if idiomas.get(p["url"]) not in ("en", "otro")]     # su ficha ya dijo que no está en castellano

    camel = historico.todos()

    def limpio(a):
        d = camel.get(a.get("asin"))
        return {k: v for k, v in a.items() if k != "palabras"} | {
            "idioma": idiomas.get(a["url"]) if "idioma" not in a else a["idioma"],
            "camel": {**d, "frases": historico.frases(d, aviso=False)} if d else None}
    salida, referencias = [], set()
    for p in prods:
        p["clave"] = motor.clave_producto(p["titulo"])
        vin = vinculos.get(p["clave"])
        if vin:                    # vinculado a mano: manda, aunque BuscaTron todavía no tenga precios suyos
            a = amazon.get(url_amazon(vin))
            cands = [limpio(a or {"url": url_amazon(vin), "asin": vin, "titulo": "", "n": 0})]
        else:
            cands = [limpio(a) for a in _candidatos(p, amazon, excl.get(p["seg_id"]), idiomas)]
        salida.append({**p, "asin": asin(p["url"]) if p["tienda"] == AMAZON else None, "vinculado": bool(vin),
                       "amazon": cands[0] if cands else None, "alternativas": cands[1:], "sugerencias": []})
        if cands and p["tienda"] != AMAZON:
            referencias.add(cands[0]["url"])
    for x in salida:               # lo que no tiene equivalente: parecidas que no sean ya el de otro producto
        if not x["amazon"]:
            x["sugerencias"] = [limpio(a) for a in _sugerencias(x, amazon, excl.get(x["seg_id"]), referencias)]
    # un producto de Amazon que ya sale como referencia de otro no se repite como producto aparte
    salida = [x for x in salida if not (x["tienda"] == AMAZON and x["url"] in referencias)]
    # los añadidos por enlace (sin stock en tus tiendas): su bloque con el histórico, salvo que ya salgan arriba
    ya = {x["amazon"]["asin"] for x in salida if x["amazon"] and x["amazon"].get("asin")}
    for a_, titulo in extras:
        if a_ in ya:
            continue
        visto = amazon.get(url_amazon(a_))
        cand = limpio(visto or {"url": url_amazon(a_), "asin": a_, "titulo": titulo, "n": 0})
        salida.append({"titulo": titulo, "precio": None, "tienda": "", "url": url_amazon(a_), "ts": 0, "seg_id": None, "clave": "", "asin": a_,
                       "vinculado": False, "extra": True, "amazon": cand, "alternativas": [], "sugerencias": []})
    return salida


def por_vigilada():
    """{id de la vigilada: [{titulo, asin, minimo, fecha_minimo, maximo, fecha_maximo, actual}]} de los productos que encontró en
    su última revisión y tienen histórico de camelcamelcamel ya leído. Vale para las vigiladas activas y las que están en pausa;
    las que no tienen ningún producto con historial no aparecen."""
    camel = historico.todos()
    if not camel:
        return {}
    with bd.conecta() as c:
        amazon = _amazon(c)
        excl = {sid: exc for sid, exc in c.execute("SELECT id, excluir FROM seguimientos")}
        vinculos = {k: a for k, a in c.execute("SELECT clave, asin FROM vinculos_amazon")}
        filas = {}
        for titulo, precio, tienda, url, ts, sid in _de_vigiladas(c, "todas"):
            filas.setdefault(sid, []).append((titulo, precio, tienda, url))
    ocultos = set(motor.ignorados())
    idiomas = motor.idiomas_de_fichas(list(amazon))
    out = {}
    for sid, rows in filas.items():
        grupos = {}
        for titulo, precio, tienda, url in rows:
            k = motor.clave_producto(titulo)
            if k not in ocultos and (k not in grupos or precio < grupos[k]["precio"]):
                grupos[k] = {"titulo": titulo, "precio": precio, "tienda": tienda, "url": url}
        items, vistos = [], set()
        for k, p in grupos.items():
            a_ = vinculos.get(k)
            if not a_:
                cands = _candidatos(p, amazon, excl.get(sid), idiomas)
                a_ = cands[0]["asin"] if cands else None
            d = camel.get(a_)
            if not d or a_ in vistos or d.get("minimo") is None or d.get("maximo") is None:
                continue
            vistos.add(a_)
            items.append({"titulo": p["titulo"], "asin": a_, **{f: d.get(f) for f in ("minimo", "fecha_minimo", "maximo", "fecha_maximo", "actual")}})
        if items:
            out[sid] = sorted(items, key=lambda x: extract.normaliza(x["titulo"]))
    return out
