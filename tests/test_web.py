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


class YaAbierto(unittest.TestCase):
    def test_si_ya_hay_uno_abre_su_web_en_vez_de_fallar(self):
        with mock.patch.object(web, "Servidor", side_effect=OSError(98, "puerto ocupado")), mock.patch.object(web, "_ya_hay_uno", lambda p: True),                 mock.patch.object(web.webbrowser, "open") as abre:
            web.sirve(8790, "0.0.0.0", abrir=True)
        abre.assert_called_once_with("http://127.0.0.1:8790")

    def test_si_el_puerto_lo_usa_otra_cosa_falla_con_un_mensaje(self):
        with mock.patch.object(web, "Servidor", side_effect=OSError(98, "puerto ocupado")), mock.patch.object(web, "_ya_hay_uno", lambda p: False):
            with self.assertRaises(SystemExit):
                web.sirve(8790, "0.0.0.0", abrir=True)
        with mock.patch.object(web, "Servidor", side_effect=OSError(98, "puerto ocupado")), mock.patch.object(web, "_ya_hay_uno", lambda p: True):
            with self.assertRaises(SystemExit):                     # sin --abrir no se asume nada
                web.sirve(8790, "0.0.0.0", abrir=False)


class BusquedaEnSegundoPlano(unittest.TestCase):
    def setUp(self):
        web.TRABAJOS.clear()

    def espera(self, tid):
        import time
        for _ in range(200):
            r = web.estado_trabajo(tid)
            if r["estado"] != "buscando":
                return r
            time.sleep(0.01)
        self.fail("la búsqueda no terminó")

    def test_devuelve_un_numero_al_instante_y_el_resultado_despues(self):
        import time
        def lenta(c):
            time.sleep(0.2)
            return {"resultados": [1, 2], "total": 2}
        with mock.patch.object(web, "busca", lenta):
            r = web.lanza_busqueda({"q": "x"})
            self.assertEqual(web.estado_trabajo(r["trabajo"])["estado"], "buscando")
            fin = self.espera(r["trabajo"])
        self.assertEqual((fin["estado"], fin["resp"]["total"]), ("hecho", 2))

    def test_un_error_se_cuenta_en_vez_de_perderse(self):
        def rota(c):
            raise ValueError("falla la tienda")
        with mock.patch.object(web, "busca", rota):
            fin = self.espera(web.lanza_busqueda({"q": "x"})["trabajo"])
        self.assertEqual((fin["estado"], fin["error"]), ("error", "falla la tienda"))

    def test_numero_desconocido(self):
        self.assertEqual(web.estado_trabajo("no-existe"), {"estado": "desconocido"})

    def test_los_trabajos_viejos_se_limpian(self):
        web.TRABAJOS["viejo"] = {"estado": "hecho", "resp": {}, "ts": 0}
        with mock.patch.object(web, "busca", lambda c: {}):
            self.espera(web.lanza_busqueda({"q": "x"})["trabajo"])
        self.assertNotIn("viejo", web.TRABAJOS)


if __name__ == "__main__":
    unittest.main()
