"""Reiniciar y cerrar BuscaTron desde la web o la bandeja, como en PixelatIA: nunca con un trabajo en marcha (búsqueda,
revisión de una vigilada o búsqueda del bot), y el botón 🆕 cuando el código cambió desde que arrancó.
Al reiniciar sale con el código 3: BuscaTron.bat lo vuelve a lanzar (sin abrir otra pestaña). Si no hay .bat (el arranque
con Windows lanza pythonw directamente), se relanza él mismo antes de salir."""
import contextlib
import glob
import os
import subprocess
import sys
import threading
import time

from . import tiendas as cfg

CODIGO_REINICIO = 3            # BuscaTron.bat vuelve a lanzar la app cuando sale con este código
DESDE = time.time()
ARCHIVOS = sorted(glob.glob(os.path.join(cfg.RAIZ, "buscatron", "*.py")))   # pagina.html se lee en cada visita: no cuenta
_fechas = lambda: [os.path.getmtime(f) if os.path.exists(f) else 0 for f in ARCHIVOS]   # noqa: E731
FECHAS = _fechas()
_cerrojo = threading.Lock()
_en_curso = {}                 # {tipo: cuántos}
_saliendo = {"si": False}
NOMBRES = {"busqueda": "una búsqueda", "revision": "una revisión de una vigilada", "telegram": "una búsqueda del bot de Telegram"}


@contextlib.contextmanager
def trabajo(tipo):
    """Marca un trabajo en marcha mientras dura el bloque."""
    with _cerrojo:
        _en_curso[tipo] = _en_curso.get(tipo, 0) + 1
    try:
        yield
    finally:
        with _cerrojo:
            _en_curso[tipo] -= 1


def saliendo():
    return _saliendo["si"]


def en_curso():
    with _cerrojo:
        return {k: v for k, v in _en_curso.items() if v}


def ocupado():
    """Frase con lo que está en marcha, o '' si nada."""
    return ", ".join(f"{n} × {NOMBRES.get(k, k)}" if n > 1 else NOMBRES.get(k, k) for k, n in en_curso().items())


def desactualizado():
    return _fechas() != FECHAS


def estado():
    return {"desde": DESDE, "desactualizado": desactualizado(), "ocupado": ocupado(), "pid": os.getpid()}


def sale(reiniciar, servidor=None):
    """Reinicia o cierra. Lanza ValueError si hay un trabajo en marcha (no se toca: hay que esperar a que termine)."""
    o = ocupado()
    if o:
        raise ValueError(f"Hay {o} en marcha: espera a que termine para {'reiniciar' if reiniciar else 'cerrar'}")
    with _cerrojo:
        if _saliendo["si"]:
            return
        _saliendo["si"] = True

    def adios():                 # un poco después, para que la página reciba la respuesta
        try:
            from . import navegador
            navegador.cierra(espera=8)        # que Chrome suelte su perfil antes de que lo use el BuscaTron nuevo
        except Exception:   # noqa: BLE001
            pass
        if servidor is not None:
            try:
                servidor.shutdown()           # deja de atender (sin cortar las respuestas en curso)…
                servidor.server_close()       # …y suelta el puerto para el nuevo
            except OSError:
                pass
        try:
            from . import bandeja             # sale con os._exit (sin atexit): el icono se quita a mano para que no quede «fantasma»
            bandeja._quita()
        except Exception:   # noqa: BLE001
            pass
        if reiniciar and os.environ.get("BUSCATRON_LANZADOR") != "bat":
            _relanza()
        print("BuscaTron:", "reiniciando…" if reiniciar else "cerrado desde la web.")
        os._exit(CODIGO_REINICIO if reiniciar else 0)
    threading.Timer(0.8, adios).start()


def _relanza():
    """Sin BuscaTron.bat que lo vuelva a lanzar: arranca otro igual (sin --abrir, como el .bat) y este sale."""
    args = [a for a in sys.argv[1:] if a != "--abrir"]
    flags = 0
    if sys.platform == "win32":
        flags = 0x00000008 | 0x00000200      # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        if not os.path.basename(sys.executable).lower().startswith("pythonw"):
            flags = 0x00000010 | 0x00000200  # con consola: CREATE_NEW_CONSOLE, para seguir viendo los mensajes
    subprocess.Popen([sys.executable, "-m", "buscatron", *args], cwd=cfg.RAIZ, creationflags=flags, close_fds=True,
                     env=dict(os.environ, BUSCATRON_REINICIO="1"))
