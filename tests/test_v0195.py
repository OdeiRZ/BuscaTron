"""v0.19.5: lo pegado crea al momento los avisos de las vigiladas activas, sin consultar ninguna tienda."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento


class AvisosDePegados(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.t = {"host": "www.dynos.es", "nombre": "Dynos", "activa": True, "plantilla": None, "manual": True, "tipo": "tienda"}
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),
                        mock.patch.object(motor.cfg, "carga", return_value=[self.t]),
                        mock.patch.object(motor, "_tienda_consulta", side_effect=AssertionError("no debe consultarse")),
                        mock.patch.object(motor, "ficha", side_effect=AssertionError("no debe leer fichas")),
                        mock.patch.object(seguimiento.notifica, "envia", return_value={})]
        for p in self.parches:
            p.start()
        pegados = [{"titulo": "Marvel Champions: Los Más Buscados de la Galaxia", "precio": 35.28, "url": "https://www.dynos.es/?btitem=a",
                    "agotado": False, "preventa": False, "estado": "", "importado": time.time()},
                   {"titulo": "Marvel Champions: Hulk", "precio": 45.0, "url": "https://www.dynos.es/?btitem=b",
                    "agotado": False, "preventa": False, "estado": "", "importado": time.time()}]
        self.p2 = mock.patch.object(motor.importar, "vigentes", side_effect=lambda h, q, ahora=None: [dict(x) for x in pegados])
        self.p2.start()
        seguimiento.guarda({"nombre": "MC", "consulta": "marvel champions", "objetivo": 39, "canales": "app,telegram", "castellano": False})

    def tearDown(self):
        self.p2.stop()
        for p in reversed(self.parches):
            p.stop()

    def test_crea_el_aviso_y_no_lo_repite(self):
        self.assertEqual(seguimiento.avisa_pegados("www.dynos.es"), 1)
        a = seguimiento.avisos()
        self.assertEqual([(x["precio"], x["tienda"]) for x in a], [(35.28, "www.dynos.es")])
        self.assertIn("pegado a mano", a[0]["motivo"])
        self.assertEqual(seguimiento.avisa_pegados("www.dynos.es"), 0)       # mismo precio: no se repite


if __name__ == "__main__":
    unittest.main()
