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


if __name__ == "__main__":
    unittest.main()
