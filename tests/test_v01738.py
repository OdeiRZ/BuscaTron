"""v0.17.38: qué tipo de producto es cada resultado (juego, expansión, complemento, accesorio), lo que seguro que no es un juego
se descarta en todas las tiendas y cada vigilada elige qué tipos quiere. Lo que no se reconoce cuenta como juego: nunca se descarta."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import motor, seguimiento  # noqa: E402


class Tipos(unittest.TestCase):
    def test_tipos(self):
        casos = {"Marvel Champions: El Juego de Cartas": "juego",
                 "Vantage": "juego",                                            # no dice «juego» y es un juego
                 "Heat: Pedal to the Metal": "juego",
                 "Marvel Champions: Civil War - Expansión de campaña": "expansion",
                 "Too Many Bones: Gasket Add-on": "complemento",
                 "Too Many Bones Character - Tink": "complemento",
                 "Marvel Champions: Wolverine Pack de Héroe": "expansion",
                 "Asmodee Marvel Champions Trickster Takeover, Pack de Escenario": "expansion",
                 "Fundas Mayday Premium 63,5 x 88": "accesorio",
                 "Tapete de neopreno Marvel Champions": "accesorio",
                 "Organizador para Gloomhaven": "accesorio",
                 "Dune Imperium: Linajes (+ Promo)": "juego",
                 "DUNE IMPERIUM: Inmmortalidad+ Promo": "juego",
                 "Marvel Champions Promo Card": "complemento"}
        self.assertEqual({t: motor.tipo_de(t) for t in casos}, casos)

    def test_no_juego(self):
        for t in ("Talla: 45 - Under Armour Zapatillas Charged Vantage 2", "Rociador Berthoud Vantage", "Camiseta Marvel Talla M", "Protector de pantalla para Polar Vantage V3", "Correa para Polar Vantage V2"):
            self.assertTrue(motor.es_no_juego(t), t)
        for t in ("Vantage", "Guerra del Anillo", "Dixit", "Agentes de S.H.I.E.L.D."):
            self.assertFalse(motor.es_no_juego(t), t)

    def seg(self, tipos=None):
        return {"consulta": "too many bones", "incluir": "", "excluir": "", "pmin": None, "pmax": None,
                "opciones": {"tipos": tipos or [], "alguna": ""}}

    def test_vigilada_sin_tipos_quiere_todo(self):
        s = self.seg()
        self.assertTrue(all(seguimiento.cumple(s, t) for t in ("Too Many Bones", "Too Many Bones Gasket Add-on", "Too Many Bones fundas")))

    def test_vigilada_solo_juego_base(self):
        s = self.seg(["juego"])
        self.assertTrue(seguimiento.cumple(s, "Too Many Bones"))
        self.assertFalse(seguimiento.cumple(s, "Too Many Bones Gasket Add-on"))
        self.assertFalse(seguimiento.cumple(s, "Too Many Bones Undertow expansión"))

    def test_lo_que_no_es_juego_nunca_cumple(self):
        self.assertFalse(seguimiento.cumple(self.seg(), "Too Many Bones camiseta talla 42"))

    def test_las_opciones_guardan_solo_tipos_validos(self):
        self.assertEqual(seguimiento._opciones({"tipos": ["juego", "pepino", "expansion"]})["tipos"], ["juego", "expansion"])
        self.assertEqual(seguimiento._opciones({})["tipos"], [])


if __name__ == "__main__":
    unittest.main()
