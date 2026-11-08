"""v0.12.1: tarjetas que no se mezclan con la siguiente, precios con descuento, «casi agotado» y repaso de Amazon."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import extract, motor  # noqa: E402

BASE = "https://tienda.es/buscar?controller=search&s=x"


def tarjeta(id_, titulo, precio, stock):
    return (f'<article><h2><a href="https://tienda.es/{id_}.html">{titulo}</a></h2><span class="price">{precio} €</span>'
            f'<span class="stock">{stock}</span></article>')


class TarjetaDeOtroProducto(unittest.TestCase):
    def test_el_stock_del_siguiente_que_no_encaja_no_es_suyo(self):
        # Dungeon Marvels: Mage Knight (preventa) seguido de Krang (en reposición), que no encaja con la búsqueda
        html = (tarjeta("mage-knight-edicion-definitiva-28309", "Mage Knight: Edición Definitiva", "114,71",
                        "PREVENTA. Lanzamiento aproximado: 31/12/2026")
                + tarjeta("mage-knight-krang-5130", "Mage Knight: Krang Character", "24,95", "EN REPOSICIÓN"))
        (x,) = extract.extrae(html, BASE, "Mage Knight: Edición Definitiva")
        self.assertEqual(x["precio"], 114.71)
        self.assertTrue(x["preventa"])
        self.assertFalse(x["agotado"])

    def test_el_enlace_a_la_misma_ficha_no_corta_la_tarjeta(self):
        html = ('<a href="https://tienda.es/catan-1.html">Catan</a><span>42,00 €</span>'
                '<a href="https://tienda.es/catan-1.html">Vista rápida</a><span>Agotado</span>'
                '<a href="https://tienda.es/otro-2.html">Otro juego</a><span>10,00 €</span>')
        (x,) = extract.extrae(html, BASE, "catan")
        self.assertTrue(x["agotado"])

    def test_lo_que_va_entre_la_imagen_y_el_titulo_es_suyo(self):
        # Jugamos Una: enlace de la imagen, «Agotado», enlace del título y el precio
        html = ('<a href="https://tienda.es/lost-legion.html"><img alt="Comprar Lost Legion Mage Knight"></a>'
                '<span>No disponible</span><span>Agotado</span>'
                '<a href="https://tienda.es/lost-legion.html">The Lost Legion - Mage Knight</a><span>44,96 €</span>'
                '<a href="https://tienda.es/galaxy.html"><img alt="Galaxy Trucker"></a><span>Disponible</span>'
                '<a href="https://tienda.es/galaxy.html">Galaxy Trucker</a><span>32,36 €</span>')
        (x,) = extract.extrae(html, BASE, "mage knight")
        self.assertEqual(x["precio"], 44.96)
        self.assertTrue(x["agotado"])


class StockYPrecios(unittest.TestCase):
    def test_casi_agotado_es_que_hay(self):
        html = tarjeta("catan-energias", "Catán: Energías", "54,00", "Últimas unidades · Casi agotado")
        (x,) = extract.extrae(html, BASE, "catan")
        self.assertFalse(x["agotado"])

    def test_precio_con_descuento_no_es_tachado(self):
        # Goblin Trader: «price--original» es el de antes; «price--discount», el que se paga
        html = ('<a href="https://tienda.es/mage-knight.html">Mage Knight Edición Definitiva</a>'
                '<span class="product-card__price--original">134,95 €</span>'
                '<span class="product-card__price product-card__price--discount">121,45 €</span>'
                '<a href="https://tienda.es/codigo-secreto.html">Código Secreto</a><span>27,00 €</span>')
        (x,) = extract.extrae(html, BASE, "mage knight")
        self.assertEqual(x["precio"], 121.45)


class RepasoDeAmazon(unittest.TestCase):
    T = {"host": "www.amazon.es", "js": True, "plantilla": "https://www.amazon.es/s?k={q}&i=toys"}

    def test_solo_se_toman_los_juegos(self):
        html = ('<a href="https://www.amazon.es/dp/A1">Eternal Decks | Juego de Cartas cooperativo</a><span>29,90 €</span>'
                '<a href="https://www.amazon.es/dp/A2">Funda Eternal Decks para móvil</a><span>9,90 €</span>')
        with mock.patch.object(motor.fetch, "get", return_value=(200, html)), mock.patch.object(motor.time, "sleep"):
            items = motor._repaso(dict(self.T, js=False), "https://www.amazon.es/s?k={q}", "Eternal decks", None)
        self.assertEqual([x["url"] for x in items], ["https://www.amazon.es/dp/A1"])

    def test_suma_lo_nuevo_y_quita_el_sin_coincidencias(self):
        uno = {"url": "https://www.amazon.es/dp/A1", "titulo": "Eternal Decks juego", "precio": 29.9}
        with mock.patch.object(motor, "_tienda_base", return_value=("www.amazon.es", [], motor.SIN_COINCIDENCIAS)), \
                mock.patch.object(motor, "_repaso", return_value=[uno]):
            h, items, err = motor._tienda(self.T, "Eternal decks")
        self.assertEqual((items, err), ([uno], None))

    def test_no_repite_ni_repasa_si_la_tienda_esta_caida(self):
        uno = {"url": "https://www.amazon.es/dp/A1", "titulo": "Eternal Decks juego", "precio": 29.9}
        with mock.patch.object(motor, "_tienda_base", return_value=("www.amazon.es", [uno], None)), \
                mock.patch.object(motor, "_repaso", return_value=[uno]):
            self.assertEqual(motor._tienda(self.T, "Eternal decks")[1], [uno])
        with mock.patch.object(motor, "_tienda_base", return_value=("www.amazon.es", [], "no se pudo conectar")), \
                mock.patch.object(motor, "_repaso") as repaso:
            motor._tienda(self.T, "Eternal decks")
        repaso.assert_not_called()


if __name__ == "__main__":
    unittest.main()
