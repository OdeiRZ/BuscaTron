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
            self.assertEqual((t["hechas"], t["total"], t["parte"]), (2, 4, 0.5))
            self.assertIsNotNone(t["queda"])
        self.assertEqual(progreso.lista(), [])
        self.assertIsNone(progreso.actual())

    def test_sin_tarea_no_hace_nada(self):
        progreso.total(None, 3)
        progreso.avanza(None)
        self.assertEqual(progreso.lista(), [])


if __name__ == "__main__":
    unittest.main()
