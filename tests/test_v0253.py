"""v0.25.3: tercera revisión de código."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, extract, fetch, motor, navegador, ritmo, seguimiento, tiendas, web


class Arreglos(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(m, "RUTA", os.path.join(d, n)) for m, n in ((bd, "t.db"), (ajustes, "c.json"), (tiendas, "l.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def test_ninguna_peticion_a_una_bloqueada_por_ninguna_via(self):
        tiendas.guarda([{"host": "www.dm.es", "activa": True, "manual": False, "bloqueo": {"desde": 1}}])     # aun con las marcas mal
        with mock.patch.object(fetch.urllib.request, "urlopen", side_effect=AssertionError("petición")), \
                mock.patch.object(navegador, "_Hilo", side_effect=AssertionError("petición")):
            for via in (fetch.get, navegador.get):
                for u in ("https://www.dm.es/x", "https://dm.es/"):
                    self.assertRaises(ritmo.Prohibida, via, u)

    def test_bloqueo_mientras_espera_turno(self):
        tiendas.guarda([{"host": "dm.es", "activa": True}])
        ritmo._turno["dm.es"] = time.monotonic() + 5

        def duerme(_s):
            motor.bloquea("dm.es")
        with mock.patch.object(ritmo.time, "sleep", duerme):
            self.assertRaises(ritmo.Prohibida, ritmo.espera, "https://dm.es/")

    def test_anadirla_otra_vez_no_la_desbloquea_y_reactivarla_la_deja_como_estaba(self):
        h = web.Handler.__new__(web.Handler)
        tiendas.guarda([{"host": "dm.es", "activa": True, "manual": True}])
        motor.bloquea("dm.es")
        t = h._cambia_tiendas({"anadir": "https://dm.es/?s={q}"})[0]
        self.assertTrue(t["manual"] and t["bloqueo"])
        t = h._cambia_tiendas({"activas": ["dm.es"], "reactivar": "dm.es"})[0]
        self.assertEqual((t["activa"], t["manual"], "bloqueo" in t), (True, True, False))

    def test_envio(self):
        self.assertEqual(extract.detecta_envio("<p>Gastos de envío gratis desde 39 €</p>"), {"gratis_desde": 39.0, "coste": None})
        tiendas.guarda([{"host": "a.es", "activa": True}])
        for d in ({"coste": 4.9, "gratis_desde": 50.0}, {"coste": None, "gratis_desde": 60.0}):
            motor._envio_visto["a.es"] = d
            motor.guarda_envios_vistos()
        self.assertEqual(tiendas.carga()[0]["envio_auto"], {"coste": 4.9, "gratis_desde": 60.0})

    def test_mi_lista_con_objetivo_de_campana_ficha_y_revision_fallida(self):
        sid = seguimiento.guarda({"consulta": "agentes de shield"})
        with bd.conecta() as c:
            c.execute("INSERT INTO objetivos(clave,titulo,precio,ts) VALUES('f:shield','Shield',39,1)")
            for u, p in (("https://a.es/1", 30), ("https://b.es/1", 35)):
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,preventa,seg_id) VALUES(?,?,?,?,?,?,0,0,?)",
                          (1000, "agentes de shield", u[8:12], "Agentes de Shield", u, p, sid))
            c.execute("UPDATE seguimientos SET ultima=1000, estado='ok' WHERE id=?", (sid,))
            c.execute("INSERT INTO fichas(url,agotado,ts) VALUES('https://a.es/1',1,?)", (time.time(),))
        p = seguimiento.mi_lista()[0]
        self.assertEqual((p["objetivo"], p["objetivo_clave"], p["mejor"]["tienda"]), (39, "f:shield", "b.es"))
        with bd.conecta() as c:
            c.execute("UPDATE seguimientos SET ultima=9000, estado='la revisión falló: x' WHERE id=?", (sid,))
        self.assertEqual(len(seguimiento.mi_lista()), 1)

    def test_lotes_y_fundas(self):
        self.assertNotEqual(motor.tipo_de("Marvel Champions Scenario Pack 2"), "lote")
        self.assertEqual(motor.tipo_de("Pack 3 expansiones"), "lote")
        self.assertTrue(motor.grupo_de("Fundas Civil War", ["civil war"]).startswith("c:"))


if __name__ == "__main__":
    unittest.main()
