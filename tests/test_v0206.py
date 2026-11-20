"""v0.20.6: la marca de «rechazó una página siguiente» es de cada consulta y no se queda puesta."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor


class RechazoEnPaginaSiguiente(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def test_no_se_olvida_en_esa_consulta_y_si_en_la_siguiente(self):
        def con_rechazo(*a):
            motor._hilo_rechazo.hubo = True
            return "t.es", [{"titulo": "x"}], None
        with mock.patch.object(motor, "_tienda_consulta", side_effect=con_rechazo), mock.patch.object(motor, "limpia_caida") as l:
            motor._tienda_viva({"host": "t.es"}, "x", None, 1, False)
        l.assert_not_called()
        with mock.patch.object(motor, "_tienda_consulta", return_value=("t.es", [{"titulo": "x"}], None)), \
             mock.patch.object(motor, "limpia_caida") as l:
            motor._tienda_viva({"host": "t.es"}, "x", None, 1, False)
        l.assert_called_once()                 # la siguiente consulta sana sí limpia: la marca no se quedó puesta


if __name__ == "__main__":
    unittest.main()
