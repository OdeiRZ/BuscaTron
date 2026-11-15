"""Mínimo y máximo históricos de un producto, leídos del texto de la gráfica de camelcamelcamel que pegas (ocr.py), y lo
que se puede decir de ellos: cuánto se aleja el precio de hoy de su mínimo, cuándo fue (y si coincidió con una campaña de
ofertas que este año vuelve) y, con honestidad, qué NO se puede saber solo con los extremos (la frecuencia con que se
repite una bajada necesita la serie completa)."""
import datetime
import re
import unicodedata

import os
import time

from . import bd, extract

MESES = {"ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "aug": 8,
         "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12}
ETIQUETAS = (("minimo", r"mas bajo|lowest|minimo|precio minimo|min\b"), ("maximo", r"mas alto|highest|maximo|precio maximo|max\b"),
             ("media", r"media|promedio|average|avg"), ("actual", r"actual|current|ahora"))
IMPORTE = re.compile(r"(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+,\d{1,2}|\d+\.\d{2})")      # la leyenda siempre lleva decimales
MES = r"(ene|jan|feb|mar|abr|apr|may|jun|jul|ago|aug|sep|set|oct|nov|dic|dec)[a-z]*"
FECHAS = (re.compile(r"\b(\d{1,2})[ .\-/]+" + MES + r"\.?[ ,.\-/]+(\d{2,4})\b"),          # 12 nov. 2026 · 12-nov-26
          re.compile(r"\b" + MES + r"\.?[ ]+(\d{1,2})[ ,.]+(\d{4})\b"),                    # nov 12, 2026
          re.compile(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b"))                    # 12/11/2026


def euros(v):
    return f"{v:.2f}".replace(".", ",") + " €"


def black_friday(anio):
    """El viernes después del cuarto jueves de noviembre."""
    d = datetime.date(anio, 11, 1)
    jueves = [d + datetime.timedelta(days=i) for i in range(30) if (d + datetime.timedelta(days=i)).weekday() == 3]
    return jueves[3] + datetime.timedelta(days=1)


def _plano(t):
    """Minúsculas y sin acentos, pero con la puntuación: «94,47» sigue siendo 94,47."""
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


FECHA_SUELTA = re.compile(r"\b\d{1,2}[ ./-]+[a-z]{3,5}\.?[ ,.\-/]*\d{2,4}\b|\b[a-z]{3,5}\.? \d{1,2},? ?\d{4}\b|\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b")


def _anio(a):
    a = int(a)
    return a + 2000 if a < 100 else a


def fecha_en(texto):
    """Primera fecha reconocible de un texto, como datetime.date, o None."""
    t = _plano(texto)
    for i, rx in enumerate(FECHAS):
        for m in rx.finditer(t):
            try:
                if i == 0:
                    return datetime.date(_anio(m.group(3)), MESES[m.group(2)[:3]], int(m.group(1)))
                if i == 1:
                    return datetime.date(_anio(m.group(3)), MESES[m.group(1)[:3]], int(m.group(2)))
                return datetime.date(_anio(m.group(3)), int(m.group(2)), int(m.group(1)))
            except (ValueError, KeyError):
                continue
    return None


ENTRADA = re.compile(r"(\d{1,3}(?:\.\d{3})*[.,]\d{2}|\d+[.,]\d{2})\s*\(([^)]{5,24})\)")


def entradas_leyenda(t):
    """[(importe, fecha)] de las entradas «€32,89 (Mar 20, 2024)» de la leyenda, en el orden en que salen en el texto."""
    out = []
    for m in ENTRADA.finditer(t):
        f, v = fecha_en(m.group(2)), extract.precio_texto(m.group(1))
        if f and v:
            out.append((v, f))
    return out


def parsea(texto):
    """{minimo, fecha_minimo, maximo, fecha_maximo, media, actual} de lo que se haya podido leer (lo que falte no aparece)."""
    t = _plano(texto)
    marcas = []
    for clave, patron in ETIQUETAS:
        for m in re.finditer(r"\b(?:" + patron + r")", t):
            marcas.append((m.start(), m.end(), clave))
    marcas.sort()
    out = {}
    for i, (ini, fin, clave) in enumerate(marcas):
        if clave in out and not clave.startswith("fecha"):
            continue
        tramo = t[fin:marcas[i + 1][0] if i + 1 < len(marcas) else len(t)]
        mi = IMPORTE.search(re.sub(r"\b\d{1,2}[ ./-][a-z]{3,5}\.? ?\d{2,4}\b|\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b", " ", tramo))
        if not mi:
            continue
        v = extract.precio_texto(mi.group(1))
        if not v:
            continue
        out[clave] = v
        f = fecha_en(tramo)
        if f and clave in ("minimo", "maximo"):
            out["fecha_" + clave] = f.isoformat()
    # Si el lector no reconoce una etiqueta (a veces falta «Lowest»), se reparten las entradas de la leyenda («€32,89 (Mar 20,
    # 2024)») que NO se han reconocido ya por su etiqueta, en el orden de la leyenda: mínimo, máximo y actual.
    libres = entradas_leyenda(t)
    if libres and any(k not in out for k in ("minimo", "maximo", "actual")):
        def quita(valor, fecha=None, la_ultima=False):
            idx = [i for i, (v, f) in enumerate(libres) if abs(v - valor) < 0.005 and (fecha is None or f.isoformat() == fecha)]
            if idx:
                libres.pop(max(idx, key=lambda i: libres[i][1]) if la_ultima else idx[0])
        if "maximo" in out:
            quita(out["maximo"], out.get("fecha_maximo"))
        if "actual" in out:
            quita(out["actual"], la_ultima=True)          # la del precio actual es la fecha más reciente
        if "minimo" in out:
            quita(out["minimo"], out.get("fecha_minimo"))
        faltan = [k for k in ("minimo", "maximo", "actual") if k not in out]
        hoy = datetime.date.today()
        while faltan and libres:
            v, f = libres.pop(0)
            if len(libres) + 1 < len(faltan):             # entradas de menos: la del precio actual es de hoy; si no, por el orden
                clave = "actual" if "actual" in faltan and (hoy - f).days <= 3 else next((k for k in faltan if k != "actual"), "actual")
            else:
                clave = faltan[0]
            faltan.remove(clave)
            out[clave] = v
            if clave != "actual":
                out["fecha_" + clave] = f.isoformat()
    return out


def escala_eje(texto):
    """(mínimo, máximo, escalón) de la escala vertical de la gráfica, por sus etiquetas («€30», «€35»…), o None."""
    nums = sorted({float(n) for n in re.findall(r"(?m)^\s*[€E(C]\s?(\d{1,5})\s*$", texto or "")})
    if len(nums) < 2:
        return None
    return nums[0], nums[-1], min(y - x for x, y in zip(nums, nums[1:]))


CONFUSIONES = str.maketrans("ZOolIS", "200115")      # lo que el lector suele confundir: Z→2, O→0, l→1, S→5
SUELTO = re.compile(r"(?m)^[\s\-–—]*[€(C«]?\s?(?:(\d{1,3}|[0-9ZOolIS]{1,3})[.,]([0-9ZOolIS]{2})|([0-9ZOolIS]{2,3})([0-9ZOolIS]{2}))\s*$")


def importes_sueltos(texto):
    """Importes que están solos en su línea (las etiquetas de colores a la derecha de la gráfica: el máximo, el actual y el
    mínimo, en letra grande, que se leen mucho mejor que la leyenda). Admite la coma perdida («€5Z95» = 52,95)."""
    out = []
    for m in SUELTO.finditer(texto or ""):
        ent, cts = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        try:
            out.append(float(ent.translate(CONFUSIONES) + "." + cts.translate(CONFUSIONES)))
        except ValueError:
            continue
    return out


def parecido(v, s):
    """¿Se lee `v` donde pone `s`? Mismo final (se perdió la primera cifra: «4,99» por «44,99») o una sola cifra distinta."""
    dv, ds = f"{v:.2f}".replace(".", ""), f"{s:.2f}".replace(".", "")
    return (len(dv) < len(ds) and ds.endswith(dv.lstrip("0") or dv)) or (len(dv) == len(ds) and sum(a != b for a, b in zip(dv, ds)) == 1)


def repara(texto, d):
    """Corrige las cifras de la leyenda que quedan fuera de la escala de la gráfica con la etiqueta lateral que se les parece
    y sí cabe en la escala. Devuelve (datos, [lo que se ha corregido])."""
    esc = escala_eje(texto)
    if not esc:
        return d, []
    lo, hi, paso = esc
    dentro = lambda x: lo - paso <= x <= hi + paso      # noqa: E731
    candidatos = {s for s in importes_sueltos(texto) if dentro(s)}
    out, cambios = dict(d), []
    for clave, nombre in (("minimo", "el mínimo"), ("maximo", "el máximo"), ("actual", "el precio actual")):
        v = d.get(clave)
        if v is None or dentro(v):
            continue
        c = [s for s in candidatos if parecido(v, s)]
        if len(c) == 1:
            out[clave] = c[0]
            cambios.append(f"{nombre}: la leyenda se leyó {euros(v)} y la etiqueta de la gráfica dice {euros(c[0])}")
    if out.get("actual") is None and out.get("minimo") is not None and out.get("maximo") is not None:
        # el precio actual no se leyó en la leyenda: es la etiqueta lateral que no es ni el mínimo ni el máximo
        resto = {s for s in candidatos if abs(s - out["minimo"]) > 0.005 and abs(s - out["maximo"]) > 0.005}
        if len(resto) == 1:
            out["actual"] = resto.pop()
            cambios.append(f"el precio actual no se leyó en la leyenda: es {euros(out['actual'])}, la otra etiqueta de la gráfica")
    return out, cambios


def es_grafica(texto):
    """¿El texto es de una gráfica de camelcamelcamel? Tiene que traer su escala vertical («€30», «€35»…) y alguna palabra de su
    leyenda (Price type, Lowest, Highest, Current). Sin esto no se guarda nada: BuscaTron llegó a leer el texto de su propia
    página, con otros históricos, y a guardarlo como si fuera de un producto."""
    t = (texto or "").lower()
    return escala_eje(texto) is not None and any(k in t for k in ("price type", "lowest", "highest", "current"))


def valida(texto, d):
    """Motivos para no fiarse de lo leído (lista vacía si todo cuadra). Una lectura mala que parece buena es peor que
    ninguna: con la letra pequeña «€33,09» se lee «03,09»."""
    if re.search(r"requested\s+product|find\s+the\s+requested", texto or "", re.I):
        return ["camelcamelcamel no tiene este producto (su imagen dice «We can't find the requested product»): no hay histórico que leer."]
    if not es_grafica(texto):
        return ["la imagen no parece una gráfica de camelcamelcamel (no trae su escala ni su leyenda): no se guarda nada."]
    out = []
    esc = escala_eje(texto)
    if esc:
        lo, hi, m = esc          # un escalón de margen: a veces el lector se salta una etiqueta del eje
        for clave, nombre in (("minimo", "el mínimo"), ("maximo", "el máximo"), ("actual", "el precio actual")):
            v = d.get(clave)
            if v is not None and not lo - m <= v <= hi + m:
                out.append(f"{nombre} leído ({euros(v)}) queda fuera de la escala de la gráfica ({euros(lo)} a {euros(hi)}).")
    if d.get("minimo") is not None and d.get("maximo") is not None and d["minimo"] > d["maximo"]:
        out.append("el mínimo leído es mayor que el máximo.")
    if None not in (d.get("minimo"), d.get("maximo"), d.get("actual")) and not d["minimo"] <= d["actual"] <= d["maximo"]:
        out.append("el precio actual queda fuera del rango entre el mínimo y el máximo leídos.")
    return out


# Campañas de ofertas: (nombre, ventana en el año que pasó, fecha de este año)
def _campanas(anio):
    """[(nombre, desde, hasta, día de la campaña)] de ese año."""
    bf = black_friday(anio)
    d = datetime.timedelta
    return [("Black Friday", bf - d(days=5), bf + d(days=1), bf),
            ("Cyber Monday", bf + d(days=2), bf + d(days=5), bf + d(days=3)),
            ("las rebajas de enero", datetime.date(anio, 1, 7), datetime.date(anio, 1, 20), datetime.date(anio, 1, 7)),
            ("el Prime Day de julio", datetime.date(anio, 7, 5), datetime.date(anio, 7, 20), datetime.date(anio, 7, 15)),
            ("las ofertas de otoño de Amazon", datetime.date(anio, 10, 5), datetime.date(anio, 10, 20), datetime.date(anio, 10, 10))]


def campana_de(fecha):
    for nombre, desde, hasta, _ in _campanas(fecha.year):
        if desde <= fecha <= hasta:
            return nombre
    return None


def hace(dias):
    if dias < 45:
        return f"hace {dias} días"
    if dias < 700:
        return f"hace {round(dias / 30.4)} meses"
    return f"hace {dias / 365.25:.1f} años".replace(".", ",")


CLAVES = ("minimo", "fecha_minimo", "maximo", "fecha_maximo", "media", "actual")


def guarda(asin, d):
    """Recuerda lo leído de la gráfica de camelcamelcamel de ese producto (se sustituye si lo vuelves a leer)."""
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO camel_extremos(asin, minimo, fecha_minimo, maximo, fecha_maximo, media, actual, ts) VALUES(?,?,?,?,?,?,?,?)",
                  (asin, *[d.get(k) for k in CLAVES], time.time()))


def conserva_captura(asin, imagen, guardado, maximo=12):
    """Si una gráfica no se pudo guardar, deja su imagen en la carpeta capturas_fallidas (solo esa imagen, local, las últimas
    `maximo`) para poder ver qué recibió BuscaTron; si se guardó, se borra la de una vez anterior."""
    carpeta = os.path.join(cfg_raiz(), "capturas_fallidas")
    ruta = os.path.join(carpeta, f"{asin}.png")
    try:
        if guardado:
            if os.path.exists(ruta):
                os.remove(ruta)
            return
        os.makedirs(carpeta, exist_ok=True)
        with open(ruta, "wb") as f:
            f.write(imagen)
        viejas = sorted((os.path.join(carpeta, n) for n in os.listdir(carpeta)), key=os.path.getmtime)
        for v in viejas[:-maximo]:
            os.remove(v)
    except OSError:
        pass


def cfg_raiz():
    from . import tiendas
    return tiendas.RAIZ


def anota_lectura(asin, texto, problemas, ancho, guardado):
    """Lo último que se leyó de la gráfica de ese producto, para saber por qué una no se guardó (solo el texto, no la imagen)."""
    with bd.conecta() as c:
        c.execute("INSERT OR REPLACE INTO camel_lecturas(asin, texto, problemas, ancho, guardado, ts) VALUES(?,?,?,?,?,?)",
                  (asin, (texto or "")[:3000], " | ".join(problemas), ancho, int(guardado), time.time()))


def todos():
    """{asin: {minimo, fecha_minimo, maximo, fecha_maximo, media, actual, ts}} de lo ya leído."""
    with bd.conecta() as c:
        return {r["asin"]: {k: r[k] for k in CLAVES + ("ts",) if r[k] is not None} for r in c.execute("SELECT * FROM camel_extremos")}


def frases(d, hoy=None, aviso=True):
    hoy = hoy or datetime.date.today()
    e = euros
    out = []
    mn, mx, act = d.get("minimo"), d.get("maximo"), d.get("actual")
    if mn is not None:
        f = datetime.date.fromisoformat(d["fecha_minimo"]) if d.get("fecha_minimo") else None
        out.append(f"Mínimo histórico: {e(mn)}" + (f" el {f.strftime('%d/%m/%Y')} ({hace((hoy - f).days)})." if f else " (no se ha podido leer la fecha)."))
    if mx is not None:
        f = datetime.date.fromisoformat(d["fecha_maximo"]) if d.get("fecha_maximo") else None
        out.append(f"Máximo histórico: {e(mx)}" + (f" el {f.strftime('%d/%m/%Y')}." if f else "."))
    if d.get("media") is not None:
        out.append(f"Precio medio: {e(d['media'])}.")
    if act is not None and mn:
        extra = round(100 * (act / mn - 1))
        out.append(f"Ahora {e(act)}: " + ("está en su mínimo histórico." if act <= mn * 1.005 else f"un {extra} % por encima de su mínimo" +
                   (f" y al {round(100 * (act - mn) / (mx - mn))} % del recorrido hasta su máximo." if mx and mx > mn else ".")))
    if d.get("fecha_minimo"):
        f = datetime.date.fromisoformat(d["fecha_minimo"])
        camp = campana_de(f)
        if camp:
            futuras = [(n, dia) for n, _, _, dia in _campanas(hoy.year) + _campanas(hoy.year + 1) if n == camp and dia >= hoy]
            prox = min(futuras, key=lambda x: x[1]) if futuras else None
            out.append(f"Su mínimo coincidió con {camp} de {f.year}: es una época en la que ha bajado. " +
                       (f"La próxima ({camp}) cae hacia el {prox[1].strftime('%d/%m')}, dentro de {(prox[1] - hoy).days} días."
                        if prox else ""))
        else:
            out.append(f"Su mínimo no coincidió con ninguna campaña conocida (cayó el {f.strftime('%d/%m')}).")
    if aviso:
        out.append("Con solo los extremos no se puede calcular cada cuánto se repite una bajada: eso necesita toda la serie de precios, "
                   "que la gráfica dibuja pero la leyenda no escribe. Lo anterior es lo que se puede afirmar con lo leído.")
    return out
