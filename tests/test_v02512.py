"""v0.25.12: quinta revisión de código."""
import os
import tempfile
import unittest
from unittest import mock

from buscatron import ajustes, bd, motor, ritmo, seguimiento, tiendas


class Arreglos(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.p = [mock.patch.object(m, "RUTA", os.path.join(d, n)) for m, n in ((bd, "t.db"), (ajustes, "c.json"), (tiendas, "l.json"))]
        for p in self.p:
            p.start()
        motor._alias_leido[0] = None

    def tearDown(self):
        for p in reversed(self.p):
            p.stop()
        motor._alias_leido[0] = None

    def test_sin_el_juego_no_se_para(self):
        tiendas.guarda([{"host": "a.es", "activa": True, "plantilla": None}])
        for _ in range(4):
            motor.para_inservibles({"a.es": {"brutos": 0, "encontrados": 0, "error": motor.SIN_COINCIDENCIAS}}, {"a.es": tiendas.carga()[0]})
        self.assertTrue(tiendas.carga()[0]["activa"])

    def test_bloqueada_aunque_falle_leer_el_archivo(self):
        tiendas.guarda([{"host": "dm.es", "activa": False, "bloqueo": {"desde": 1}}])
        ritmo._bloqueadas[:] = [None, frozenset()]
        with mock.patch.object(ritmo, "__name__", "x"), mock.patch("os.stat", side_effect=PermissionError("en uso")):
            self.assertRaises(ritmo.Prohibida, ritmo._comprueba, "dm.es")

    def test_bloqueo_seguido_de_otra_escritura(self):
        tiendas.guarda([{"host": "dm.es", "activa": True}])
        ritmo._comprueba("dm.es")
        tiendas.guarda([{"host": "dm.es", "activa": False, "bloqueo": {"desde": 1}}])     # sin esperar: misma fecha posible
        self.assertRaises(ritmo.Prohibida, ritmo._comprueba, "dm.es")

    def test_la_fusion_se_recuerda(self):
        corto, largo = "La Tiranía de Cráneo Rojo (Expansión Marvel Champions)", "Marvel Champions La Tiranía de Cráneo Rojo | Cinco escenarios"
        g = [x["grupo"] for x in motor.grupos([corto, largo], "tirania craneo rojo")]
        self.assertEqual(g[0], g[1])
        self.assertEqual(motor.grupos([largo], "tirania craneo rojo")[0]["grupo"], g[0])      # sola, va al mismo grupo

    def test_ant_man_no_se_traga(self):
        self.assertEqual(len({x["grupo"] for x in motor.grupos(["Marvel Champions", "Marvel Champions Ant-Man"], "ant man")}), 2)

    def test_maximo_como_aviso_al_vuelo(self):
        sid = seguimiento.guarda({"consulta": "x", "pmax": "39"})
        seguimiento.guarda({"id": sid, "consulta": "x", "pmax": "50"})
        s = next(s for s in seguimiento.lista() if s["id"] == sid)
        self.assertEqual((s["objetivo"], seguimiento.objetivo_de(s)), (None, 50))

    def test_vistos_no_pasa_del_ultimo_aviso(self):
        with bd.conecta() as c:
            c.execute("INSERT INTO avisos(id,seg_id,ts,tienda,titulo,url,precio) VALUES(5,1,1,'t','X','u',1)")
        ajustes.guarda({"avisos_vistos": 97})
        self.assertEqual(seguimiento.marca_vistos(0), 5)
        self.assertEqual(seguimiento.marca_vistos(3), 5)


if __name__ == "__main__":
    unittest.main()
