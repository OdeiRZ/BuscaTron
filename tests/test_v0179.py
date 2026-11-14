"""v0.17.9: una ficha que falla conserva el idioma ya leído, una tienda bloqueada no se consulta aunque se pida, vuelta
suave al reactivarla a mano, avisos quitados antiguos fuera y /revisar dice lo que no repitió."""
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, motor, telegram_bot, web  # noqa: E402


class ConBD(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()


class FichaFallidaConservaIdioma(ConBD):
    def test_el_idioma_leido_no_se_pierde(self):
        url = "https://a.es/p"
        with bd.conecta() as c:
            c.execute("INSERT INTO fichas(url, idioma, agotado, preventa, ts) VALUES(?,?,?,?,?)", (url, "otro", 0, 0, time.time() - 7 * 3600))
        with mock.patch.object(motor.fetch, "get", lambda u, timeout=20: (403, "")):
            self.assertEqual(motor.ficha({"url": url, "tienda": "a.es"}, [])["agotado"], None)
        self.assertEqual(motor.idiomas_de_fichas([url]), {url: "otro"})
        self.assertEqual(motor.stock_de_fichas([url]), {})             # el stock viejo ya no cuenta


class BloqueadaNoSeConsulta(ConBD):
    def test_ni_aunque_la_pida_la_pagina(self):
        tiendas = [{"host": "a.es", "activa": True, "plantilla": "https://a.es/?q={q}", "tipo": "tienda"},
                   {"host": "b.es", "activa": False, "plantilla": "https://b.es/?q={q}", "tipo": "tienda", "bloqueo": {"desde": 1}}]
        vistas = []
        with mock.patch.object(motor.cfg, "carga", lambda: tiendas), mock.patch.object(motor.cfg, "aplica_descubiertas", lambda c: None), \
                mock.patch.object(motor, "_tienda", lambda t, q, nav=None, pag=1: vistas.append(t["host"]) or (t["host"], [], None)):
            motor.buscar("algo", hosts=["a.es", "b.es"])
        self.assertEqual(vistas, ["a.es"])


class ReactivarAMano(unittest.TestCase):
    def test_vuelve_con_calma(self):
        lista = [{"host": "b.es", "activa": False, "bloqueo": {"desde": 1}}, {"host": "a.es", "activa": True}]
        with mock.patch.object(web.cfg, "carga", lambda: lista), mock.patch.object(web.cfg, "guarda", lambda l: None):
            r = web.Handler._cambia_tiendas(None, {"activas": ["a.es", "b.es"]})
        self.assertNotIn("bloqueo", r[0])
        self.assertGreater(r[0]["suave_hasta"], time.time() + 2 * 86400)
        self.assertNotIn("suave_hasta", r[1])


class LimpiezaDeAvisos(ConBD):
    def test_los_quitados_antiguos_se_borran(self):
        ahora = time.time()
        with bd.conecta() as c:
            c.executemany("INSERT INTO avisos(ts, seg_id, titulo, tienda, url, precio, motivo, oculto) VALUES(?,1,'t','a','u',1,'m',?)",
                          [(ahora - 90 * 86400, 1), (ahora - 90 * 86400, 0), (ahora - 86400, 1)])
        self.assertEqual(bd.limpia(ahora=ahora)["avisos"], 1)


class RevisarDesdeTelegram(unittest.TestCase):
    def test_dice_la_que_no_repitio(self):
        dicho = []
        segs = [{"id": 1, "nombre": "Uno", "activo": 1}, {"id": 2, "nombre": "Dos", "activo": 1}]
        with mock.patch.object(telegram_bot.seguimiento, "lista", lambda: segs), mock.patch.object(telegram_bot, "responde", dicho.append), \
                mock.patch.object(telegram_bot.seguimiento, "revisa", lambda sid: {"ocupado": True} if sid == 2 else {"resultados": 0}):
            telegram_bot.revisar()
        self.assertIn("Dos", dicho[-1])
        self.assertNotIn("Uno", dicho[-1])


if __name__ == "__main__":
    unittest.main()
