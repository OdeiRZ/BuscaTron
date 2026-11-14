"""v0.17.8: una tienda que rechaza (403/429) deja de recibir consultas, fichas fallidas recordadas, tope de fichas al
avisar, vigiladas en su hilo sin gastar el turno, mínimo > máximo rechazado."""
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, motor, programador, seguimiento  # noqa: E402


class ConBD(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()
        motor._rechazos.clear()
        motor._caidas.clear()

    def tearDown(self):
        self.p.stop()


class Rechazos(ConBD):
    def tienda(self, st):
        t = {"host": "r.es", "plantilla": "https://r.es/?q={q}"}
        with mock.patch.object(motor.fetch, "get", lambda u, timeout=25: (st, "")):
            return motor._tienda_base(t, "algo")

    def test_un_403_no_frena_pero_dos_si(self):
        self.tienda(403)
        self.assertEqual(motor.caida_hasta("r.es"), 0)
        self.tienda(403)
        self.assertGreater(motor.caida_hasta("r.es"), time.time())
        _, _, err = self.tienda(200)
        self.assertIn("no responde", err)                  # no se llama: está esperando

    def test_un_429_frena_a_la_primera(self):
        self.tienda(429)
        self.assertGreater(motor.caida_hasta("r.es"), time.time())

    def test_una_respuesta_buena_olvida_el_rechazo(self):
        self.tienda(403)
        self.tienda(200)
        self.tienda(403)
        self.assertEqual(motor.caida_hasta("r.es"), 0)

    def test_rechazos_repetidos_la_bloquean(self):
        lista = [{"host": "r.es", "activa": True}]
        with mock.patch.object(motor.cfg, "carga", lambda: lista), mock.patch.object(motor.cfg, "guarda", lambda l: None), \
                mock.patch("buscatron.notifica.envia", lambda *a: {}) as _:
            for _ in range(motor.BLOQUEO_FALLOS):
                motor.registra_rechazo("r.es", "rechaza (error 429)")
        self.assertFalse(lista[0]["activa"])
        self.assertIn("bloqueo", lista[0])
        self.assertEqual(motor.caida_hasta("r.es"), 0)       # desde ahí manda la prueba de la portada


class FichaFallida(ConBD):
    def test_no_se_pide_otra_vez(self):
        pedidas = []
        with mock.patch.object(motor.fetch, "get", lambda u, timeout=20: pedidas.append(u) or (403, "")):
            motor.ficha({"url": "https://z.es/p", "tienda": "z.es"}, [])
            motor.ficha({"url": "https://z.es/p", "tienda": "z.es"}, [])
        self.assertEqual(len(pedidas), 1)


class TopeDeFichasAlAvisar(ConBD):
    def test_como_mucho_unas_pocas_por_tienda(self):
        sid = seguimiento.guarda({"consulta": "q", "objetivo": 100})
        res = [{"url": f"https://z.es/{i}", "titulo": f"Juego {i}", "tienda": "z.es", "precio": 10 + i, "agotado": False} for i in range(10)]
        leidas = []
        with mock.patch.object(motor, "buscar", lambda *a, **k: (res, {})), mock.patch.object(motor.cfg, "carga", lambda: []), \
                mock.patch.object(motor, "ficha", lambda x, l: leidas.append(x["precio"]) or {"agotado": None, "preventa": None, "idioma": None}):
            seguimiento.revisa(sid, enviar=False)
        self.assertEqual(sorted(leidas), [10, 11, 12, 13])


class MinimoMayorQueMaximo(ConBD):
    def test_se_rechaza(self):
        with self.assertRaises(ValueError):
            seguimiento.guarda({"consulta": "q", "pmin": 50, "pmax": 20})


class VigiladaOcupada(unittest.TestCase):
    def test_se_salta_sin_gastar_el_turno(self):
        segs = [{"id": 1, "ultima": 100, "revisando": True}, {"id": 2, "ultima": 300}]
        revisadas = []
        with mock.patch.object(programador.seguimiento, "pendientes", lambda ahora=None: [1, 2]), \
                mock.patch.object(programador.seguimiento, "lista", lambda: segs), \
                mock.patch.object(programador.seguimiento, "revisa", revisadas.append), \
                mock.patch.object(programador, "_ultima_revision", [0.0]), mock.patch.object(programador, "_hilo", [None]):
            self.assertEqual(programador.vigiladas(10_000.0), 2)
        self.assertEqual(revisadas, [2])

    def test_en_su_hilo_y_no_empieza_otra_hasta_que_acaba(self):
        import threading
        sigue = threading.Event()
        with mock.patch.object(programador.seguimiento, "pendientes", lambda ahora=None: [1]), \
                mock.patch.object(programador.seguimiento, "lista", lambda: [{"id": 1, "ultima": 0}]), \
                mock.patch.object(programador.seguimiento, "revisa", lambda sid: sigue.wait(5)), \
                mock.patch.object(programador, "_ultima_revision", [0.0]), mock.patch.object(programador, "_hilo", [None]):
            self.assertEqual(programador.vigiladas(10_000.0, hilo=True), 1)      # vuelve enseguida
            self.assertIsNone(programador.vigiladas(10_000.0 + 2 * programador.ESPACIO_VIGILADAS, hilo=True))
            sigue.set()
            programador._hilo[0].join(5)


class ResumenSinBusquedaAbierta(unittest.TestCase):
    def test_no_cuenta_como_tienda(self):
        self.assertEqual(seguimiento.tiendas_caidas({"a.es": {"caida": True}, "Búsqueda abierta": {"caida": True}}), 1)


if __name__ == "__main__":
    unittest.main()
