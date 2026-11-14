"""v0.17.10: el lector de precios ya no toma por precio «2 Europa», «Ahorra 5 €», «10 € de descuento», el mínimo del
envío gratis ni el «€» de un precio leído otra vez con el número de detrás."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import extract, importar  # noqa: E402


def precio(tarjeta, consulta="catan"):
    r = extract.extrae(f'<a href="/p/1">{tarjeta[0]}</a>' + "".join(f"<span>{t}</span>" for t in tarjeta[1:]), "https://t.es/s?q=x", consulta)
    return r[0]["precio"] if r else None


class LectorDePrecios(unittest.TestCase):
    def test_eur_tiene_que_ser_la_palabra_entera(self):
        self.assertEqual(precio(["Ticket to Ride Europa", "Expansión 2 Europa", "39,95 €"], "ticket"), 39.95)
        self.assertIsNone(precio(["Catan juego 5 Eurogames"]))
        self.assertEqual(extract.precios_en("12 euros"), [12.0])
        self.assertEqual(extract.precios_en("EUR 12,50"), [12.5])

    def test_lo_que_ahorras_no_es_el_precio(self):
        self.assertEqual(precio(["Catan juego", "Ahorra 5 €", "29,95 €"]), 29.95)
        self.assertEqual(precio(["Catan juego", "3-4 jugadores · 10 € de descuento", "29,95 €"]), 29.95)
        self.assertEqual(extract.precios_en("Precio con descuento 29,95 €"), [29.95])

    def test_el_minimo_del_envio_gratis_no_es_el_precio(self):
        self.assertEqual(precio(["Catan juego", "Envío gratis desde 50 €", "29,95 €"]), 29.95)
        self.assertEqual(extract.precios_en("Desde 29,95 €"), [29.95])          # «desde» a secas sí es un precio

    def test_el_euro_no_se_lee_dos_veces(self):
        self.assertEqual(extract.precios_en("29,95 € 2 jugadores"), [29.95])
        self.assertEqual(extract.precios_en("-2,59 € 25,00 €"), [25.0])

    def test_numero_y_euro_separados_con_descuento(self):
        self.assertEqual(precio(["Catan juego", "<b>5</b> € de descuento", "<b>29,95</b> €"]), 29.95)

    def test_lo_pegado_usa_el_mismo_lector(self):
        items = importar.parsea("Catan juego base\n29,95 € 2 jugadores\n", "catan")
        self.assertEqual([x["precio"] for x in items], [29.95])


if __name__ == "__main__":
    unittest.main()
