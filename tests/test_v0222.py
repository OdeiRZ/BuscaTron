"""v0.22.2: tiendas que no quieres en una vigilada."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento


class SinTiendas(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json"))]
        for p in self.p:
            p.start()
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "opciones": {"sin_tiendas": ["b.es"]}})
        self.seg = next(s for s in seguimiento.lista() if s["id"] == self.sid)

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def test_se_guarda_y_filtra(self):
        self.assertEqual(self.seg["opciones"]["sin_tiendas"], ["b.es"])
        self.assertFalse(seguimiento.cumple(self.seg, "Marvel Hulk", 30, "b.es"))
        self.assertTrue(seguimiento.cumple(self.seg, "Marvel Hulk", 30, "a.es"))

    def test_la_revision_no_la_consulta(self):
        pedidas = {}
        def falsa(consulta, incluir, excluir, sin_ag, hosts, *a, **k):
            pedidas["hosts"] = hosts
            return [], {}
        lista = [{"host": "a.es", "activa": True}, {"host": "b.es", "activa": True}, {"host": "c.es", "activa": False}]
        with mock.patch.object(motor, "buscar", falsa), mock.patch.object(motor.cfg, "carga", return_value=lista):
            seguimiento.revisa(self.sid, enviar=False)
        self.assertEqual(pedidas["hosts"], ["a.es"])


if __name__ == "__main__":
    unittest.main()
