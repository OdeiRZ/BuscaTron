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
        self.p2 = mock.patch.object(historico, "cfg_raiz", lambda: tempfile.mkdtemp())      # las capturas fallidas, a una carpeta temporal
        self.p.start()
        self.p2.start()

    def tearDown(self):
        self.p2.stop()
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
        sid = __import__("buscatron.seguimiento", fromlist=["x"]).guarda({"consulta": "clave"})
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
        a, b, c = (seguimiento.guarda({"consulta": "marvel champions"}), seguimiento.guarda({"consulta": "marvel champions", "activo": False}),
                   seguimiento.guarda({"consulta": "marvel champions"}))
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


class FiltrosActuales(ConBD):
    """Editar los filtros de una vigilada tiene que notarse YA en lo guardado, sin esperar a la siguiente revisión."""

    def prepara(self, **filtros):
        import time
        from buscatron import seguimiento
        sid = seguimiento.guarda({"consulta": "too many bones", **filtros})
        ahora = time.time()
        with bd.conecta() as con:
            con.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,0,?,0,?)",
                            [(ahora, "x", "www.amazon.es", "Too Many Bones: Gasket Add-on Character", "https://www.amazon.es/dp/B0BJPCXYHW", 63.42, sid, "a"),
                             (ahora, "x", "zacatrus.es", "Too Many Bones Edición Definitiva", "https://zacatrus.es/tmb", 120.0, sid, "b")])
            con.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                        (ahora, sid, "Too Many Bones: Gasket Add-on Character", "www.amazon.es", "https://www.amazon.es/dp/B0BJPCXYHW", 63.42, "m"))
        return sid

    def titulos(self, ambito="vigiladas", estado="activas"):
        return sorted(p["titulo"] for p in referencia.resumen(ambito, estado))

    def test_subir_el_minimo_quita_lo_viejo_de_la_referencia_al_instante(self):
        from buscatron import seguimiento
        sid = self.prepara(pmin=50)
        self.assertEqual(len(self.titulos()), 2)
        seguimiento.guarda({"id": sid, "consulta": "too many bones", "pmin": 90})
        self.assertEqual(self.titulos(), ["Too Many Bones Edición Definitiva"])

    def test_descartar_una_palabra_tambien_(self):
        from buscatron import seguimiento
        sid = self.prepara()
        seguimiento.guarda({"id": sid, "consulta": "too many bones", "excluir": "add-on"})
        self.assertEqual(self.titulos(), ["Too Many Bones Edición Definitiva"])

    def test_al_guardar_se_van_los_avisos_que_ya_no_cumplen(self):
        from buscatron import seguimiento
        sid = self.prepara(pmin=50)
        self.assertEqual(len(seguimiento.avisos()), 1)
        seguimiento.guarda({"id": sid, "consulta": "too many bones", "pmin": 90})
        self.assertEqual(seguimiento.avisos(), [])

    def test_un_cambio_sin_efecto_no_borra_avisos(self):
        from buscatron import seguimiento
        sid = self.prepara(pmin=50)
        seguimiento.guarda({"id": sid, "consulta": "too many bones", "pmin": 50, "nombre": "otro nombre"})
        self.assertEqual(len(seguimiento.avisos()), 1)

    def test_la_referencia_respeta_la_pestana(self):
        from buscatron import seguimiento
        activa = self.prepara()
        pausa = seguimiento.guarda({"consulta": "too many bones", "activo": False})
        import time
        with bd.conecta() as con:
            con.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,0,?,0,?)",
                        (time.time(), "x", "mathom.es", "Too Many Bones Undertow", "https://mathom.es/u", 99.0, pausa, "c"))
        self.assertEqual(len(self.titulos(estado="activas")), 2)
        self.assertEqual(self.titulos(estado="pausa"), ["Too Many Bones Undertow"])
        self.assertEqual(len(self.titulos(estado="todas")), 3)
        self.assertTrue(activa != pausa)

    def test_el_resumen_por_vigilada_tambien(self):
        from buscatron import seguimiento
        sid = self.prepara(pmin=50)
        historico.guarda("B0BJPCXYHW", {"minimo": 40.0, "maximo": 70.0, "actual": 63.42})
        self.assertIn(sid, referencia.por_vigilada())
        seguimiento.guarda({"id": sid, "consulta": "too many bones", "pmin": 90})
        self.assertNotIn(sid, referencia.por_vigilada())


PAGINA_DE_BUSCATRON = ("BuscaTron • Comparador de pre X\nhttp://127.0.0.1:8790/#seguir\nReferencia de Amazon\n14 búsquedas vigiladas: 4 activas, 10 en pausa\n"
                       "Todas • 14\nHistórico (camelcamelcamel)\nMínimo histórico: 29,99 € el 10/03/2026 (hace 8 meses).\n"
                       "Máximo histórico: 52,95 € el 01/10/2024.\nAhora 39,00 €: un 30 % por encima de su mínimo.\n«Los Más Buscados de la Galaxia» • hasta 39,00 €")


class SoloGraficasDeVerdad(ConBD):
    def test_el_texto_de_la_propia_pagina_no_es_una_grafica(self):
        d = historico.parsea(PAGINA_DE_BUSCATRON)
        self.assertEqual(d.get("minimo"), 29.99)                       # lo que había llegado a guardar
        self.assertTrue(historico.valida(PAGINA_DE_BUSCATRON, d))
        self.assertFalse(historico.es_grafica(PAGINA_DE_BUSCATRON))

    def test_una_grafica_real_si_lo_es(self):
        from tests.test_v01720 import GRANDE, PEQUENA
        self.assertTrue(historico.es_grafica(GRANDE) and historico.es_grafica(PEQUENA))

    def test_el_endpoint_no_guarda_la_pagina(self):
        from buscatron import ocr
        h = web.Handler.__new__(web.Handler)
        with mock.patch.object(ocr, "lee", lambda b: PAGINA_DE_BUSCATRON), mock.patch.object(ocr, "decodifica", lambda u: b"\x89PNG\r\n\x1a\n" + b"\0" * 20):
            r = web.Handler._post(h, "/api/grafica", {"imagen": "x", "asin": "B0BJPCXYHW"})
        self.assertFalse(r["guardado"])
        self.assertEqual(historico.todos(), {})
        self.assertTrue(r["problemas"])

    def test_camel_dice_que_no_tiene_el_producto(self):
        t = "We canit find the requested product."
        self.assertIn("no tiene este producto", historico.valida(t, {})[0])


class SoloJuegos(unittest.TestCase):
    def test_una_palabra_en_tienda_generalista_exige_titulo_de_juego(self):
        from buscatron import motor
        self.assertFalse(motor.solo_juego("outlet-pc.es", "Talla: 45 - Under Armour Zapatillas Charged Vantage 2", "Vantage"))
        self.assertFalse(motor.solo_juego("www.amazon.es", "Rociador Berthoud Vantage", "Vantage"))
        self.assertTrue(motor.solo_juego("www.amazon.es", "Stonemaier Games | Vantage | Juego de Mesa cooperativo", "Vantage"))

    def test_en_tiendas_de_juegos_o_con_varias_palabras_no_se_exige(self):
        from buscatron import motor
        self.assertTrue(motor.solo_juego("zacatrus.es", "Vantage", "Vantage"))
        self.assertTrue(motor.solo_juego("www.amazon.es", "Asmodee Marvel Champions: La Era de Apocalipsis", "marvel champions"))

    def test_cumple_aplica_la_regla_a_lo_guardado(self):
        from buscatron import seguimiento
        seg = {"consulta": "Vantage", "incluir": "", "excluir": "", "pmin": None, "pmax": None, "opciones": "{}"}
        self.assertFalse(seguimiento.cumple(seg, "Rociador Berthoud Vantage", 135.0, "www.amazon.es"))
        self.assertTrue(seguimiento.cumple(seg, "Vantage", 81.0, "zacatrus.es"))


class CapturasFallidas(ConBD):
    def test_lo_que_no_se_guarda_deja_su_imagen_y_lo_guardado_la_borra(self):
        raiz = tempfile.mkdtemp()
        with mock.patch.object(historico, "cfg_raiz", lambda: raiz):
            historico.conserva_captura("B0BJPCXYHW", b"imagen", False)
            ruta = os.path.join(raiz, "capturas_fallidas", "B0BJPCXYHW.png")
            self.assertEqual(open(ruta, "rb").read(), b"imagen")
            historico.conserva_captura("B0BJPCXYHW", b"imagen", True)
            self.assertFalse(os.path.exists(ruta))

    def test_solo_se_guardan_las_ultimas(self):
        raiz = tempfile.mkdtemp()
        with mock.patch.object(historico, "cfg_raiz", lambda: raiz):
            for i in range(15):
                historico.conserva_captura(f"B0000000{i:02d}", b"x", False, maximo=12)
        self.assertEqual(len(os.listdir(os.path.join(raiz, "capturas_fallidas"))), 12)
