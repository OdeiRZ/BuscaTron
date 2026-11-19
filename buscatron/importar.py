"""Importar a mano los resultados de una tienda que no se puede consultar automáticamente (Cloudflare, etc.).
Tú abres la tienda en tu navegador, copias lo que ves y lo pegas en BuscaTron: se leen los productos y precios y se
mezclan con el resto de resultados (y con el historial) durante unas horas.
Acepta el texto de la página (Ctrl+A, Ctrl+C) o su código HTML, y no hace ninguna petición a la tienda."""
import re
import time

from . import bd, extract

CADUCA_HORAS = 72
AVISO_ANTES_HORAS = 12      # el recordatorio llega unas horas antes de que caduque
MAX_BLOQUE = 8          # líneas que se miran tras un título para encontrar su precio
IGNORAR = ("resultado", "busqueda", "buscar", "mostrando", "ordenar", "filtrar", "filtros", "te recomendamos", "has buscado")


def _precios(linea):
    return extract.precios_en(linea)


def _sin_precios(linea):
    t = extract.PRECIO.sub(" ", linea)
    t = extract.PRECIO_ANTES.sub(" ", t)
    return " ".join(t.split()).strip(" -–·|:")


def _junta_marca(lineas, palabras):
    """Tiendas con la marca en su propia línea («15%», «VANTAGE», «Pizarra blanca…», «76,51 € 90,01 €»): si buscas la
    marca, ninguna línea de nombre la lleva y no salía nada. La marca suelta se une al nombre que la sigue; si detrás
    viene ya el precio, la marca sola hace de nombre."""
    q = " ".join(palabras)
    out, i = [], 0
    while i < len(lineas):
        l = lineas[i]
        if extract.normaliza(l).strip() == q and not _precios(l):
            sig = lineas[i + 1] if i + 1 < len(lineas) else ""
            if sig and not _precios(sig) and not all(extract.encaja(extract.normaliza(sig), w) for w in palabras):
                out.append(f"{l} {sig}")
                i += 2
                continue
            out.append(f"{l} (sin nombre en lo pegado)")    # distinto de la búsqueda: así cuenta como nombre
            i += 1
            continue
        out.append(l)
        i += 1
    return out


def parsea(texto, consulta, base=""):
    """Productos de un texto pegado: [{titulo, precio, agotado, preventa, estado, url?}]."""
    palabras = extract.normaliza(consulta).split()
    if re.search(r"<a\s[^>]*href", texto, re.I):                  # código HTML: se lee como una web (con sus enlaces)
        return extract.extrae(texto, base or "https://tienda.invalid/", consulta)
    lineas = [" ".join(l.split()) for l in texto.splitlines()]
    lineas = [l for l in lineas if l]
    lineas = _junta_marca(lineas, palabras)

    def es_titulo(l):
        n = extract.normaliza(_sin_precios(l))
        return (len(n) >= 6 and all(extract.encaja(n, w) for w in palabras) and n.strip() != " ".join(palabras)
                and not n.startswith(IGNORAR))
    idx = [i for i, l in enumerate(lineas) if es_titulo(l)]
    out, vistos = [], set()
    for k, i in enumerate(idx):
        fin = min(idx[k + 1] if k + 1 < len(idx) else len(lineas), i + MAX_BLOQUE)
        bloque = lineas[i:max(fin, i + 1)]
        precios = _precios(lineas[i])
        for l in bloque[1:]:                       # solo el grupo de precios pegado al título (el anterior y el actual)
            p = _precios(l)
            if p:
                precios += p
            elif precios:
                break                              # lo que venga después es de otro producto
        if not precios:
            continue
        titulo = _sin_precios(lineas[i])
        clave = (extract.normaliza(titulo), min(precios))
        if clave in vistos:
            continue
        vistos.add(clave)
        out.append({"titulo": titulo, "precio": min(precios),            # con dos precios, el anterior es el mayor
                    "agotado": any(extract.AGOTADO.search(l) for l in bloque),
                    "preventa": any(extract.PREVENTA.search(l) for l in bloque), "estado": ""})
    return out


def _url_item(base, titulo):
    """Dirección propia de cada producto importado (para el historial y los avisos). Abre una búsqueda en la tienda."""
    slug = re.sub(r"[^a-z0-9]+", "-", extract.normaliza(titulo)).strip("-")[:60]
    return base + ("&" if "?" in base or "#" in base else "?") + "btitem=" + slug


def _base_item(host, titulo, url_busqueda):
    """La búsqueda de la tienda con el nombre del producto, no con lo que buscabas: pegar el mismo producto desde dos
    búsquedas daba dos direcciones (salía dos veces, avisaba dos veces y partía su historial)."""
    from . import tiendas as cfg
    t = next((t for t in cfg.carga() if t["host"] == host), {})
    return cfg.url_busqueda(t["plantilla"], titulo) if t.get("plantilla") else (f"https://{host}/" if host else url_busqueda)


def guarda(host, consulta, items, url_busqueda):
    """Guarda (y sustituye) lo importado de esa tienda para esa búsqueda."""
    from . import motor          # aquí: motor ya importa este módulo
    ts = time.time()
    filas = [(host, ts, extract.normaliza(consulta), x["titulo"], x.get("url") or _url_item(_base_item(host, x["titulo"], url_busqueda), x["titulo"]), x["precio"],
              int(bool(x.get("agotado"))), int(bool(x.get("preventa")))) for x in items]
    with bd.conecta() as c:
        c.execute("DELETE FROM importados WHERE host=? AND consulta=?", (host, extract.normaliza(consulta)))
        c.executemany("DELETE FROM importados WHERE host=? AND url=?", [(host, f[4]) for f in filas])   # el mismo producto, pegado antes con otra búsqueda
        c.executemany("INSERT INTO importados(host,ts,consulta,titulo,url,precio,agotado,preventa) VALUES(?,?,?,?,?,?,?,?)", filas)
        # al historial de precios, una vez por pegado (las búsquedas ya no lo vuelven a apuntar cada vez que lo muestran)
        c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,?,NULL,?,?)",
                      [(f[1], f[2], host, f[3], f[4], f[5], f[6], f[7], motor.clave_producto(f[3])) for f in filas])
    return len(filas)


def por_caducar(ahora=None):
    """Tiendas cuyo último pegado caduca en las próximas horas y de las que aún no se ha avisado:
    [(host, ts_del_pegado, segundos_que_quedan, consulta)]."""
    ahora = ahora or time.time()
    out = []
    with bd.conecta() as c:
        for f in c.execute("SELECT host, MAX(ts) ts FROM importados GROUP BY host").fetchall():
            queda = f["ts"] + CADUCA_HORAS * 3600 - ahora
            if 0 < queda <= AVISO_ANTES_HORAS * 3600 and not c.execute(
                    "SELECT 1 FROM recordatorios WHERE host=? AND ts_importado=?", (f["host"], f["ts"])).fetchone():
                consulta = c.execute("SELECT consulta FROM importados WHERE host=? AND ts=? LIMIT 1", (f["host"], f["ts"])).fetchone()[0]
                out.append((f["host"], f["ts"], queda, consulta))
    return out


def marca_recordado(host, ts_importado):
    with bd.conecta() as c:
        c.execute("INSERT OR IGNORE INTO recordatorios(host, ts_importado) VALUES(?,?)", (host, ts_importado))


def vigentes(host, consulta, ahora=None):
    """Lo importado de esa tienda que no ha caducado y encaja con la búsqueda actual."""
    ahora = ahora or time.time()
    palabras = extract.normaliza(consulta).split()
    with bd.conecta() as c:
        filas = [dict(r) for r in c.execute("SELECT * FROM importados WHERE host=? AND ts>? ORDER BY ts DESC",
                                           (host, ahora - CADUCA_HORAS * 3600))]
    return [{"titulo": f["titulo"], "url": f["url"], "precio": f["precio"], "agotado": bool(f["agotado"]), "preventa": bool(f["preventa"]),
             "estado": "", "importado": f["ts"]} for f in filas if all(extract.encaja(extract.normaliza(f["titulo"]), w) for w in palabras)]
