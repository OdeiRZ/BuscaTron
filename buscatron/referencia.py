"""Referencia de Amazon para tus productos: su equivalente en Amazon y lo que BuscaTron ha visto allí (precio actual,
mínimo y máximo). Todo sale de la base de datos: no consulta nada. Para el histórico de años están camelcamelcamel y
Keepa, que no se pueden leer automáticamente (camelcamelcamel lo bloquea y Keepa pide una clave de pago): se enlazan.
Hay fichas de Amazon cuyo título no dice qué es («Fantasy MC16ES Flight Games Marvel Champions» es Los Más Buscados de la
Galaxia): para esas se sugieren parecidas y se puede vincular a mano pegando su enlace (se recuerda)."""
import re
import time
import urllib.request

from . import bd, extract, motor

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


def _productos(c, ambito):
    """Los productos de tus avisos o de lo que encuentran ahora tus vigiladas activas, uno por producto (el más barato)."""
    if ambito == "avisos":
        filas = c.execute("SELECT titulo, precio, tienda, url, ts, seg_id FROM avisos WHERE oculto=0").fetchall()
    else:
        filas = []
        for sid, ts in c.execute("SELECT s.id, MAX(p.ts) FROM seguimientos s JOIN precios p ON p.seg_id=s.id "
                                 "WHERE s.activo=1 GROUP BY s.id").fetchall():
            filas += c.execute("SELECT titulo, precio, tienda, url, ts, seg_id FROM precios "
                               "WHERE seg_id=? AND ts=? AND agotado=0", (sid, ts)).fetchall()
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
        if comun < COBERTURA:
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


def resumen(ambito="avisos"):
    """[{producto…, amazon: {…}|None, alternativas: [...]}] para la vista «Referencia de Amazon»."""
    with bd.conecta() as c:
        amazon = _amazon(c)
        prods = _productos(c, ambito)
        excl = {sid: exc for sid, exc in c.execute("SELECT id, excluir FROM seguimientos")}
        vinculos = {k: a for k, a in c.execute("SELECT clave, asin FROM vinculos_amazon")}
    idiomas = motor.idiomas_de_fichas(list(amazon) + [p["url"] for p in prods])
    prods = [p for p in prods if idiomas.get(p["url"]) not in ("en", "otro")]     # su ficha ya dijo que no está en castellano

    def limpio(a):
        return {k: v for k, v in a.items() if k != "palabras"} | {"idioma": idiomas.get(a["url"])}
    salida, referencias = [], set()
    for p in prods:
        p["clave"] = motor.clave_producto(p["titulo"])
        vin = vinculos.get(p["clave"])
        if vin:                    # vinculado a mano: manda, aunque BuscaTron todavía no tenga precios suyos
            a = amazon.get(url_amazon(vin))
            cands = [limpio(a) if a else {"url": url_amazon(vin), "asin": vin, "titulo": "", "n": 0, "idioma": idiomas.get(url_amazon(vin))}]
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
    return [x for x in salida if not (x["tienda"] == AMAZON and x["url"] in referencias)]
