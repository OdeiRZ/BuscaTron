import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, seguimiento, notifica  # noqa: E402


def item(precio, url="https://t.es/a", agotado=False):
    return {"titulo": "Marvel Champions: Saga", "url": url, "precio": precio, "agotado": agotado, "tienda": "t.es"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(bd, "RUTA", os.path.join(self.tmp, "t.db"))
        self.p.start()
        self.enviados = []
        self.n = mock.patch.object(notifica, "envia", lambda c, a, t: self.enviados.append((c, a, t)) or {})
        self.n.start()
        self.idioma_ficha = None          # lo que «lee» la ficha del producto: None, 'es', 'en' u 'otro'
        self.agotado_ficha = None
        self.preventa_ficha = None
        self.fichas = []
        self.v = mock.patch("buscatron.motor.ficha", lambda x, lista=None: self.fichas.append(x["url"]) or
                            {"idioma": self.idioma_ficha, "agotado": self.agotado_ficha, "preventa": self.preventa_ficha})
        self.t = mock.patch("buscatron.tiendas.carga", lambda: [])
        self.v.start()
        self.t.start()

    def tearDown(self):
        self.p.stop()
        self.n.stop()
        self.v.stop()
        self.t.stop()

    def busca(self, precio, **kw):
        def falsa(consulta, incluir, excluir, sin_ag, tiendas, pmin, pmax, seg_id, castellano=True, **opciones):
            x = item(precio, **kw)
            with bd.conecta() as c:  # el motor real guarda cada resultado en el historial
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id) VALUES(?,?,?,?,?,?,?,?)",
                          (time.time(), consulta, x["tienda"], x["titulo"], x["url"], x["precio"], 0, seg_id))
            return [x], {"t.es": {"encontrados": 1, "error": None}}
        with mock.patch("buscatron.motor.buscar", falsa):
            return seguimiento.revisa(self.sid)


class Avisos(Base):
    def test_precio_objetivo_y_sin_repetir(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "telegram"})
        self.assertEqual(self.busca(45)["avisos"], [])
        self.assertEqual(len(self.busca(39)["avisos"]), 1)
        self.assertEqual(len(self.enviados), 1)
        self.assertEqual(self.busca(39)["avisos"], [])          # mismo precio: no repite
        self.assertEqual(len(self.busca(35)["avisos"]), 1)      # baja más: avisa otra vez
        self.assertEqual(len(seguimiento.avisos()), 2)

    def test_media_historica(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "bajo_historico": "15"})
        for _ in range(4):
            self.busca(40)
            time.sleep(0.01)
        self.assertEqual(self.busca(36)["avisos"], [])          # 10 % menos: no basta
        r = self.busca(30)                                      # 25 % menos
        self.assertEqual(len(r["avisos"]), 1)
        self.assertIn("precio habitual", r["avisos"][0]["motivo"])

    def test_historial_insuficiente(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "bajo_historico": "10"})
        self.busca(40)
        self.assertEqual(self.busca(20)["avisos"], [])

    def revisa_con(self, items, informe):
        with mock.patch("buscatron.motor.buscar", lambda *a, **k: (items, informe)):
            return seguimiento.revisa(self.sid)

    def test_retira_avisos_de_productos_que_ya_no_cumplen(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.busca(30)
        self.assertEqual(len(seguimiento.avisos()), 1)
        # la tienda responde pero el producto ya no cumple (agotado, otro idioma, fuera de precio...)
        self.revisa_con([], {"t.es": {"encontrados": 0, "error": None}})
        self.assertEqual(seguimiento.avisos(), [])

    def test_si_la_tienda_falla_no_se_borra_nada(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.busca(30)
        self.revisa_con([], {"t.es": {"encontrados": 0, "error": "HTTP 503"}})
        self.assertEqual(len(seguimiento.avisos()), 1)

    def test_vuelve_a_avisar_si_el_producto_regresa(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.busca(30)
        self.revisa_con([], {"t.es": {"encontrados": 0, "error": None}})
        self.assertEqual(len(self.busca(30)["avisos"]), 1)

    def test_borrar_un_seguimiento_se_lleva_sus_avisos(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        otro = seguimiento.guarda({"consulta": "otro", "objetivo": "40"})
        self.busca(30)
        seguimiento.borra(self.sid)
        self.assertEqual(seguimiento.avisos(), [])
        self.assertEqual([s["id"] for s in seguimiento.lista()], [otro])

    def test_quitar_un_aviso_lo_oculta_sin_provocar_un_aviso_repetido(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "telegram"})
        self.busca(30)
        aviso = seguimiento.avisos()[0]
        seguimiento.borra_aviso(aviso["id"])
        self.assertEqual(seguimiento.avisos(), [])                 # ya no sale en la lista
        self.assertEqual(len(self.enviados), 1)
        self.assertEqual(self.busca(30)["avisos"], [])             # mismo precio: no se vuelve a avisar
        self.assertEqual(len(self.enviados), 1)
        self.assertEqual(len(self.busca(25)["avisos"]), 1)         # si baja más, avisa otra vez
        self.assertEqual([x["precio"] for x in seguimiento.avisos()], [25])

    def test_quitar_solo_afecta_al_aviso_elegido(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        with mock.patch("buscatron.motor.buscar", lambda *a, **k: ([item(30, url="https://t.es/a"), item(31, url="https://t.es/b")], {"t.es": {"encontrados": 2, "error": None}})):
            seguimiento.revisa(self.sid)
        a, b = seguimiento.avisos()
        seguimiento.borra_aviso(a["id"])
        self.assertEqual([x["id"] for x in seguimiento.avisos()], [b["id"]])

    def test_un_aviso_de_un_precio_importado_dice_que_no_es_en_directo(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "telegram"})
        directo = item(30, url="https://t.es/directo")
        importado = {**item(31, url="https://f.es/importado"), "importado": time.time() - 5 * 3600}
        r = self.revisa_con([directo, importado], {"t.es": {"encontrados": 2, "error": None}})
        motivos = {x["url"]: x["motivo"] for x in r["avisos"]}
        self.assertNotIn("pegado", motivos["https://t.es/directo"])
        self.assertIn("pegado a mano hace 5 h, sin comprobar en directo", motivos["https://f.es/importado"])
        self.assertIn("sin comprobar en directo", self.enviados[0][2])                     # y también en el mensaje de Telegram

    def test_una_ficha_en_otro_idioma_impide_el_aviso(self):          # el caso de «Extensión Marvel Champions: Deadpool» en francés
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "telegram"})
        self.idioma_ficha = "otro"
        r = self.busca(30)
        self.assertEqual((r["avisos"], seguimiento.avisos(), self.enviados), ([], [], []))
        self.assertEqual(self.fichas, ["https://t.es/a"])               # se miró la ficha de ese producto

    def test_si_no_se_puede_leer_la_ficha_se_avisa_pero_se_dice(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.idioma_ficha = None
        self.assertIn("idioma sin confirmar", self.busca(30)["avisos"][0]["motivo"])

    def test_una_ficha_en_castellano_avisa_sin_reservas(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.idioma_ficha = "es"
        self.assertNotIn("sin confirmar", self.busca(30)["avisos"][0]["motivo"])

    def test_con_cualquier_idioma_la_ficha_no_filtra_por_idioma(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "castellano": False})
        self.idioma_ficha = "otro"
        self.assertEqual(len(self.busca(30)["avisos"]), 1)

    def test_si_la_ficha_dice_agotado_no_se_avisa(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "telegram"})
        self.agotado_ficha = True
        self.assertEqual((self.busca(30)["avisos"], self.enviados), ([], []))

    def test_si_la_ficha_dice_preventa_solo_avisa_con_preventas_activadas(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.preventa_ficha = True
        self.assertEqual(self.busca(30)["avisos"], [])
        seguimiento.guarda({"id": self.sid, "consulta": "marvel", "objetivo": "40", "opciones": {"preventas": True}})
        self.assertEqual(len(self.busca(29)["avisos"]), 1)

    def test_modo_estricto_tambien_exige_la_ficha(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "opciones": {"idioma": "estricto"}})
        self.idioma_ficha = "en"
        self.assertEqual(self.busca(30)["avisos"], [])

    def test_resumen_por_telegram_si_no_hay_avisos(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "20", "canales": "app,telegram", "opciones": {"resumen": True}})
        r = self.revisa_con([item(30, url="https://t.es/a"), item(25, url="https://t.es/b"), item(40, url="https://t.es/c", agotado=True)],
                            {"t.es": {"encontrados": 3, "error": None}, "x.es": {"encontrados": 0, "error": "no responde"}})
        self.assertEqual(r["avisos"], [])
        canales, asunto, texto = self.enviados[0]
        self.assertEqual((canales, asunto), (["telegram"], "BuscaTron · marvel · resumen"))
        self.assertIn("Sin avisos nuevos", texto)
        self.assertIn("1 tiendas sin respuesta", texto)
        self.assertLess(texto.index("25,00 €"), texto.index("30,00 €"))     # del más barato al más caro
        self.assertNotIn("40,00 €", texto)                                  # el agotado no cuenta

    def test_sin_la_opcion_o_sin_telegram_no_hay_resumen(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "20", "canales": "telegram"})
        self.busca(30)
        seguimiento.guarda({"id": self.sid, "consulta": "marvel", "objetivo": "20", "canales": "app", "opciones": {"resumen": True}})
        self.busca(30)
        self.assertEqual(self.enviados, [])

    def test_con_avisos_nuevos_se_envia_el_aviso_no_el_resumen(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "telegram", "opciones": {"resumen": True}})
        self.busca(30)
        self.assertEqual(len(self.enviados), 1)
        self.assertNotIn("resumen", self.enviados[0][1])

    def test_vaciar_avisos(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40"})
        self.busca(30)
        seguimiento.vacia_avisos()
        self.assertEqual(seguimiento.avisos(), [])

    def test_pendientes(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "cada_horas": "1"})
        self.assertEqual(seguimiento.pendientes(), [self.sid])
        self.busca(10)
        self.assertEqual(seguimiento.pendientes(), [])
        self.assertEqual(seguimiento.pendientes(time.time() + 3601), [self.sid])


if __name__ == "__main__":
    unittest.main()
