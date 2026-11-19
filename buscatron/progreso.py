"""Progreso de las tareas largas (búsquedas y revisiones de vigiladas), para la barra de carga de la página.

Vive en el servidor, no en la página: así la barra sigue ahí aunque cambies de pestaña, recargues o la abras en el móvil.
Cada tarea se apunta en el hilo que la ejecuta (`tarea`) y motor.buscar va contando las tiendas que termina.
"""
import contextlib
import threading
import time

_cerrojo = threading.Lock()
_tareas = {}                  # clave → {tipo, nombre, inicio, hechas, total, fase, estimado}
_local = threading.local()


@contextlib.contextmanager
def tarea(clave, tipo, nombre, estimado=None):
    """Apunta una tarea mientras dura el bloque. `estimado`: segundos que suele tardar (si se sabe)."""
    with _cerrojo:
        _tareas[clave] = {"clave": clave, "tipo": tipo, "nombre": nombre, "inicio": time.time(), "hechas": 0, "total": 0,
                          "fase": "Empezando…", "estimado": estimado}
    anterior, _local.clave = getattr(_local, "clave", None), clave
    try:
        yield
    finally:
        _local.clave = anterior
        with _cerrojo:
            _tareas.pop(clave, None)


def actual():
    """La tarea del hilo que llama (None si no hay ninguna)."""
    return getattr(_local, "clave", None)


def total(clave, n, fase="Consultando tiendas"):
    if clave:
        with _cerrojo:
            if clave in _tareas:
                _tareas[clave].update(total=n, hechas=0, fase=fase)


def avanza(clave):
    if clave:
        with _cerrojo:
            if clave in _tareas:
                _tareas[clave]["hechas"] += 1


def fase(clave, texto):
    if clave:
        with _cerrojo:
            if clave in _tareas:
                _tareas[clave]["fase"] = texto


def lista():
    """Las tareas en marcha, con lo que llevan y una estimación de lo que les queda (s)."""
    ahora = time.time()
    with _cerrojo:
        tareas = [dict(t) for t in _tareas.values()]
    for t in tareas:
        t["lleva"] = ahora - t["inicio"]
        queda = None
        if t["total"] and t["hechas"]:
            queda = t["lleva"] / t["hechas"] * (t["total"] - t["hechas"])
        elif t["estimado"]:
            queda = max(0, t["estimado"] - t["lleva"])
        t["queda"] = queda
        t["parte"] = round(t["hechas"] / t["total"], 3) if t["total"] else None
    return sorted(tareas, key=lambda t: t["inicio"])
