import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import ajustes, bd, motor, tiendas  # noqa: E402


class Idioma(unittest.TestCase):
    def test_detecta_otros_idiomas(self):
        for t in ("Marvel Champions: Civil War Expansion (Inglés)", "Hero pack ingles", "Jeu en Français", "Edición English"):
            self.assertTrue(motor.en_otro_idioma(t), t)

    def test_castellano_o_sin_marca_no_se_filtra(self):
        for t in ("Marvel Champions: Civil War (Castellano)", "Marvel Champions: Vision",
                  "Pack de héroe (Inglés / Castellano)", "Marvel Champions: Edición en español"):
            self.assertFalse(motor.en_otro_idioma(t), t)


def pagina(*productos, siguiente=None):
    lis = "".join(f'<a href="/p/{n}">Marvel Champions {n}</a><b>{pr} €</b>' for n, pr in productos)
    return (f'<link rel="next" href="{siguiente}">' if siguiente else "") + lis


class Paginacion(unittest.TestCase):
    TIENDA = {"host": "t.es", "plantilla": "https://t.es/buscar?q={q}"}

    def paginas(self, mapa):
        return lambda url: (200, mapa[url]) if url in mapa else (404, "")

    def test_sigue_las_paginas_siguientes(self):
        get = self.paginas({"https://t.es/buscar?q=marvel+champions": pagina(("a", 10), ("b", 11), siguiente="/pag2"),
                            "https://t.es/pag2": pagina(("c", 12), ("d", 13), siguiente="/pag3"),
                            "https://t.es/pag3": pagina(("e", 14))})
        self.assertEqual(len(motor._intenta(dict(self.TIENDA), "marvel champions", get, paginas=1)[0]), 2)
        self.assertEqual(len(motor._intenta(dict(self.TIENDA), "marvel champions", get, paginas=2)[0]), 4)
        self.assertEqual(len(motor._intenta(dict(self.TIENDA), "marvel champions", get, paginas=5)[0]), 5)

    def test_no_se_enreda_si_la_siguiente_repite_resultados(self):
        get = self.paginas({"https://t.es/buscar?q=marvel+champions": pagina(("a", 10), siguiente="/pag2"),
                            "https://t.es/pag2": pagina(("a", 10), siguiente="/pag3"),
                            "https://t.es/pag3": pagina(("b", 20))})
        self.assertEqual(len(motor._intenta(dict(self.TIENDA), "marvel champions", get, paginas=5)[0]), 1)


class Envio(unittest.TestCase):
    def test_envio_gratis_desde_un_importe(self):
        t = {"envio": 4.95, "envio_gratis": 50}
        self.assertEqual(motor.envio_de(t, 30), 4.95)
        self.assertEqual(motor.envio_de(t, 50), 0.0)
        self.assertEqual(motor.envio_de({"envio": 3}, 100), 3)
        self.assertIsNone(motor.envio_de({}, 20))


class Buscar(unittest.TestCase):
    """buscar() con las tiendas simuladas: filtros, preventas, envío e historial."""

    def setUp(self):
        d = tempfile.mkdtemp()
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),
                        mock.patch.object(tiendas, "guarda", lambda l: None)]
        for p in self.parches:
            p.start()
        ajustes.guarda({"usar_navegador": False, "segunda_mano_sembrada": True})
        self.lista = [{"host": "a.es", "activa": True, "tipo": "tienda", "envio": 5, "envio_gratis": 100},
                      {"host": "b.es", "activa": True, "tipo": "tienda"},
                      {"host": "usado.es", "activa": True, "tipo": "segunda_mano"}]
        self.items = {"a.es": [self.x("Juego A", 20), self.x("Juego P", 15, preventa=True), self.x("Juego Agotado", 5, agotado=True)],
                      "b.es": [self.x("Juego B", 24)],
                      "usado.es": [self.x("Juego Usado", 8, estado="bueno")]}
        self.parches += [mock.patch.object(tiendas, "carga", lambda: self.lista),
                         mock.patch.object(motor, "_tienda", lambda t, c, nav=None, paginas=1: (t["host"], [dict(i) for i in self.items[t["host"]]], None))]
        for p in self.parches[3:]:
            p.start()

    def tearDown(self):
        for p in self.parches:
            p.stop()

    @staticmethod
    def x(titulo, precio, **kw):
        return {"titulo": titulo, "url": "https://x/" + titulo.replace(" ", "-"), "precio": precio, "agotado": False, "preventa": False, "estado": "", **kw}

    def titulos(self, res):
        return [x["titulo"] for x in res]

    def test_por_defecto_oculta_preventas_agotados_y_segunda_mano(self):
        res, _ = motor.buscar("juego")
        self.assertEqual(self.titulos(res), ["Juego A", "Juego B"])

    def test_preventas_y_segunda_mano_son_opcionales(self):
        res, _ = motor.buscar("juego", preventas=True, segunda_mano=True)
        self.assertEqual(self.titulos(res), ["Juego Usado", "Juego P", "Juego A", "Juego B"])
        self.assertEqual({x["titulo"]: x["origen"] for x in res}["Juego Usado"], "segunda_mano")

    def test_total_con_envio_y_orden(self):
        res, _ = motor.buscar("juego", con_envio=True)
        self.assertEqual([(x["titulo"], x["total"], x["envio"]) for x in res], [("Juego B", 24, None), ("Juego A", 25, 5)])  # 20 + 5 > 24
        res, _ = motor.buscar("juego")                       # sin la opción, se ordena por precio
        self.assertEqual(self.titulos(res), ["Juego A", "Juego B"])

    def test_minimo_historico(self):
        for p in (30, 28, 26):                                # tres observaciones previas más caras
            with bd.conecta() as c:
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa) VALUES(?,?,?,?,?,?,?,?,?)",
                          (time.time() - 100 + p, "juego", "a.es", "Juego A", "https://x/Juego-A", p, 0, None, 0))
        res, _ = motor.buscar("juego")
        a = {x["titulo"]: x for x in res}
        self.assertTrue(a["Juego A"]["minimo"])               # 20 € es lo más barato que se le ha visto
        self.assertFalse(a["Juego B"]["minimo"])              # sin historial no hay mínimo


class VentanaSoloSiHaceFalta(unittest.TestCase):
    def test_solo_se_abre_la_ventana_para_la_tienda_que_pide_comprobacion(self):
        d = tempfile.mkdtemp()
        llamadas = []

        def tienda(t, consulta, nav=None, paginas=1):
            llamadas.append((t["host"], nav and nav["visible"]))
            if t["host"] == "pide.es" and not nav["visible"]:
                return t["host"], [], motor.DESAFIO
            return t["host"], [{"titulo": "Juego " + t["host"], "url": "https://x/" + t["host"], "precio": 10.0, "agotado": False,
                                "preventa": False, "estado": ""}], None
        lista = [{"host": "a.es", "activa": True}, {"host": "pide.es", "activa": True}, {"host": "b.es", "activa": True}]
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),                 mock.patch.object(tiendas, "carga", lambda: lista), mock.patch.object(tiendas, "guarda", lambda l: None),                 mock.patch.object(motor, "_tienda", tienda), mock.patch.object(motor.navegador, "disponible", lambda: True):
            ajustes.guarda({"usar_navegador": True, "navegador_visible": True, "segunda_mano_sembrada": True, "amazon_automatico": True})
            res, inf = motor.buscar("juego")
        self.assertEqual(sorted(h for h, v in llamadas if v is False), ["a.es", "b.es", "pide.es"])   # todo en segundo plano primero
        self.assertEqual([h for h, v in llamadas if v is True], ["pide.es"])                          # ventana solo para la que la pide
        self.assertEqual(len(res), 3)
        self.assertIsNone(inf["pide.es"]["error"])


class Historial(unittest.TestCase):
    def test_un_punto_por_revision_con_el_precio_mas_bajo(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")):
            with bd.conecta() as c:
                for ts, p, ag in ((100, 12, 0), (100, 10, 0), (200, 11, 0), (300, 9, 1)):   # el agotado no cuenta
                    c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa) VALUES(?,?,?,?,?,?,?,?,?)",
                              (ts, "q", "t.es", "Juego", "https://x/j", p, ag, None, 0))
            h = motor.historial_de("https://x/j")
        self.assertEqual([(q["ts"], q["precio"]) for q in h["puntos"]], [(100, 10), (200, 11)])
        self.assertEqual(motor.historial_de("https://x/nada")["puntos"], [])


if __name__ == "__main__":
    unittest.main()
