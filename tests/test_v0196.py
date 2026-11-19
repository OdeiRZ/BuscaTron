"""v0.19.6: lo pegado se apunta en el historial una vez (al pegarlo) y la ficha de una tienda «solo enlace» no se consulta."""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, importar, motor


class HistorialDePegados(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.db = os.path.join(d, "t.db")
        t = {"host": "www.dynos.es", "nombre": "Dynos", "activa": True, "plantilla": None, "manual": True, "tipo": "tienda"}
        self.parches = [mock.patch.object(bd, "RUTA", self.db), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),
                        mock.patch.object(motor.cfg, "carga", return_value=[t]),
                        mock.patch.object(motor, "_tienda_consulta", side_effect=AssertionError("no debe consultarse"))]
        for p in self.parches:
            p.start()

    def tearDown(self):
        for p in reversed(self.parches):
            p.stop()

    def filas(self):
        with sqlite3.connect(self.db) as c:
            return c.execute("SELECT COUNT(*) FROM precios WHERE tienda='www.dynos.es'").fetchone()[0]

    def test_una_fila_por_pegado(self):
        importar.guarda("www.dynos.es", "marvel champions", [{"titulo": "Marvel Champions Hulk", "precio": 13.32}], "https://www.dynos.es/")
        self.assertEqual(self.filas(), 1)
        for _ in range(3):                     # mostrarlo en búsquedas no lo vuelve a apuntar
            res, _ = motor.buscar("marvel champions", hosts=["www.dynos.es"], castellano=False)
            self.assertEqual(len(res), 1)
        self.assertEqual(self.filas(), 1)


class FichaDeTiendaManual(unittest.TestCase):
    def test_no_se_consulta(self):
        lista = [{"host": "bixoto.com", "manual": True, "js": False}]
        with mock.patch.object(motor.fetch, "get", side_effect=AssertionError("no debe consultarse")):
            f = motor.ficha({"url": "https://bixoto.com/es/producto-x", "tienda": "bixoto.com"}, lista)
        self.assertEqual(f, {"idioma": None, "agotado": None, "preventa": None})


if __name__ == "__main__":
    unittest.main()
