"""Ritmo máximo por tienda: entre dos peticiones a la misma web pasan al menos INTERVALO segundos, vengan de una búsqueda,
de sus páginas siguientes o de las fichas. A una tienda que te ha bloqueado, ninguna. Las ráfagas son lo que hace que una web
bloquee tu conexión (Dungeon Marvels, 9/11/2026) o que su protección te marque como un programa (Cloudflare)."""
import threading
import time
from urllib.parse import urlparse

INTERVALO = 15
_cerrojo = threading.Lock()
_turno = {}           # host -> momento (time.monotonic) a partir del cual le toca la siguiente petición


def host(url):
    h = urlparse(url).netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


class Prohibida(ValueError):
    """Petición a una tienda que te ha bloqueado: no se hace ninguna hasta que la reactives."""


_bloqueadas = [None, frozenset()]      # (marca del archivo de tiendas, hosts bloqueados)


def _comprueba(h):
    import os
    from . import tiendas as cfg
    try:
        marca = (cfg.RUTA, os.stat(cfg.RUTA).st_mtime_ns)
    except OSError:
        marca = (cfg.RUTA, None)
    if marca != _bloqueadas[0]:
        lista = cfg.lee_json(cfg.RUTA) if marca[1] is not None else []
        _bloqueadas[:] = [marca, frozenset(host("https://" + t["host"]) for t in lista if t.get("bloqueo"))]
    if h in _bloqueadas[1]:
        raise Prohibida("esa tienda te ha bloqueado: no se le hace ninguna petición hasta que la reactives")


def espera(url):
    """Espera su turno para pedir `url` y reserva el siguiente. Devuelve los segundos esperados."""
    h = host(url)
    if not h or h in ("127.0.0.1", "localhost"):
        return 0
    _comprueba(h)
    with _cerrojo:                      # se reserva el turno dentro del cerrojo y se espera fuera: varios hilos hacen cola
        ahora = time.monotonic()
        turno = max(ahora, _turno.get(h, 0))
        _turno[h] = turno + INTERVALO
    pausa = turno - ahora
    if pausa > 0:
        time.sleep(pausa)
        _comprueba(h)                   # pudo bloquearte mientras esperaba su turno
    return pausa
