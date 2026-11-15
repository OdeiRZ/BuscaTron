"""v0.17.20: lectura de la gráfica real de camelcamelcamel (Fantasy Flight MC16ES) y rechazo de lecturas dudosas."""
import datetime
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import historico, ocr, web  # noqa: E402

# Lo que el lector de Windows saca de la gráfica real, a 1200 px (se salta la etiqueta «€50» del eje)
GRANDE = ("€45\n€35\n€30\nFantasy MCI 6ES Flight Games Marvel Champions\n- €48,98\n€40,33\n- €33,09\nI\nI\nI\nJul Oct '22\nPrice type\nAmazon\n"
          "Apr\nJul Oct '23 Apr Jul Oct\nLowest\n€33,09 (Aug 2, 2026)\n@ camelcamelcamel.com\n'24 Apr Jul Oct '25 Apr Jul Oct '26 Apr Jul Oct\n"
          "Highest\n€48,98 (sep 6, 2023)\n- https://3cmls.co/ES/B091 Q2GGMR\nCurrent\n€40,33 (Nov 1 5, 2026)")
# …y a 600 px: «€33,09» se lee «03,09»
PEQUENA = ("€50\n€45\n€40\n€35\n€30\n--- -------------- €48,98\n€40,33\n-- 03,09\nPrice type\nLowest\n03,09 (Aug Z 2026)\nHighest\n"
           "€48,98 (sep 6, 2023)\nCurrent\n€40,33 (Nov 1 5, 2026)")


def png(ancho):
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + ancho.to_bytes(4, "big") + b"\x00" * 8


class GraficaReal(unittest.TestCase):
    def test_lectura_grande_correcta(self):
        d = historico.parsea(GRANDE)
        self.assertEqual((d["minimo"], d["fecha_minimo"], d["maximo"], d["fecha_maximo"], d["actual"]),
                         (33.09, "2026-08-02", 48.98, "2023-09-06", 40.33))
        self.assertEqual(historico.valida(GRANDE, d), [])

    def test_la_etiqueta_de_eje_perdida_no_rechaza_lo_bueno(self):
        self.assertEqual(historico.escala_eje(GRANDE), (30.0, 45.0, 5.0))

    def test_lectura_pequena_se_rechaza_en_vez_de_dar_un_minimo_falso(self):
        d = historico.parsea(PEQUENA)
        self.assertEqual(d["minimo"], 3.09)
        problemas = historico.valida(PEQUENA, d)
        self.assertTrue(problemas and "3,09" in problemas[0] and "fuera de la escala" in problemas[0])

    def test_frases_de_la_lectura_buena(self):
        f = historico.frases(historico.parsea(GRANDE), datetime.date(2026, 11, 15))
        self.assertIn("33,09", f[0])
        self.assertIn("02/08/2026", f[0])
        self.assertTrue(any("22 %" in x for x in f))        # 40,33 está un 22 % por encima del mínimo

    def test_actual_fuera_del_rango_se_rechaza(self):
        self.assertTrue(historico.valida("", {"minimo": 50, "maximo": 60, "actual": 40}))

    def test_ancho_del_png(self):
        self.assertEqual(ocr.ancho(png(600)), 600)
        self.assertEqual(ocr.ancho(b"no es png"), 0)


class Endpoint(unittest.TestCase):
    def llama(self, texto, ancho):
        with mock.patch.object(ocr, "lee", lambda b: texto), mock.patch.object(ocr, "decodifica", lambda u: png(ancho)):
            return web.Handler._post(web.Handler.__new__(web.Handler), "/api/grafica", {"imagen": "x"})

    def test_buena_da_frases_y_no_avisa(self):
        r = self.llama(GRANDE, 1200)
        self.assertTrue(r["frases"] and not r["problemas"] and not r["nota"])

    def test_dudosa_no_da_frases_y_explica(self):
        r = self.llama(PEQUENA, 600)
        self.assertEqual(r["frases"], [])
        self.assertTrue(r["problemas"])
        self.assertIn("pequeña", r["nota"])


if __name__ == "__main__":
    unittest.main()


class EscalaDelLector(unittest.TestCase):
    def test_las_imagenes_grandes_casi_no_se_amplian(self):
        self.assertEqual((ocr.escala_para(600), ocr.escala_para(1200, 600), ocr.escala_para(1920, 1080), ocr.escala_para(3840, 2160)), (3, 3, 3, 2))


import tempfile  # noqa: E402
import time  # noqa: E402
from buscatron import bd, referencia, seguimiento  # noqa: E402


class ConBD(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()


class Guardado(ConBD):
    def llama(self, texto, ancho, asin):
        with mock.patch.object(ocr, "lee", lambda b: texto), mock.patch.object(ocr, "decodifica", lambda u: png(ancho)):
            return web.Handler._post(web.Handler.__new__(web.Handler), "/api/grafica", {"imagen": "x", "asin": asin})

    def test_una_lectura_buena_se_guarda_por_producto(self):
        r = self.llama(GRANDE, 1200, "B091Q2GGMR")
        self.assertTrue(r["guardado"])
        d = historico.todos()["B091Q2GGMR"]
        self.assertEqual((d["minimo"], d["fecha_minimo"], d["maximo"], d["actual"]), (33.09, "2026-08-02", 48.98, 40.33))

    def test_una_dudosa_no_se_guarda(self):
        self.assertFalse(self.llama(PEQUENA, 600, "B091Q2GGMR")["guardado"])
        self.assertEqual(historico.todos(), {})

    def test_sin_producto_no_se_guarda(self):
        self.assertFalse(self.llama(GRANDE, 1200, "")["guardado"])
        self.assertEqual(historico.todos(), {})

    def test_leer_otra_vez_sustituye(self):
        historico.guarda("B091Q2GGMR", {"minimo": 1.0, "maximo": 2.0})
        self.llama(GRANDE, 1200, "B091Q2GGMR")
        self.assertEqual(historico.todos()["B091Q2GGMR"]["minimo"], 33.09)


class EnLaReferencia(ConBD):
    def test_cada_bloque_trae_lo_ya_leido_y_los_demas_no(self):
        sid, ahora = seguimiento.guarda({"consulta": "marvel"}), time.time()
        with bd.conecta() as c:
            c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa) VALUES(?,?,?,?,?,?,0,?,0)",
                          [(ahora, "marvel", "www.amazon.es", "Fantasy Flight Games Marvel Champions Era de Apocalipsis",
                            "https://www.amazon.es/dp/B091Q2GGMR", 40.33, sid),
                           (ahora, "marvel", "www.amazon.es", "Asmodee Marvel Champions Civil War Expansion",
                            "https://www.amazon.es/dp/B0AAAAAAAA", 43.65, sid)])
        historico.guarda("B091Q2GGMR", historico.parsea(GRANDE))
        por_asin = {p["amazon"]["asin"]: p["amazon"] for p in referencia.resumen("vigiladas") if p["amazon"]}
        self.assertEqual(por_asin["B091Q2GGMR"]["camel"]["minimo"], 33.09)
        self.assertTrue(por_asin["B091Q2GGMR"]["camel"]["frases"])
        self.assertFalse(any("no se puede calcular" in f for f in por_asin["B091Q2GGMR"]["camel"]["frases"]))   # el aviso va una vez, no en cada bloque
        self.assertIsNone(por_asin["B0AAAAAAAA"]["camel"])


class PaginaSinErroresConocidos(unittest.TestCase):
    def test_get_settings_se_llama_sobre_su_pista(self):
        """`(pista||{}).getSettings` separado de la pista da «Illegal invocation» en el navegador (v0.17.23)."""
        html = open(os.path.join(os.path.dirname(web.__file__), "pagina.html"), encoding="utf-8").read()
        self.assertNotIn("||{}).getSettings", html)
        self.assertIn("pista.getSettings()", html)


# Lo que el lector sacó de capturas REALES de la pantalla (solo las líneas de la gráfica): la leyenda sale con la letra deformada
# («4,99» por «44,99», «62,06» por «52,06», «01,48» por «31,48»), a veces sin «Lowest», y las etiquetas de colores de la derecha
# salen bien. Valores esperados: los de las etiquetas laterales.
CAPTURAS = {
    "heroes": ("Fantasy Flight Games - Marvel Champions: Héroes Reunidos 2\n----- €5206\n(44,99\n(31,48\n€55\n€50\n(45\n€40\n€35\n€30\n"
               "Highest\n62,06 (Aug 29, 2026)\nPrice type\nAmazon\n01,48 (Nov 20, 2025)\nCurrent\n€44.99 (Nov 15.2026)",
               (31.48, "2025-11-20", 52.06, "2026-08-29", 44.99)),
    "proxima": ("Marvel Champions LCG - La próXima evolución\n(43,49\n€50\n€45\n(40\n€35\n€30\n€25\n------ €48,96\nHighest\n«8,96 (Sep 24.2024)\n"
                "Current\n€43.49 (Nov 15.2026)\nPrice type\nAmazon\n€29,99 (Mar 10, 2026)",
                (29.99, "2026-03-10", 48.96, "2024-09-24", 43.49)),
    "sombra": ("€55\n€50\n(45\n€40\n€35\n€30\nPrice type\nAmazon\n€32.89 (Mar 20, 2024)\nHighest\n62,95 (Oct 1, 2024)\n"
               "Current\n€44.99 (Nov 15.2026)\n€5Z95\n(32,89\n(44,99",
               (32.89, "2024-03-20", 52.95, "2024-10-01", 44.99)),
    "civil": ("€70\n€60\n€50\n€40\n€30\n€20\nPrice type\nAmazon\n€44,99 (Dec 14, 2025)\nHighest\n«4,99 (Dec 14.2025)\nCurrent\n€44.99 (Nov 15.2026)\n€44,99",
              (44.99, "2025-12-14", 44.99, "2025-12-14", 44.99)),
}


class CapturasReales(unittest.TestCase):
    def test_cada_captura_da_sus_extremos_y_pasa_el_control(self):
        for nombre, (texto, esperado) in CAPTURAS.items():
            d, _ = historico.repara(texto, historico.parsea(texto))
            self.assertEqual((d.get("minimo"), d.get("fecha_minimo"), d.get("maximo"), d.get("fecha_maximo"), d.get("actual")), esperado, nombre)
            self.assertEqual(historico.valida(texto, d), [], nombre)

    def test_se_dice_que_cifra_se_corrigio(self):
        texto = CAPTURAS["proxima"][0]
        _, cambios = historico.repara(texto, historico.parsea(texto))
        self.assertTrue(cambios and "8,96" in cambios[0] and "48,96" in cambios[0])

    def test_lo_que_ya_cuadra_no_se_toca(self):
        d, cambios = historico.repara(GRANDE, historico.parsea(GRANDE))
        self.assertEqual((d["minimo"], d["maximo"], cambios), (33.09, 48.98, []))

    def test_parecido(self):
        self.assertTrue(historico.parecido(4.99, 44.99))      # se perdió la primera cifra
        self.assertTrue(historico.parecido(62.95, 52.95))     # una cifra distinta
        self.assertTrue(historico.parecido(1.48, 31.48))
        self.assertFalse(historico.parecido(30.68, 0.68))
        self.assertFalse(historico.parecido(40.00, 44.99))

    def test_importes_sueltos_con_la_coma_perdida_y_letras_confundidas(self):
        self.assertEqual(historico.importes_sueltos("€5Z95\n(32,89\n----- €5206\n€50\n(45"), [52.95, 32.89, 52.06])
