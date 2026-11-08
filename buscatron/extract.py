"""Extractor genérico de productos: enlaces cuyo texto encaja con la búsqueda y el primer precio
vigente de su tarjeta (dentro del enlace o justo después, antes del siguiente producto)."""
import json
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

# «1.299 €» y «2.500€» llevan punto de miles (antes se leían 299 y 500); «29.99 €» y «1.50 €», punto decimal.
PRECIO = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+,\d{1,2}|\d+(?:\.\d{1,2})?)\s*(?:€|eur)", re.I)
PRECIO_ANTES = re.compile(r"(?:€|eur)\s*(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)", re.I)
MILES = re.compile(r"\d{1,3}(?:\.\d{3})+")


def precio_texto(s):
    """Número de un precio escrito en la página: «1.299» son mil doscientos noventa y nueve; «29,99» o «29.99», decimales."""
    s = str(s).strip()
    return a_numero(s.replace(".", "") if MILES.fullmatch(s) else s)
TACHADO_PARTES = {"old", "regular", "before", "compare", "was", "strike", "strikethrough", "through", "tachado", "tachada", "antes",
                  "original", "msrp", "saving", "savings", "ahorro", "ahorras", "reduction", "rebaja"}


def es_tachado(attrs):
    """¿Es un precio tachado (el anterior)? Se comparan palabras completas de la clase («a-text-bold» no es «old»),
    además de style=line-through y el atributo data-a-strike de Amazon."""
    cls = re.sub(r"([a-z])([A-Z])", r"\1 \2", attrs.get("class", "") or "")
    return (bool({p.lower() for p in re.findall(r"[A-Za-z]+", cls)} & TACHADO_PARTES)
            or attrs.get("data-a-strike") == "true" or "line-through" in (attrs.get("style", "") or ""))
OCULTO = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)
VACIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
RESERVA = re.compile(r"reserva|en reposici[oó]n", re.I)
AGOTADO = re.compile(r"(?<!casi )agotad|en reposici[oó]n|vuelva a estar disponible|sin existencias|no hay existencias|sin stock|no disponible|out of stock|sold.?out|fuera de stock", re.I)
PREVENTA = re.compile(r"pre-?venta|pre-?order|lanzamiento aproximado|pr[oó]ximamente|pr[oó]xima aparici[oó]n|fecha (?:de salida|prevista)|disponible a partir", re.I)
ESTADO = re.compile(r"\b(precintado|sin abrir|sin estrenar|como nuevo|seminuevo|reacondicionado|nuevo|muy bueno|buen estado|bueno|aceptable|usado|segunda mano|para piezas|ha sido utilizado)\b", re.I)
def normaliza_simple(t):
    return re.sub(r"[^a-z0-9 ]+", " ", t.lower()).strip()


PAGINA = re.compile(r"(?:[?&/](?:page|p|pagina|pag|pg|pageno|pagenumber|start|offset|from|desde)[=/-]?\d+)|/page/\d+|/pagina-?\d+", re.I)
SIGUIENTE_TEXTO = {"siguiente", "next", ">", "»", "›", "pagina siguiente", "siguiente »", "siguiente >", "next »", "next >", "→"}
SIGUIENTE_NORM = {n for n in (normaliza_simple(t) for t in SIGUIENTE_TEXTO) if n}


def normaliza(texto):
    t = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in t if not unicodedata.combining(c)))


def encaja(n, w):
    """¿El texto normalizado n contiene w empezando en una palabra? «carta» encaja en «cartas», pero «vantage» no en
    «advantage». También vale escrito junto o separado: «spider man» y «spiderman»."""
    w = w.strip()
    if not w:
        return True
    if re.search(r"(?<![a-z0-9])" + re.escape(w), n):
        return True
    junto, objetivo, pos, inicios = n.replace(" ", ""), w.replace(" ", ""), 0, []
    for p in n.split():
        inicios.append(pos)
        pos += len(p)
    return any(junto.startswith(objetivo, i) for i in inicios)


SEGUIMIENTO = re.compile(r"^(utm_.*|srsltid|gclid|fbclid|msclkid|igshid|mc_[a-z]+|ref|ref_|referrer|dib|dib_tag|qid|sr|crid|sprefix|keywords|pd_rd_.*|pf_rd_.*|content-id|psc|th|spLa|smid)$", re.I)
ASIN = re.compile(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})(?:[/?]|$)")


def limpia_url(url):
    """Dirección canónica de un producto: sin códigos de seguimiento que cambian en cada visita. Así un mismo producto es
    siempre la misma dirección (historial, mínimo histórico y avisos sin repetir). Amazon: /dp/ASIN."""
    u = urlparse(url)
    if u.netloc.startswith(("www.amazon.", "amazon.")):
        m = ASIN.search(u.path)
        if m:
            return f"{u.scheme}://{u.netloc}/dp/{m.group(1)}"
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if not SEGUIMIENTO.match(k)]
    return urlunparse((u.scheme, u.netloc, re.sub(r"/ref=[^/?#]*", "", u.path), u.params, urlencode(q), u.fragment))


def titulo_desde_url(url):
    """Título legible a partir del último tramo de la dirección (respaldo si la web recorta el título)."""
    seg = urlparse(url).path.rstrip("/").split("/")[-1]
    seg = re.sub(r"\.html?$", "", seg)
    seg = re.sub(r"^\d+-|-\d+$", "", seg)
    t = seg.replace("-", " ").strip()
    return t[:1].upper() + t[1:]


def a_numero(s):
    s = str(s).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


class _Parser(HTMLParser):
    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base = base
        # ("a", href, texto, precios_dentro, textos_dentro, indice_inicio) | ("p", valor) | ("x", texto)
        self.eventos = []
        self.siguiente = {1: None}            # rel="next": el más fiable
        self._sig_texto, self._sig_clase = [], []   # enlaces «Siguiente» por su texto / por su clase CSS
        self._a = None
        self._tachado = 0
        self._oculto = 0
        self._pila = []
        self._skip = 0

    def _candidato_siguiente(self, nivel, href, palabra=False):
        h = urljoin(self.base, href or "")
        if not href or href.startswith(("#", "javascript")) or h == self.base:
            return
        if nivel == 1:
            self.siguiente[1] = self.siguiente[1] or h
        else:
            if nivel == 2:
                self._sig_texto.append((h, palabra))
            else:
                self._sig_clase.append(h)

    def elegir_siguiente(self):
        """rel=next; si no, un enlace con texto «Siguiente»; si no, uno por clase CSS que tenga pinta de paginación
        (así no se confunde con los botones de un carrusel de productos)."""
        if self.siguiente[1]:
            return self.siguiente[1]
        for h in [h for h, _ in self._sig_texto] + self._sig_clase:      # con dirección de paginación
            if PAGINA.search(h):
                return h
        return next((h for h, palabra in self._sig_texto if palabra), None)   # último recurso: la palabra «Siguiente», no un símbolo

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        marca = bool(tag in ("del", "s", "strike") or es_tachado(a))
        oculto = bool("hidden" in a or OCULTO.search(a.get("style", "") or ""))
        if tag not in VACIAS:
            self._pila.append((tag, marca, oculto))
            self._tachado += marca
            self._oculto += oculto
        if tag == "link" and "next" in (a.get("rel") or "").lower().split():
            self._candidato_siguiente(1, a.get("href"))
        if tag == "a" and a.get("href"):
            etiquetas = " ".join(a.get(k, "") or "" for k in ("class", "aria-label", "title"))
            self._a = {"href": urljoin(self.base, a["href"]), "raw": a["href"], "txt": [], "title": a.get("title", ""), "p": [], "x": [],
                       "ini": len(self.eventos), "rel_next": "next" in (a.get("rel") or "").lower().split(),
                       "clase_next": bool(re.search(r"\bnext\b|siguiente", etiquetas, re.I))}
        if tag == "img" and self._a is not None and a.get("alt"):
            self._a["txt"].append(a["alt"])
        if a.get("itemprop") == "price" and a.get("content") and not self._tachado:    # precio de los microdatos (el bueno)
            v = a_numero(a["content"])
            if v:
                self.eventos.append(("p", v))
        if a.get("itemprop") == "availability" and a.get("content"):                  # stock de los microdatos
            disp = a["content"].lower()
            if any(k in disp for k in ("outofstock", "soldout", "discontinued")):
                self.eventos.append(("x", "Agotado"))
            elif any(k in disp for k in ("preorder", "presale")):
                self.eventos.append(("x", "Preventa"))

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1
        if tag in VACIAS:
            return
        while self._pila:
            t, marca, oculto = self._pila.pop()
            self._tachado -= marca
            self._oculto -= oculto
            if t == tag:
                break
        if tag == "a" and self._a is not None:
            a = self._a
            txt = " ".join(a["txt"]).strip() or a["title"]
            titulo = " ".join(a["title"].split())
            corto = txt.rstrip(".… ").lower()
            if txt.endswith(("...", "…")) and len(titulo) > len(corto) and titulo.lower().startswith(corto):
                txt = titulo   # la web recorta el texto del enlace, pero el title está completo
            txt = " ".join(txt.split())
            if a["rel_next"]:
                self._candidato_siguiente(1, a["raw"])
            elif txt.strip() in SIGUIENTE_TEXTO or (normaliza(txt).strip() and normaliza(txt).strip() in SIGUIENTE_NORM):
                self._candidato_siguiente(2, a["raw"], palabra=bool(normaliza(txt).strip()))
            elif a["clase_next"]:
                self._candidato_siguiente(3, a["raw"])
            self.eventos.append(("a", a["href"], txt, a["p"], a["x"], a["ini"]))
            self._a = None

    def handle_data(self, data):
        if self._skip or self._oculto:
            return
        if self._a is not None:
            self._a["txt"].append(data)
        d = " ".join(data.split())
        if not d:
            return
        if not self._tachado:
            for rx in (PRECIO, PRECIO_ANTES):
                for m in rx.finditer(d):
                    if d[:m.start()].rstrip().endswith(("-", "−", "–")):      # «-2,59 €» es un descuento, no un precio
                        continue
                    v = precio_texto(m.group(1))
                    if v:
                        self.eventos.append(("p", v))
                        if self._a is not None:
                            self._a["p"].append(v)
        if self._a is not None:
            self._a["x"].append(d)
        self.eventos.append(("x", d))


# Sugerencias del buscador de la tienda («En lugar de lo anterior, busca X» en Amazon): llevan a otra búsqueda, no a un producto.
SUGERENCIA = re.compile(r"^\s*(en lugar de lo anterior|buscar en su lugar|busca en su lugar|quiz[aá]s? quisiste decir|quisiste decir|"
                        r"mostrando resultados (de|para)|resultados para|search instead|did you mean|showing results for)", re.I)


def es_otra_busqueda(url, base):
    """¿El enlace lleva a la propia página de resultados (misma ruta y los mismos parámetros de búsqueda) y no a un producto?"""
    u, b = urlparse(url), urlparse(base)
    claves_b = {k for k, _ in parse_qsl(b.query)}
    return bool(claves_b) and u.netloc == b.netloc and u.path == b.path and claves_b <= {k for k, _ in parse_qsl(u.query)}


def _forma(url):
    """Forma de la dirección de una ficha: dominio, número de tramos de la ruta y extensión («/juego-123.html»)."""
    u = urlparse(limpia_url(url))
    tramos = [t for t in u.path.split("/") if t]
    return u.netloc, len(tramos), tramos[-1].rpartition(".")[2] if tramos and "." in tramos[-1] else ""


def analiza(html, base, consulta, ventana=40, con_estado=False):
    """Devuelve (productos, url_de_la_página_siguiente|None).
    Producto: {titulo, url, precio, agotado, preventa, estado}."""
    palabras = normaliza(consulta).split()
    p = _Parser(base)
    p.feed(html)
    ev = p.eventos
    encajan = [i for i, e in enumerate(ev) if e[0] == "a" and len(e[2]) >= 4 and all(encaja(normaliza(e[2]), w) for w in palabras)
               and not SUGERENCIA.match(e[2]) and not es_otra_busqueda(e[1], base)]
    # La tarjeta también acaba donde empieza la de otro producto que NO encaja (su enlace tiene la misma forma de ficha):
    # si no, su «En reposición» se le atribuía al anterior (Dungeon Marvels: Mage Knight salía agotado por el de Krang).
    formas = {_forma(ev[i][1]) for i in encajan}
    out, vistos, previos = [], set(), {}
    for k, i in enumerate(encajan):
        e = ev[i]
        limite = ev[encajan[k + 1]][5] if k + 1 < len(encajan) else len(ev)   # el siguiente producto empieza ahí
        propia = urlparse(limpia_url(e[1])).path
        otro = next((j for j in range(i + 1, min(limite, i + 1 + ventana)) if ev[j][0] == "a" and _forma(ev[j][1]) in formas
                     and urlparse(limpia_url(ev[j][1])).path != propia), None)
        if otro is not None:
            limite = ev[otro][5]
        titulo, textos, precio = e[2], list(e[4]), (e[3][0] if e[3] else None)
        pv = re.search(r"(\d+(?:[.,]\d{1,2})?)\s*€\s*,\s*\d+(?:[.,]\d{1,2})?\s*€\s*$", titulo) if "Estado:" in titulo else None
        if pv:                                   # Vinted: «..., Estado: Muy bueno, 1.00 €, 1.75 €» (artículo y con protección)
            precio = a_numero(pv.group(1))
        for j in range(i + 1, min(i + 1 + ventana, max(limite, i + 1))):
            f = ev[j]
            if f[0] == "p" and precio is None:
                precio = f[1]
            elif f[0] == "x":
                textos.append(f[1])
        url = limpia_url(e[1])
        if precio is None and url not in vistos:     # enlace de la imagen: lo que va hasta el del título («Agotado») es suyo
            previos.setdefault(url, []).extend(textos)
        if precio is None or url in vistos or not url.startswith(("http://", "https://")):   # nunca «javascript:» y similares
            continue
        textos = previos.pop(url, []) + textos
        vistos.add(url)
        if titulo.endswith(("...", "…")) and len(titulo_desde_url(e[1])) > len(titulo):
            titulo = titulo_desde_url(e[1])
        detalle = re.search(r"Estado:\s*([^,]+)", titulo)         # Vinted: «Título, Marca: X, Estado: Muy bueno, 1.00 €»
        titulo = re.split(r",\s*(?:Marca|Estado|Tama[ñn]o):", titulo)[0].strip()
        marca = re.match(r"\s*(producto agotado|agotado|sin stock|fuera de stock)\s*[:\-–]?\s*", titulo, re.I)
        if marca:                                    # Turol Games: «Producto agotado Marvel Champions…» dentro del título
            titulo = titulo[marca.end():]
        preventa = bool(PREVENTA.search(titulo) or any(PREVENTA.search(t) for t in textos))
        agotado = bool(marca) or any(AGOTADO.search(t) for t in textos) or (not preventa and any(RESERVA.fullmatch(t.strip()) for t in textos))
        estado = ""
        if con_estado and detalle:
            estado = detalle.group(1).strip().lower()
        elif con_estado:
            for t in textos:
                m = len(t) <= 45 and ESTADO.search(t)
                if m:
                    estado = m.group(1).lower()
                    break
        out.append({"titulo": titulo, "url": url, "precio": precio, "agotado": agotado, "preventa": preventa, "estado": estado})
    return out, p.elegir_siguiente()


def extrae(html, base, consulta, ventana=40, con_estado=False):
    return analiza(html, base, consulta, ventana, con_estado)[0]


# ---- páginas de un solo producto (búsqueda abierta) -------------------------------------------------

_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
_META = re.compile(r"<meta\s+[^>]*>", re.I)


def _nodos(obj):
    if isinstance(obj, list):
        for o in obj:
            yield from _nodos(o)
    elif isinstance(obj, dict):
        yield obj
        for v in obj.values():
            if isinstance(v, (dict, list)):
                yield from _nodos(v)


def _meta(html):
    d = {}
    for m in _META.finditer(html):
        tag = m.group(0)
        k = re.search(r'(?:property|name|itemprop)=["\']([^"\']+)', tag, re.I)
        v = re.search(r'content=["\']([^"\']*)', tag, re.I)
        if k and v:
            d.setdefault(k.group(1).lower(), v.group(1))
    return d


def datos_producto(html, url=""):
    """Lee un producto de una página individual: JSON-LD (schema.org), Open Graph o microdatos.
    Devuelve {titulo, precio, moneda, agotado, preventa, url} o None."""
    for bloque in _LD.findall(html):
        try:
            datos = json.loads(bloque.strip())
        except ValueError:
            continue
        for n in _nodos(datos):
            tipo = n.get("@type")
            tipos = tipo if isinstance(tipo, list) else [tipo]
            if "Product" not in tipos or "offers" not in n:
                continue
            for o in _nodos(n["offers"]):
                precio = a_numero(o.get("price") if o.get("price") not in (None, "") else o.get("lowPrice", ""))
                if precio:
                    disp = str(o.get("availability", "")).lower()
                    return {"titulo": str(n.get("name", "")).strip(), "precio": precio, "moneda": o.get("priceCurrency", "EUR"),
                            "agotado": any(s in disp for s in ("outofstock", "soldout", "discontinued")),
                            "preventa": any(s in disp for s in ("preorder", "presale")), "url": n.get("url") or url}
    m = _meta(html)
    for clave in ("product:price:amount", "og:price:amount", "price"):
        precio = a_numero(m.get(clave, "")) if m.get(clave) else None
        if precio:
            disp = (m.get("product:availability") or m.get("og:availability") or "").lower()
            return {"titulo": (m.get("og:title") or "").strip(), "precio": precio,
                    "moneda": m.get("product:price:currency") or m.get("og:price:currency") or "EUR",
                    "agotado": "out of stock" in disp or "oos" in disp, "preventa": "preorder" in disp, "url": url}
    return None


# ---- idioma real de un producto (ficha) --------------------------------------------------------------

MARCAS_UNICODE = re.compile(r"[\u200e\u200f\u202a-\u202e]+")
LENGUAS = re.compile(r"\b(castellano|espanol|spanish|ingles|english|frances|french|francais|aleman|german|deutsch|italiano|italian|"
                     r"portugues|portuguese|polaco|polish|neerlandes|dutch|catalan|euskera|gallego|ruso|russian|chino|japones|"
                     r"multilingue|multi-?idioma|independiente del idioma)\b")
ETIQUETA_IDIOMA = re.compile(r"^(?:idiomas?|language|languages|langue|sprache)\b[\s:：-]*(.*)$", re.I)


def idioma_pagina(html):
    """Valor del campo «Idioma» de la ficha de un producto («Francés», «Español, Inglés»…) o None.
    Lee las filas de detalles de Amazon y de otras tiendas, tanto «Idioma: Francés» como etiqueta y valor en elementos separados."""
    p = _Parser("")
    p.feed(html)
    textos = [MARCAS_UNICODE.sub("", e[1]).strip() for e in p.eventos if e[0] == "x"]
    for i, t in enumerate(textos):
        m = ETIQUETA_IDIOMA.match(re.sub(r"\s+", " ", t))
        if not m:
            continue
        valor = m.group(1).strip(" :：")
        if not valor:                  # etiqueta y valor separados: lo siguiente solo vale si es un idioma
            siguiente = next((x.strip(" :：") for x in textos[i + 1:i + 3] if x.strip(" :：")), "")
            valor = siguiente if LENGUAS.search(normaliza(siguiente)) else ""
        if valor and len(valor) <= 60:     # si no, sigue: Dungeon Marvels tiene un «Idiomas:» vacío antes del bueno
            return valor
    return None


def codigo_idioma(valor):
    """'es' | 'en' | 'otro' a partir del texto de la ficha; None si está vacío. Si admite varios idiomas, manda el castellano."""
    n = normaliza(valor or "")
    if not n.strip():
        return None
    if re.search(r"\b(castellano|espanol|spanish)\b", n):
        return "es"
    if re.search(r"\b(ingles|english)\b", n):
        return "en"
    return "otro"


# ---- gastos de envío --------------------------------------------------------------------------------

_GRATIS = re.compile(r"(?:env[ií]os?|portes|gastos de env[ií]o)(?:\s+[\w\-]+){0,3}?\s+(?:gratis|gratuitos?)[^.\d€]{0,45}?"
                     r"(?:a partir de|desde|superior(?:es)? a|m[aá]s de|por compras? de|en pedidos? (?:de|superiores a))\s*(\d+(?:[.,]\d{1,2})?)\s*(?:€|eur)", re.I)
_GRATIS2 = re.compile(r"(?:a partir de|desde|superior(?:es)? a|m[aá]s de)\s*(\d+(?:[.,]\d{1,2})?)\s*(?:€|eur)[^.\d€]{0,25}?(?:env[ií]o|portes)\s+gratis", re.I)
_COSTE = re.compile(r"(?:gastos de env[ií]o|env[ií]o est[aá]ndar|portes)[^.\d€]{0,30}?(\d+(?:[.,]\d{1,2})?)\s*(?:€|eur)", re.I)


def detecta_envio(html):
    """Busca en una página (la portada) el envío gratis desde X € y/o el coste del envío.
    Devuelve {'gratis_desde': float|None, 'coste': float|None}; es solo una pista y hay que revisarla."""
    p = _Parser("")
    p.feed(html)
    texto = " ".join(e[1] for e in p.eventos if e[0] == "x")
    g = _GRATIS.search(texto) or _GRATIS2.search(texto)
    c = _COSTE.search(texto)
    coste = a_numero(c.group(1)) if c else None
    return {"gratis_desde": a_numero(g.group(1)) if g else None, "coste": coste if coste and 0 < coste < 40 else None}
