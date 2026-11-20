"""v0.20.5: figuras de colección fuera, y avisos que dejan de cumplir el objetivo al bajarlo."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento


class Figuras(unittest.TestCase):
    def test_figura_no_es_juego(self):
        self.assertTrue(motor.es_no_juego("MARVEL LEGENDS FIGURA 15CM SURTIDO F01685L0 - CIVIL WARRIOR CONTEST OF CHAMPIONS"))
        self.assertFalse(motor.es_no_juego("Juego con 30 figuras de plástico"))


class ObjetivoBajado(unittest.TestCase):
    def test_al_bajar_el_objetivo_sobran_los_de_encima(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            sid = seguimiento.guarda({"consulta": "marvel champions", "objetivo": "39"})
            with bd.conecta() as c:
                for p, u in ((38.65, "a"), (35.0, "b")):
                    c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                              (time.time(), sid, "Marvel Champions Hulk", "t.es", "https://t.es/" + u, p,
                               f"cuesta {p} €, por debajo de tu objetivo de 39,00 €"))
            seguimiento.guarda({"id": sid, "consulta": "marvel champions", "objetivo": "38"})
            self.assertEqual([a["precio"] for a in seguimiento.avisos()], [35.0])


if __name__ == "__main__":
    unittest.main()
