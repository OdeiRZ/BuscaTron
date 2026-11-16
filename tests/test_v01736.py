"""v0.17.36: Telegram solo avisa si hay cambios (un aviso de objetivo o un cambio de límites), nunca como resumen."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, historico, motor, referencia, seguimiento  # noqa: E402

TITULO = "Marvel Champions: La Tiranía del Cráneo Rojo"
ASIN = "B08VW72D4F"


class ConBD(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()
        historico.guarda(ASIN, {"minimo": 33.73, "fecha_minimo": "2023-03-27", "maximo": 48.64, "fecha_maximo": "2024-11-04", "actual": 44.99})

    def tearDown(self):
        self.p.stop()

    def prod(self, precio, tienda="www.amazon.es", asin=ASIN):
        return {"titulo": TITULO, "precio": precio, "tienda": tienda, "url": f"https://{tienda}/dp/{asin}" if "amazon" in tienda else f"https://{tienda}/craneo"}


class LimitesDe(ConBD):
    def test_dentro_de_sus_limites_no_hay_cambio(self):
        self.assertEqual(referencia.limites_de([self.prod(40.0)]), [])

    def test_por_debajo_del_minimo_historico(self):
        c = referencia.limites_de([self.prod(31.0)])
        self.assertEqual([(x["tipo"], x["valor"], x["limite"]) for x in c], [("min", 31.0, 33.73)])
        self.assertIn("nuevo mínimo histórico", referencia.texto_limite(c[0]))
        self.assertIn("27/03/2023", referencia.texto_limite(c[0]))

    def test_por_encima_del_maximo_historico(self):
        c = referencia.limites_de([self.prod(52.0)])
        self.assertEqual([(x["tipo"], x["limite"]) for x in c], [("max", 48.64)])
        self.assertIn("nuevo máximo histórico", referencia.texto_limite(c[0]))

    def test_no_se_repite_el_mismo_limite_pero_si_va_mas_lejos(self):
        referencia.marca_limites(referencia.limites_de([self.prod(31.0)]))
        self.assertEqual(referencia.limites_de([self.prod(31.0)]), [])             # el mismo: ya se avisó
        self.assertEqual(referencia.limites_de([self.prod(32.0)]), [])             # menos lejos: tampoco
        self.assertEqual(len(referencia.limites_de([self.prod(29.5)])), 1)         # más bajo: sí

    def test_otras_tiendas_mas_baratas_que_amazon_no_son_un_cambio(self):
        """Zacatrus a 31 € por debajo del mínimo de Amazon no es un cambio de límites: las tiendas casi siempre son más baratas."""
        self.assertEqual(referencia.limites_de([self.prod(31.0, tienda="zacatrus.es")]), [])

    def test_una_ficha_de_amazon_sin_historico_leido_no_cuenta(self):
        self.assertEqual(referencia.limites_de([self.prod(10.0, asin="B0AAAAAAAA")]), [])

    def test_de_varias_ofertas_de_la_misma_ficha_vale_la_mas_barata(self):
        c = referencia.limites_de([self.prod(32.0), self.prod(31.0), self.prod(40.0)])
        self.assertEqual([x["valor"] for x in c], [31.0])

    def test_sin_historico_leido_no_hay_nada_que_comparar(self):
        with bd.conecta() as c:
            c.execute("DELETE FROM camel_extremos")
        self.assertEqual(referencia.limites_de([self.prod(10.0)]), [])


class Aviso(ConBD):
    def envia(self, canales="app,telegram", res=None):
        enviados = []
        seg = {"nombre": "Cráneo Rojo", "canales": canales}
        with mock.patch.object(seguimiento.notifica, "envia", lambda c, a, t: enviados.append((c, a, t)) or {k: None for k in c}):
            seguimiento._avisa_limites(seg, res if res is not None else [self.prod(31.0)])
        return enviados

    def test_manda_el_cambio_por_telegram_una_sola_vez(self):
        e = self.envia()
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0][0], ["telegram"])
        self.assertIn("cambio de límites", e[0][1])
        self.assertIn("nuevo mínimo histórico", e[0][2])
        self.assertEqual(self.envia(), [])                                              # la siguiente revisión no lo repite

    def test_sin_cambios_no_manda_nada(self):
        self.assertEqual(self.envia(res=[self.prod(40.0)]), [])

    def test_sin_telegram_ni_correo_no_manda_nada(self):
        self.assertEqual(self.envia(canales="app"), [])

    def test_si_no_llega_se_vuelve_a_intentar(self):
        seg = {"nombre": "x", "canales": "telegram"}
        with mock.patch.object(seguimiento.notifica, "envia", lambda c, a, t: {"telegram": "sin conexión"}):
            seguimiento._avisa_limites(seg, [self.prod(31.0)])
        self.assertEqual(len(self.envia(canales="telegram")), 1)                         # no se anotó: se avisa ahora


class SinResumen(unittest.TestCase):
    def test_la_pagina_ya_no_ofrece_el_resumen(self):
        html = open(os.path.join(os.path.dirname(seguimiento.__file__), "pagina.html"), encoding="utf-8").read()
        self.assertNotIn("s-resumen", html)


if __name__ == "__main__":
    unittest.main()
