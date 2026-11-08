"""v0.13.1: editar o borrar una vigilada mientras se revisa, y «Buscando…» que dice el servidor."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, extract, motor, seguimiento  # noqa: E402
from tests.test_v0114 import ConArchivos  # noqa: E402


class EditarMientrasSeRevisa(ConArchivos):
    def test_si_cambias_la_busqueda_se_repite_con_lo_nuevo(self):
        sid = seguimiento.guarda({"consulta": "vantage", "objetivo": "65"})
        vistas = []

        def buscar(consulta, *a, **k):
            vistas.append(consulta)
            if len(vistas) == 1:          # la editas mientras busca
                seguimiento.guarda({"id": sid, "consulta": "vantage stonemaier", "objetivo": "65"})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        self.assertEqual(vistas, ["vantage", "vantage stonemaier"])

    def test_cambiar_solo_el_nombre_o_pausarla_no_la_repite(self):
        sid = seguimiento.guarda({"consulta": "vantage", "objetivo": "65"})
        vistas = []

        def buscar(consulta, *a, **k):
            vistas.append(consulta)
            seguimiento.guarda({"id": sid, "nombre": "Vantage (juego)", "consulta": "vantage", "objetivo": "65", "activo": False})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        self.assertEqual(vistas, ["vantage"])

    def test_no_se_repite_sin_fin(self):
        sid = seguimiento.guarda({"consulta": "q0"})
        n = []

        def buscar(consulta, *a, **k):
            n.append(consulta)
            seguimiento.guarda({"id": sid, "consulta": f"q{len(n)}"})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        self.assertEqual(len(n), 3)


class BorrarMientrasSeRevisa(ConArchivos):
    def test_no_quedan_avisos_huerfanos(self):
        sid = seguimiento.guarda({"consulta": "vantage", "objetivo": "65"})

        def buscar(*a, **k):
            seguimiento.borra(sid)
            with bd.conecta() as c:       # lo que la revisión en curso habría guardado después de borrarla
                c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(1,?,'Vantage','a.es','https://a.es/v',60,'x')", (sid,))
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        with bd.conecta() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM avisos WHERE seg_id=?", (sid,)).fetchone()[0], 0)


class EstadoRevisando(ConArchivos):
    def test_la_lista_dice_cual_se_esta_revisando(self):
        a = seguimiento.guarda({"consulta": "vantage"})
        b = seguimiento.guarda({"consulta": "eternal decks"})
        durante = {}

        def buscar(*a_, **k):
            durante.update({s["id"]: s["revisando"] for s in seguimiento.lista()})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(a)
        self.assertEqual(durante, {a: True, b: False})
        self.assertFalse(any(s["revisando"] for s in seguimiento.lista()))

    def test_tras_un_fallo_deja_de_estar_revisandose(self):
        sid = seguimiento.guarda({"consulta": "vantage"})
        with mock.patch.object(motor, "buscar", side_effect=RuntimeError("se rompió")):
            with self.assertRaises(RuntimeError):
                seguimiento.revisa(sid)
        self.assertFalse(seguimiento.lista()[0]["revisando"])


class IdiomaDeLaFicha(unittest.TestCase):
    def test_etiqueta_vacia_no_toma_el_texto_siguiente(self):
        # Dungeon Marvels: «Idiomas:» vacío arriba y «Idioma | Castellano» en la ficha técnica
        html = ('<p>Idiomas:</p><p></p><a href="#">+ Detalles del producto</a>'
                '<dl class="data-sheet"><dt>Idioma</dt><dd>Castellano</dd><dt>Edad mínima</dt><dd>14</dd></dl>')
        self.assertEqual(extract.codigo_idioma(extract.idioma_pagina(html)), "es")

    def test_etiqueta_seguida_de_otra_etiqueta(self):
        # Goblin Trader: un título «Idioma» y debajo la fila «Idioma: Español»
        html = "<h3>Idioma</h3><h4>Idioma</h4><span>Español</span>"
        self.assertEqual(extract.codigo_idioma(extract.idioma_pagina(html)), "es")

    def test_sigue_leyendo_otros_idiomas(self):
        self.assertEqual(extract.codigo_idioma(extract.idioma_pagina("<th>Idioma</th><td>Francés</td>")), "otro")
        self.assertEqual(extract.codigo_idioma(extract.idioma_pagina("<span>Idioma: Inglés</span>")), "en")

    def test_sin_idioma_de_verdad_no_inventa_uno(self):
        self.assertIsNone(extract.idioma_pagina("<p>Idiomas:</p><a>+ Detalles del producto</a><p>Juegos de Tablero</p>"))


class StockDeLaFicha(unittest.TestCase):
    def test_sin_disponibilidad_en_los_datos_es_no_se_sabe(self):
        h = '<meta property="og:title" content="Mage Knight"><meta property="product:price:amount" content="108">'
        d = extract.datos_producto(h)
        self.assertEqual((d["precio"], d["agotado"], d["preventa"]), (108.0, None, None))

    def test_boton_de_avisadme_es_agotado(self):
        # Zacatrus: «No está disponible … Avisadme cuando esté disponible»
        self.assertTrue(extract.sin_stock_pagina("<h1>Mage Knight</h1><p>108,00 €</p><button>Avisadme cuando esté disponible</button>"))

    def test_el_texto_fijo_del_envio_no_es_agotado(self):
        # Zacatrus lo pone en todas las fichas, también en las que tienen stock
        h = ("<h1>Vantage</h1><button>Añadir al carrito</button><div>¡Ouch! El envío 24 horas no está disponible. "
             "Lamentablemente este producto está fuera de stock en nuestro almacén.</div>")
        self.assertIsNone(extract.sin_stock_pagina(h))

    def test_la_ficha_usa_el_texto_si_los_datos_no_lo_dicen(self):
        h = '<meta property="product:price:amount" content="108"><button>Avisadme cuando esté disponible</button>'
        with mock.patch.object(motor.fetch, "get", return_value=(200, h)), mock.patch.object(motor.bd, "conecta") as con:
            con.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
            f = motor.ficha({"url": "https://zacatrus.es/mk.html", "tienda": "zacatrus.es"}, [{"host": "zacatrus.es"}])
        self.assertTrue(f["agotado"])


class TituloDeZacatrus(unittest.TestCase):
    def test_nombre_repetido_y_precios_fuera(self):
        self.assertEqual(extract.limpia_titulo("Marvel Champions: Hulk Marvel Champions: Hulk 16,95 € Club -10% 15,26 € ?"), "Marvel Champions: Hulk")
        self.assertEqual(extract.limpia_titulo("Dune Imperium: Insurrección Dune Imperium: Insurrección 55,99 €"), "Dune Imperium: Insurrección")

    def test_los_demas_titulos_no_cambian(self):
        for t in ("Marvel Champions: Hulk", "Pack Pack 2", "Dune Dune Imperium", "Marvel Champions Promo Card 4,5€/u", "Juego 2 2 jugadores"):
            self.assertEqual(extract.limpia_titulo(t), t)


class IdiomaPorOpiniones(unittest.TestCase):
    def test_todas_de_otro_pais_es_otro_idioma(self):
        # Amazon: Civil War FFGMC56 con «Versión ES» en el título y 4 opiniones de Francia
        h = "".join(f"<span>Reseñado en Francia el {d} de julio de 2026</span>" for d in (1, 2, 3, 4))
        self.assertEqual(extract.idioma_por_resenas(h), "otro")

    def test_con_alguna_de_espana_o_pocas_no_se_sabe(self):
        self.assertIsNone(extract.idioma_por_resenas("Reseñado en España el 1 de mayo · Reseñado en Francia el 2 de mayo"))
        self.assertIsNone(extract.idioma_por_resenas("Reseñado en Francia el 1 de mayo"))
        self.assertIsNone(extract.idioma_por_resenas("<p>Sin opiniones</p>"))


class LaFichaMandaEnLaBusqueda(ConArchivos):
    def test_ficha_en_otro_idioma_se_oculta_aunque_el_titulo_diga_es(self):
        fr, es = "https://www.amazon.es/dp/FR", "https://www.amazon.es/dp/ES"
        with bd.conecta() as c:
            c.execute("INSERT INTO fichas(url,idioma,agotado,preventa,ts) VALUES(?,?,NULL,NULL,1)", (fr, "otro"))
            c.execute("INSERT INTO fichas(url,idioma,agotado,preventa,ts) VALUES(?,?,NULL,NULL,1)", (es, "es"))
        items = [{"titulo": "Marvel Champions: Civil War - Versión ES", "url": fr, "precio": 36.94, "agotado": False, "preventa": False, "estado": ""},
                 {"titulo": "Marvel Champions: Civil War", "url": es, "precio": 39.0, "agotado": False, "preventa": False, "estado": ""}]
        tienda = lambda t, c, nav=None, paginas=1: (t["host"], [dict(i) for i in items] if t["host"] == "a.es" else [], None)
        with mock.patch.object(motor, "_tienda", tienda), mock.patch.object(motor.navegador, "disponible", lambda: False):
            res, _ = motor.buscar("civil war")
        self.assertEqual([(x["url"], x["idioma"], x["idioma_seguro"]) for x in res], [(es, "es", True)])


if __name__ == "__main__":
    unittest.main()
