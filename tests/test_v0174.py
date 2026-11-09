"""v0.17.4: editar una vigilada en pausa la deja en pausa (antes se reactivaba sola al guardar el formulario)."""
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, seguimiento  # noqa: E402

PAGINA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "buscatron", "pagina.html")


class EditarRespetaPausa(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(bd, "RUTA", os.path.join(self.tmp, "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def estado(self, i):
        return next(s["activo"] for s in seguimiento.lista() if s["id"] == i)

    def test_editar_sin_activo_conserva_la_pausa(self):
        i = seguimiento.guarda({"consulta": "marvel champions", "activo": False})
        seguimiento.guarda({"id": i, "consulta": "marvel champions", "pmax": "50"})
        self.assertEqual(self.estado(i), 0)

    def test_editar_sin_activo_conserva_activa(self):
        i = seguimiento.guarda({"consulta": "dune"})
        seguimiento.guarda({"id": i, "consulta": "dune imperium"})
        self.assertEqual(self.estado(i), 1)

    def test_pausar_y_reanudar_siguen_funcionando(self):
        i = seguimiento.guarda({"consulta": "vantage"})
        seguimiento.guarda({"id": i, "consulta": "vantage", "activo": False})
        self.assertEqual(self.estado(i), 0)
        seguimiento.guarda({"id": i, "consulta": "vantage", "activo": True})
        self.assertEqual(self.estado(i), 1)

    def test_nueva_sin_activo_empieza_activa(self):
        self.assertEqual(self.estado(seguimiento.guarda({"consulta": "mage knight"})), 1)

    def test_formulario_envia_el_estado_previo(self):
        html = open(PAGINA, encoding="utf-8").read()
        envio = re.search(r"\$\('sf'\)\.onsubmit=.*?api\('seguimientos',\{accion:'guardar',[^}]*", html, re.S).group(0)
        self.assertIn("activo:previa?!!previa.activo:true", envio)


if __name__ == "__main__":
    unittest.main()
