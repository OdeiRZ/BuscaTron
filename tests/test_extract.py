import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import extract  # noqa: E402

HTML = """
<ul>
 <li><a href="/a">Marvel Champions: Saga</a><br>
   <span class="price-old">60,00 €</span> <span>45,50 €</span><br>
   <div style="display: none">Producto agotado</div> <em>Disponible en stock</em></li>
 <li><a href="/b">Marvel Champions: Otra</a><img src="x.png"> <span>12,00 €</span> <b>Agotado</b></li>
 <li><a href="/c">Catan</a> <span>30,00 €</span></li>
</ul>"""


class Extrae(unittest.TestCase):
    def test_precio_vigente_y_stock(self):
        r = {x["url"].split("/")[-1]: x for x in extract.extrae(HTML, "https://t.es/", "marvel champions")}
        self.assertEqual(set(r), {"a", "b"})                 # Catan no encaja
        self.assertEqual(r["a"]["precio"], 45.5)             # ignora el precio tachado
        self.assertFalse(r["a"]["agotado"])                  # el «agotado» oculto no cuenta
        self.assertTrue(r["b"]["agotado"])                   # el visible sí
        self.assertEqual(r["b"]["precio"], 12.0)             # etiquetas sin cierre no descuadran

    def test_titulo_recortado_usa_title(self):
        h = '<a href="/x" title="Marvel Champions: La Tiranía del Cráneo Rojo">Marvel Champions:...</a><b>45,00 €</b>'
        r = extract.extrae(h, "https://t.es/", "marvel champions")
        self.assertEqual(r[0]["titulo"], "Marvel Champions: La Tiranía del Cráneo Rojo")

    def test_titulo_recortado_sin_title_usa_la_url(self):
        h = '<a href="/marvel-champions-shadowland-pack-de-escenarios-castellano-99438.html">Marvel Champions:...</a><b>25,95 €</b>'
        r = extract.extrae(h, "https://t.es/", "marvel champions")
        self.assertEqual(r[0]["titulo"], "Marvel champions shadowland pack de escenarios castellano")

    def test_reposicion_y_reserva_cuentan_como_no_disponible(self):
        h = ('<a href="/a">Marvel Champions: Uno</a><b>25,95 €</b><span class="stock-tag"> Reserva </span>'
             '<a href="/b">Marvel Champions: Dos</a><b>20,00 €</b><p>EN REPOSICIÓN. El envío se realizará cuando el artículo vuelva a estar disponible</p>'
             '<a href="/c">Marvel Champions: Tres</a><b>30,00 €</b><span>En stock</span>')
        r = {x["url"].split("/")[-1]: x["agotado"] for x in extract.extrae(h, "https://t.es/", "marvel champions")}
        self.assertEqual(r, {"a": True, "b": True, "c": False})


class Tarjetas(unittest.TestCase):
    def test_precio_y_estado_dentro_del_enlace(self):
        h = ('<a href="/item/1"><img src="a.jpg"><span>25 €</span><p>Marvel Champions: Saga</p><span>Buen estado</span></a>'
             '<a href="/item/2"><span>30 €</span><p>Marvel Champions: Otra</p><span>Nuevo</span></a>')
        r = {x["url"].split("/")[-1]: x for x in extract.extrae(h, "https://w.es/", "marvel champions", con_estado=True)}
        self.assertEqual((r["1"]["precio"], r["1"]["estado"]), (25.0, "buen estado"))
        self.assertEqual((r["2"]["precio"], r["2"]["estado"]), (30.0, "nuevo"))

    def test_sin_estados_si_no_se_piden(self):
        h = '<a href="/item/1"><span>25 €</span><p>Marvel Champions: Saga</p><span>Nuevo</span></a>'
        self.assertEqual(extract.extrae(h, "https://w.es/", "marvel champions")[0]["estado"], "")

    def test_un_producto_sin_precio_no_roba_el_del_siguiente(self):
        h = '<a href="/a">Marvel Champions: Uno</a><a href="/b"><b>20 €</b> Marvel Champions: Dos</a>'
        r = extract.extrae(h, "https://t.es/", "marvel champions")
        self.assertEqual([(x["url"].split("/")[-1], x["precio"]) for x in r], [("b", 20.0)])


class Vinted(unittest.TestCase):
    def test_titulo_estado_y_precio_salen_del_title(self):
        h = ('<a href="/items/1-a" title="Sleeves Marvel Champions, Marca: Marvel, Estado: Muy bueno, 2.50 €, 3.25 €"></a>'
             '<a href="/items/2-b" title="Marvel Champions, Estado: Bueno, 12.00 €, 13.10 €"></a>')
        r = {x["url"].split("/")[-1]: (x["titulo"], x["precio"], x["estado"]) for x in extract.extrae(h, "https://v.es/", "marvel champions", con_estado=True)}
        self.assertEqual(r["1-a"], ("Sleeves Marvel Champions", 2.5, "muy bueno"))
        self.assertEqual(r["2-b"], ("Marvel Champions", 12.0, "bueno"))


class Preventas(unittest.TestCase):
    def test_preventa_no_es_agotado(self):
        h = ('<a href="/a">Marvel Champions: Uno</a><b>38,23 €</b><span> Reserva </span><span>PREVENTA. Lanzamiento aproximado: 26/3/2027</span>'
             '<a href="/b">Marvel Champions: Dos</a><b>25,95 €</b><span> Reserva </span><span>EN REPOSICIÓN. El envío se realizará cuando vuelva</span>'
             '<a href="/c">Marvel Champions: Tres (PREVENTA)</a><b>38,65 €</b>')
        r = {x["url"].split("/")[-1]: (x["preventa"], x["agotado"]) for x in extract.extrae(h, "https://t.es/", "marvel champions")}
        self.assertEqual(r, {"a": (True, False), "b": (False, True), "c": (True, False)})


class Paginas(unittest.TestCase):
    def test_rel_next_gana_a_los_enlaces_de_texto(self):
        h = '<link rel="next" href="/p/2"><a href="/p/9">Siguiente</a><a href="/x">Marvel Champions: Uno</a><b>1 €</b>'
        self.assertEqual(extract.analiza(h, "https://t.es/p/1", "marvel")[1], "https://t.es/p/2")

    def test_enlace_siguiente_por_texto_o_clase(self):
        for h in ('<a href="?page=2">Siguiente</a>', '<a href="?page=2">»</a>', '<a class="pagination-next" href="?page=2">2</a>'):
            self.assertEqual(extract.analiza(h, "https://t.es/b", "x")[1], "https://t.es/b?page=2", h)

    def test_sin_pagina_siguiente(self):
        self.assertIsNone(extract.analiza('<a href="#">Siguiente</a><a href="javascript:void(0)">next</a>', "https://t.es/", "x")[1])


class Producto(unittest.TestCase):
    def test_json_ld(self):
        h = ('<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"Product","name":"Juego X",'
             '"offers":{"@type":"Offer","price":"29.95","priceCurrency":"EUR","availability":"https://schema.org/InStock"}}]}</script>')
        d = extract.datos_producto(h, "https://t.es/x")
        self.assertEqual((d["titulo"], d["precio"], d["moneda"], d["agotado"], d["preventa"]), ("Juego X", 29.95, "EUR", False, False))

    def test_json_ld_agotado_y_preventa(self):
        base = '<script type="application/ld+json">{"@type":"Product","name":"J","offers":[{"price":10,"availability":"http://schema.org/%s"}]}</script>'
        self.assertTrue(extract.datos_producto(base % "OutOfStock")["agotado"])
        self.assertTrue(extract.datos_producto(base % "PreOrder")["preventa"])

    def test_open_graph(self):
        h = '<meta property="og:title" content="Juego Y"><meta property="product:price:amount" content="19,90"><meta property="product:price:currency" content="EUR">'
        d = extract.datos_producto(h)
        self.assertEqual((d["titulo"], d["precio"]), ("Juego Y", 19.9))

    def test_sin_datos(self):
        self.assertIsNone(extract.datos_producto("<html><body>Nada que vender</body></html>"))


class Envio(unittest.TestCase):
    def test_envio_gratis_desde(self):
        h = "<p>Envío gratis a partir de 49 € en península</p><p>Gastos de envío: 4,95 €</p>"
        self.assertEqual(extract.detecta_envio(h), {"gratis_desde": 49.0, "coste": 4.95})

    def test_palabras_entre_envio_y_gratis(self):
        self.assertEqual(extract.detecta_envio("<b>Envío 24 horas gratis a partir de 50 €</b>")["gratis_desde"], 50.0)
        self.assertEqual(extract.detecta_envio("<p>Envío gratis en pedidos de más de 89 €</p>")["gratis_desde"], 89.0)

    def test_formulacion_inversa(self):
        self.assertEqual(extract.detecta_envio("<b>Desde 60€ envío gratis</b>")["gratis_desde"], 60.0)

    def test_sin_datos(self):
        self.assertEqual(extract.detecta_envio("<p>Bienvenido</p>"), {"gratis_desde": None, "coste": None})


if __name__ == "__main__":
    unittest.main()
