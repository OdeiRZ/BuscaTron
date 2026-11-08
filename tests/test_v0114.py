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


class RevisionQueFalla(ConArchivos):
    def test_se_anota_para_no_repetirla_cada_minuto(self):
        from buscatron import seguimiento
        sid = seguimiento.guarda({"consulta": "civil war", "objetivo": "30"})
        with mock.patch.object(motor, "buscar", side_effect=RuntimeError("se rompió")):
            with self.assertRaises(RuntimeError):
                seguimiento.revisa(sid)
        s = seguimiento.lista()[0]
        self.assertIn("la revisión falló: se rompió", s["estado"])
        self.assertEqual(seguimiento.pendientes(), [])          # no le vuelve a tocar hasta dentro de 12 h


class PaginasLimitadas(ConArchivos):
    def test_nunca_mas_de_6_paginas_por_tienda(self):
        vistas = []
        ajustes.guarda({"paginas": 50})
        with mock.patch.object(motor, "_tienda", lambda t, c, nav, paginas: (vistas.append(paginas), (t["host"], [], None))[1]), \
                mock.patch.object(motor.navegador, "disponible", lambda: False):
            motor.buscar("algo")
            motor.buscar("algo", paginas="abc")
        self.assertEqual(set(vistas[:2]), {6})
        self.assertEqual(set(vistas[2:]), {1})


class Recordatorio(ConArchivos):
    def test_si_telegram_falla_se_reintenta(self):
        from buscatron import importar, programador
        ajustes.guarda({"telegram_token": "t", "telegram_chat": "1"})
        cfg.guarda([{"host": "f.es", "activa": True, "plantilla": "https://f.es/?q={q}", "manual": True}])
        importar.guarda("f.es", "civil war", [{"titulo": "Civil War", "precio": 30}], "https://f.es/?q=civil+war")
        with bd.conecta() as c:
            c.execute("UPDATE importados SET ts = ts - 65 * 3600")         # caduca dentro de 7 h
        with mock.patch.object(programador.notifica, "envia", lambda *a: {"telegram": "sin conexión"}):
            programador.recordatorios()
        self.assertEqual(len(importar.por_caducar()), 1)                   # no se da por avisado
        with mock.patch.object(programador.notifica, "envia", lambda *a: {"telegram": None}):
            programador.recordatorios()
        self.assertEqual(importar.por_caducar(), [])


class PreciosConMiles(unittest.TestCase):
    def test_punto_de_miles_y_punto_decimal(self):
        from buscatron import extract, importar
        casos = {"1.299 €": 1299, "2.500€": 2500, "€ 1.299": 1299, "1.299,00 €": 1299, "29,99 €": 29.99, "29.99 €": 29.99,
                 "1.50 €": 1.5, "12 €": 12}
        for texto, esperado in casos.items():
            html = f'<a href="/p/x">Mesa de juego</a><span>{texto}</span>'
            self.assertEqual(extract.extrae(html, "https://t.es/", "mesa de juego")[0]["precio"], esperado, texto)
            self.assertEqual(importar._precios(texto), [esperado], texto)


class SugerenciaDelBuscador(unittest.TestCase):
    def test_en_lugar_de_lo_anterior_no_es_un_producto(self):
        from buscatron import extract
        base = "https://www.amazon.es/s?k=Eternal+decks&s=price-asc-rank"
        html = ('<span>Mostrando resultados de eternal desk</span>'
                '<a href="/s?k=Eternal+decks&s=price-asc-rank&dc=">En lugar de lo anterior, busca Eternal decks</a>'
                '<a href="/dp/B0ABCDEFGH/ref=sr_1_1">Caja Eternal Decks para cartas</a><span>9,99 €</span>')
        r = extract.extrae(html, base, "Eternal decks")
        self.assertEqual([(x["titulo"], x["precio"], x["url"]) for x in r],
                         [("Caja Eternal Decks para cartas", 9.99, "https://www.amazon.es/dp/B0ABCDEFGH")])

    def test_un_producto_con_otra_ruta_o_parametros_no_se_descarta(self):
        from buscatron import extract
        base = "https://t.es/index.php?controller=search&s=civil+war"
        self.assertFalse(extract.es_otra_busqueda("https://t.es/index.php?id_product=5&controller=product", base))
        self.assertTrue(extract.es_otra_busqueda("https://t.es/index.php?controller=search&s=civil+war&page=2", base))


class PalabrasCompletas(unittest.TestCase):
    def test_la_palabra_tiene_que_empezar_una_palabra_del_titulo(self):
        from buscatron import extract
        n = extract.normaliza
        self.assertFalse(extract.encaja(n("Tactical Advantage"), "vantage"))
        self.assertTrue(extract.encaja(n("Vantage (castellano)"), "vantage"))
        self.assertTrue(extract.encaja(n("Pack de cartas"), "carta"))                  # plurales y prefijos, como antes
        self.assertTrue(extract.encaja(n("Spider-Man: Marvel Champions"), "spiderman"))
        self.assertTrue(extract.encaja(n("Spiderman Marvel"), "spider man"))
        self.assertTrue(extract.encaja(n("La Tiranía de Cráneo Rojo"), "craneo rojo"))
        self.assertFalse(extract.encaja(n("Tacticaladvantage"), "vantage"))

    def test_una_frase_igual_a_la_busqueda_no_junta_productos_distintos(self):
        html = ('<a href="/p/1">Vantage</a><span>81,00 €</span>'
                '<a href="/p/2">Protector de pantalla Polar Vantage M3</a><span>9,00 €</span>'
                '<a href="/p/3">Tactical Advantage</a><span>0,25 €</span>')
        from buscatron import extract
        items = extract.extrae(html, "https://t.es/buscar?q=vantage", "vantage")
        self.assertEqual([x["titulo"] for x in items], ["Vantage", "Protector de pantalla Polar Vantage M3"])
        tmp = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(tmp, "t.db")), mock.patch.object(cfg, "RUTA", os.path.join(tmp, "t.json")), \
                mock.patch.object(ajustes, "RUTA", os.path.join(tmp, "c.json")), mock.patch.object(motor.navegador, "disponible", lambda: False), \
                mock.patch.object(motor, "_tienda", lambda t, *a: (t["host"], [dict(x) for x in items], None)):
            cfg.guarda([{"host": "t.es", "activa": True, "plantilla": "https://t.es/buscar?q={q}"}])
            res, _ = motor.buscar("Vantage", alguna="Vantage", castellano=False)
            self.assertEqual(len({x["grupo"] for x in res}), 2)                             # el juego y el protector, por separado
            res, _ = motor.buscar("juegos", alguna="vantage", castellano=False)             # frase que añade algo (campañas): agrupa
            self.assertEqual({x["grupo"] for x in res}, {"f:vantage"})


class AmazonEnJuguetes(ConArchivos):
    def test_cambia_la_direccion_de_siempre_pero_no_una_tuya(self):
        for propia, esperada in ((cfg.AMAZON_ANTES, cfg.CONOCIDAS["www.amazon.es"]),
                                 ("https://www.amazon.es/s?k={q}&i=videogames", "https://www.amazon.es/s?k={q}&i=videogames")):
            ajustes.guarda({"amazon_juguetes": False, "amazon_automatico": True})
            cfg.guarda([{"host": "www.amazon.es", "activa": True, "plantilla": propia, "js": True}])
            self.assertEqual(cfg.carga()[0]["plantilla"], esperada)
        self.assertIn("i=toys", cfg.CONOCIDAS["www.amazon.es"])


class EnlacesSeguros(unittest.TestCase):
    def test_solo_direcciones_web(self):
        from buscatron import extract
        html = ('<a href="javascript:alert(1)">Civil War malicioso</a><span>10,00 €</span>'
                '<a href="/p/civil-war">Civil War</a><span>20,00 €</span>')
        self.assertEqual([x["url"] for x in extract.extrae(html, "https://t.es/buscar", "civil war")], ["https://t.es/p/civil-war"])


class MinimoHistorico(ConArchivos):
    def test_si_el_precio_nunca_cambia_no_es_minimo_historico(self):
        import time
        for i, url in enumerate(("https://t.es/fijo", "https://t.es/baja")):
            for k, p in enumerate((20, 20, 20) if i == 0 else (25, 22, 20)):
                with bd.conecta() as c:
                    c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado) VALUES(?,?,?,?,?,?,0)",
                              (time.time() - 100 + k, "x", "a.es", "x", url, p))
        previo = motor.historial_previo({"https://t.es/fijo", "https://t.es/baja"})
        self.assertEqual(previo["https://t.es/fijo"], (20, 3, 20))
        self.assertEqual(previo["https://t.es/baja"], (20, 3, 25))


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
