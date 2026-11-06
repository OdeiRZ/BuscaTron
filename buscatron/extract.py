"""Extractor genérico de productos: enlaces cuyo texto encaja con la búsqueda
y el primer precio vigente que aparece después, antes del siguiente enlace."""
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

PRECIO = re.compile(r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})|\d+(?:\.\d{1,2})?)\s*(?:€|eur)", re.I)
PRECIO_ANTES = re.compile(r"(?:€|eur)\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})|\d+(?:[.,]\d{1,2})?)", re.I)
TACHADO = re.compile(r"old|regular|before|compare|tachad|was-|strike|antes|original|msrp", re.I)
OCULTO = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)
VACIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
RESERVA = re.compile(r"reserva|en reposici[oó]n", re.I)
AGOTADO = re.compile(r"agotad|en reposici[oó]n|vuelva a estar disponible|sin existencias|no hay existencias|sin stock|no disponible|out of stock|sold.?out|fuera de stock", re.I)


def normaliza(texto):
    t = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in t if not unicodedata.combining(c)))


def titulo_desde_url(url):
    """Título legible a partir del último tramo de la dirección (respaldo si la web recorta el título)."""
    seg = urlparse(url).path.rstrip("/").split("/")[-1]
    seg = re.sub(r"\.html?$", "", seg)
    seg = re.sub(r"^\d+-|-\d+$", "", seg)
    t = seg.replace("-", " ").strip()
    return t[:1].upper() + t[1:]


def a_numero(s):
    s = s.strip()
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
        self.eventos = []          # ("a", href, texto) | ("p", valor) | ("x", texto)
        self._a = None
        self._tachado = 0
        self._oculto = 0
        self._pila = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        marca = bool(tag in ("del", "s", "strike") or TACHADO.search(a.get("class", "") or ""))
        oculto = bool("hidden" in a or OCULTO.search(a.get("style", "") or ""))
        if tag not in VACIAS:
            self._pila.append((tag, marca, oculto))
            self._tachado += marca
            self._oculto += oculto
        if tag == "a" and a.get("href"):
            self._a = {"href": urljoin(self.base, a["href"]), "txt": [], "title": a.get("title", "")}
        if tag == "img" and self._a is not None and a.get("alt"):
            self._a["txt"].append(a["alt"])
        if tag == "meta" and a.get("itemprop") == "price" and a.get("content"):
            v = a_numero(a["content"])
            if v:
                self.eventos.append(("p", v))

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
            txt = " ".join(self._a["txt"]).strip() or self._a["title"]
            titulo = " ".join(self._a["title"].split())
            corto = txt.rstrip(".… ").lower()
            if txt.endswith(("...", "…")) and len(titulo) > len(corto) and titulo.lower().startswith(corto):
                txt = titulo   # la web recorta el texto del enlace, pero el title está completo
            self.eventos.append(("a", self._a["href"], " ".join(txt.split())))
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
            for m in PRECIO.finditer(d):
                v = a_numero(m.group(1))
                if v:
                    self.eventos.append(("p", v))
            for m in PRECIO_ANTES.finditer(d):
                v = a_numero(m.group(1))
                if v:
                    self.eventos.append(("p", v))
        self.eventos.append(("x", d))


def extrae(html, base, consulta, ventana=40):
    """Devuelve [{titulo, url, precio, agotado}] de los enlaces que contienen
    todas las palabras de la consulta."""
    palabras = normaliza(consulta).split()
    p = _Parser(base)
    p.feed(html)
    ev = p.eventos
    out, vistos = [], set()
    for i, e in enumerate(ev):
        if e[0] != "a" or len(e[2]) < 4:
            continue
        titulo = e[2]
        if not all(w in normaliza(titulo) for w in palabras):
            continue
        precio, agotado = None, False
        for j in range(i + 1, min(i + 1 + ventana, len(ev))):
            f = ev[j]
            if f[0] == "a" and all(w in normaliza(f[2]) for w in palabras) and f[1] != e[1]:
                break
            if f[0] == "p" and precio is None:
                precio = f[1]
            if f[0] == "x" and (AGOTADO.search(f[1]) or RESERVA.fullmatch(f[1].strip())):
                agotado = True
        if precio is None or e[1] in vistos:
            continue
        vistos.add(e[1])
        if titulo.endswith(("...", "…")) and len(titulo_desde_url(e[1])) > len(titulo):
            titulo = titulo_desde_url(e[1])
        out.append({"titulo": titulo, "url": e[1], "precio": precio, "agotado": agotado})
    return out
