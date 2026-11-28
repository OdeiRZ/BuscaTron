"""v0.25.13: revisión xhigh."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, tiendas


class Paradas(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(m, "RUTA", os.path.join(d, n)) for m, n in ((bd, "t.db"), (ajustes, "c.json"), (tiendas, "l.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def _tres_dias(self, err, host="a.es"):
        tiendas.guarda([{"host": host, "activa": True, "plantilla": None}])
        for _ in range(3):
            motor.para_inservibles({host: {"brutos": 0, "encontrados": 0, "error": err}}, {host: tiendas.carga()[0]})
            l = tiendas.carga()
            if "fallos_desde" in l[0]:
                l[0]["fallos_desde"] -= 13 * 3600
            tiendas.guarda(l)
        return tiendas.carga()[0]

    def test_sin_buscador_404_se_para(self):
        t = self._tres_dias("no encuentra la página de búsqueda (error 404)")
        self.assertTrue(t["activa"] and t["no_lee"])      # marcada, pero activa: la desactivas tú

    def test_si_alguna_vez_dio_resultados_no_se_para(self):
        with bd.conecta() as c:
            c.execute("INSERT INTO estado_tiendas(host, ts, consulta, encontrados, error) VALUES('a.es', ?, 'x', 3, '')", (time.time() - 86400,))
        self.assertNotIn("no_lee", self._tres_dias(motor.SIN_COINCIDENCIAS))

    def test_caida_no_cuenta_ni_reinicia(self):
        self.assertNotIn("no_lee", self._tres_dias("no se pudo conectar (timed out)"))


if __name__ == "__main__":
    unittest.main()
