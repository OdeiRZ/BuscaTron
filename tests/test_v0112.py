"""Tiendas caídas frente a tiendas sin ese producto, mensajes largos de Telegram y conexiones cortadas."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from buscatron import bd, motor, notifica, seguimiento, web  # noqa: E402


class Caidas(unittest.TestCase):
    def test_sin_coincidencias_no_es_una_caida(self):
        self.assertFalse(motor.es_caida(None))
        self.assertFalse(motor.es_caida(motor.SIN_COINCIDENCIAS))
        self.assertFalse(motor.es_caida(motor.SIN_COINCIDENCIAS + " (quizá solo la lea un navegador: activa «Usar Chrome» en Ajustes)"))
        self.assertTrue(motor.es_caida("no se pudo conectar (The read operation timed out)"))
        self.assertTrue(motor.es_caida(motor.DESAFIO))
        self.assertTrue(motor.es_caida("rechaza las consultas automáticas (error 403)"))

    def test_limpieza_de_avisos_solo_respeta_las_tiendas_caidas(self):
        tmp = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(tmp, "t.db")):
            with bd.conecta() as c:
                for tienda in ("a.es", "b.es"):
                    c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(1,7,'x',?,?,10,'m')",
                              (tienda, f"https://{tienda}/x"))
            informe = {"a.es": {"encontrados": 0, "error": motor.SIN_COINCIDENCIAS, "caida": False},     # respondió sin el producto
                       "b.es": {"encontrados": 0, "error": "no se pudo conectar (timeout)", "caida": True}}
            seguimiento.limpia_avisos(7, [], informe)
            with bd.conecta() as c:
                self.assertEqual([r[0] for r in c.execute("SELECT tienda FROM avisos")], ["b.es"])


class Textos(unittest.TestCase):
    def test_productos_y_ofertas(self):
        res = [{"grupo": "a", "url": "1", "precio": 1}, {"grupo": "a", "url": "2", "precio": 2}, {"grupo": "b", "url": "3", "precio": 3}]
        self.assertEqual(seguimiento.productos(res), "2 productos (3 ofertas)")
        self.assertEqual(seguimiento.productos(res[:1]), "1 producto (1 oferta)")

    def test_que_vigiladas_cubren_un_producto(self):
        tmp = tempfile.mkdtemp()
        with mock.patch.object(bd, "RUTA", os.path.join(tmp, "t.db")):
            seguimiento.guarda({"nombre": "Cráneo", "consulta": "tirania craneo rojo", "excluir": "funda"})
            seguimiento.guarda({"nombre": "Caras", "consulta": "marvel champions", "pmin": "50"})
            seguimiento.guarda({"nombre": "Pausada", "consulta": "tirania", "activo": False})
            t = "Marvel Champions: La Tiranía de Cráneo Rojo"
            self.assertEqual(seguimiento.cubren(t, 30), ["Cráneo"])                  # «Caras» exige 50 € o más
            self.assertEqual(seguimiento.cubren(t, 60), ["Cráneo", "Caras"])
            self.assertEqual(seguimiento.cubren("Funda Tiranía de Cráneo Rojo", 30), [])
            self.assertEqual(seguimiento.cubren("Marvel Champions: Civil War", 30), [])


class Trocea(unittest.TestCase):
    def test_corto_va_en_un_mensaje(self):
        self.assertEqual(notifica.trocea("hola\n\nadiós"), ["hola\n\nadiós"])

    def test_largo_se_parte_entre_productos(self):
        parrafos = [f"Producto {i}\n" + "x" * 300 for i in range(40)]
        trozos = notifica.trocea("\n\n".join(parrafos))
        self.assertGreater(len(trozos), 1)
        self.assertTrue(all(len(t) <= notifica.MAX_TELEGRAM for t in trozos))
        self.assertEqual("\n\n".join(trozos), "\n\n".join(parrafos))

    def test_parrafo_enorme_se_corta(self):
        trozos = notifica.trocea("y" * 9000)
        self.assertEqual([len(t) for t in trozos], [4000, 4000, 1000])

    def test_telegram_envia_cada_trozo(self):
        enviados = []

        class R:
            def __init__(self, req):
                enviados.append(req.data)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self, *a):
                return b'{"ok": true}'

        with mock.patch.object(notifica.urllib.request, "urlopen", lambda req, timeout: R(req)):
            notifica.telegram("\n\n".join("z" * 3000 for _ in range(3)), {"telegram_token": "t", "telegram_chat": "1"})
        self.assertEqual(len(enviados), 3)


class ConexionCortada(unittest.TestCase):
    def test_no_se_anota_en_el_log(self):
        s = web.Servidor.__new__(web.Servidor)
        with mock.patch("socketserver.BaseServer.handle_error") as base:
            try:
                raise ConnectionResetError(10054, "cortada")
            except ConnectionResetError:
                s.handle_error(None, ("192.168.0.15", 1))
            base.assert_not_called()
            try:
                raise RuntimeError("otro fallo")
            except RuntimeError:
                s.handle_error(None, ("192.168.0.15", 1))
            base.assert_called_once()


if __name__ == "__main__":
    unittest.main()
