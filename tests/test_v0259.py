"""v0.25.9: sin precio de aviso, se avisa al precio máximo."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, seguimiento, tiendas


class AvisoPorMaximo(unittest.TestCase):
    def test_sin_aviso_usa_el_maximo(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")), \
                mock.patch.object(tiendas, "RUTA", os.path.join(d, "l.json")):
            a = seguimiento.guarda({"consulta": "x", "pmax": "39"})
            b = seguimiento.guarda({"consulta": "y", "pmax": "39", "objetivo": "35"})
            c = seguimiento.guarda({"consulta": "z"})
            obj = {s["id"]: s["objetivo"] for s in seguimiento.lista()}
        self.assertEqual((obj[a], obj[b], obj[c]), (39, 35, None))


if __name__ == "__main__":
    unittest.main()
