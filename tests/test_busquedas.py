import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, busquedas  # noqa: E402


def resp(n=2):
    return {"resultados": [{"titulo": f"Juego {i}", "url": f"https://x/{i}", "precio": 10 + i} for i in range(n)], "total": 50,
            "informe": {"a.es": {"encontrados": n, "error": None}, "f.es": {"manual": "https://f.es/?q=x"}}, "webs": ["nueva.es"]}


class Busquedas(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch.object(bd, "RUTA", os.path.join(tempfile.mkdtemp(), "t.db"))
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_guarda_y_recupera_todo(self):
        bid, ts = busquedas.guarda({"q": "marvel champions", "pmin": "25", "tiendas": ["a.es"]}, resp())
        b = busquedas.obtiene(bid)
        self.assertEqual((b["id"], b["ts"], b["total"], b["webs"]), (bid, ts, 50, ["nueva.es"]))
        self.assertEqual([x["titulo"] for x in b["resultados"]], ["Juego 0", "Juego 1"])
        self.assertEqual(b["params"]["q"], "marvel champions")
        self.assertNotIn("tiendas", b["params"])                  # la lista de tiendas activas no forma parte de la búsqueda
        self.assertEqual(b["informe"]["f.es"]["manual"], "https://f.es/?q=x")
        self.assertIsNone(busquedas.obtiene(999))

    def test_lista_de_la_mas_reciente_a_la_mas_antigua_sin_resultados(self):
        a, _ = busquedas.guarda({"q": "uno"}, resp(1))
        b, _ = busquedas.guarda({"q": "dos"}, resp(3))
        l = busquedas.lista()
        self.assertEqual([(x["consulta"], x["mostrados"]) for x in l], [("dos", 3), ("uno", 1)])
        self.assertNotIn("resultados", l[0])

    def test_repetir_la_misma_busqueda_sustituye_a_la_anterior(self):
        busquedas.guarda({"q": "uno", "pmin": "5"}, resp(1))
        busquedas.guarda({"q": "uno", "pmin": "10"}, resp(1))      # otros filtros: es otra
        busquedas.guarda({"q": "uno", "pmin": "5"}, resp(4))       # igual que la primera: la sustituye
        self.assertEqual([x["mostrados"] for x in busquedas.lista()], [4, 1])

    def test_solo_se_conservan_las_ultimas(self):
        for i in range(busquedas.MAXIMO + 5):
            busquedas.guarda({"q": f"b{i}"}, resp(1))
        l = busquedas.lista()
        self.assertEqual(len(l), busquedas.MAXIMO)
        self.assertEqual(l[0]["consulta"], f"b{busquedas.MAXIMO + 4}")
        self.assertEqual(l[-1]["consulta"], "b5")

    def test_actualizar_borrar_y_vaciar(self):
        a, ts = busquedas.guarda({"q": "uno"}, resp(1))
        b, _ = busquedas.guarda({"q": "dos"}, resp(1))
        busquedas.actualiza(a, [{"titulo": "Importado", "url": "https://x/z", "precio": 1}])
        self.assertEqual(busquedas.obtiene(a)["resultados"][0]["titulo"], "Importado")
        self.assertEqual(busquedas.obtiene(a)["ts"], ts)           # la fecha no cambia
        busquedas.borra(a)
        self.assertEqual([x["id"] for x in busquedas.lista()], [b])
        busquedas.vacia()
        self.assertEqual(busquedas.lista(), [])


if __name__ == "__main__":
    unittest.main()
