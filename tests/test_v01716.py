"""v0.17.16: leer el mínimo y el máximo históricos de la gráfica de camelcamelcamel que pega el usuario (lector de Windows)."""
import datetime
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import historico, ocr, web  # noqa: E402

TEXTO = "Amazon: Actual 94,47 EUR MAS alto 102,86 EUR (12 nov. 2026)\nMAS bajo 61,50 EUR (24 nov. 2025) Media 84,12 EUR"


class Parseo(unittest.TestCase):
    def test_extremos_con_decimales_y_fechas(self):
        d = historico.parsea(TEXTO)
        self.assertEqual((d["minimo"], d["fecha_minimo"], d["maximo"], d["fecha_maximo"], d["media"], d["actual"]),
                         (61.5, "2025-11-24", 102.86, "2026-11-12", 84.12, 94.47))

    def test_formatos_en_ingles_y_miles(self):
        d = historico.parsea("Lowest 12.99 € (Nov 24, 2025) Highest 1.299,00 € (12/03/2024) Average 20,10")
        self.assertEqual((d["minimo"], d["fecha_minimo"], d["maximo"], d["fecha_maximo"], d["media"]), (12.99, "2025-11-24", 1299.0, "2024-03-12", 20.1))

    def test_sin_nada_legible(self):
        self.assertEqual(historico.parsea("gráfica sin etiquetas 2025 2026"), {})

    def test_campana_del_minimo_y_proxima(self):
        f = historico.frases(historico.parsea(TEXTO), datetime.date(2026, 11, 15))
        self.assertTrue(any("Black Friday de 2025" in x and "27/11" in x and "12 días" in x for x in f))

    def test_no_promete_la_frecuencia_de_las_bajadas(self):
        f = historico.frases(historico.parsea(TEXTO), datetime.date(2026, 11, 15))
        self.assertIn("no se puede calcular cada cuánto", f[-1])

    def test_en_su_minimo(self):
        f = historico.frases({"minimo": 50, "actual": 50.1, "maximo": 80}, datetime.date(2026, 11, 15))
        self.assertTrue(any("en su mínimo histórico" in x for x in f))


class Imagen(unittest.TestCase):
    def test_decodifica(self):
        self.assertEqual(ocr.decodifica("data:image/png;base64,aGk="), b"hi")
        with self.assertRaises(ValueError):
            ocr.decodifica("hola")

    def test_endpoint_lee_parsea_y_no_pide_nada_a_camel(self):
        with mock.patch.object(ocr, "lee", lambda b: TEXTO), mock.patch("urllib.request.urlopen", side_effect=AssertionError("no debía haber red")):
            r = web.Handler._post(web.Handler.__new__(web.Handler), "/api/grafica", {"imagen": "data:image/png;base64,aGk="})
        self.assertEqual(r["datos"]["minimo"], 61.5)
        self.assertTrue(r["frases"])

    @unittest.skipUnless(os.name == "nt", "solo en Windows")
    def test_lector_de_windows_de_verdad(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            png, ps1 = os.path.join(d, "t.png"), os.path.join(d, "t.ps1")
            with open(ps1, "w", encoding="utf-8-sig") as f:
                f.write("\n".join(["param($ruta)", "Add-Type -AssemblyName System.Drawing",
                                   "$b = New-Object System.Drawing.Bitmap 500,60",
                                   "$g = [System.Drawing.Graphics]::FromImage($b)",
                                   "$g.Clear([System.Drawing.Color]::White)",
                                   "$g.DrawString('Lowest 61,50 EUR', (New-Object System.Drawing.Font('Arial',10)), [System.Drawing.Brushes]::Black, 10, 20)",
                                   "$b.Save($ruta)"]))
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, png], check=True, capture_output=True, timeout=60)
            self.assertIn("61,50", ocr.lee(open(png, "rb").read()))


if __name__ == "__main__":
    unittest.main()
