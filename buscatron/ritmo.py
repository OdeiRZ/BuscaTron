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


def _comprueba(h):
    from . import tiendas as cfg
    if any(t.get("bloqueo") and host("https://" + t["host"]) == h for t in cfg.carga()):
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
