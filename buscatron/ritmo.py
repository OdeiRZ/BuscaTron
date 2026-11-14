"""Ritmo máximo por tienda: entre dos peticiones a la misma web pasan al menos INTERVALO segundos, vengan de una búsqueda,
de sus páginas siguientes, de las fichas o de la prueba de una tienda bloqueada. Las ráfagas son lo que hace que una web
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


def espera(url):
    """Espera su turno para pedir `url` y reserva el siguiente. Devuelve los segundos esperados."""
    h = host(url)
    if not h or h in ("127.0.0.1", "localhost"):
        return 0
    with _cerrojo:                      # se reserva el turno dentro del cerrojo y se espera fuera: varios hilos hacen cola
        ahora = time.monotonic()
        turno = max(ahora, _turno.get(h, 0))
        _turno[h] = turno + INTERVALO
    pausa = turno - ahora
    if pausa > 0:
        time.sleep(pausa)
    return pausa
