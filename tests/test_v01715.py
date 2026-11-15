"""v0.17.15: análisis del precio de Amazon (mínimo, máximo, bajadas, estimación y fiabilidad)."""
import datetime
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import analisis  # noqa: E402

HOY = time.mktime(datetime.date(2026, 11, 15).timetuple()) + 43200


def serie(precios_por_dia):
    """{días_atrás: precio} → [(ts, precio)]"""
    return [(HOY - d * 86400, p) for d, p in sorted(precios_por_dia.items(), reverse=True)]


class Analisis(unittest.TestCase):
    def test_sin_datos(self):
        self.assertIsNone(analisis.analiza([]))

    def test_precio_plano_dice_que_no_hay_estimacion(self):
        r = analisis.analiza(serie({i: 44.99 for i in range(10)}), HOY)
        self.assertFalse(r["cambia"])
        self.assertEqual(r["fiabilidad"], "insuficiente")
        self.assertIsNone(r["proxima_bajada"])
        self.assertIn("no ha cambiado", r["frases"][0])

    def test_minimo_maximo_y_posicion(self):
        r = analisis.analiza(serie({10: 100, 5: 80, 0: 90}), HOY)
        self.assertEqual((r["minimo"], r["maximo"], r["actual"]), (80, 100, 90))
        self.assertEqual(r["posicion"], 50)
        self.assertEqual(r["fecha_minimo"], "2026-11-10")
        self.assertFalse(r["en_minimo"])

    def test_en_su_minimo(self):
        self.assertTrue(analisis.analiza(serie({10: 100, 5: 90, 0: 80}), HOY)["en_minimo"])

    def test_varias_consultas_el_mismo_dia_cuentan_una(self):
        s = [(HOY - 86400 * 2, 100), (HOY - 86400 * 2 + 600, 90), (HOY - 86400 * 2 + 1200, 95), (HOY, 100)]
        r = analisis.analiza(s, HOY)
        self.assertEqual(r["n_dias"], 2)
        self.assertEqual(r["minimo"], 90)

    def test_estimacion_de_bajadas_con_patron_semanal(self):
        p = {i: 100 for i in range(45)}
        for dias in (38, 31, 24, 17):          # cuatro bajadas, una por semana
            p[dias] = 85
        r = analisis.analiza(serie(p), HOY)
        self.assertEqual(len(r["bajadas"]), 4)
        self.assertEqual(r["proxima_bajada"]["mediana"], 7)
        self.assertEqual(r["fiabilidad"], "baja")        # cuatro eventos: pocos para fiarse
        self.assertTrue(any("Estimación de una bajada" in f for f in r["frases"]))

    def test_con_pocas_bajadas_no_se_inventa_una_fecha(self):
        p = {i: 100 for i in range(20)}
        p[5] = 80
        r = analisis.analiza(serie(p), HOY)
        self.assertEqual(r["fiabilidad"], "insuficiente")
        self.assertIsNone(r["proxima_bajada"])
        self.assertTrue(any("No hay bajadas suficientes" in f for f in r["frases"]))

    def test_una_bajada_pequena_no_cuenta(self):
        p = {i: 100 for i in range(10)}
        p[3] = 97
        self.assertEqual(analisis.analiza(serie(p), HOY)["bajadas"], [])

    def test_igual_que_la_mediana_no_dice_cero_por_ciento(self):
        r = analisis.analiza(serie({10: 100, 5: 80, 0: 100}), HOY)
        self.assertTrue(any("igual que la mediana" in f for f in r["frases"]))

    def test_black_friday_2026_y_calendario(self):
        self.assertEqual(analisis.black_friday(2026), datetime.date(2026, 11, 27))
        c = analisis.analiza(serie({3: 10, 0: 12}), HOY)["calendario"]
        self.assertEqual(c[0]["nombre"], "Black Friday")
        self.assertEqual(c[0]["en_dias"], 12)


if __name__ == "__main__":
    unittest.main()
