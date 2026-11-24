"""v0.25.1: arreglos de la revisión de código de v0.21-v0.25."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento


class Arreglos(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json"))]
        for p in self.p:
            p.start()

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()

    def test_bloqueada_ninguna_peticion_pero_cuenta_lo_pegado(self):
        t = {"host": "b.es", "activa": False, "manual": True, "bloqueo": {"desde": 1}, "plantilla": None, "tipo": "tienda"}
        pegado = {"titulo": "Marvel Hulk", "precio": 13.0, "url": "https://b.es/?btitem=x", "agotado": False, "preventa": False,
                  "estado": "", "importado": time.time()}
        falla = AssertionError("ninguna petición")
        with mock.patch.object(motor.cfg, "carga", return_value=[t]), mock.patch.object(motor.importar, "vigentes", return_value=[pegado]), \
             mock.patch.object(motor.fetch, "get", side_effect=falla), mock.patch.object(motor.navegador, "get", side_effect=falla):
            for hosts in (None, ["b.es"]):
                res, _ = motor.buscar("marvel", hosts=hosts, castellano=False)
                self.assertEqual([x["precio"] for x in res], [13.0])

    def test_juego_en_dos_vigiladas(self):
        o = {"x.es": {"precio": 30, "url": "1", "titulo": "A"}}
        ml = [{"grupo": "a", "por_tienda": o}, {"grupo": "a", "por_tienda": o}, {"grupo": "b", "por_tienda": o}]
        with mock.patch.object(seguimiento, "mi_lista", return_value=ml), \
             mock.patch.object(motor.cfg, "carga", return_value=[{"host": "x.es", "envio": 0}]):
            self.assertEqual(seguimiento.compra_conjunta(["a", "b"])[0]["total"], 60)

    def test_objetivo_bajado_con_envio(self):
        a = {"precio": 34, "motivo": "cuesta 38,95 € con envío, por debajo de tu objetivo de 40,00 €"}
        self.assertTrue(seguimiento._fuera_de_objetivo({"objetivo": 37}, a))
        self.assertFalse(seguimiento._fuera_de_objetivo({"objetivo": 39}, a))

    def test_la_limpieza_conserva_40_dias_de_estado(self):
        ahora = time.time()
        with bd.conecta() as c:
            for i in range(80):
                c.execute("INSERT INTO estado_tiendas VALUES('z.es',?,'x',1,'')", (ahora - i * 86400 / 2,))
        bd.limpia(ahora=ahora)
        with bd.conecta() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM estado_tiendas").fetchone()[0], 80)


if __name__ == "__main__":
    unittest.main()
