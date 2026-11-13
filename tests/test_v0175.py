"""v0.17.5: el resumen de Telegram trae cada producto de la vigilada con sus 3 ofertas más baratas (antes, solo los 5
productos más baratos: siempre los mismos)."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import seguimiento  # noqa: E402


def oferta(juego, precio, tienda):
    return {"titulo": juego, "grupo": juego, "url": f"https://{tienda}/{juego}-{precio}", "precio": precio, "tienda": tienda}


class Resumen(unittest.TestCase):
    def setUp(self):
        self.t = mock.patch("buscatron.tiendas.carga", lambda: [{"host": "a.es", "nombre": "A"}, {"host": "b.es", "nombre": "B"},
                                                                  {"host": "c.es", "nombre": "C"}, {"host": "d.es", "nombre": "D"}])
        self.t.start()

    def tearDown(self):
        self.t.stop()

    def texto(self, res):
        return seguimiento.resumen({"sin_agotados": 1}, {}, "todos", res, {})

    def test_salen_todos_los_productos_no_solo_cinco(self):
        res = [oferta(f"juego{i}", 10 + i, "a.es") for i in range(7)]
        t = self.texto(res)
        self.assertIn("Tus 7 productos y sus 3 ofertas más baratas", t)
        for i in range(7):
            self.assertIn(f"juego{i}", t)

    def test_cada_producto_lleva_sus_3_ofertas_mas_baratas(self):
        res = [oferta("titan", p, h) for p, h in ((40, "d.es"), (30, "a.es"), (35, "b.es"), (33, "c.es"), (50, "a.es"))]
        t = self.texto(res)
        self.assertIn("30,00 € en A", t)
        self.assertIn("También: 33,00 € en C, 35,00 € en B y 2 más", t)
        self.assertNotIn("40,00 €", t)
        self.assertIn("Tu producto y sus 3 ofertas", t)

    def test_ordenados_del_mas_barato_al_mas_caro(self):
        t = self.texto([oferta("caro", 60, "a.es"), oferta("barato", 20, "b.es")])
        self.assertLess(t.index("barato"), t.index("caro"))

    def test_muchos_productos_se_cortan_con_aviso(self):
        t = self.texto([oferta(f"j{i:02d}", 10 + i, "a.es") for i in range(seguimiento.MAX_RESUMEN + 4)])
        self.assertIn("… y 4 productos más en BuscaTron", t)

    def test_los_avisos_siguen_con_hasta_3_tiendas_mas(self):
        g = [oferta("x", p, "a.es") for p in (10, 11, 12, 13, 14, 15)]
        self.assertIn("y 2 más", seguimiento.linea_grupo(g, nombres={"a.es": "A"}))


if __name__ == "__main__":
    unittest.main()
