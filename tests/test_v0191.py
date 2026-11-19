"""v0.19.1: al pegar, la marca en su propia línea (Ferretería Ibermadrid) se une al nombre que la sigue."""
import unittest

from buscatron import importar


class MarcaEnSuLinea(unittest.TestCase):
    def test_marca_y_nombre_en_lineas_separadas(self):
        t = "15%\nVANTAGE\nPizarra blanca magnética 120x90 cm\n76,51 € 90,01 €\n10%\nVANTAGE\nPizarra 90x60\n40,00 € 44,50 €"
        r = importar.parsea(t, "Vantage", "https://tienda.invalid/")
        self.assertEqual([(x["titulo"], x["precio"]) for x in r],
                         [("VANTAGE Pizarra blanca magnética 120x90 cm", 76.51), ("VANTAGE Pizarra 90x60", 40.0)])

    def test_marca_sola_con_precio(self):
        r = importar.parsea("15%\nVANTAGE\n76,51 € 90,01 €", "Vantage", "https://tienda.invalid/")
        self.assertEqual([x["precio"] for x in r], [76.51])

    def test_nombre_que_ya_lleva_la_marca(self):
        r = importar.parsea("Pizarra Vantage 120x90\n76,51 €", "Vantage", "https://tienda.invalid/")
        self.assertEqual([x["titulo"] for x in r], ["Pizarra Vantage 120x90"])


class ManualSinPlantilla(unittest.TestCase):
    """Una tienda «solo enlace» sin dirección de búsqueda (Dynos) se consultaba igual y no salía lo pegado."""

    def test_no_se_consulta_y_salen_los_pegados(self):
        import os
        import tempfile
        from unittest import mock
        from buscatron import ajustes, bd, motor
        d = tempfile.mkdtemp()           # base y ajustes temporales: la búsqueda guarda precios
        t = {"host": "www.dynos.es", "nombre": "Dynos", "activa": True, "plantilla": None, "manual": True, "tipo": "tienda"}
        pegado = {"titulo": "Juego De Mesa Marvel Champions Hulk", "precio": 13.32, "url": "https://www.dynos.es/?btitem=x",
                  "agotado": False, "preventa": False, "estado": "", "importado": 1.0}
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")), \
             mock.patch.object(motor.cfg, "carga", return_value=[t]), \
             mock.patch.object(motor.importar, "vigentes", return_value=[dict(pegado)]), \
             mock.patch.object(motor, "_tienda_consulta", side_effect=AssertionError("no debe consultarse")):
            res, inf = motor.buscar("marvel champions", hosts=["www.dynos.es"], castellano=False)
        self.assertEqual(inf["www.dynos.es"]["manual"], "https://www.dynos.es/")
        self.assertEqual([x["precio"] for x in res], [13.32])


if __name__ == "__main__":
    unittest.main()
