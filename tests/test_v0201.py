"""v0.20.1: el enlace a la foto no es el producto, y la ficha a la que salta una búsqueda de un solo resultado se lee bien."""
import unittest

from buscatron import extract

LISTADO = """<ul class="products"><li class="product"><a href="https://t.es/wp-content/uploads/2026/10/eternal-1.jpg"><img alt="Eternal Decks"></a>
<h2><a href="https://t.es/producto/eternal-decks/">Eternal Decks</a></h2><span class="price">39,99 €</span></li></ul>"""

FICHA = """<html><head><link rel="canonical" href="https://t.es/shop/eternal-decks/">
<script type="application/ld+json">{"@type":"Product","name":"Eternal Decks","offers":{"@type":"Offer","price":"35.95",
"availability":"https://schema.org/InStock"}}</script></head><body>
<a href="https://t.es/wp-content/uploads/2026/10/eternal-face3d.jpg"><img alt="Eternal Decks"></a>
<section class="related"><a href="https://t.es/shop/otro/">Otro juego</a> 19,75 €</section></body></html>"""


class Enlaces(unittest.TestCase):
    def test_la_foto_no_es_el_producto(self):
        r, _ = extract.analiza(LISTADO, "https://t.es/?s=eternal", "eternal decks")
        self.assertEqual([(x["url"], x["precio"]) for x in r], [("https://t.es/producto/eternal-decks/", 39.99)])

    def test_ficha_de_un_solo_resultado(self):
        r, sig = extract.analiza(FICHA, "https://t.es/?post_type=product&s=eternal+decks", "eternal decks")
        self.assertEqual([(x["url"], x["precio"], x["agotado"]) for x in r], [("https://t.es/shop/eternal-decks/", 35.95, False)])
        self.assertIsNone(sig)

    def test_un_listado_con_canonica_de_busqueda_no_es_una_ficha(self):
        html = LISTADO.replace("<ul", '<link rel="canonical" href="https://t.es/?s=eternal"><ul', 1)
        self.assertEqual(len(extract.analiza(html, "https://t.es/?s=eternal", "eternal decks")[0]), 1)


if __name__ == "__main__":
    unittest.main()
