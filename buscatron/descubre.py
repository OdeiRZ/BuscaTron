"""Descubre la URL de búsqueda de una tienda leyendo el formulario de su portada."""
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlencode

CAMPOS = ("s", "q", "search", "search_query", "query", "keyword", "keywords", "term", "searchterm")


class _Forms(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms, self._f = [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self._f = {"action": a.get("action", ""), "method": (a.get("method") or "get").lower(), "campos": []}
        elif tag == "input" and self._f is not None and a.get("name"):
            self._f["campos"].append((a["name"], a.get("type", "text"), a.get("value", "")))

    def handle_endtag(self, tag):
        if tag == "form" and self._f is not None:
            self.forms.append(self._f)
            self._f = None


def plantilla(html, base):
    """Devuelve una URL con {q} o None."""
    p = _Forms()
    p.feed(html)
    for f in p.forms:
        if f["method"] != "get":
            continue
        buscador = [c for c in f["campos"] if c[0].lower() in CAMPOS and c[1] in ("text", "search", "")]
        if not buscador:
            continue
        nombre = buscador[0][0]
        extra = [(n, v) for n, t, v in f["campos"] if n != nombre and t == "hidden"]
        url = urljoin(base, f["action"] or "/")
        sep = "&" if "?" in url else "?"
        return url + sep + urlencode(extra + [(nombre, "\0")]).replace("%00", "{q}")
    m = re.search(r'<link[^>]+rel=["\']search["\'][^>]+href=["\']([^"\']+)', html, re.I)
    return None
