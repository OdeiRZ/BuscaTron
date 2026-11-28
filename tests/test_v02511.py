"""v0.25.11: las variantes de nombre del mismo juego se juntan; los productos distintos, no."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import bd, motor


class Fusion(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()
        motor._alias_leido[0] = None

    def tearDown(self):
        self.p.stop()
        motor._alias_leido[0] = None

    def g(self, titulos, q):
        return [x["grupo"] for x in motor.grupos(titulos, q)]

    def test_coletilla_de_tienda(self):
        r = self.g(["La Tiranía de Cráneo Rojo (Expansión Marvel Champions)", "Marvel Champions La Tiranía de Cráneo Rojo | Cinco escenarios"],
                   "La Tiranía de Cráneo Rojo")
        self.assertEqual(len(set(r)), 1)

    def test_no_junta_productos_distintos(self):
        casos = [(["Marvel Champions Black Panther", "Marvel Champions Black Panther Shuri"], "marvel champions"),
                 (["Marvel Champions Héroes Reunidos", "Marvel Champions Héroes Reunidos 2"], "marvel champions"),
                 (["Marvel Champions", "Marvel Champions: La Tiranía de Cráneo Rojo"], "marvel champions"),
                 (["Marvel Champions La Tiranía de Cráneo Rojo", "Folded Space inserto Marvel Champions La Tiranía de Cráneo Rojo"], "tirania craneo rojo"),
                 (["Too Many Bones", "Too Many Bones Undertow"], "too many bones")]
        for t, q in casos:
            self.assertEqual(len(set(self.g(t, q))), 2, t)


if __name__ == "__main__":
    unittest.main()
