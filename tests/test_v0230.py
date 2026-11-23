"""v0.23.0: precio raro, lotes, copia de seguridad."""
import os
import sqlite3
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, programador, seguimiento


class Lotes(unittest.TestCase):
    def test_lote_no_es_el_juego_suelto(self):
        self.assertEqual(motor.tipo_de("Pack 3 expansiones Marvel Champions"), "lote")
        self.assertEqual(motor.tipo_de("Marvel Champions: Pack de héroe Hulk"), "expansion")
        self.assertNotEqual(motor.clave_producto("Lote Marvel Champions Civil War"), motor.clave_producto("Marvel Champions: Civil War"))


class PrecioRaro(unittest.TestCase):
    def test_marca_el_precio_muy_bajo(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            sid = seguimiento.guarda({"consulta": "x", "objetivo": "40", "opciones": {"idioma": "todos"}})
            with bd.conecta() as c:
                seg = dict(c.execute("SELECT * FROM seguimientos WHERE id=?", (sid,)).fetchone())
                base = {"grupo": "c:x", "agotado": False, "preventa": False, "titulo": "X"}
                res = [{**base, "tienda": f"t{i}.es", "url": f"u{i}", "precio": p} for i, p in enumerate((19.75, 36, 38, 39))]
                n = seguimiento._registra_avisos(c, seg, seguimiento.opciones_de(seg), "todos", res, time.time())
        motivos = {x["url"]: x["motivo"] for x in n}
        self.assertIn("⚠️", motivos["u0"])
        self.assertNotIn("⚠️", motivos["u1"])


class Copia(unittest.TestCase):
    def test_copia_y_guarda_siete(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(programador.cfg, "RAIZ", d):
            with bd.conecta() as c:
                c.execute("INSERT INTO ignorados(clave,titulo,ts) VALUES('a','b',1)")
            carpeta = os.path.join(d, "copias")
            os.makedirs(carpeta)
            for i in range(9):
                open(os.path.join(carpeta, f"buscatron-2026010{i}.db"), "w").close()
            destino = programador.copia_de_seguridad()
            self.assertEqual(sqlite3.connect(destino).execute("SELECT COUNT(*) FROM ignorados").fetchone()[0], 1)
            self.assertEqual(len(os.listdir(carpeta)), programador.COPIAS)


if __name__ == "__main__":
    unittest.main()
