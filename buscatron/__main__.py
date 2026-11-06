"""Uso: python -m buscatron                    -> interfaz web en http://127.0.0.1:8790
       python -m buscatron --host 0.0.0.0     -> accesible desde otros equipos (sin contraseña: úsalo solo en red de confianza)
       python -m buscatron "consulta"          -> búsqueda por línea de comandos"""
import argparse

from . import motor, web

ap = argparse.ArgumentParser(prog="buscatron")
ap.add_argument("consulta", nargs="*")
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--puerto", type=int, default=8790)
ap.add_argument("--abrir", action="store_true", help="abre el navegador al arrancar")
a = ap.parse_args()
if a.consulta:
    res, _ = motor.buscar(" ".join(a.consulta))
    for x in res[:20]:
        print(f"{x['precio']:8.2f} € {'(agotado) ' if x['agotado'] else ''}{x['tienda']}  {x['titulo']}\n          {x['url']}")
else:
    web.sirve(a.puerto, a.host, a.abrir)
