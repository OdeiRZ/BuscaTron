"""v0.19.9: progreso de búsquedas y revisiones para la barra de carga."""
import threading
import unittest

from buscatron import progreso


class Progreso(unittest.TestCase):
    def test_cuenta_tiendas_y_desaparece_al_acabar(self):
        with progreso.tarea("busqueda:x", "busqueda", "marvel"):
            clave = progreso.actual()
            progreso.total(clave, 4)
            hilos = [threading.Thread(target=progreso.avanza, args=(clave,)) for _ in range(2)]   # desde los hilos de las tiendas
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
            t = progreso.lista()[0]
            self.assertEqual((t["hechas"], t["total"], t["parte"]), (2, 4, 0.4))     # las tiendas son el 80 % de la barra
            self.assertIsNotNone(t["queda"])
        self.assertEqual(progreso.lista(), [])
        self.assertIsNone(progreso.actual())

    def test_con_todas_las_tiendas_no_marca_100_si_suele_tardar_mas(self):
        from unittest import mock
        with mock.patch.object(progreso.time, "time", return_value=1000.0):
            with progreso.tarea("vigilada:1", "vigilada", "MC", estimado=400):
                progreso.total("vigilada:1", 10)
                for _ in range(10):
                    progreso.avanza("vigilada:1")
                progreso.fase("vigilada:1", "Buscando en otras webs")
                with mock.patch.object(progreso.time, "time", return_value=1200.0):     # a mitad de lo que suele tardar
                    t = progreso.lista()[0]
        self.assertEqual(t["parte"], 0.8)          # las tiendas hechas, pero aún queda trabajo
        self.assertAlmostEqual(t["queda"], 200)

    def test_si_tarda_mas_de_lo_normal_no_inventa_lo_que_queda(self):
        from unittest import mock
        with mock.patch.object(progreso.time, "time", return_value=0.0):
            with progreso.tarea("vigilada:2", "vigilada", "MC", estimado=100):
                with mock.patch.object(progreso.time, "time", return_value=150.0):
                    t = progreso.lista()[0]
        self.assertEqual((t["parte"], t["queda"]), (0.99, None))

    def test_sin_tarea_no_hace_nada(self):
        progreso.total(None, 3)
        progreso.avanza(None)
        self.assertEqual(progreso.lista(), [])


if __name__ == "__main__":
    unittest.main()
