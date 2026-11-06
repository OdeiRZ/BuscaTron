"""Descarga de páginas con la biblioteca estándar."""
import gzip
import re
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, timeout=25):
    """Devuelve (estado, texto). Lanza URLError si la red falla."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept-Encoding": "gzip",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            return r.status, decodifica(data, r.headers.get_content_charset())
    except urllib.error.HTTPError as e:
        return e.code, ""


def decodifica(data, charset=None):
    """UTF-8 estricto primero; si falla, el charset declarado o cp1252."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = re.search(rb"charset=[\"']?([A-Za-z0-9_-]+)", data[:4096])
    for c in (charset, m.group(1).decode() if m else None, "cp1252"):
        if c:
            try:
                return data.decode(c)
            except (LookupError, UnicodeDecodeError):
                continue
    return data.decode("utf-8", "replace")
