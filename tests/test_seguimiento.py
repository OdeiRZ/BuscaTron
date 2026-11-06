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

    def tearDown(self):
        self.p.stop()
        self.n.stop()

    def busca(self, precio, **kw):
        def falsa(consulta, incluir, excluir, sin_ag, tiendas, pmin, pmax, seg_id):
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
        self.assertIn("media", r["avisos"][0]["motivo"])

    def test_historial_insuficiente(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "bajo_historico": "10"})
        self.busca(40)
        self.assertEqual(self.busca(20)["avisos"], [])

    def test_pendientes(self):
        self.sid = seguimiento.guarda({"consulta": "marvel", "cada_horas": "1"})
        self.assertEqual(seguimiento.pendientes(), [self.sid])
        self.busca(10)
        self.assertEqual(seguimiento.pendientes(), [])
        self.assertEqual(seguimiento.pendientes(time.time() + 3601), [self.sid])


if __name__ == "__main__":
    unittest.main()
