"""v0.21.1: la descripción de la tienda no separa el mismo juego; las claves guardadas se recalculan al arrancar."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor


class Descripcion(unittest.TestCase):
    def test_mismo_juego_con_descripcion(self):
        self.assertEqual(motor.clave_producto("Eternal Decks: juego de cartas cooperativo y estratégico."), motor.clave_producto("Eternal Decks"))

    def test_juegos_distintos_siguen_separados(self):
        for a, b in (("Marvel Champions: Héroes Reunidos 1", "Marvel Champions: Héroes Reunidos 2"),
                     ("Too Many Bones", "Too Many Bones: Undertow"), ("Catan", "Catan: Ampliación 5-6 jugadores")):
            self.assertNotEqual(motor.clave_producto(a), motor.clave_producto(b))


class Recalculo(unittest.TestCase):
    def test_recalcula_historial_e_ignorados(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            t = "Eternal Decks: juego de cartas cooperativo y estratégico."
            with bd.conecta() as c:
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,clave) VALUES(?,?,?,?,?,?,?,?)",
                          (time.time(), "x", "t.es", t, "https://t.es/a", 30, 0, "vieja"))
                c.execute("INSERT INTO ignorados(clave,titulo,ts) VALUES(?,?,?)", ("vieja", t, time.time()))
            motor.rellena_claves()
            with bd.conecta() as c:
                self.assertEqual(c.execute("SELECT clave FROM precios").fetchone()[0], "deck eternal")
                self.assertEqual(c.execute("SELECT clave FROM ignorados").fetchone()[0], "deck eternal")
            self.assertEqual(ajustes.carga()["version_claves"], motor.VERSION_CLAVES)


if __name__ == "__main__":
    unittest.main()
