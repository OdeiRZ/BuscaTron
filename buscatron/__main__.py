"""Uso: python -m buscatron            -> interfaz web en http://127.0.0.1:8790
       python -m buscatron "consulta"  -> búsqueda por línea de comandos"""
import sys

from . import motor, web

if len(sys.argv) > 1:
    res, inf = motor.buscar(" ".join(sys.argv[1:]))
    for x in res[:20]:
        print(f"{x['precio']:8.2f} € {'(agotado) ' if x['agotado'] else ''}{x['tienda']}  {x['titulo']}\n          {x['url']}")
else:
    web.sirve()
