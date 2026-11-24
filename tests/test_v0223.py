"""v0.22.3: aviso cuando vuelve a haber stock."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, seguimiento


class VuelveStock(unittest.TestCase):
    def test_avisa_si_estaba_agotado(self):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            sid = seguimiento.guarda({"consulta": "x", "objetivo": "40"})
            with bd.conecta() as c:
                seg = dict(c.execute("SELECT * FROM seguimientos WHERE id=?", (sid,)).fetchone())
                ahora = time.time()
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id) VALUES(?,?,?,?,?,?,?,?)", (ahora - 3600, "x", "t", "X", "u", 44, 1, sid))
                c.execute("INSERT INTO precios(ts,consulta,tienda,titulo,url,precio,agotado,seg_id) VALUES(?,?,?,?,?,?,?,?)", (ahora - 3600, "x", "t", "X", "v", 44, 0, sid))
                self.assertIn("vuelve a estar disponible", seguimiento._motivo(c, seg, {"url": "u", "precio": 44, "_ts": ahora}))
                self.assertIsNone(seguimiento._motivo(c, seg, {"url": "v", "precio": 44, "_ts": ahora}))          # ya tenía stock
                self.assertIsNone(seguimiento._motivo(c, seg, {"url": "u", "precio": 60, "_ts": ahora}))          # muy lejos del objetivo


if __name__ == "__main__":
    unittest.main()
