"""Auditoría v0.11.4: cambios de tiendas durante una búsqueda, escrituras seguras, errores del servidor y Bixoto."""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import abierta, ajustes, bd, motor, tiendas as cfg, web  # noqa: E402


class ConArchivos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.parches = [mock.patch.object(cfg, "RUTA", os.path.join(self.tmp, "tiendas.json")),
                        mock.patch.object(ajustes, "RUTA", os.path.join(self.tmp, "config.json")),
                        mock.patch.object(bd, "RUTA", os.path.join(self.tmp, "t.db"))]
        for p in self.parches:
            p.start()
        cfg.guarda([{"host": "a.es", "activa": True, "plantilla": None}, {"host": "b.es", "activa": True, "plantilla": None}])

    def tearDown(self):
        for p in self.parches:
            p.stop()


class TiendasDuranteUnaBusqueda(ConArchivos):
    def test_lo_que_cambias_mientras_busca_no_se_pierde(self):
        def tienda(t, consulta, nav, paginas):
            if t["host"] == "a.es":
                web.Handler._tiendas(web.Handler.__new__(web.Handler), {"activas": ["b.es"]})   # el usuario desactiva a.es mientras se busca
                t["plantilla"] = "https://a.es/buscar?q={q}"               # y la búsqueda descubre el buscador de a.es
            return t["host"], [], motor.SIN_COINCIDENCIAS
        with mock.patch.object(motor, "_tienda", tienda), mock.patch.object(motor.navegador, "disponible", lambda: False):
            motor.buscar("algo")
        lista = {t["host"]: t for t in cfg.carga()}
        self.assertFalse(lista["a.es"]["activa"])                                   # el cambio del usuario sigue ahí
        self.assertEqual(lista["a.es"]["plantilla"], "https://a.es/buscar?q={q}")    # y lo descubierto también


class EscriturasSeguras(ConArchivos):
    def test_leer_mientras_se_guarda_nunca_ve_un_archivo_a_medias(self):
        errores, parar = [], threading.Event()

        def lee():
            while not parar.is_set():
                try:
                    ajustes.carga()
                    cfg.carga()
                except (ValueError, OSError) as e:
                    errores.append(e)
        hilo = threading.Thread(target=lee)
        hilo.start()
        try:
            for i in range(150):
                ajustes.guarda({"paginas": i % 6 + 1})
                cfg.guarda([{"host": f"t{j}.es", "activa": True, "plantilla": None} for j in range(30)])
        finally:
            parar.set()
            hilo.join()
        self.assertEqual(errores, [])
        self.assertEqual(len(cfg.carga()), 30)


class DireccionHttps(unittest.TestCase):
    def test_lee_la_de_tailscale_serve(self):
        salida = json.dumps({"Web": {"pc.tail1.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8790"}}}}})
        web._https["ts"] = 0
        with mock.patch.object(web.os.path, "exists", lambda p: True), \
                mock.patch.object(web.subprocess, "run", lambda *a, **k: mock.Mock(stdout=salida)):
            self.assertEqual(web.direccion_https(8790), "https://pc.tail1.ts.net")
            web._https["ts"] = 0
            self.assertIsNone(web.direccion_https(9000))          # publica otro puerto, no BuscaTron
        web._https["ts"] = 0


class ErroresDelServidor(ConArchivos):
    def test_un_fallo_inesperado_responde_con_su_error(self):
        srv = web.Servidor(("127.0.0.1", 0), web.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            with mock.patch.object(web.fetch, "get", side_effect=OSError("tiempo agotado")):
                req = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}/api/envio_detectar",
                                             data=json.dumps({"host": "a.es"}).encode())
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(req, timeout=10)
            self.assertEqual(e.exception.code, 500)
            self.assertIn("tiempo agotado", json.load(e.exception)["error"])
        finally:
            srv.shutdown()
            srv.server_close()


class BusquedaAbierta(unittest.TestCase):
    def test_nunca_consulta_las_tiendas_que_bloquean(self):
        urls = ["https://bixoto.com/es/p/1", "https://www.ferreteriaibermadrid.es/x", "https://otra.es/y"]
        leidas = []
        with mock.patch.object(abierta, "buscadores", lambda *a, **k: (urls, [])), \
                mock.patch.object(abierta, "_lee_pagina", lambda u, c: (leidas.append(u), (200, []))[1]):
            abierta.busca("civil war", excluir_hosts=set())
        self.assertEqual(leidas, ["https://otra.es/y"])

    def test_sin_precios_no_es_una_caida(self):
        with mock.patch.object(abierta, "busca", lambda *a, **k: ([], "no encontré precios en las 3 webs revisadas")), \
                mock.patch.object(motor, "_tienda", lambda t, *a: (t["host"], [], None)):
            tmp = tempfile.mkdtemp()
            with mock.patch.object(bd, "RUTA", os.path.join(tmp, "t.db")), mock.patch.object(cfg, "RUTA", os.path.join(tmp, "t.json")), \
                    mock.patch.object(ajustes, "RUTA", os.path.join(tmp, "c.json")):
                cfg.guarda([])
                _, informe = motor.buscar("civil war", abierta=True)
        self.assertFalse(informe["Búsqueda abierta"]["caida"])


if __name__ == "__main__":
    unittest.main()
