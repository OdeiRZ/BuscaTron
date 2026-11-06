import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import motor  # noqa: E402


class Idioma(unittest.TestCase):
    def test_detecta_otros_idiomas(self):
        for t in ("Marvel Champions: Civil War Expansion (Inglés)", "Hero pack ingles", "Jeu en Français", "Edición English"):
            self.assertTrue(motor.en_otro_idioma(t), t)

    def test_castellano_o_sin_marca_no_se_filtra(self):
        for t in ("Marvel Champions: Civil War (Castellano)", "Marvel Champions: Vision",
                  "Pack de héroe (Inglés / Castellano)", "Marvel Champions: Edición en español"):
            self.assertFalse(motor.en_otro_idioma(t), t)


if __name__ == "__main__":
    unittest.main()
