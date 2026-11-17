"""v0.17.42: una tienda cuya página se lee bien pero no tiene el producto no se repite con Chrome en cada búsqueda (Chrome es uno
solo y con 70 tiendas la cola hacía caducar las consultas de las demás); el tiempo límite de Chrome cuenta desde que atiende la página."""
import os
import queue
import sys
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import motor, navegador  # noqa: E402

VACIA = "<html><body>" + "<p>sin resultados</p>" * 50 + "</body></html>"


class SinChrome(unittest.TestCase):
    def setUp(self):
        motor._sin_chrome.clear()

    def test_si_chrome_tampoco_encuentra_nada_no_se_repite(self):
        t = {"host": "x.es", "plantilla": "https://x.es/?s={q}"}
        usado = []
        with mock.patch.object(motor.fetch, "get", lambda u, **k: (200, VACIA)), \
                mock.patch.object(motor.navegador, "get", lambda u, **k: usado.append(u) or (200, VACIA)):
            motor._tienda_base(dict(t), "marvel champions", nav={"visible": False})
            motor._tienda_base(dict(t), "marvel champions", nav={"visible": False})
        self.assertEqual(len(usado), 1)

    def test_un_fallo_de_la_lectura_directa_si_prueba_con_chrome(self):
        t = {"host": "y.es", "plantilla": "https://y.es/?s={q}"}
        usado = []
        with mock.patch.object(motor.fetch, "get", lambda u, **k: (404, "")), \
                mock.patch.object(motor.navegador, "get", lambda u, **k: usado.append(u) or (200, VACIA)):
            motor._tienda_base(dict(t), "marvel champions", nav={"visible": False})
            motor._tienda_base(dict(t), "marvel champions", nav={"visible": False})
        self.assertEqual(len(usado), 2)


class ColaDeChrome(unittest.TestCase):
    def test_el_limite_cuenta_desde_que_empieza_con_la_pagina(self):
        """Una página que espera 1,5 s su turno no caduca con un límite de 1 s: el límite es para cargarla."""
        class Falso:
            visible = False
            error = None
            def __init__(self):
                self.cola, self.listo = queue.Queue(), threading.Event()
                self.listo.set()
                threading.Thread(target=self.atiende, daemon=True).start()
            def is_alive(self):
                return True
            def atiende(self):
                time.sleep(1.5)                                   # ocupado con otra tienda
                url, sal, espera, empieza = self.cola.get()
                empieza.set()
                sal.put((200, "<html>ok</html>" * 400))
        with mock.patch.object(navegador, "_hilo", Falso()), mock.patch.object(navegador.ritmo, "espera", lambda u: None):
            self.assertEqual(navegador.get("https://z.es/", timeout=1)[0], 200)


class PestanaColgada(unittest.TestCase):
    def test_tras_un_cuelgue_se_abre_otra_pestana(self):
        """«Page crashed» en una tienda no deja la pestaña muerta para las siguientes."""
        class Pag:
            def __init__(self, n): self.n = n
            def goto(self, url, **k):
                if self.n == 0: raise RuntimeError("Page.goto: Page crashed")
                return mock.Mock(status=200)
            def wait_for_load_state(self, *a, **k): pass
            def wait_for_timeout(self, ms): pass
            def content(self): return "<html>bien</html>" * 400
            def close(self): pass
        paginas = []
        class Ctx:
            pages = []
            def new_page(self):
                paginas.append(Pag(len(paginas))); return paginas[-1]
            def close(self): pass
        pw = mock.MagicMock()
        pw.__enter__.return_value.chromium.launch_persistent_context.return_value = Ctx()
        with mock.patch("playwright.sync_api.sync_playwright", lambda: pw):
            h = navegador._Hilo(False); h.start(); h.listo.wait(5)
            r = []
            for u in ("https://a.es/", "https://b.es/"):
                sal, emp = queue.Queue(), threading.Event(); h.cola.put((u, sal, 0, emp)); r.append(sal.get(timeout=5))
            h.cola.put((None, None, 0, None))
        self.assertIsInstance(r[0], Exception)
        self.assertEqual(r[1][0], 200)


if __name__ == "__main__":
    unittest.main()
