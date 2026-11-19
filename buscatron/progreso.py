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
_ultimas = {}                 # tipo → (segundos, tiendas) de la última que terminó: para estimar las búsquedas
TIENDAS = 0.8                 # parte de la barra para consultar las tiendas; el resto, lo que viene después


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
            t = _tareas.pop(clave, None)
            if t and t["total"]:
                _ultimas[tipo] = (time.time() - t["inicio"], t["total"])


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


def _estimado(t):
    """Segundos que suele tardar: el de la tarea (revisión anterior de esa vigilada) o la última del mismo tipo,
    a escala de las tiendas que consulta."""
    if t["estimado"]:
        return t["estimado"]
    ult = _ultimas.get(t["tipo"])
    if ult and t["total"]:
        return ult[0] * t["total"] / ult[1]
    return None


def lista():
    """Las tareas en marcha, con lo que llevan, la parte hecha (0-1) y lo que les queda (s; None si no se sabe).
    Las tiendas lentas acaban las últimas y después aún queda trabajo (otras webs, fichas…): contar solo tiendas daba
    100 % a mitad. Así que manda el tiempo que suele tardar, y las tiendas hechas solo sirven de suelo."""
    ahora = time.time()
    with _cerrojo:
        tareas = [dict(t) for t in _tareas.values()]
        est = {t["clave"]: _estimado(t) for t in tareas}
    for t in tareas:
        lleva = t["lleva"] = ahora - t["inicio"]
        de_tiendas = t["hechas"] / t["total"] if t["total"] else 0
        en_tiendas = t["fase"] in ("Empezando…", "Consultando tiendas")
        suelo = TIENDAS * de_tiendas if en_tiendas else TIENDAS
        e = est[t["clave"]]
        if e:
            parte = max(suelo, min(lleva / e, 0.99))
            queda = e - lleva if lleva < e else None          # ya tarda más de lo normal: no se inventa una cifra
        elif t["total"] and t["hechas"]:
            parte = suelo if en_tiendas else 0.9
            queda = (lleva / t["hechas"] * (t["total"] - t["hechas"]) + 0.25 * lleva) if en_tiendas else None
        else:
            parte, queda = (suelo or None), None
        t["parte"] = round(min(parte, 0.99), 3) if parte is not None else None
        t["queda"] = queda
    return sorted(tareas, key=lambda t: t["inicio"])
