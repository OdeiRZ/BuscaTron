import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import ajustes, bd, importar, motor, tiendas  # noqa: E402

TEXTO = """Resultados de búsqueda para "marvel champions"
Ordenar por: precio
Marvel Champions: Los Más Buscados de la Galaxia
Asmodee
42,90 €
38,50 €
Añadir al carrito
Marvel Champions: Civil War
Disponible a partir del 12/03/2027
44,95 €
Marvel Champions: Pack de Héroe Hulk
Agotado
16,99 €
Camiseta Marvel
12,00 €
Marvel Champions: Deadpool 30,37 €
Marvel Champions: Deadpool 30,37 €
marvel champions
"""


class Parsea(unittest.TestCase):
    def setUp(self):
        self.r = {x["titulo"]: x for x in importar.parsea(TEXTO, "marvel champions")}

    def test_lee_titulos_y_precios_ignorando_cabeceras_y_otros_productos(self):
        self.assertEqual(set(self.r), {"Marvel Champions: Los Más Buscados de la Galaxia", "Marvel Champions: Civil War",
                                       "Marvel Champions: Pack de Héroe Hulk", "Marvel Champions: Deadpool"})

    def test_con_dos_precios_vale_el_menor(self):
        self.assertEqual(self.r["Marvel Champions: Los Más Buscados de la Galaxia"]["precio"], 38.5)

    def test_no_se_lleva_el_precio_del_producto_de_al_lado(self):
        self.assertEqual(self.r["Marvel Champions: Pack de Héroe Hulk"]["precio"], 16.99)   # la camiseta de 12 € va detrás
        self.assertEqual(self.r["Marvel Champions: Civil War"]["precio"], 44.95)

    def test_precio_en_la_misma_linea_y_sin_duplicados(self):
        self.assertEqual(self.r["Marvel Champions: Deadpool"]["precio"], 30.37)
        self.assertEqual(len([1 for x in importar.parsea(TEXTO, "marvel champions") if "Deadpool" in x["titulo"]]), 1)

    def test_preventa_y_agotado(self):
        self.assertTrue(self.r["Marvel Champions: Civil War"]["preventa"])
        self.assertFalse(self.r["Marvel Champions: Civil War"]["agotado"])
        self.assertTrue(self.r["Marvel Champions: Pack de Héroe Hulk"]["agotado"])

    def test_acepta_codigo_html_con_enlaces(self):
        h = '<a href="/p/1">Marvel Champions Uno</a><b>20 €</b>'
        r = importar.parsea(h, "marvel champions", "https://f.es/buscar")
        self.assertEqual([(x["titulo"], x["precio"], x["url"]) for x in r], [("Marvel Champions Uno", 20.0, "https://f.es/p/1")])

    def test_texto_sin_nada_util(self):
        self.assertEqual(importar.parsea("hola\nadiós", "marvel champions"), [])


class Guardado(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_url_propia_que_conserva_la_busqueda_de_la_tienda(self):
        u = importar._url_item("https://f.es/#3273/fullscreen/m=and&q=marvel+champions", "Marvel Champions: Hulk")
        self.assertEqual(u, "https://f.es/#3273/fullscreen/m=and&q=marvel+champions&btitem=marvel-champions-hulk")
        self.assertTrue(importar._url_item("https://f.es/buscar", "A b").endswith("?btitem=a-b"))

    def test_se_sustituye_lo_anterior_y_caduca(self):
        items = importar.parsea(TEXTO, "marvel champions")
        self.assertEqual(importar.guarda("f.es", "marvel champions", items, "https://f.es/?q=x"), 4)
        self.assertEqual(importar.guarda("f.es", "marvel champions", items[:1], "https://f.es/?q=x"), 1)
        self.assertEqual(len(importar.vigentes("f.es", "marvel champions")), 1)
        despues = time.time() + (importar.CADUCA_HORAS + 1) * 3600
        self.assertEqual(importar.vigentes("f.es", "marvel champions", ahora=despues), [])

    def test_solo_devuelve_lo_que_encaja_con_la_busqueda_actual(self):
        importar.guarda("f.es", "marvel champions", importar.parsea(TEXTO, "marvel champions"), "https://f.es/?q=x")
        self.assertEqual([x["titulo"] for x in importar.vigentes("f.es", "marvel champions hulk")], ["Marvel Champions: Pack de Héroe Hulk"])


class Recordatorios(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_avisa_una_vez_antes_de_caducar(self):
        importar.guarda("f.es", "marvel champions", importar.parsea(TEXTO, "marvel champions"), "https://f.es/?q=x")
        with bd.conecta() as c:
            ts = c.execute("SELECT MAX(ts) FROM importados").fetchone()[0]
        self.assertEqual(importar.por_caducar(ahora=ts + 3600), [])                          # recién pegado
        pend = importar.por_caducar(ahora=ts + 65 * 3600)                                    # quedan 7 h
        self.assertEqual([(h, c) for h, _, _, c in pend], [("f.es", "marvel champions")])
        importar.marca_recordado("f.es", ts)
        self.assertEqual(importar.por_caducar(ahora=ts + 66 * 3600), [])                     # no se repite
        self.assertEqual(importar.por_caducar(ahora=ts + 80 * 3600), [])                     # ya caducado: nada


class EnLaBusqueda(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),
                        mock.patch.object(tiendas, "guarda", lambda l: None)]
        for p in self.parches:
            p.start()
        ajustes.guarda({"usar_navegador": False, "segunda_mano_sembrada": True, "amazon_automatico": True})
        self.lista = [{"host": "f.es", "activa": True, "manual": True, "plantilla": "https://f.es/#1/fullscreen/m=and&q={q}"},
                      {"host": "a.es", "activa": True}]
        self.parches += [mock.patch.object(tiendas, "carga", lambda: self.lista),
                         mock.patch.object(motor, "_tienda", lambda t, c, nav=None, paginas=1: (t["host"], [
                             {"titulo": "Marvel Champions: Otro", "url": "https://a.es/o", "precio": 40.0, "agotado": False, "preventa": False, "estado": ""}], None))]
        for p in self.parches[3:]:
            p.start()

    def tearDown(self):
        for p in self.parches:
            p.stop()

    def test_lo_importado_se_mezcla_con_el_resto_y_se_avisa_de_ello(self):
        importar.guarda("f.es", "marvel champions", importar.parsea(TEXTO, "marvel champions"), "https://f.es/#1/fullscreen/m=and&q=marvel+champions")
        res, inf = motor.buscar("marvel champions")
        self.assertEqual([(x["tienda"], x["precio"]) for x in res][:2], [("f.es", 30.37), ("f.es", 38.5)])    # ordenados con todos los demás
        self.assertTrue(all("importado" in x for x in res if x["tienda"] == "f.es"))
        self.assertEqual(inf["f.es"]["importados"], 2)       # el agotado y la preventa se ocultan, como en cualquier tienda
        self.assertIn("manual", inf["f.es"])                  # sigue ofreciendo su enlace
        self.assertEqual(len({x["url"] for x in res}), len(res))   # cada producto con su propia dirección


if __name__ == "__main__":
    unittest.main()
