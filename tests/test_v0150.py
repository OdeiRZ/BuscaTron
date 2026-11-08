"""v0.15.0: referencia de Amazon (cada producto con su equivalente en Amazon y lo visto allí)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, referencia, seguimiento  # noqa: E402
from tests.test_v0114 import ConArchivos  # noqa: E402

AMZ = "www.amazon.es"


def precio(c, ts, tienda, titulo, url, p, seg=None):
    c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,0,?,0,'')",
              (ts, "q", tienda, titulo, url, p, seg))


class Referencia(ConArchivos):
    def setUp(self):
        super().setUp()
        self.sid = seguimiento.guarda({"consulta": "civil war", "excluir": "funda"})
        with bd.conecta() as c:
            precio(c, 1, AMZ, "Asmodee Marvel Champions: Civil War, Expansión, Juego de cartas", "https://www.amazon.es/dp/B0AAAAAAA1", 45.0)
            precio(c, 2, AMZ, "Asmodee Marvel Champions: Civil War, Expansión, Juego de cartas", "https://www.amazon.es/dp/B0AAAAAAA1", 41.5)
            precio(c, 2, AMZ, "Funda Marvel Champions Civil War", "https://www.amazon.es/dp/B0FUNDA001", 39.0)
            precio(c, 2, AMZ, "Pack Marvel Champions Civil War + Titán Loco", "https://www.amazon.es/dp/B0PACK0001", 89.9)
            c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(3,?,?,?,?,?,?)",
                      (self.sid, "Marvel Champions: Civil War", "tablerum.com", "https://tablerum.com/cw", 38.65, "x"))

    def test_empareja_con_amazon_y_resume_lo_visto(self):
        (p,) = referencia.resumen("avisos")
        a = p["amazon"]
        self.assertEqual((a["asin"], a["actual"], a["minimo"], a["maximo"], a["n"]), ("B0AAAAAAA1", 41.5, 41.5, 45.0, 2))

    def test_ni_la_funda_que_descarta_la_vigilada_ni_un_pack_al_doble(self):
        (p,) = referencia.resumen("avisos")
        self.assertEqual([x["asin"] for x in [p["amazon"]] + p["alternativas"]], ["B0AAAAAAA1"])

    def test_ficha_de_amazon_en_otro_idioma_se_marca(self):
        with bd.conecta() as c:
            c.execute("INSERT INTO fichas(url,idioma,agotado,preventa,ts) VALUES(?,?,NULL,NULL,1)", ("https://www.amazon.es/dp/B0AAAAAAA1", "otro"))
        self.assertEqual(referencia.resumen("avisos")[0]["amazon"]["idioma"], "otro")

    def test_lo_de_las_vigiladas_activas(self):
        with bd.conecta() as c:
            precio(c, 5, "zacatrus.es", "Marvel Champions: Civil War", "https://zacatrus.es/cw", 40.0, self.sid)
        (p,) = referencia.resumen("vigiladas")
        self.assertEqual((p["tienda"], p["amazon"]["asin"]), ("zacatrus.es", "B0AAAAAAA1"))


if __name__ == "__main__":
    unittest.main()
