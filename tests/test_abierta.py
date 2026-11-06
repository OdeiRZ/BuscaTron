import base64
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import abierta, arranque, seguimiento  # noqa: E402


class Direcciones(unittest.TestCase):
    def test_desenvuelve_bing(self):
        real = "https://dungeonmarvels.com/495-marvel-champions"
        u = "a1" + base64.urlsafe_b64encode(real.encode()).decode().rstrip("=")
        self.assertEqual(abierta._desenvuelve_bing(f"https://www.bing.com/ck/a?!&amp;&amp;p=x&amp;u={u}&amp;ntb=1"), real)
        self.assertEqual(abierta._desenvuelve_bing("https://tienda.es/x"), "https://tienda.es/x")

    def test_desenvuelve_duckduckgo_y_descarta_anuncios(self):
        self.assertEqual(abierta._desenvuelve_ddg("//duckduckgo.com/l/?uddg=https%3A%2F%2Ftienda.es%2Fx&rut=abc"), "https://tienda.es/x")
        self.assertEqual(abierta._desenvuelve_ddg("//duckduckgo.com/l/?uddg=https%3A%2F%2Fduckduckgo.com%2Fy.js%3Fad_domain%3Damazon.es"), "")

    def test_dominio(self):
        self.assertEqual(abierta._dominio("https://www.Tienda.es:443/x?y=1"), "tienda.es")

    def test_regiones(self):
        self.assertTrue(abierta._region_ok("tienda.es", "es"))
        self.assertTrue(abierta._region_ok("tienda.com", "es"))       # genérico: no dice el país
        self.assertFalse(abierta._region_ok("tienda.fr", "es"))
        self.assertTrue(abierta._region_ok("tienda.fr", "ue"))
        self.assertFalse(abierta._region_ok("tienda.co.uk", "ue"))
        self.assertFalse(abierta._region_ok("tienda.jp", "ue"))
        self.assertTrue(abierta._region_ok("tienda.jp", "mundo"))


class Busca(unittest.TestCase):
    def test_filtra_webs_conocidas_bloqueadas_o_que_no_son_tiendas(self):
        urls = ["https://nueva.es/p/1", "https://www.tuya.es/p/2", "https://www.amazon.es/dp/3", "https://es.wikipedia.org/wiki/X",
                "https://otra.fr/p/4", "https://nueva.es/p/5", "https://nueva.es/p/6", "https://youtube.com/watch"]
        leidas = []

        def lee(url, consulta):
            leidas.append(url)
            return 200, [{"titulo": "Juego " + url[-1], "url": url, "precio": 10.0, "agotado": False, "preventa": False, "estado": "",
                          "tienda": abierta._dominio(url)}]
        with mock.patch.object(abierta, "buscadores", lambda *a, **k: (urls, [])), mock.patch.object(abierta, "_lee_pagina", lee):
            items, info = abierta.busca("juego", region="es", excluir_hosts={"tuya.es"})
        self.assertEqual(sorted(leidas), ["https://nueva.es/p/1", "https://nueva.es/p/5"])   # 2 por dominio; sin conocidas, bloqueadas, redes ni otros países
        self.assertEqual(len(items), 2)
        self.assertIsNone(info)

    def test_sin_buscador_da_un_mensaje_claro(self):
        with mock.patch.object(abierta, "buscadores", lambda *a, **k: ([], ["Bing: HTTP 429"])):
            items, info = abierta.busca("juego")
        self.assertEqual(items, [])
        self.assertIn("Bing: HTTP 429", info)


class OpcionesSeguimiento(unittest.TestCase):
    def test_se_normalizan_las_opciones(self):
        o = seguimiento._opciones({"preventas": 1, "abierta": True, "region": "marte", "paginas": "9", "con_envio": ""})
        self.assertEqual(o, {"preventas": True, "con_envio": False, "segunda_mano": False, "abierta": True, "region": "es", "paginas": 6})
        self.assertIsNone(seguimiento._opciones(None)["paginas"])

    def test_opciones_de_un_seguimiento_antiguo(self):
        self.assertEqual(seguimiento.opciones_de({"opciones": None}), seguimiento.OPCIONES)
        self.assertEqual(seguimiento.opciones_de({"opciones": "esto no es json"}), seguimiento.OPCIONES)


class Arranque(unittest.TestCase):
    def test_comillas_para_powershell(self):
        self.assertEqual(arranque._q("C:\\Users\\O'Neil\\x"), "C:\\Users\\O''Neil\\x")

    def test_activo_segun_exista_el_acceso_directo(self):
        with mock.patch.object(arranque, "disponible", lambda: True), mock.patch.object(arranque, "ruta_acceso", lambda: __file__):
            self.assertTrue(arranque.activo())
        with mock.patch.object(arranque, "disponible", lambda: True), mock.patch.object(arranque, "ruta_acceso", lambda: __file__ + ".no"):
            self.assertFalse(arranque.activo())


if __name__ == "__main__":
    unittest.main()
