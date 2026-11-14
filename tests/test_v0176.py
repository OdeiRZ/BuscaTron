"""v0.17.6: el precio rebajado «15,75 € - 20% = 12,6 €» (Más que Oca) y el stock que el listado de Zacatrus no dice."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, extract, motor  # noqa: E402

BASE = "https://www.masqueoca.com/tienda/buscardo.asp?txtbusqueda=hero"


def tarjeta(precio_html, item=8715):
    return f"""<div><div><a href="producto.asp?item={item}&tit=Hero-Realms:-Odiseas"><img src="x.gif" alt="Hero Realms: Odiseas"/></a></div>
    <div><div><a href="producto.asp?item={item}&tit=Hero-Realms:-Odiseas">Hero Realms: Odiseas</a></div>
    <div>Precio: {precio_html}</div></div></div>"""


def precios(html):
    return [x["precio"] for x in extract.analiza(f"<html><body>{html}</body></html>", BASE, "Hero Realms Odiseas")[0]]


class PrecioRebajado(unittest.TestCase):
    def test_mas_que_oca_precio_final_en_negrita(self):
        self.assertEqual(precios(tarjeta('<img src="oferta.gif"> 15,75 &euro; - 20% = <b>12,6</b> &euro;')), [12.6])

    def test_rebaja_en_un_solo_texto(self):
        self.assertEqual(precios(tarjeta("15,75 € - 20% = 12,60 €")), [12.6])

    def test_numero_y_euro_en_trozos_distintos(self):
        self.assertEqual(precios(tarjeta("<span>18</span><span>€</span>")), [18.0])

    def test_precio_normal_sin_cambios(self):
        self.assertEqual(precios(tarjeta("<b>15,75 €</b>")), [15.75])

    def test_un_descuento_suelto_no_es_precio(self):
        self.assertEqual(precios(tarjeta("15,75 € <span>-2,59 €</span>")), [15.75])


def item(url, precio, tienda="zacatrus.es"):
    return {"url": url, "precio": precio, "tienda": tienda, "agotado": False, "preventa": False, "titulo": "x"}


class StockEnFicha(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(bd, "RUTA", os.path.join(self.tmp, "t.db"))
        self.p.start()
        self.leidas = []
        self.agotadas = set()
        self.f = mock.patch.object(motor, "ficha", lambda x, lista=None: self.leidas.append(x["url"]) or
                                   {"idioma": None, "agotado": x["url"] in self.agotadas, "preventa": False})
        self.f.start()
        self.s = mock.patch.object(motor, "PAUSA_FICHA", 0)
        self.s.start()

    def tearDown(self):
        self.p.stop()
        self.f.stop()
        self.s.stop()

    def test_zacatrus_lee_la_ficha_de_los_mas_baratos_y_marca_agotados(self):
        res = [item(f"https://zacatrus.es/{i}", 10 - i) for i in range(6)]       # el más barato es el 5
        self.agotadas = {"https://zacatrus.es/5"}
        motor.corrige_stock(res, [])
        self.assertEqual(self.leidas, [f"https://zacatrus.es/{i}" for i in (5, 4, 3, 2)])   # 4 y del más barato al más caro
        self.assertTrue(next(x for x in res if x["url"].endswith("/5"))["agotado"])
        self.assertFalse(next(x for x in res if x["url"].endswith("/0"))["agotado"])

    def test_otras_tiendas_no_piden_fichas(self):
        motor.corrige_stock([item("https://t.es/a", 5, "t.es")], [])
        self.assertEqual(self.leidas, [])

    def test_lo_ya_leido_en_la_ficha_manda_sin_volver_a_pedirla(self):
        import time
        with bd.conecta() as c:
            c.execute("INSERT INTO fichas(url, idioma, agotado, preventa, ts) VALUES(?,?,?,?,?)", ("https://t.es/a", "", 1, 0, time.time()))
            c.execute("INSERT INTO fichas(url, idioma, agotado, preventa, ts) VALUES(?,?,?,?,?)", ("https://zacatrus.es/b", "", 1, 0, time.time()))
        res = [item("https://t.es/a", 5, "t.es"), item("https://zacatrus.es/b", 4)]
        motor.corrige_stock(res, [])
        self.assertEqual(self.leidas, [])
        self.assertTrue(all(x["agotado"] for x in res))

    def test_una_ficha_vieja_se_vuelve_a_leer(self):
        with bd.conecta() as c:
            c.execute("INSERT INTO fichas(url, idioma, agotado, preventa, ts) VALUES(?,?,?,?,?)", ("https://zacatrus.es/b", "", 1, 0, 1.0))
        res = [item("https://zacatrus.es/b", 4)]
        motor.corrige_stock(res, [])
        self.assertEqual(self.leidas, ["https://zacatrus.es/b"])
        self.assertFalse(res[0]["agotado"])


if __name__ == "__main__":
    unittest.main()
