"""v0.22.0: envío de cada tienda (lo tuyo o lo que anuncia su web) y avisos por el precio final."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento


class Envio(unittest.TestCase):
    def test_lo_tuyo_manda_y_si_no_lo_de_su_web(self):
        auto = {"envio_auto": {"coste": 4.95, "gratis_desde": 50.0}}
        self.assertEqual(motor.envio_de(auto, 30), 4.95)
        self.assertEqual(motor.envio_de(auto, 60), 0.0)
        self.assertEqual(motor.envio_de({**auto, "envio": 2.5}, 60), 2.5)       # pusiste tú el envío (sin «gratis desde»)
        self.assertIsNone(motor.envio_de({}, 30))

    def test_la_pagina_de_resultados_dice_el_envio(self):
        motor._envio_visto.clear()
        motor._apunta_envio("t.es", "<html><body><p>¡Envío gratis a partir de 49 €!</p></body></html>")
        self.assertEqual(motor._envio_visto["t.es"]["gratis_desde"], 49.0)
        motor._envio_visto.clear()


class AvisoConEnvio(unittest.TestCase):
    def test_compara_el_precio_final(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            sid = seguimiento.guarda({"consulta": "x", "objetivo": "40", "opciones": {"con_envio": True}})
            seg = next(s for s in seguimiento.lista() if s["id"] == sid)
            with bd.conecta() as c:
                caro = seguimiento._motivo(c, seg, {"precio": 38, "envio": 4.95, "url": "u", "_ts": 0})
                bien = seguimiento._motivo(c, seg, {"precio": 34, "envio": 4.95, "url": "u", "_ts": 0})
        self.assertIsNone(caro)                        # 38 + 4,95 = 42,95: no llega
        self.assertIn("38,95 € con envío", bien)


if __name__ == "__main__":
    unittest.main()
