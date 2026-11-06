import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import ajustes, web  # noqa: E402


class Red(unittest.TestCase):
    def test_solo_se_admiten_ips_de_red_local(self):
        for ip in ("127.0.0.1", "::1", "192.168.0.28", "10.0.0.5", "172.16.3.4", "100.80.22.18", "::ffff:192.168.0.9"):
            self.assertTrue(web.ip_permitida(ip), ip)
        for ip in ("8.8.8.8", "81.34.2.1", "2001:4860:4860::8888", "no-es-una-ip"):
            self.assertFalse(web.ip_permitida(ip), ip)

    def test_es_local(self):
        self.assertTrue(web.es_local("127.0.0.1"))
        self.assertFalse(web.es_local("192.168.0.28"))


class Direcciones(unittest.TestCase):
    def test_dominio(self):
        self.assertEqual(web.analiza_direccion("https://www.tienda.es/ofertas"), ("www.tienda.es", None))
        self.assertEqual(web.analiza_direccion("  tienda.es "), ("tienda.es", None))

    def test_url_de_busqueda(self):
        host, pl = web.analiza_direccion("tienda.es/buscar?q={q}")
        self.assertEqual((host, pl), ("tienda.es", "https://tienda.es/buscar?q={q}"))

    def test_no_valida(self):
        for malo in ("", "   ", "sinpunto"):
            with self.assertRaises(ValueError):
                web.analiza_direccion(malo)


class Sesion(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(ajustes, "RUTA", os.path.join(tempfile.mkdtemp(), "config.json"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_token_depende_del_pin_y_es_estable(self):
        a, b = web.token_sesion("1234"), web.token_sesion("1234")
        self.assertEqual(a, b)
        self.assertNotEqual(a, web.token_sesion("4321"))

    def test_secreto_no_se_expone(self):
        web.token_sesion("1234")
        self.assertNotIn("secreto", ajustes.publico())
        ajustes.guarda({"secreto": "manipulado"})
        self.assertNotEqual(ajustes.secreto(), "manipulado")

    def test_pin_enmascarado_y_no_se_pisa(self):
        ajustes.guarda({"pin": "1234"})
        self.assertEqual(ajustes.publico()["pin"], "********")
        ajustes.guarda({"pin": "********"})
        self.assertEqual(ajustes.carga()["pin"], "1234")


if __name__ == "__main__":
    unittest.main()
