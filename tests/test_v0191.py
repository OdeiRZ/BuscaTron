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


if __name__ == "__main__":
    unittest.main()
