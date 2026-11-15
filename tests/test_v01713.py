"""v0.17.13: la búsqueda abierta usa Brave Search con la clave del usuario (y Bing solo si no hay clave o falla)."""
import io
import json
import os
import sys
import urllib.error
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import abierta, ajustes  # noqa: E402

RESPUESTA = {"web": {"results": [
    {"title": "Mage Knight Edición Definitiva", "url": "https://tienda.es/mage-knight", "description": "Juego de mesa en castellano"},
    {"title": "Mage AI", "url": "https://www.mage.ai/", "description": "Data pipelines"}]}}


class Resp(io.BytesIO):
    headers = mock.Mock(get=lambda k: None)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def con_clave(clave):
    return mock.patch.object(abierta.ajustes, "carga", lambda: {"busqueda_clave": clave})


class PorApi(unittest.TestCase):
    def test_con_clave_usa_brave_y_filtra(self):
        peticiones = []

        def abre(req, timeout=0):
            peticiones.append((req.full_url, req.get_header("X-subscription-token")))
            return Resp(json.dumps(RESPUESTA).encode())
        with con_clave("K"), mock.patch("urllib.request.urlopen", abre), mock.patch.object(abierta.time, "sleep"):
            urls, err = abierta.buscadores("Mage Knight Edición Definitiva")
        self.assertEqual(urls, ["https://tienda.es/mage-knight"])
        self.assertEqual(err, [])
        self.assertTrue(all(t == "K" and u.startswith(abierta.BRAVE) for u, t in peticiones))
        self.assertEqual(len(peticiones), 2)

    def test_limite_gastado_cae_a_bing_y_lo_dice(self):
        def abre(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 429, "x", {}, None)
        bing = '<li class="b_algo"><h2><a href="https://t.es/mage-knight-edicion-definitiva">Mage Knight Edición Definitiva</a></h2></li>'
        with con_clave("K"), mock.patch("urllib.request.urlopen", abre), mock.patch.object(abierta.time, "sleep"), \
                mock.patch.object(abierta.fetch, "get", lambda u, timeout=15: (200, bing)):
            urls, err = abierta.buscadores("Mage Knight Edición Definitiva", paginas=1)
        self.assertEqual(urls, ["https://t.es/mage-knight-edicion-definitiva"])
        self.assertIn("límite", err[0])

    def test_sin_clave_no_llama_a_brave(self):
        with con_clave(""), mock.patch("urllib.request.urlopen", side_effect=AssertionError("no debía llamar")), \
                mock.patch.object(abierta.fetch, "get", lambda u, timeout=15: (200, "")):
            self.assertEqual(abierta.buscadores("algo", paginas=1)[0], [])

    def test_la_clave_se_enmascara_en_ajustes(self):
        self.assertIn("busqueda_clave", ajustes.SECRETOS)


if __name__ == "__main__":
    unittest.main()
