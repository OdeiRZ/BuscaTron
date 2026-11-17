"""v0.17.37: una web cuyo certificado no valida Python (pero sí Chrome) se lee con el navegador; otros fallos siguen siendo «no responde»."""
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, extract, motor  # noqa: E402

HTML = '<a href="https://comicstores.es/p/1">Marvel Champions Civil War</a><span>40,49 €</span>'


class Certificado(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_sin_certificado_valido_se_usa_el_navegador(self):
        t = {"host": "comicstores.es", "plantilla": "https://comicstores.es/?s={q}"}
        malo = urllib.error.URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
        with mock.patch.object(motor.fetch, "get", side_effect=malo), mock.patch.object(motor.navegador, "get", lambda u, **k: (200, HTML)):
            h, items, err = motor._tienda_base(t, "marvel champions", nav={"visible": False})
        self.assertEqual((err, [x["precio"] for x in items]), (None, [40.49]))
        self.assertTrue(t.get("js"))                                   # la próxima vez, directamente con el navegador

    def test_sin_navegador_sigue_siendo_un_fallo(self):
        t = {"host": "comicstores.es", "plantilla": "https://comicstores.es/?s={q}"}
        malo = urllib.error.URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
        with mock.patch.object(motor.fetch, "get", side_effect=malo):
            _, items, err = motor._tienda_base(t, "marvel champions", nav=None)
        self.assertEqual(items, [])
        self.assertIn("no se pudo conectar", err)

    def test_otro_fallo_de_conexion_no_usa_el_navegador(self):
        t = {"host": "somosjuegos.com", "plantilla": "https://somosjuegos.com/?s={q}"}
        usado = []
        with mock.patch.object(motor.fetch, "get", side_effect=ConnectionResetError("Remote end closed connection")), \
                mock.patch.object(motor.navegador, "get", lambda u, **k: usado.append(u) or (200, HTML)):
            _, items, err = motor._tienda_base(t, "marvel champions", nav={"visible": False})
        self.assertEqual((items, usado), ([], []))                    # un rechazo no se esquiva con el navegador


if __name__ == "__main__":
    unittest.main()
