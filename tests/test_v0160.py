"""v0.16.0: reiniciar y cerrar desde la web, como en PixelatIA (nunca con un trabajo en marcha)."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import servicio, web  # noqa: E402


class Salir(unittest.TestCase):
    def setUp(self):
        servicio._saliendo["si"] = False

    def tearDown(self):
        servicio._saliendo["si"] = False

    def _sale(self, reiniciar, entorno=None):
        """Ejecuta la salida sin salir de verdad: devuelve (código, se relanzó, servidor detenido)."""
        srv, hecho = mock.Mock(), {}
        with mock.patch.object(servicio.threading, "Timer", lambda t, f: mock.Mock(start=f)), \
                mock.patch.object(servicio.os, "_exit", lambda c: hecho.setdefault("codigo", c)), \
                mock.patch.object(servicio, "_relanza", lambda: hecho.setdefault("relanza", True)), \
                mock.patch.dict(os.environ, entorno or {}, clear=False):
            os.environ.pop("BUSCATRON_LANZADOR", None) if not entorno else None
            servicio.sale(reiniciar, srv)
        return hecho.get("codigo"), hecho.get("relanza", False), srv.shutdown.called or srv.server_close.called

    def test_con_un_trabajo_en_marcha_no_reinicia_ni_cierra(self):
        with servicio.trabajo("busqueda"):
            for reiniciar in (True, False):
                with self.assertRaises(ValueError) as e:
                    servicio.sale(reiniciar)
                self.assertIn("una búsqueda en marcha", str(e.exception))
        self.assertFalse(servicio.saliendo())

    def test_reiniciar_sale_con_3_y_se_relanza_sin_bat(self):
        self.assertEqual(self._sale(True), (3, True, False))   # no se detiene el servidor: va en el hilo principal (9/11)

    def test_con_el_bat_lo_relanza_el_bat(self):
        self.assertEqual(self._sale(True, {"BUSCATRON_LANZADOR": "bat"}), (3, False, False))

    def test_cerrar_sale_con_0(self):
        self.assertEqual(self._sale(False), (0, False, False))

    def test_mientras_sale_no_empieza_busquedas(self):
        servicio._saliendo["si"] = True
        with self.assertRaises(ValueError):
            web.busca({"q": "catan"})


class SiFallaElRelanzamientoSaleIgual(unittest.TestCase):
    def test_sale_aunque_no_pueda_lanzar_el_nuevo(self):
        hecho = {}
        with mock.patch.object(servicio.threading, "Timer", lambda t, f: mock.Mock(start=f)),                 mock.patch.object(servicio.os, "_exit", lambda c: hecho.setdefault("codigo", c)),                 mock.patch.object(servicio, "_relanza", mock.Mock(side_effect=OSError("no"))):
            os.environ.pop("BUSCATRON_LANZADOR", None)
            servicio._saliendo["si"] = False
            try:
                servicio.sale(True)
            except OSError:
                pass
            finally:
                servicio._saliendo["si"] = False
        self.assertEqual(hecho.get("codigo"), 3)


class Estado(unittest.TestCase):
    def test_codigo_cambiado(self):
        self.assertFalse(servicio.desactualizado())
        with mock.patch.object(servicio, "FECHAS", [0] * len(servicio.ARCHIVOS)):
            self.assertTrue(servicio.desactualizado())

    def test_que_hay_en_marcha(self):
        self.assertEqual(servicio.ocupado(), "")
        with servicio.trabajo("revision"), servicio.trabajo("revision"), servicio.trabajo("telegram"):
            self.assertEqual(servicio.ocupado(), "2 × una revisión de una vigilada, una búsqueda del bot de Telegram")
        self.assertEqual(servicio.ocupado(), "")


if __name__ == "__main__":
    unittest.main()
