"""v0.25.15: revisión max."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, navegador, tiendas


class Arreglos(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(m, "RUTA", os.path.join(d, n)) for m, n in ((bd, "t.db"), (ajustes, "c.json"), (tiendas, "l.json"))]
        for p in self.p:
            p.start()
        motor._alias_leido[0] = None
        motor._caidas.clear()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()
        motor._alias_leido[0] = None
        motor._caidas.clear()

    def test_captcha_espera_como_una_caida(self):
        t = {"host": "a.es", "activa": True, "plantilla": "https://a.es/?q={q}"}
        with mock.patch.object(motor, "_tienda_viva", side_effect=navegador.Desafio("captcha")) as viva:
            self.assertEqual(motor._tienda_base(t, "x")[2], motor.DESAFIO)
            r = motor._tienda_base(t, "x")                       # enseguida: no se le vuelve a pedir
        self.assertEqual(viva.call_count, 1)
        self.assertTrue(r[2].startswith("no responde"))

    def test_historial_y_objetivo_de_una_fusion_en_cadena(self):
        with bd.conecta() as c:
            c.executemany("INSERT INTO alias_grupos(de, a, ts) VALUES(?,?,1)", [("c:a b c d", "c:a b c"), ("c:a b c", "c:a b")])
            for clave, p in (("a b c d", 10), ("a b c", 20), ("a b", 30)):
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,preventa,clave) VALUES(?,?,?,?,?,?,0,0,?)",
                          (time.time(), "x", "t" + clave, clave, "u" + clave, p, clave))
            c.execute("INSERT INTO objetivos(clave,titulo,precio,ts) VALUES('c:a b c d','x',40,1)")
        motor._alias_leido[0] = None
        h = motor.historial_producto("c:a b")
        self.assertEqual((h["tienda"], min(p["precio"] for p in h["puntos"])), ("3 tiendas", 10))
        self.assertEqual(motor.clave_objetivo({"grupo": "c:a b c", "titulo": "a b c"}, motor.objetivos()), "c:a b c d")


if __name__ == "__main__":
    unittest.main()
