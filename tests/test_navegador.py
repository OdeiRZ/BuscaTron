import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import navegador  # noqa: E402

CLOUDFLARE_ES = ("<html><head><title>Un momento…</title></head><body><h1>ferreteria.es</h1><h2>Verificación de seguridad en curso</h2>"
                 "<p>Este sitio web utiliza un servicio de seguridad para protegerse contra ataques en línea.</p>"
                 "<script>" + "x" * 40000 + "</script></body></html>")
TIENDA = "<html><body>" + "<a href='/p'>Juego</a><b>10 €</b>" * 300 + "</body></html>"


class Desafios(unittest.TestCase):
    def test_reconoce_la_pantalla_de_cloudflare_en_español(self):
        self.assertTrue(navegador.desafio(403, CLOUDFLARE_ES))

    def test_reconoce_otros_desafios(self):
        self.assertTrue(navegador.desafio(403, "<html><body>Just a moment... Verify you are human</body></html>"))
        self.assertTrue(navegador.desafio(200, "<html><body>Introduce el captcha para continuar</body></html>"))
        self.assertTrue(navegador.desafio(202, "<html><body>...</body></html>"))     # pantalla casi vacía con 202

    def test_una_tienda_normal_no_es_un_desafio(self):
        self.assertFalse(navegador.desafio(200, TIENDA))
        self.assertFalse(navegador.desafio(404, TIENDA))


if __name__ == "__main__":
    unittest.main()
