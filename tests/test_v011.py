"""Objetivo por producto, historial por producto y órdenes por Telegram."""
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, motor, seguimiento, telegram_bot  # noqa: E402


class ConBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(bd, "RUTA", os.path.join(self.tmp, "t.db"))
        self.p.start()
        self.t = mock.patch("buscatron.tiendas.carga", lambda: [{"host": "v.es", "tipo": "segunda_mano"}])
        self.t.start()

    def tearDown(self):
        self.p.stop()
        self.t.stop()


class Objetivos(ConBase):
    def test_poner_quitar_y_encontrar_por_grupo_clave_o_frase(self):
        motor.pon_objetivo("f:civil war", "Marvel Champions: Civil War", 30)
        motor.pon_objetivo("c:" + motor.clave_producto("Marvel Champions Tirania de Cráneo Rojo"), "Tiranía", 22.5)
        objs = motor.objetivos()
        self.assertEqual(len(objs), 2)
        self.assertEqual(motor.objetivo_para({"titulo": "Civil War - Marvel Champions", "grupo": "c:x"}, objs), 30)   # por la frase
        self.assertEqual(motor.objetivo_para({"titulo": "Marvel Champions: Tirania de Cráneo Rojo"}, objs), 22.5)    # por la clave
        self.assertIsNone(motor.objetivo_para({"titulo": "Marvel Champions: Era de Apocalipsis"}, objs))
        motor.quita_objetivo("f:civil war")
        self.assertEqual(list(motor.objetivos()), ["c:" + motor.clave_producto("Tirania de Cráneo Rojo Marvel Champions")])

    def test_precio_no_valido(self):
        with self.assertRaises(ValueError):
            motor.pon_objetivo("f:x", "x", None)

    def test_el_objetivo_del_producto_manda_sobre_el_de_la_busqueda(self):
        seg = {"objetivo": 39, "bajo_historico": 0}
        with bd.conecta() as c:
            self.assertIn("para este producto de 25,00", seguimiento._motivo(c, seg, {"precio": 24, "objetivo_producto": 25, "url": "u", "_ts": 0}))
            self.assertIsNone(seguimiento._motivo(c, seg, {"precio": 30, "objetivo_producto": 25, "url": "u", "_ts": 0}))   # 30 < 39, pero no < 25
            self.assertIn("objetivo de 39,00", seguimiento._motivo(c, seg, {"precio": 30, "objetivo_producto": None, "url": "u", "_ts": 0}))


class Historial(ConBase):
    def guarda(self, ts, tienda, titulo, precio, agotado=0):
        with bd.conecta() as c:
            c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id,preventa,clave) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (ts, "q", tienda, titulo, f"https://{tienda}/{titulo}", precio, agotado, None, 0, motor.clave_producto(titulo)))

    def test_mejor_precio_de_cada_busqueda_entre_tiendas(self):
        H = 3600
        self.guarda(H, "a.es", "Marvel Champions Civil War", 40)
        self.guarda(H, "b.es", "Civil War (Marvel Champions)", 36)
        self.guarda(H, "v.es", "Civil War Marvel Champions", 10)        # segunda mano: no cuenta
        self.guarda(H + 600, "a.es", "Marvel Champions Civil War", 40)  # búsqueda parcial en la misma hora: no es una subida
        self.guarda(2 * H, "a.es", "Marvel Champions Civil War", 33)
        self.guarda(2 * H, "b.es", "Civil War (Marvel Champions)", 20, agotado=1)   # agotado: no cuenta
        h = motor.historial_producto("f:civil war")
        self.assertEqual([(p["ts"], p["precio"], p["tienda"]) for p in h["puntos"]], [(H, 36, "b.es"), (2 * H, 33, "a.es")])
        self.assertEqual(h["tienda"], "2 tiendas")
        h2 = motor.historial_producto("c:" + motor.clave_producto("Marvel Champions Civil War"))
        self.assertEqual([p["precio"] for p in h2["puntos"]], [36, 33])    # misma clave, aunque cambie el orden de las palabras

    def test_rellena_claves_de_precios_antiguos(self):
        with bd.conecta() as c:
            c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado) VALUES(1,'q','a.es','Era de Apocalipsis','u',30,0)")
        self.assertEqual(motor.rellena_claves(), 1)
        self.assertEqual(motor.rellena_claves(), 0)
        self.assertEqual(len(motor.historial_producto("c:" + motor.clave_producto("Era de Apocalipsis"))["puntos"]), 1)


class Bot(unittest.TestCase):
    def setUp(self):
        self.enviados = []
        self.r = mock.patch.object(telegram_bot, "responde", self.enviados.append)
        self.r.start()

    def tearDown(self):
        self.r.stop()

    def test_ordenes(self):
        with mock.patch.object(telegram_bot, "buscar") as b:
            telegram_bot.atiende("/buscar civil war")
            telegram_bot.atiende("era de apocalipsis")
            telegram_bot.atiende("/buscar@BuscaTronBot  titan loco ")
            self.assertEqual([c.args[0] for c in b.call_args_list], ["civil war", "era de apocalipsis", "titan loco"])
        telegram_bot.atiende("/start")
        telegram_bot.atiende("/nose")
        telegram_bot.atiende("/buscar")
        self.assertIn("/vigiladas", self.enviados[0])
        self.assertTrue(self.enviados[1].startswith("No conozco"))
        self.assertIn("Dime qué buscar", self.enviados[2])

    def test_buscar_responde_con_los_mas_baratos(self):
        res = [{"titulo": "Civil War", "precio": p, "url": f"u{p}", "tienda": "a.es", "grupo": f"g{p}"} for p in (40, 30, 35)]
        with mock.patch("buscatron.motor.buscar", lambda *a, **k: (res, {})), mock.patch.object(seguimiento, "_nombres", lambda: {"a.es": "Tienda A"}):
            telegram_bot.buscar("civil war")
        self.assertEqual(len(self.enviados), 2)
        self.assertIn("3 productos", self.enviados[1])
        self.assertLess(self.enviados[1].index("30,00"), self.enviados[1].index("40,00"))

    def test_una_busqueda_a_la_vez(self):
        telegram_bot._ocupado.acquire()
        try:
            telegram_bot.buscar("x")
        finally:
            telegram_bot._ocupado.release()
        self.assertIn("otra búsqueda", self.enviados[0])


if __name__ == "__main__":
    unittest.main()
