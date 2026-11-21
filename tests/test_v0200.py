"""v0.20.0: arreglos de la revisión completa (rechazos de tiendas, avisos que no se pierden ni se repiten, accesos)."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, progreso, seguimiento, tiendas, web


class Base(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.parches = [mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json"))]
        for p in self.parches:
            p.start()

    def tearDown(self):
        motor._caidas.clear()            # marca_caida también apunta en memoria
        for p in reversed(self.parches):
            p.stop()


class Rechazos(Base):
    def test_un_403_no_prueba_otras_direcciones(self):
        llamadas = []
        t = {"host": "t.es", "plantilla": None}
        with mock.patch.object(motor, "_candidatas", return_value=([("a", "https://t.es/a"), ("b", "https://t.es/b")], None)):
            r, err = motor._intenta(t, "x", lambda u: llamadas.append(u) or (403, ""))
        self.assertEqual((r, len(llamadas)), ([], 1))
        self.assertIn("(error 403)", err)

    def test_un_rechazo_directo_no_se_repite_con_chrome(self):
        t = {"host": "t.es", "plantilla": "https://t.es/?q={q}"}
        with mock.patch.object(motor, "_intenta", return_value=([], "rechaza las consultas automáticas (error 403)")) as i:
            h, r, err = motor._tienda_consulta(t, "x", {"visible": False}, 1, False)
        self.assertEqual(i.call_count, 1)
        self.assertIn("403", err)

    def test_bixoto_siempre_solo_enlace(self):
        with mock.patch.object(tiendas, "lee_json", side_effect=lambda r: [{"host": "bixoto.com", "manual": False, "activa": True, "plantilla": None}]
                                if r == tiendas.RUTA else {}), \
             mock.patch.object(tiendas.os.path, "exists", return_value=True), mock.patch.object(tiendas, "guarda"):
            l = tiendas.carga()
        self.assertTrue(next(t for t in l if t["host"] == "bixoto.com")["manual"])

    def test_ficha_de_tienda_caida_no_se_consulta(self):
        motor.marca_caida("t.es")
        with mock.patch.object(motor.fetch, "get", side_effect=AssertionError("no debe consultarse")):
            motor.ficha({"url": "https://t.es/p", "tienda": "t.es"}, [{"host": "t.es"}])


class Avisos(Base):
    def setUp(self):
        super().setUp()
        self.sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "canales": "app,telegram"})
        self.x = {"titulo": "Marvel Hulk", "precio": 30.0, "url": "https://t.es/p", "tienda": "t.es"}

    def apunta(self):
        with bd.conecta() as c:
            if not seguimiento._apunta_aviso(c, self.sid, self.x, time.time()):
                return False
            c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                      (time.time(), self.sid, self.x["titulo"], "t.es", self.x["url"], 30.0, "m"))
            return True

    def test_vaciar_no_hace_repetir_el_aviso(self):
        self.assertTrue(self.apunta())
        seguimiento.vacia_avisos()
        self.assertEqual(seguimiento.avisos(), [])
        self.assertFalse(self.apunta())

    def test_si_el_mensaje_no_llega_se_reintenta(self):
        ts = time.time()
        with bd.conecta() as c:
            seguimiento._apunta_aviso(c, self.sid, self.x, ts)
            c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                      (ts, self.sid, self.x["titulo"], "t.es", self.x["url"], 30.0, "m"))
        seg = next(s for s in seguimiento.lista() if s["id"] == self.sid)
        with mock.patch.object(seguimiento.notifica, "envia", return_value={"telegram": "sin conexión"}):
            seguimiento._envia_avisos(seg, [self.x], ts)
        self.assertTrue(self.apunta())                 # el pendiente no cuenta: se vuelve a avisar…
        self.assertEqual(len(seguimiento.avisos()), 1)  # …y sustituye al que no llegó

    def test_tienda_bloqueada_no_pierde_sus_avisos(self):
        self.apunta()
        with mock.patch.object(motor.cfg, "carga", return_value=[{"host": "t.es"}]):
            seguimiento.limpia_avisos(self.sid, [], {"otra.es": {"encontrados": 0}})
        self.assertEqual(len(seguimiento.avisos()), 1)


class Accesos(unittest.TestCase):
    def manejador(self, cabeceras):
        h = web.Handler.__new__(web.Handler)
        h.headers = cabeceras
        return h

    def test_otra_web_no_puede_mandar_ordenes(self):
        self.assertTrue(self.manejador({"Origin": "https://malo.example", "Host": "127.0.0.1:8790"})._origen_ajeno())
        import socket
        equipo = socket.gethostname().lower()
        self.assertTrue(self.manejador({"Origin": "https://otro.tail1.ts.net", "Host": "127.0.0.1:8790"})._origen_ajeno())   # otra máquina de tailscale
        self.assertTrue(self.manejador({"Origin": "http://malo.example:8790", "Host": "malo.example:8790"})._origen_ajeno())  # DNS rebinding
        for o in ("http://127.0.0.1:8790", f"https://{equipo}.tail1.ts.net", "http://192.168.1.20:8790", f"http://{equipo}:8790"):
            self.assertFalse(self.manejador({"Origin": o, "Host": "127.0.0.1:8790"})._origen_ajeno(), o)
        self.assertFalse(self.manejador({"Host": "127.0.0.1:8790"})._origen_ajeno())


class EsperaTurno(unittest.TestCase):
    def test_esperando_no_marca_porcentaje(self):
        with progreso.tarea("vigilada:9", "vigilada", "X", estimado=100):
            progreso.fase("vigilada:9", "Esperando a que acabe otra revisión")
            t = progreso.lista()[0]
        self.assertEqual((t["parte"], t["queda"]), (None, None))


if __name__ == "__main__":
    unittest.main()
