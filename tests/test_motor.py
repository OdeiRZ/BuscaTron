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

    def test_detecta_titulos_en_ingles_aunque_no_lo_digan(self):          # títulos de Amazon
        for t in ("Fantasy Flight Games, Marvel Champions: Hero Pack: Ms. Marvel, Card Game, 1 to 4 Players, Ages 14+, 40 to 70 Minutes Playing Time",
                  "Asmodee Juego 2 Players", "Game Ages 8 and up"):
            self.assertTrue(motor.en_otro_idioma(t), t)
        self.assertFalse(motor.en_otro_idioma("Marvel Champions Hero Pack (Castellano) para 1-4 jugadores, 40-70 minutos"))   # castellano gana
        self.assertFalse(motor.en_otro_idioma("Marvel Champions: Pack de Héroe Hulk"))

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

    def test_alguna_de_estas_palabras(self):
        res, _ = motor.buscar("juego", alguna="juego b, otra cosa", preventas=True)
        self.assertEqual(self.titulos(res), ["Juego B"])
        res, _ = motor.buscar("juego", alguna="  ,  ")                    # vacío: no filtra
        self.assertEqual(self.titulos(res), ["Juego A", "Juego B"])

    def test_alguna_ignora_espacios_y_puntos(self):                     # «shield» encuentra «S.H.I.E.L.D.»
        self.items["a.es"] = [self.x("Marvel Champions: Agentes de S.H.I.E.L.D.", 38)]
        res, _ = motor.buscar("juego", alguna="shield")
        self.assertEqual(self.titulos(res), ["Marvel Champions: Agentes de S.H.I.E.L.D."])

    def test_ocultos_no_salen_y_el_precio_de_mercado_usa_tambien_las_caras(self):
        motor.ignora("Juego B")
        self.items["b.es"] = [self.x("Juego A", 44)]
        self.items["a.es"] = [self.x("Juego A", 30), self.x("Juego B", 10)]
        self.lista.append({"host": "c.es", "activa": True, "tipo": "tienda"})
        self.items["c.es"] = [self.x("Juego A", 44.5)]
        res, _ = motor.buscar("juego", pmax=40)
        self.assertEqual([(x["titulo"], x["precio"]) for x in res], [("Juego A", 30)])   # las de 44 € se filtran por precio, «Juego B» está oculto
        self.assertEqual((res[0]["pvp"], res[0]["descuento"]), (44.5, 33))              # pero cuentan para el precio de mercado

    def test_minimo_historico(self):
        for p in (30, 28, 26):                                # tres observaciones previas más caras
            with bd.conecta() as c:
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa) VALUES(?,?,?,?,?,?,?,?,?)",
                          (time.time() - 100 + p, "juego", "a.es", "Juego A", "https://x/Juego-A", p, 0, None, 0))
        res, _ = motor.buscar("juego")
        a = {x["titulo"]: x for x in res}
        self.assertTrue(a["Juego A"]["minimo"])               # 20 € es lo más barato que se le ha visto
        self.assertFalse(a["Juego B"]["minimo"])              # sin historial no hay mínimo


class ClasificaIdioma(unittest.TestCase):
    def test_lo_que_dice_expresamente_es_seguro(self):
        for t, esperado in (("Marvel Champions: Civil War (Castellano)", ("es", True)), ("Edición en español", ("es", True)),
                            ("Hero pack (Inglés)", ("en", True)), ("Jeu en Français", ("otro", True)),
                            ("Game, 1 to 4 Players, Ages 14+", ("en", True))):
            self.assertEqual(motor.idioma_de(t), esperado, t)

    def test_deduccion_por_las_palabras(self):
        self.assertEqual(motor.idioma_de("Marvel Champions: La Tiranía del Cráneo Rojo"), ("es", False))          # artículos y acentos
        self.assertEqual(motor.idioma_de("Fundas Marvel Champions Guardians of the Galaxy Logo"), ("?", False))   # mezcla: no se afirma nada
        self.assertEqual(motor.idioma_de("INSERTO MARVEL CHAMPIONS: THE CARD GAME FS-MARCH"), ("en", False))
        self.assertEqual(motor.idioma_de("Civil War Expansion - Marvel Champions"), ("?", False))                  # sin pistas
        self.assertEqual(motor.idioma_de("Marvel Champions: Vision"), ("?", False))

    def test_los_tres_modos(self):
        casos = {"Juego (Castellano)": (True, True, True), "Los héroes de la caja": (True, True, True),
                 "Juego English": (False, False, True), "The Game of the Year": (True, False, True), "Marvel Champions Vision": (True, False, True)}
        for t, (castellano, estricto, todos) in casos.items():
            self.assertEqual((motor.pasa_idioma(t, "castellano"), motor.pasa_idioma(t, "estricto"), motor.pasa_idioma(t, "todos")),
                             (castellano, estricto, todos), t)


class IdiomaDeLaTienda(unittest.TestCase):
    def it(self, *titulos):
        return [{"titulo": t} for t in titulos]

    def test_la_preposicion_de_y_heroes_cuentan_como_espanol(self):
        self.assertEqual(motor.idioma_de("Marvel champions the card game deadpool pack de heroes"), ("?", False))   # mezcla: no se afirma inglés
        self.assertEqual(motor.idioma_de("Pack de héroes Hulk"), ("es", False))

    def test_una_tienda_en_su_mayoria_castellana_aporta_su_prior(self):
        espanola = self.it("Juego A (Castellano)", "Los héroes de la caja", "Pack de héroes Hulk", "Marvel Champions: Motivos Siniestros")
        self.assertEqual(motor.prior_tienda(espanola), "es")
        self.assertEqual(motor.idioma_con_tienda("Marvel Champions: Motivos Siniestros", "es"), ("es", False))
        self.assertEqual(motor.idioma_con_tienda("Marvel Champions: Motivos Siniestros", None), ("?", False))

    def test_una_tienda_mixta_no_aporta_prior_ni_cambia_lo_que_se_ve_claro(self):
        amazon = self.it("Hero Pack Hulk - Card Game", "Hero Pack Thor - Card Game", "Ficha (Castellano)", "Los héroes de la caja", "Pack de héroes Wasp")
        self.assertIsNone(motor.prior_tienda(amazon))
        self.assertEqual(motor.idioma_con_tienda("Game of the Year", "es"), ("en", False))   # el prior solo rellena lo que no se sabe


class IdiomaEnLaBusqueda(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")),
                        mock.patch.object(tiendas, "guarda", lambda l: None), mock.patch.object(tiendas, "carga", lambda: [{"host": "a.es", "activa": True}])]
        titulos = ["Juego (Castellano)", "Los héroes de la caja", "Juego English", "The Game of the Year", "Marvel Champions Vision"]
        self.parches.append(mock.patch.object(motor, "_tienda", lambda t, c, nav=None, paginas=1: (t["host"], [
            {"titulo": x, "url": "https://x/" + str(i), "precio": 10.0 + i, "agotado": False, "preventa": False, "estado": ""} for i, x in enumerate(titulos)], None)))
        for p in self.parches:
            p.start()
        ajustes.guarda({"usar_navegador": False, "segunda_mano_sembrada": True, "amazon_automatico": True})

    def tearDown(self):
        for p in self.parches:
            p.stop()

    def titulos(self, **kw):
        return [x["titulo"] for x in motor.buscar("juego", **kw)[0]]

    def test_castellano_es_el_modo_por_defecto_y_oculta_solo_lo_expreso(self):
        self.assertEqual(self.titulos(), ["Juego (Castellano)", "Los héroes de la caja", "The Game of the Year", "Marvel Champions Vision"])

    def test_estricto_deja_solo_lo_que_esta_o_parece_en_castellano(self):
        self.assertEqual(self.titulos(idioma="estricto"), ["Juego (Castellano)", "Los héroes de la caja"])

    def test_todos_no_filtra_y_el_parametro_antiguo_sigue_valiendo(self):
        self.assertEqual(len(self.titulos(idioma="todos")), 5)
        self.assertEqual(len(self.titulos(castellano=False)), 5)                      # compatibilidad con «castellano» a secas
        self.assertEqual(len(self.titulos(idioma="no-existe", castellano=True)), 4)   # un valor desconocido se ignora

    def test_cada_resultado_dice_su_idioma(self):
        r = {x["titulo"]: (x["idioma"], x["idioma_seguro"]) for x in motor.buscar("juego", idioma="todos")[0]}
        self.assertEqual(r["Juego (Castellano)"], ("es", True))
        self.assertEqual(r["Los héroes de la caja"], ("es", False))
        self.assertEqual(r["Juego English"], ("en", True))
        self.assertEqual(r["Marvel Champions Vision"], ("?", False))


class Cortesia(unittest.TestCase):
    """BuscaTron no machaca las tiendas: pausas, tope de direcciones, 429 y tiendas caídas."""

    def setUp(self):
        self.p = mock.patch.object(motor.time, "sleep")
        self.pausas = self.p.start()
        self.bd = mock.patch.object(motor.bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))   # las caídas se guardan en la BD
        self.bd.start()
        motor._caidas.clear()

    def tearDown(self):
        self.p.stop()
        self.bd.stop()
        motor._caidas.clear()

    def test_prueba_pocas_direcciones_y_con_pausa_si_no_conoce_el_buscador(self):
        pedidas = []
        def get(u):
            pedidas.append(u)
            return (200, "<html><body>nada</body></html>") if u.endswith("/") else (404, "")
        r, err = motor._intenta({"host": "t.es"}, "x", get)
        self.assertEqual(r, [])
        self.assertLessEqual(len(pedidas), 1 + motor.MAX_INTENTOS)                       # la portada y como mucho 4 buscadores
        self.assertGreaterEqual(self.pausas.call_count, 1)

    def test_si_la_tienda_dice_429_se_para(self):
        pedidas = []
        def get(u):
            pedidas.append(u)
            return 429, ""
        r, err = motor._intenta({"host": "t.es", "plantilla": "https://t.es/?q={q}"}, "x", get)
        self.assertEqual((r, len(pedidas)), ([], 1))
        self.assertIn("429", err)

    def test_pausa_entre_las_paginas_de_una_misma_tienda(self):
        mapa = {"https://t.es/?q=marvel": '<link rel="next" href="/p2"><a href="/a">Marvel Uno</a><b>1 €</b>',
                "https://t.es/p2": '<a href="/b">Marvel Dos</a><b>2 €</b>'}
        motor._intenta({"host": "t.es", "plantilla": "https://t.es/?q={q}"}, "marvel", lambda u: (200, mapa[u]) if u in mapa else (404, ""), paginas=2)
        self.pausas.assert_called_with(motor.PAUSA)

    def test_una_tienda_que_no_responde_no_se_vuelve_a_llamar_enseguida(self):
        llamadas = []
        def tienda_rota(*a, **k):
            llamadas.append(1)
            raise TimeoutError("timed out")
        with mock.patch.object(motor, "_intenta", tienda_rota):
            h, r, err = motor._tienda({"host": "caida.es", "plantilla": "https://caida.es/?q={q}"}, "x")
            self.assertIn("no se pudo conectar", err)
            h, r, err = motor._tienda({"host": "caida.es", "plantilla": "https://caida.es/?q={q}"}, "x")
            self.assertIn("no responde", err)
        self.assertEqual(len(llamadas), 1)                                                # la segunda vez ni se intenta

    def test_los_errores_http_no_marcan_la_tienda_como_caida(self):
        with mock.patch.object(motor, "_intenta", lambda *a, **k: ([], "HTTP 500")):
            motor._tienda({"host": "t.es", "plantilla": "https://t.es/?q={q}"}, "x")
        self.assertNotIn("t.es", motor._caidas)
        self.assertEqual(motor.caida_hasta("t.es"), 0)

    def test_si_sigue_sin_conectar_se_espera_cada_vez_mas_y_se_recuerda(self):
        def rota(*a, **k):
            raise TimeoutError("timed out")
        t = {"host": "caida.es", "plantilla": "https://caida.es/?q={q}"}
        esperas = []
        with mock.patch.object(motor, "_intenta", rota), mock.patch.object(motor.fetch, "get", rota):   # nunca a la red
            for _ in range(5):
                motor._tienda_base(t, "x")
                esperas.append(round((motor.caida_hasta("caida.es") - time.time()) / 60))
                with motor.bd.conecta() as c:            # que haya pasado la espera, para volver a probar
                    c.execute("UPDATE caidas SET desde=0 WHERE host='caida.es'")
            self.assertEqual(esperas, [10, 60, 360, 1440, 1440])     # 10 min, 1 h, 6 h y como mucho 24 h
            with motor.bd.conecta() as c:
                c.execute("UPDATE caidas SET desde=? WHERE host='caida.es'", (time.time(),))
            motor._caidas.clear()                        # como tras reiniciar BuscaTron: lo guardado en la BD sigue mandando
            self.assertIn("no responde", motor._tienda_base(t, "x")[2])

    def test_cuando_vuelve_a_responder_se_olvida(self):
        motor.marca_caida("t.es")
        with motor.bd.conecta() as c:
            c.execute("UPDATE caidas SET desde=0 WHERE host='t.es'")
        with mock.patch.object(motor, "_intenta", lambda *a, **k: ([], motor.SIN_COINCIDENCIAS)):
            motor._tienda_base({"host": "t.es", "plantilla": "https://t.es/?q={q}"}, "x")
        self.assertEqual(motor.caida_hasta("t.es"), 0)


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


class Agrupacion(unittest.TestCase):
    def test_la_misma_expansion_en_tiendas_distintas_tiene_la_misma_clave(self):
        titulos = ["Asmodee Marvel Champions: La Era de Apocalipsis", "Marvel Champions: La era de Apocalipsis",
                   "La Era de Apocalípsis - Marvel Champions", "Marvel Champions (El Juego de Cartas) Expansion La era de Apocalipsis",
                   "Fantasy Flight Games | Marvel Champions: La era de Apocalípsis"]
        self.assertEqual(len({motor.clave_producto(t) for t in titulos}), 1)

    def test_productos_distintos_no_se_juntan(self):
        self.assertNotEqual(motor.clave_producto("Marvel Champions: Héroes Reunidos 1"), motor.clave_producto("Marvel Champions: Héroes Reunidos 2"))
        self.assertNotEqual(motor.clave_producto("Marvel Champions: Civil War"), motor.clave_producto("Marvel Champions: La Era de Apocalipsis"))

    def test_las_referencias_de_la_tienda_no_cuentan(self):
        self.assertEqual(motor.clave_producto("MARVEL CHAMPIONS ASMODEE SHADOWLANDS SCENARIO PACK ASM631069"),
                         motor.clave_producto("Marvel Champions Shadowlands Scenario Pack"))

    def test_con_frases_el_grupo_es_la_frase(self):
        self.assertEqual(motor.grupo_de("Asmodee Marvel Champions: Agentes de S.H.I.E.L.D.", ["tirania", "shield"]), "f:shield")
        self.assertTrue(motor.grupo_de("Marvel Champions Vision", ["tirania"]).startswith("c:"))

    def test_precio_de_mercado(self):
        self.assertEqual(motor.pvp_de([36.5, 38.21, 44.99, 44.95, 44.9]), 44.99)       # el que más se repite
        self.assertEqual(motor.pvp_de([40.49, 40.46, 44.99, 44.99]), 44.99)           # empate: el más alto
        self.assertIsNone(motor.pvp_de([30, 40]))                                      # pocas tiendas
        self.assertIsNone(motor.pvp_de([20, 30, 40]))                                  # ningún precio se repite


class OcultosYEstado(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_ocultar_y_recuperar(self):
        motor.ignora("Marvel Champions: Héroes Reunidos 1")
        self.assertIn(motor.clave_producto("Heroes Reunidos 1 - Marvel Champions"), motor.ignorados())   # otra tienda, mismo producto
        motor.deja_de_ignorar(motor.clave_producto("Marvel Champions: Héroes Reunidos 1"))
        self.assertEqual(motor.ignorados(), {})

    def test_estado_de_las_tiendas(self):
        lista = [{"host": "nada.es", "activa": True}, {"host": "bien.es", "activa": True}, {"host": "manual.es", "activa": True, "manual": True}]
        with mock.patch.object(tiendas, "carga", lambda: lista):
            for i in range(6):
                motor.registra_estado({"nada.es": {"brutos": 0, "error": "no tiene nada"}, "bien.es": {"brutos": 5, "error": None}}, f"q{i}")
            e = {x["host"]: x for x in motor.estado_tiendas()}
        self.assertTrue(e["nada.es"]["sugerir_desactivar"])
        self.assertEqual((e["bien.es"]["con_resultados"], e["bien.es"]["sugerir_desactivar"]), (6, False))
        self.assertFalse(e["manual.es"]["sugerir_desactivar"])
        self.assertEqual(e["nada.es"]["ultimo_error"], "no tiene nada")


class Limpieza(unittest.TestCase):
    def test_compacta_lo_viejo_y_conserva_lo_reciente(self):
        d = tempfile.mkdtemp()
        ahora = 400 * 86400
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")):
            with bd.conecta() as c:
                filas = [(10 * 86400 + h * 3600, p) for h, p in ((1, 12), (5, 10), (9, 11))]          # 3 precios del mismo día, viejos
                filas += [(11 * 86400, 13)]                                                           # otro día viejo
                filas += [(ahora - 3600 * k, 20 + k) for k in range(3)]                              # recientes
                c.executemany("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa) VALUES(?,?,?,?,?,?,?,?,?)",
                              [(ts, "q", "t.es", "J", "https://x/j", p, 0, None, 0) for ts, p in filas])
                for k in range(35):
                    c.execute("INSERT INTO estado_tiendas VALUES(?,?,?,?,?)", ("t.es", float(k), "q", 1, ""))
            borradas = bd.limpia(dias=180, ahora=ahora)
            with bd.conecta() as c:
                quedan = sorted(r[0] for r in c.execute("SELECT precio FROM precios"))
                n_estado = c.execute("SELECT COUNT(*) FROM estado_tiendas").fetchone()[0]
        self.assertEqual(quedan, [10, 13, 20, 21, 22])          # del día con 3 precios queda el más bajo
        self.assertEqual((borradas["precios"], n_estado), (2, 30))


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
