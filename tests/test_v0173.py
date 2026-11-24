"""v0.17.3: una tienda que bloqueó tu conexión se vigila con una petición cada 6 h y se reactiva sola al volver."""
import os
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import programador, tiendas as cfg  # noqa: E402
from tests.test_v0114 import ConArchivos  # noqa: E402


class ReactivarlaATuMano(ConArchivos):
    def test_quita_la_marca_de_bloqueo(self):
        from buscatron import web
        cfg.guarda([{"host": "dm.es", "activa": False, "plantilla": None, "bloqueo": {"desde": 1}}])
        web.Handler._tiendas(web.Handler.__new__(web.Handler), {"activas": ["dm.es"], "reactivar": "dm.es"})
        t = next(x for x in cfg.carga() if x["host"] == "dm.es")
        self.assertTrue(t["activa"])
        self.assertNotIn("bloqueo", t)


if __name__ == "__main__":
    unittest.main()
