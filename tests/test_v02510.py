"""v0.25.10: las tiendas que nunca se pueden leer se paran solas."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, tiendas, web


class Inservibles(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(m, "RUTA", os.path.join(d, n)) for m, n in ((bd, "t.db"), (ajustes, "c.json"), (tiendas, "l.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def _vuelta(self, informe):
        return motor.para_inservibles(informe, {t["host"]: t for t in tiendas.carga()})

    def test_para_tras_tres_y_se_reactiva(self):
        tiendas.guarda([{"host": "a.es", "activa": True, "plantilla": None}, {"host": "b.es", "activa": True, "plantilla": "https://b.es/?q={q}"},
                        {"host": "c.es", "activa": True, "plantilla": "https://c.es/?q={q}"}])
        inf = {"a.es": {"brutos": 0, "encontrados": 0, "error": motor.SIN_COINCIDENCIAS},
               "b.es": {"brutos": 0, "encontrados": 0, "error": motor.DESAFIO},
               "c.es": {"brutos": 0, "encontrados": 0, "error": motor.SIN_COINCIDENCIAS}}
        self.assertEqual(self._vuelta(inf), [])
        self._vuelta(inf)
        self.assertEqual(sorted(self._vuelta(inf)), ["a.es", "b.es"])
        t = {x["host"]: x for x in tiendas.carga()}
        self.assertEqual((t["a.es"]["activa"], t["a.es"]["parada"]["motivo"]), (False, "no encuentro su buscador"))
        self.assertTrue(t["c.es"]["activa"])                       # responde sin el juego: no es un fallo
        r = web.Handler.__new__(web.Handler)._cambia_tiendas({"activas": ["a.es", "c.es"], "reactivar": "a.es"})
        self.assertNotIn("parada", r[0])

    def test_un_acierto_reinicia_la_cuenta(self):
        tiendas.guarda([{"host": "a.es", "activa": True, "plantilla": None}])
        mala = {"a.es": {"brutos": 0, "encontrados": 0, "error": motor.SIN_COINCIDENCIAS}}
        self._vuelta(mala), self._vuelta(mala)
        self._vuelta({"a.es": {"brutos": 5, "encontrados": 2, "error": None}})
        self._vuelta(mala), self._vuelta(mala)
        self.assertTrue(tiendas.carga()[0]["activa"])

    def test_caida_no_cuenta(self):
        tiendas.guarda([{"host": "a.es", "activa": True, "plantilla": None}])
        for _ in range(4):
            self._vuelta({"a.es": {"brutos": 0, "encontrados": 0, "error": "no se pudo conectar (timed out)"}})
        self.assertTrue(tiendas.carga()[0]["activa"])


if __name__ == "__main__":
    unittest.main()
