"""v0.20.2: títulos con el nombre repetido y la marca entre medias (Aquí Mejor)."""
import unittest

from buscatron import extract


class TituloRepetido(unittest.TestCase):
    def test_se_queda_una_vez(self):
        t = "ASMODEE JUEGO DE MESA MARVEL CHAMPIONS LA PRÓXIMA EVOLUCIÓN ASMODEE ASMODEE JUEGO DE MESA MARVEL CHAMPIONS LA PRÓXIMA EVOLUCIÓN"
        self.assertEqual(extract.limpia_titulo(t), "ASMODEE JUEGO DE MESA MARVEL CHAMPIONS LA PRÓXIMA EVOLUCIÓN")

    def test_un_titulo_normal_no_cambia(self):
        for t in ("Marvel Champions: Héroes Reunidos 2", "Juego de mesa Marvel Champions juego de cartas Marvel Champions"):
            self.assertEqual(extract.limpia_titulo(t), t)



class AvisosAgrupados(unittest.TestCase):
    def test_variantes_del_mismo_producto_mismo_grupo(self):
        import os
        import tempfile
        import time
        from unittest import mock
        from buscatron import ajustes, bd, seguimiento
        d = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(d, "t.db")), mock.patch.object(ajustes, "RUTA", os.path.join(d, "c.json")):
            sid = seguimiento.guarda({"consulta": "marvel champions", "objetivo": "40", "opciones": {"alguna": "civil war, proxima evolucion"}})
            with bd.conecta() as c:
                for t, u in (("Marvel Champions LCG: Civil War Expansion", "a"), ("MARVEL CHAMPIONS CIVIL WAR EXPANSION", "b"),
                             ("Marvel Champions: La Próxima Evolución", "c")):
                    c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                              (time.time(), sid, t, "t.es", "https://t.es/" + u, 30, "m"))
            g = {a["url"][-1]: a["grupo"] for a in seguimiento.avisos()}
        self.assertEqual(g["a"], g["b"])
        self.assertNotEqual(g["a"], g["c"])


if __name__ == "__main__":
    unittest.main()
