"""v0.25.4: cuarta revisión de código."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, ritmo, tiendas, web


class Arreglos(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(m, "RUTA", os.path.join(d, n)) for m, n in ((bd, "t.db"), (ajustes, "c.json"), (tiendas, "l.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def test_bloqueo_antiguo_vuelve_como_solo_enlace(self):
        h = web.Handler.__new__(web.Handler)
        tiendas.guarda([{"host": "dm.es", "activa": False, "manual": True, "bloqueo": {"desde": 1, "probado": 1}}])
        t = h._cambia_tiendas({"activas": ["dm.es"], "reactivar": "dm.es"})[0]
        self.assertEqual((t["activa"], t["manual"]), (True, True))

    def test_eleccion_durante_bloqueo_y_sin_cambio_de_web(self):
        h = web.Handler.__new__(web.Handler)
        tiendas.guarda([{"host": "dm.es", "activa": False, "manual": True, "bloqueo": {"desde": 1, "manual": True}}])
        self.assertTrue(h._cambia_tiendas({"editar": "dm.es", "manual": False})[0]["manual"])
        self.assertRaises(ValueError, h._cambia_tiendas, {"editar": "dm.es", "url": "https://otra.es/?s={q}"})
        self.assertFalse(h._cambia_tiendas({"activas": ["dm.es"], "reactivar": "dm.es"})[0]["manual"])

    def test_limpieza_prefiere_con_stock(self):
        viejo = time.time() - 200 * 86400
        with bd.conecta() as c:
            for p, a in ((25, 1), (30, 0)):
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado) VALUES(?,?,?,?,?,?,?)", (viejo, "x", "t", "X", "u", p, a))
        bd.limpia()
        with bd.conecta() as c:
            self.assertEqual([tuple(r) for r in c.execute("SELECT precio, agotado FROM precios")], [(30, 0)])

    def test_bloqueadas_al_dia_sin_releer(self):
        tiendas.guarda([{"host": "a.es", "activa": True}])
        ritmo._comprueba("a.es")
        time.sleep(0.02)
        tiendas.guarda([{"host": "a.es", "activa": False, "bloqueo": {"desde": 1}}])
        self.assertRaises(ritmo.Prohibida, ritmo._comprueba, "a.es")


if __name__ == "__main__":
    unittest.main()
