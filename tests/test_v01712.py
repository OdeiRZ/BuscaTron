"""v0.17.12: la búsqueda abierta descarta los resultados del buscador que no hablan de lo buscado."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import abierta  # noqa: E402

BING = ('<li class="b_algo"><h2><a href="https://tienda.es/mage-knight-edicion-definitiva">Mage Knight Edición Definitiva | Tienda</a></h2></li>'
        '<li class="b_algo"><h2><a href="https://www.mage.space/">Unlimited <b>AI</b> Image Generator | Mage</a></h2></li>'
        '<li class="b_algo"><h2><a href="https://www.idealista.com/">idealista — Casas y pisos</a></h2></li>')


class Relevancia(unittest.TestCase):
    def test_solo_lo_que_habla_de_lo_buscado(self):
        self.assertTrue(abierta.relevante("Mage Knight Edición Definitiva | Tienda", "https://t.es/x", "Mage Knight Edición Definitiva"))
        self.assertFalse(abierta.relevante("Mage | AI Image Generator", "https://www.mage.space/", "Mage Knight Edición Definitiva"))

    def test_buscadores_se_queda_con_lo_relevante(self):
        with mock.patch.object(abierta.fetch, "get", lambda u, timeout=15: (200, BING)):
            urls, _ = abierta.buscadores("Mage Knight Edición Definitiva", paginas=1)
        self.assertEqual(urls, ["https://tienda.es/mage-knight-edicion-definitiva"])


if __name__ == "__main__":
    unittest.main()
