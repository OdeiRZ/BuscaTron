"""v0.24.0: compra conjunta, rebajas a la vista y revisión de salud."""
import datetime
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, historico, programador, seguimiento


class Rebajas(unittest.TestCase):
    def test_proxima(self):
        self.assertEqual(historico.proxima_campana(datetime.date(2027, 1, 3))["dias"], 4)
        self.assertTrue(historico.proxima_campana(datetime.date(2026, 11, 25))["ya"])
        self.assertIsNone(historico.proxima_campana(datetime.date(2026, 3, 1)))


class Compra(unittest.TestCase):
    def test_junta_si_compensa_por_el_envio(self):
        ml = [{"grupo": "a", "por_tienda": {"x.es": {"precio": 30, "url": "1", "titulo": "A"}, "y.es": {"precio": 28, "url": "2", "titulo": "A"}}},
              {"grupo": "b", "por_tienda": {"x.es": {"precio": 30, "url": "3", "titulo": "B"}}}]
        tiendas = [{"host": "x.es", "envio": 5, "envio_gratis": 50}, {"host": "y.es", "envio": 5, "envio_gratis": 50}]
        with mock.patch.object(seguimiento, "mi_lista", return_value=ml), mock.patch.object(seguimiento.motor.cfg, "carga", return_value=tiendas):
            r = seguimiento.compra_conjunta(["a", "b"])
        self.assertEqual((r[0]["total"], [o["tienda"] for o in r[0]["pedidos"]]), (60.0, ["x.es"]))   # todo en x: envío gratis


if __name__ == "__main__":
    unittest.main()
