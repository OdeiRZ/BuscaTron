"""Uso: python -m buscatron                     -> interfaz web en http://127.0.0.1:8790
       python -m buscatron --bandeja           -> igual, con icono en la bandeja de Windows (sin ventana de mensajes)
       python -m buscatron --host 127.0.0.1    -> solo accesible desde este equipo
       python -m buscatron --arranque on       -> arrancar con Windows (off para quitarlo, estado para consultarlo)
       python -m buscatron "consulta"          -> búsqueda por línea de comandos"""
import argparse
import os
import sys

from . import motor, tiendas as cfg, web

if sys.stdout is None or sys.stderr is None:      # pythonw (arranque con Windows): sin consola, los mensajes van a un archivo
    _ruta_log = os.path.join(cfg.RAIZ, "buscatron.log")
    try:
        if os.path.getsize(_ruta_log) > 2_000_000:   # se guarda el anterior como .log.1 y se empieza otro
            os.replace(_ruta_log, _ruta_log + ".1")
    except OSError:
        pass
    _log = open(_ruta_log, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log

ap = argparse.ArgumentParser(prog="buscatron")
ap.add_argument("consulta", nargs="*")
ap.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = accesible desde la red local; 127.0.0.1 = solo este equipo")
ap.add_argument("--puerto", type=int, default=8790)
ap.add_argument("--abrir", action="store_true", help="abre el navegador al arrancar")
ap.add_argument("--bandeja", action="store_true", help="icono en la bandeja de Windows; oculta la ventana de mensajes")
ap.add_argument("--arranque", choices=["on", "off", "estado"], help="activa, desactiva o consulta el arranque con Windows")
a = ap.parse_args()

if a.arranque:
    from . import arranque
    try:
        if a.arranque == "on":
            arranque.activa()
        elif a.arranque == "off":
            arranque.desactiva()
    except RuntimeError as e:
        sys.exit(str(e))
    print("Arranque con Windows:", "activado" if arranque.activo() else "desactivado")
elif a.consulta:
    res, _ = motor.buscar(" ".join(a.consulta))
    for x in res[:20]:
        print(f"{x['precio']:8.2f} € {'(agotado) ' if x['agotado'] else ''}{x['tienda']}  {x['titulo']}\n          {x['url']}")
else:
    try:
        web.sirve(a.puerto, a.host, a.abrir, a.bandeja)
    except BaseException:                          # si algo falla, la ventana de mensajes vuelve a verse para poder leerlo
        if a.bandeja:
            from . import bandeja
            bandeja.muestra_consola(True)
        raise
