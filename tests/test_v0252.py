"""v0.25.2: arreglos de la segunda revisión de código."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento, web


class Arreglos(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def test_vuelta_de_stock_de_punta_a_punta(self):
        sid = seguimiento.guarda({"consulta": "marvel hulk", "objetivo": "29", "bajo_historico": "0"})
        x = {"titulo": "Marvel Hulk en castellano", "precio": 30.0, "url": "https://t.es/h", "preventa": False, "estado": ""}
        t = {"host": "t.es", "activa": True, "tipo": "tienda", "plantilla": "https://t.es/?q={q}"}
        for agotado, avisos in ((True, 0), (False, 1)):
            with mock.patch.object(motor.cfg, "carga", return_value=[t]), mock.patch.object(motor.cfg, "guarda"), \
                 mock.patch.object(motor, "_tienda", lambda *a, **k: ("t.es", [{**x, "agotado": agotado}], None)), \
                 mock.patch.object(motor, "ficha", return_value={"idioma": None, "agotado": None, "preventa": None}):
                r = seguimiento.revisa(sid, enviar=False)
            self.assertEqual(len(r["avisos"]), avisos)
        self.assertIn("vuelve a estar disponible", r["avisos"][0]["motivo"])

    def test_claves_no_vacias_ni_mezcladas(self):
        self.assertTrue(motor.clave_producto("Solo"))
        self.assertNotEqual(motor.clave_producto("Arkham Horror: juego de rol"), motor.clave_producto("Arkham Horror: El juego de cartas"))
        self.assertNotEqual(motor.tipo_de("Pack 2 jugadores"), "lote")

    def test_recalculo_con_choque_de_claves(self):
        with bd.conecta() as c:
            for k, t, p, ts in (("c:deck eternal", "Eternal Decks", 30, 1), ("c:vieja", "Eternal Decks: juego cooperativo", 28, 2)):
                c.execute("INSERT INTO objetivos(clave,titulo,precio,ts) VALUES(?,?,?,?)", (k, t, p, ts))
        motor.rellena_claves()
        with bd.conecta() as c:
            self.assertEqual([tuple(r) for r in c.execute("SELECT clave, precio FROM objetivos")], [("c:deck eternal", 28)])

    def test_pagina_vieja_no_reactiva_una_bloqueada(self):
        h = web.Handler.__new__(web.Handler)
        lista = [{"host": "a.es", "activa": True}, {"host": "b.es", "activa": False, "manual": True, "bloqueo": {"desde": 1}}]
        with mock.patch.object(web.cfg, "carga", return_value=lista), mock.patch.object(web.cfg, "guarda"):
            b = h._cambia_tiendas({"activas": ["a.es", "b.es"], "reactivar": "a.es"})[1]
            self.assertEqual((b["activa"], b["manual"], "bloqueo" in b), (False, True, True))
            b = h._cambia_tiendas({"editar": "b.es", "manual": False})[1]
            self.assertTrue(b["manual"])
            b = h._cambia_tiendas({"activas": ["a.es", "b.es"], "reactivar": "b.es"})[1]
            self.assertEqual((b["activa"], b["manual"], "bloqueo" in b), (True, False, False))


if __name__ == "__main__":
    unittest.main()
