"""v0.22.1: las revisiones se saltan las tiendas que nunca tienen ese juego (y vuelven a mirar cada semana)."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor


class TiendasSin(unittest.TestCase):
    def test_salta_y_vuelve_a_mirar(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            ahora = time.time()
            with bd.conecta() as c:
                for i in range(4):
                    c.execute("INSERT INTO estado_tiendas VALUES(?,?,?,?,?)", ("a.es", ahora - 86400 * (i + 1), "x", 0, motor.SIN_COINCIDENCIAS))
                    c.execute("INSERT INTO estado_tiendas VALUES(?,?,?,?,?)", ("b.es", ahora - 86400 * (i + 1), "x", 0, "no responde"))
                c.execute("INSERT INTO estado_tiendas VALUES(?,?,?,?,?)", ("c.es", ahora - 86400 * 9, "x", 2, ""))
                for i in range(4):
                    c.execute("INSERT INTO estado_tiendas VALUES(?,?,?,?,?)", ("c.es", ahora - 86400 * (i + 1), "x", 0, motor.SIN_COINCIDENCIAS))
            self.assertEqual(motor.tiendas_sin("x", ahora), {"a.es"})          # b falla (no es «sin el juego»), c lo tuvo
            self.assertEqual(motor.tiendas_sin("x", ahora + 7 * 86400), set())  # a la semana, se vuelve a mirar
            self.assertEqual(motor.tiendas_sin("otra", ahora), set())


if __name__ == "__main__":
    unittest.main()
