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


if __name__ == "__main__":
    unittest.main()
