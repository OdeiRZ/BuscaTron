"""v0.21.0: revisiones y pegados deciden los avisos con la misma función."""
import os
import tempfile
import time
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, seguimiento


def items():
    base = {"tienda": "t.es", "agotado": False, "preventa": False, "idioma": "es", "idioma_seguro": True}
    return [{**base, "titulo": "Marvel Hulk", "precio": 30.0, "url": "https://t.es/a"},
            {**base, "titulo": "Marvel Thor", "precio": 31.0, "url": "https://t.es/b", "agotado": True},       # agotado: no
            {**base, "titulo": "Marvel Loki", "precio": 32.0, "url": "https://t.es/c", "preventa": True},      # preventa: no
            {**base, "titulo": "Marvel Wasp", "precio": 33.0, "url": "https://t.es/d", "idioma": "en"},       # inglés: no
            {**base, "titulo": "Marvel Ant", "precio": 34.0, "url": "https://t.es/e", "importado": time.time() - 3600},
            {**base, "titulo": "Marvel Caro", "precio": 50.0, "url": "https://t.es/f"}]                        # sobre el objetivo: no


class MismaDecision(unittest.TestCase):
    def decide(self, por_pegado):
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")), \
             mock.patch.object(motor, "buscar", lambda *a, **k: ([dict(x) for x in items()], {"t.es": {"encontrados": 6}})), \
             mock.patch.object(motor, "ficha", return_value={"idioma": None, "agotado": None, "preventa": None}), \
             mock.patch.object(seguimiento.notifica, "envia", return_value={}):
            sid = seguimiento.guarda({"consulta": "marvel", "objetivo": "40", "opciones": {"idioma": "castellano"}})
            if por_pegado:
                with bd.conecta() as c:
                    seg = dict(c.execute("SELECT * FROM seguimientos WHERE id=?", (sid,)).fetchone())
                seguimiento._avisa_pegados_en(seg, "t.es", enviar=False)
            else:
                seguimiento.revisa(sid, enviar=False)
            return sorted((a["url"], a["motivo"].split(" · ")[1:]) for a in seguimiento.avisos())

    def test_revision_y_pegado_avisan_igual(self):
        r, p = self.decide(False), self.decide(True)
        self.assertEqual(r, p)
        self.assertEqual([u for u, _ in r], ["https://t.es/a", "https://t.es/e"])
        self.assertIn("precio pegado a mano hace 1 h, sin comprobar en directo", dict(r)["https://t.es/e"])


if __name__ == "__main__":
    unittest.main()
