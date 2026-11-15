"""v0.17.28: añadir a la referencia un producto de Amazon por su enlace, tenga o no stock."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, historico, referencia, web  # noqa: E402

ENLACE = "https://www.amazon.es/Marvel-Champions-Tiran%C3%ADa-Cr%C3%A1neo-Rojo/dp/B08VW72D4F/"


class ConBD(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()


class Extras(ConBD):
    def test_titulo_y_asin_salen_del_enlace(self):
        self.assertEqual(referencia.titulo_de_enlace(ENLACE), "Marvel Champions Tiranía Cráneo Rojo")
        r = referencia.anade_extra(ENLACE)
        self.assertEqual((r["asin"], r["titulo"]), ("B08VW72D4F", "Marvel Champions Tiranía Cráneo Rojo"))

    def test_sale_en_la_referencia_sin_stock_ni_precio(self):
        referencia.anade_extra(ENLACE)
        for ambito in ("avisos", "vigiladas"):
            l = [p for p in referencia.resumen(ambito) if p.get("extra")]
            self.assertEqual(len(l), 1)
            self.assertEqual((l[0]["precio"], l[0]["tienda"], l[0]["amazon"]["asin"]), (None, "", "B08VW72D4F"))

    def test_con_su_historico_leido(self):
        referencia.anade_extra(ENLACE)
        historico.guarda("B08VW72D4F", {"minimo": 30.0, "fecha_minimo": "2025-11-28", "maximo": 45.0, "fecha_maximo": "2023-05-01", "actual": 40.0})
        a = [p for p in referencia.resumen("avisos") if p.get("extra")][0]["amazon"]
        self.assertEqual(a["camel"]["minimo"], 30.0)
        self.assertTrue(a["camel"]["frases"])

    def test_quitar_y_no_repetir(self):
        referencia.anade_extra(ENLACE)
        referencia.anade_extra(ENLACE)
        self.assertEqual(len([p for p in referencia.resumen("avisos") if p.get("extra")]), 1)
        referencia.quita_extra("B08VW72D4F")
        self.assertEqual([p for p in referencia.resumen("avisos") if p.get("extra")], [])

    def test_enlace_que_no_es_de_amazon(self):
        with self.assertRaises(ValueError):
            referencia.anade_extra("https://tienda.es/algo")

    def test_endpoint(self):
        h = web.Handler.__new__(web.Handler)
        r = web.Handler._post(h, "/api/referencia", {"extra": ENLACE})
        self.assertEqual(r["asin"], "B08VW72D4F")
        self.assertEqual(web.Handler._post(h, "/api/referencia", {"quitar_extra": "B08VW72D4F"}), {"ok": True})

    def test_vinculado_sin_precios_tambien_trae_su_historico(self):
        historico.guarda("B08VW72D4F", {"minimo": 30.0, "maximo": 45.0, "actual": 40.0})
        referencia.vincula("clave x", "B08VW72D4F", "algo")
        sid = __import__("buscatron.seguimiento", fromlist=["x"]).guarda({"consulta": "q"})
        import time
        with bd.conecta() as c:
            c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,0,?,0,?)",
                      (time.time(), "q", "zacatrus.es", "clave x", "https://zacatrus.es/x", 40.0, sid, "clave x"))
        r = [p for p in referencia.resumen("vigiladas") if p["clave"] == "clave x"][0]
        self.assertEqual(r["amazon"]["camel"]["minimo"], 30.0)


if __name__ == "__main__":
    unittest.main()


class PaginaVieja(ConBD):
    def test_un_añadido_no_lleva_tienda_nula(self):
        """Una pestaña con la página anterior hace `tienda.replace(...)`: con None se rompía («h is null»)."""
        referencia.anade_extra(ENLACE)
        for ambito in ("avisos", "vigiladas"):
            for p in referencia.resumen(ambito):
                self.assertIsNotNone(p["tienda"], p["titulo"])


class ResumenEnVigiladas(ConBD):
    def prepara(self):
        import time
        from buscatron import seguimiento
        a, b, c = seguimiento.guarda({"consulta": "uno"}), seguimiento.guarda({"consulta": "dos", "activo": False}), seguimiento.guarda({"consulta": "tres"})
        ahora = time.time()
        with bd.conecta() as con:
            fila = ("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,0,?,0,?)")
            con.executemany(fila, [
                (ahora, "uno", "www.amazon.es", "Marvel Champions Era de Apocalipsis expansion", "https://www.amazon.es/dp/B0CZPDLZ6L", 40.0, a, "k1"),
                (ahora - 99999, "dos", "www.amazon.es", "Marvel Champions Civil War expansion", "https://www.amazon.es/dp/B0G6FKDBNN", 44.0, b, "k2"),
                (ahora, "tres", "www.amazon.es", "Marvel Champions Titan Loco expansion", "https://www.amazon.es/dp/B0971J1K8Q", 41.0, c, "k3")])
        historico.guarda("B0CZPDLZ6L", {"minimo": 30.68, "fecha_minimo": "2025-11-20", "maximo": 44.99, "fecha_maximo": "2026-08-10", "actual": 40.0})
        historico.guarda("B0G6FKDBNN", {"minimo": 44.0, "maximo": 44.99, "actual": 44.0})
        return a, b, c

    def test_activas_y_en_pausa_con_historial_y_sin_el_resto(self):
        a, b, c = self.prepara()
        r = referencia.por_vigilada()
        self.assertEqual(set(r), {a, b})                     # la tercera no tiene historial leído: no sale
        self.assertEqual((r[a][0]["minimo"], r[a][0]["maximo"]), (30.68, 44.99))
        self.assertEqual(r[b][0]["asin"], "B0G6FKDBNN")      # la que está en pausa también

    def test_sin_ningun_historial_no_devuelve_nada(self):
        self.prepara()
        with bd.conecta() as con:
            con.execute("DELETE FROM camel_extremos")
        self.assertEqual(referencia.por_vigilada(), {})

    def test_endpoint_get(self):
        a, b, c = self.prepara()
        self.assertEqual(set(referencia.por_vigilada()), {a, b})
