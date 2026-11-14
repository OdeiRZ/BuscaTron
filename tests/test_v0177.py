"""v0.17.7: ritmo máximo por tienda, vigiladas escalonadas y vuelta suave de una tienda que te bloqueó."""
import os
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, fetch, motor, programador, ritmo  # noqa: E402


class Reloj:
    """time.monotonic y time.sleep falsos: dormir solo adelanta el reloj."""
    def __init__(self):
        self.t, self.dormido = 1000.0, []

    def monotonic(self):
        return self.t

    def sleep(self, s):
        self.dormido.append(round(s, 3))
        self.t += s


class Ritmo(unittest.TestCase):
    def setUp(self):
        self.r = Reloj()
        self.ps = [mock.patch.object(ritmo.time, "monotonic", self.r.monotonic), mock.patch.object(ritmo.time, "sleep", self.r.sleep),
                   mock.patch.dict(ritmo._turno, clear=True)]
        for p in self.ps:
            p.start()

    def tearDown(self):
        for p in self.ps:
            p.stop()

    def test_la_segunda_peticion_a_la_misma_tienda_espera(self):
        self.assertEqual(ritmo.espera("https://zacatrus.es/a"), 0)
        self.assertEqual(ritmo.espera("https://zacatrus.es/b"), ritmo.INTERVALO)

    def test_tiendas_distintas_no_se_esperan(self):
        ritmo.espera("https://zacatrus.es/a")
        self.assertEqual(ritmo.espera("https://dracotienda.com/a"), 0)

    def test_con_y_sin_www_es_la_misma_tienda(self):
        ritmo.espera("https://www.masqueoca.com/a")
        self.assertEqual(ritmo.espera("https://masqueoca.com/b"), ritmo.INTERVALO)

    def test_pasado_el_intervalo_no_espera(self):
        ritmo.espera("https://t.es/a")
        self.r.t += ritmo.INTERVALO + 1
        self.assertEqual(ritmo.espera("https://t.es/b"), 0)

    def test_buscatron_mismo_no_cuenta(self):
        ritmo.espera("http://127.0.0.1:8790/api")
        self.assertEqual(ritmo.espera("http://127.0.0.1:8790/api"), 0)


class RitmoConHilos(unittest.TestCase):
    def test_varios_hilos_hacen_cola(self):
        turnos = []
        with mock.patch.object(ritmo, "INTERVALO", 0.05), mock.patch.dict(ritmo._turno, clear=True):
            hilos = [threading.Thread(target=lambda: (ritmo.espera("https://t.es/x"), turnos.append(time.monotonic()))) for _ in range(3)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
        turnos.sort()
        self.assertGreaterEqual(turnos[2] - turnos[0], 0.09)


class FetchRespetaElRitmo(unittest.TestCase):
    def test_fetch_get_pide_turno(self):
        class R:
            status, headers = 200, mock.Mock(get=lambda k: None, get_content_charset=lambda: "utf-8")

            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        with mock.patch.object(ritmo, "espera") as esp, mock.patch("urllib.request.urlopen", lambda *a, **k: R()):
            self.assertEqual(fetch.get("https://t.es/a"), (200, "ok"))
        esp.assert_called_once_with("https://t.es/a")


class VigiladasEscalonadas(unittest.TestCase):
    def setUp(self):
        self.revisadas = []
        segs = [{"id": 1, "ultima": 500}, {"id": 2, "ultima": 100}, {"id": 3, "ultima": 300}]
        self.ps = [mock.patch.object(programador.seguimiento, "pendientes", lambda ahora=None: [s["id"] for s in segs if s["id"] not in self.revisadas]),
                   mock.patch.object(programador.seguimiento, "lista", lambda: segs),
                   mock.patch.object(programador.seguimiento, "revisa", lambda sid: self.revisadas.append(sid)),
                   mock.patch.object(programador, "_ultima_revision", [0.0])]
        for p in self.ps:
            p.start()

    def tearDown(self):
        for p in self.ps:
            p.stop()

    def test_una_cada_vez_y_la_que_mas_espera_primero(self):
        t = 10_000.0
        self.assertEqual(programador.vigiladas(t), 2)
        self.assertIsNone(programador.vigiladas(t + 60))                          # aún no han pasado 10 min
        self.assertEqual(programador.vigiladas(t + programador.ESPACIO_VIGILADAS), 3)
        self.assertEqual(programador.vigiladas(t + 2 * programador.ESPACIO_VIGILADAS), 1)
        self.assertEqual(self.revisadas, [2, 3, 1])


class VueltaSuave(unittest.TestCase):
    def test_al_volver_queda_unos_dias_con_una_pagina(self):
        lista = [{"host": "dm.es", "activa": False, "bloqueo": {"desde": 1, "probado": 0}}]
        guardada = []
        with mock.patch.object(programador.cfg, "carga", lambda: [dict(t, bloqueo=dict(t["bloqueo"])) if t.get("bloqueo") else dict(t) for t in lista]), \
                mock.patch.object(programador.cfg, "guarda", lambda l: guardada.append(l)), \
                mock.patch.object(programador.fetch, "get", lambda u, timeout=20: (200, "")), \
                mock.patch.object(programador.notifica, "envia", lambda *a: {}):
            programador.bloqueadas()
        t = guardada[-1][0]
        self.assertTrue(t["activa"])
        self.assertNotIn("bloqueo", t)
        self.assertGreater(t["suave_hasta"], time.time() + 2 * 86400)

    def test_buscar_pide_una_pagina_a_la_tienda_suave(self):
        tmp = tempfile.mkdtemp()
        tiendas = [{"host": "a.es", "activa": True, "plantilla": "https://a.es/?q={q}", "tipo": "tienda"},
                   {"host": "b.es", "activa": True, "plantilla": "https://b.es/?q={q}", "tipo": "tienda", "suave_hasta": time.time() + 3600}]
        paginas = {}
        with mock.patch.object(bd, "RUTA", os.path.join(tmp, "t.db")), mock.patch.object(motor.cfg, "carga", lambda: tiendas), \
                mock.patch.object(motor.cfg, "aplica_descubiertas", lambda c: None), \
                mock.patch.object(motor, "_tienda", lambda t, q, nav=None, pag=1: paginas.__setitem__(t["host"], pag) or (t["host"], [], None)):
            motor.buscar("algo", paginas=4)
        self.assertEqual(paginas, {"a.es": 4, "b.es": 1})


if __name__ == "__main__":
    unittest.main()
