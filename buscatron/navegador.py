"""Navegador opcional (Playwright + tu Chrome/Edge) para tiendas que cargan con JavaScript.

Si Playwright no está instalado, `disponible()` devuelve False y el resto de BuscaTron funciona igual.
Usa un perfil propio y persistente. Si una tienda pide una comprobación humana (captcha), no se intenta
saltarla: se lanza `Desafio` y, con `visible=True`, puedes resolverla tú en la ventana; la sesión queda guardada.
Todas las llamadas van por un único hilo propio, porque Playwright no admite varios hilos a la vez.
"""
import os
import queue
import re
import threading

from . import tiendas as cfg

PERFIL = os.path.join(cfg.RAIZ, "navegador_perfil")
RUTAS = [r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
         r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
         r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
         r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
         r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"]
DESAFIO = re.compile(r"captcha|verify you are human|just a moment|attention required|are you a robot|"
                     r"comprobaci[oó]n de seguridad|no eres un robot|robot check|acceso denegado|access denied", re.I)


class Desafio(Exception):
    """La tienda pide una comprobación humana."""


def ejecutable():
    for r in RUTAS:
        p = os.path.expandvars(r)
        if os.path.exists(p):
            return p
    return None


def disponible():
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return ejecutable() is not None


def _contenido(pag):
    """pag.content() falla si justo se está recargando: se reintenta hasta que se estabiliza."""
    for _ in range(8):
        try:
            return pag.content()
        except Exception:
            pag.wait_for_timeout(1000)
    return pag.content()


class _Hilo(threading.Thread):
    def __init__(self, visible):
        super().__init__(daemon=True, name="navegador")
        self.visible, self.cola, self.listo, self.error = visible, queue.Queue(), threading.Event(), None

    def run(self):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                ctx = pw.chromium.launch_persistent_context(
                    PERFIL, executable_path=ejecutable(), headless=not self.visible, locale="es-ES",
                    viewport={"width": 1280, "height": 900})
                pag = ctx.pages[0] if ctx.pages else ctx.new_page()
                self.listo.set()
                while True:
                    url, sal = self.cola.get()
                    if url is None:
                        break
                    try:
                        resp = pag.goto(url, wait_until="domcontentloaded", timeout=45000)
                        try:
                            pag.wait_for_load_state("networkidle", timeout=12000)
                        except Exception:
                            pass
                        pag.wait_for_timeout(1200)
                        estado, contenido = (resp.status if resp else 200), _contenido(pag)
                        # Pantallas de carga que se recargan solas (meta refresh): se espera como haría un visitante.
                        for _ in range(5):
                            if len(contenido) < 4000 and re.search(r"http-equiv=.?refresh", contenido, re.I):
                                pag.wait_for_timeout(3500)
                                try:
                                    pag.wait_for_load_state("networkidle", timeout=8000)
                                except Exception:
                                    pass
                                contenido, estado = _contenido(pag), 200
                            else:
                                break
                        sal.put((estado, contenido))
                    except Exception as e:
                        sal.put(e)
                ctx.close()
        except Exception as e:
            self.error = e
            self.listo.set()


_hilo = None
_cerrojo = threading.Lock()


def cierra():
    global _hilo
    with _cerrojo:
        if _hilo and _hilo.is_alive():
            _hilo.cola.put((None, None))
        _hilo = None


def get(url, visible=False, timeout=120, esperar_humano=0):
    """Como fetch.get pero renderizando la página. Lanza Desafio si pide comprobación humana.
    Con visible=True y esperar_humano>0 (segundos) da tiempo a que la resuelvas tú en la ventana."""
    global _hilo
    with _cerrojo:
        if _hilo is not None and _hilo.is_alive() and _hilo.visible != visible:
            _hilo.cola.put((None, None))
            _hilo.join(10)
            _hilo = None
        if _hilo is None or not _hilo.is_alive():
            _hilo = _Hilo(visible)
            _hilo.start()
        h = _hilo
    h.listo.wait(30)
    if h.error:
        raise RuntimeError(f"no se pudo abrir el navegador: {str(h.error)[:100]}")
    for intento in range(1 + (esperar_humano // 5 if visible else 0)):
        sal = queue.Queue()
        h.cola.put((url, sal))
        r = sal.get(timeout=timeout)
        if isinstance(r, Exception):
            raise r
        estado, html = r
        texto = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
        if estado in (202, 403, 429, 503) and (DESAFIO.search(texto) or len(texto) < 3000) or DESAFIO.search(texto[:6000]) and len(texto) < 20000:
            if visible and intento < esperar_humano // 5:
                threading.Event().wait(5)   # tiempo para que lo resuelvas tú en la ventana
                continue
            raise Desafio("la tienda pide una comprobación humana")
        return estado, html
    raise Desafio("la tienda pide una comprobación humana")
