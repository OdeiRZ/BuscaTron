"""v0.19.7: arreglos de la revisión de lógica (pegados con los mismos filtros, una dirección por producto, pegar solo en
tiendas «solo enlace»)."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, importar, motor


class Pegados(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.t = {"host": "bixoto.com", "nombre": "Bixoto", "activa": True, "plantilla": "https://bixoto.com/es?search={q}", "manual": True, "tipo": "tienda"}
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),
                        mock.patch.object(motor.cfg, "carga", return_value=[self.t]),
                        mock.patch.object(motor, "_tienda_consulta", side_effect=AssertionError("no debe consultarse"))]
        for p in self.parches:
            p.start()

    def tearDown(self):
        for p in reversed(self.parches):
            p.stop()

    def test_misma_direccion_desde_dos_busquedas(self):
        x = [{"titulo": "Marvel Champions Civil War", "precio": 38.0}]
        importar.guarda("bixoto.com", "marvel champions", x, "https://bixoto.com/es?search=marvel+champions")
        importar.guarda("bixoto.com", "civil war", x, "https://bixoto.com/es?search=civil+war")
        res, _ = motor.buscar("marvel champions civil war", hosts=["bixoto.com"], castellano=False)
        self.assertEqual(len(res), 1)                      # una sola vez, no una por cada búsqueda en la que se pegó
        self.assertIn("search=Marvel+Champions+Civil+War", res[0]["url"])

    def test_lo_pegado_pasa_los_filtros_de_no_juego(self):
        importar.guarda("bixoto.com", "marvel champions", [{"titulo": "Zapatillas Marvel Champions talla 42", "precio": 5.0},
                                                           {"titulo": "Marvel Champions Hulk", "precio": 13.0}], "https://bixoto.com/")
        res, _ = motor.buscar("marvel champions", hosts=["bixoto.com"], castellano=False)
        self.assertEqual([x["titulo"] for x in res], ["Marvel Champions Hulk"])



class IdiomaDeLaFicha(unittest.TestCase):
    """En la 0.19.6 se borró por error la tienda de verifica_idioma: el fallo se tragaba y nunca se leía el idioma."""

    def setUp(self):
        d = tempfile.mkdtemp()
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json"))]
        for p in self.parches:
            p.start()

    def tearDown(self):
        for p in reversed(self.parches):
            p.stop()

    def test_lee_la_ficha_de_una_tienda_normal(self):
        lista = [{"host": "t.es", "js": False}]
        html = "<html><body><table><tr><th>Idioma</th><td>Francés</td></tr></table></body></html>"
        with mock.patch.object(motor.fetch, "get", return_value=(200, html)) as g:
            motor.verifica_idioma({"url": "https://t.es/p/1", "tienda": "t.es"}, lista)
        g.assert_called_once()

    def test_no_consulta_una_tienda_solo_enlace(self):
        with mock.patch.object(motor.fetch, "get", side_effect=AssertionError("no debe consultarse")):
            self.assertIsNone(motor.verifica_idioma({"url": "https://bixoto.com/p/1", "tienda": "bixoto.com"},
                                                    [{"host": "bixoto.com", "manual": True}]))


if __name__ == "__main__":
    unittest.main()
