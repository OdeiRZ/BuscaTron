"""v0.17.11: si el enlace envuelve toda la tarjeta (Outlet-PC), el título es el nombre del producto, sin las direcciones de
las imágenes ni los precios."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import extract  # noqa: E402

TARJETA = ('<a href="/products/z"><img alt="https://storage.googleapis.com/outletpc-images/a.jpg" src="a.jpg">'
           '<img alt="https://storage.googleapis.com/outletpc-images/b.jpg" src="b.jpg"><span>Producto nuevo</span>'
           '<span>49,99 €</span><span>89,00 €</span><span>Talla: 45 - Under Armour Zapatillas Charged Vantage 2 - Negro</span></a>')


class TituloDeTarjeta(unittest.TestCase):
    def test_outlet_pc(self):
        r = extract.extrae(TARJETA, "https://outlet-pc.es/search?q=vantage", "vantage")
        self.assertEqual([(x["titulo"], x["precio"]) for x in r], [("Talla: 45 - Under Armour Zapatillas Charged Vantage 2 - Negro", 49.99)])

    def test_un_titulo_normal_no_cambia(self):
        self.assertEqual(extract.titulo_de_tarjeta("Marvel Champions: La Era de Apocalipsis", ["marvel"]), "Marvel Champions: La Era de Apocalipsis")

    def test_zacatrus_sigue_igual(self):
        self.assertEqual(extract.limpia_titulo(extract.titulo_de_tarjeta("Hulk Hulk 16,95 € Club -10% 15,26 € ?", ["hulk"])), "Hulk")

    def test_se_queda_el_trozo_que_tiene_la_busqueda(self):
        self.assertEqual(extract.titulo_de_tarjeta("Vantage juego de mesa 39,95 € Envío en 24 horas a toda la península", ["vantage"]),
                         "Vantage juego de mesa")


if __name__ == "__main__":
    unittest.main()
