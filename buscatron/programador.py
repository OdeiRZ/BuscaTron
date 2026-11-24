"""Hilo de tareas periódicas: lanza las búsquedas vigiladas cuando les toca, compacta el historial
los precios pegados a mano y, una vez al día, compacta el historial."""
import threading
import time
import traceback

from . import ajustes, bd, seguimiento, tiendas as cfg

LIMPIEZA_HORAS = 24
SUAVE_DIAS = 3             # al volver, unos días con una sola página por búsqueda
ESPACIO_VIGILADAS = 10 * 60    # entre dos revisiones automáticas: así cada tienda ve unas pocas peticiones repartidas
_ultima_revision = [0.0]
_hilo = [None]             # la revisión automática en marcha (en su hilo, para no frenar el resto de tareas)


def vigiladas(ahora=None, hilo=False):
    """Revisa la vigilada que más tiempo lleva esperando, y solo si la anterior revisión automática fue hace al menos
    ESPACIO_VIGILADAS y ya acabó: nunca todas seguidas (las de «Buscar ahora» no esperan). Las que ya se están revisando
    (p. ej. con «Buscar ahora») se saltan sin gastar el turno. hilo=True: la revisión va en su propio hilo."""
    ahora = ahora or time.time()
    if _hilo[0] is not None and _hilo[0].is_alive():
        return None
    if ahora - _ultima_revision[0] < ESPACIO_VIGILADAS:
        return None
    segs = {s["id"]: s for s in seguimiento.lista()}
    pendientes = [i for i in seguimiento.pendientes(ahora) if not segs.get(i, {}).get("revisando")]
    if not pendientes:
        return None
    sid = min(pendientes, key=lambda i: segs.get(i, {}).get("ultima", 0))
    _ultima_revision[0] = ahora
    if hilo:
        _hilo[0] = threading.Thread(target=_revisa, args=(sid,), daemon=True, name="vigilada")
        _hilo[0].start()
    else:
        seguimiento.revisa(sid)
    return sid


def _revisa(sid):
    try:
        seguimiento.revisa(sid)
    except Exception:
        traceback.print_exc()


def recordatorios():
    """Desactivado: por Telegram solo van los cambios de límites y objetivos de tus juegos (lo pidió así). Los precios pegados
    a mano siguen caducando igual y la web lo muestra en «Tiendas que tienes que mirar tú»."""


def limpieza():
    a = ajustes.carga()
    if time.time() - float(a.get("ultima_limpieza") or 0) < LIMPIEZA_HORAS * 3600:
        return
    try:
        copia_de_seguridad()
    except Exception:              # noqa: BLE001  (disco lleno, archivo en uso…: la limpieza sigue y mañana se reintenta)
        traceback.print_exc()
    borradas = bd.limpia()
    ajustes.guarda({"ultima_limpieza": time.time()})
    print("Limpieza del historial:", borradas)


COPIAS = 7


def copia_de_seguridad():
    """Una copia de la base de datos al día en la carpeta «copias» (se guardan las COPIAS últimas). Se hace con la copia
    en caliente de SQLite: vale aunque BuscaTron esté escribiendo."""
    import os
    import sqlite3
    carpeta = os.path.join(cfg.RAIZ, "copias")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, time.strftime("buscatron-%Y%m%d.db"))
    origen = sqlite3.connect(bd.RUTA)
    try:
        copia = sqlite3.connect(destino + ".tmp")
        try:
            origen.backup(copia)
        finally:
            copia.close()
        os.replace(destino + ".tmp", destino)      # solo si se copió entera
    finally:
        origen.close()
    viejas = sorted(f for f in os.listdir(carpeta) if f.startswith("buscatron-") and f.endswith(".db"))[:-COPIAS]
    for f in viejas:
        os.remove(os.path.join(carpeta, f))
    return destino


def _bucle(pausa):
    while True:
        for tarea in (lambda: vigiladas(hilo=True), recordatorios, limpieza):
            try:
                tarea()
            except Exception:
                traceback.print_exc()
        time.sleep(pausa)


def arranca(pausa=60):
    threading.Thread(target=_bucle, args=(pausa,), daemon=True, name="programador").start()
