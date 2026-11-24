"""Se carga la primera: ninguna prueba toca los archivos reales (tiendas, ajustes, base de datos)."""
import os
import tempfile
import unittest

from buscatron import ajustes, bd, tiendas

_d = tempfile.mkdtemp()
tiendas.RUTA, ajustes.RUTA, bd.RUTA = (os.path.join(_d, n) for n in ("tiendas.json", "config.json", "buscatron.db"))


class Aislamiento(unittest.TestCase):
    def test_rutas_temporales(self):
        self.assertTrue(all(r.startswith(tempfile.gettempdir()) for r in (tiendas.RUTA, ajustes.RUTA, bd.RUTA)))
