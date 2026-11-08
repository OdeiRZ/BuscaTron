"""v0.13.1: editar o borrar una vigilada mientras se revisa, y «Buscando…» que dice el servidor."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, motor, seguimiento  # noqa: E402
from tests.test_v0114 import ConArchivos  # noqa: E402


class EditarMientrasSeRevisa(ConArchivos):
    def test_si_cambias_la_busqueda_se_repite_con_lo_nuevo(self):
        sid = seguimiento.guarda({"consulta": "vantage", "objetivo": "65"})
        vistas = []

        def buscar(consulta, *a, **k):
            vistas.append(consulta)
            if len(vistas) == 1:          # la editas mientras busca
                seguimiento.guarda({"id": sid, "consulta": "vantage stonemaier", "objetivo": "65"})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        self.assertEqual(vistas, ["vantage", "vantage stonemaier"])

    def test_cambiar_solo_el_nombre_o_pausarla_no_la_repite(self):
        sid = seguimiento.guarda({"consulta": "vantage", "objetivo": "65"})
        vistas = []

        def buscar(consulta, *a, **k):
            vistas.append(consulta)
            seguimiento.guarda({"id": sid, "nombre": "Vantage (juego)", "consulta": "vantage", "objetivo": "65", "activo": False})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        self.assertEqual(vistas, ["vantage"])

    def test_no_se_repite_sin_fin(self):
        sid = seguimiento.guarda({"consulta": "q0"})
        n = []

        def buscar(consulta, *a, **k):
            n.append(consulta)
            seguimiento.guarda({"id": sid, "consulta": f"q{len(n)}"})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        self.assertEqual(len(n), 3)


class BorrarMientrasSeRevisa(ConArchivos):
    def test_no_quedan_avisos_huerfanos(self):
        sid = seguimiento.guarda({"consulta": "vantage", "objetivo": "65"})

        def buscar(*a, **k):
            seguimiento.borra(sid)
            with bd.conecta() as c:       # lo que la revisión en curso habría guardado después de borrarla
                c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(1,?,'Vantage','a.es','https://a.es/v',60,'x')", (sid,))
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(sid)
        with bd.conecta() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM avisos WHERE seg_id=?", (sid,)).fetchone()[0], 0)


class EstadoRevisando(ConArchivos):
    def test_la_lista_dice_cual_se_esta_revisando(self):
        a = seguimiento.guarda({"consulta": "vantage"})
        b = seguimiento.guarda({"consulta": "eternal decks"})
        durante = {}

        def buscar(*a_, **k):
            durante.update({s["id"]: s["revisando"] for s in seguimiento.lista()})
            return [], {}
        with mock.patch.object(motor, "buscar", side_effect=buscar):
            seguimiento.revisa(a)
        self.assertEqual(durante, {a: True, b: False})
        self.assertFalse(any(s["revisando"] for s in seguimiento.lista()))

    def test_tras_un_fallo_deja_de_estar_revisandose(self):
        sid = seguimiento.guarda({"consulta": "vantage"})
        with mock.patch.object(motor, "buscar", side_effect=RuntimeError("se rompió")):
            with self.assertRaises(RuntimeError):
                seguimiento.revisa(sid)
        self.assertFalse(seguimiento.lista()[0]["revisando"])


if __name__ == "__main__":
    unittest.main()
