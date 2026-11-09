"""v0.17.3: una tienda que bloqueó tu conexión se vigila con una petición cada 6 h y se reactiva sola al volver."""
import os
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import programador, tiendas as cfg  # noqa: E402
from tests.test_v0114 import ConArchivos  # noqa: E402


class TiendaQueTeBloqueo(ConArchivos):
    def setUp(self):
        super().setUp()
        cfg.guarda([{"host": "a.es", "activa": True, "plantilla": None},
                    {"host": "dm.es", "activa": False, "plantilla": None, "nombre": "DM", "bloqueo": {"desde": 1, "probado": 0}}])

    def _vuelta(self, respuesta):
        pedidas, avisos = [], []
        def get(url, timeout=None):
            pedidas.append(url)
            if isinstance(respuesta, Exception):
                raise respuesta
            return respuesta, ""
        with mock.patch.object(programador.fetch, "get", get), \
                mock.patch.object(programador.notifica, "envia", lambda *a: avisos.append(a)):
            programador.bloqueadas()
        return pedidas, avisos, {t["host"]: t for t in cfg.carga()}

    def test_si_vuelve_se_reactiva_y_avisa(self):
        pedidas, avisos, l = self._vuelta(200)
        self.assertEqual(pedidas, ["https://dm.es/"])                 # una sola petición, a la portada
        self.assertTrue(l["dm.es"]["activa"])
        self.assertNotIn("bloqueo", l["dm.es"])
        self.assertIn("vuelve a responder", avisos[0][2])

    def test_si_sigue_sin_responder_no_se_toca_y_espera_6_h(self):
        pedidas, avisos, l = self._vuelta(TimeoutError("timed out"))
        self.assertEqual((len(pedidas), avisos, l["dm.es"]["activa"]), (1, [], False))
        self.assertGreater(l["dm.es"]["bloqueo"]["probado"], time.time() - 60)
        pedidas, _, _ = self._vuelta(200)                             # recién probada: no se vuelve a llamar
        self.assertEqual(pedidas, [])

    def test_las_demas_tiendas_ni_se_miran(self):
        pedidas, _, l = self._vuelta(TimeoutError("x"))
        self.assertTrue(l["a.es"]["activa"])
        self.assertNotIn("https://a.es/", pedidas)


class ReactivarlaATuMano(ConArchivos):
    def test_quita_la_marca_de_bloqueo(self):
        from buscatron import web
        cfg.guarda([{"host": "dm.es", "activa": False, "plantilla": None, "bloqueo": {"desde": 1}}])
        web.Handler._tiendas(web.Handler.__new__(web.Handler), {"activas": ["dm.es"]})
        (t,) = cfg.carga()
        self.assertTrue(t["activa"])
        self.assertNotIn("bloqueo", t)


if __name__ == "__main__":
    unittest.main()
