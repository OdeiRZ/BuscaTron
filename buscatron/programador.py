"""Hilo de tareas periódicas: lanza las búsquedas vigiladas cuando les toca, recuerda por Telegram cuando van a caducar
los precios pegados a mano, mira si vuelve una tienda que te bloqueó y, una vez al día, compacta el historial."""
import threading
import time
import traceback

from . import ajustes, bd, fetch, seguimiento, tiendas as cfg

LIMPIEZA_HORAS = 24
BLOQUEO_HORAS = 6          # una tienda que bloqueó tu conexión se prueba con UNA petición a su portada cada tanto
SUAVE_DIAS = 3             # al volver, unos días con una sola página por búsqueda
ESPACIO_VIGILADAS = 10 * 60    # entre dos revisiones automáticas: así cada tienda ve unas pocas peticiones repartidas
_ultima_revision = [0.0]
_hilo = [None]             # la revisión automática en marcha (en su hilo, para no frenar el resto de tareas)


def bloqueadas():
    """Tiendas desactivadas porque bloquearon tu conexión (campo «bloqueo»): cada BLOQUEO_HORAS una sola petición a su
    portada; cuando vuelve a responder, se reactiva y te avisa por Telegram. Sin búsquedas: tan poco no renueva el
    bloqueo (Dungeon Marvels, 9/11/2026)."""
    # Las que marques «No consultar automáticamente» no se prueban: con Dungeon Marvels, una petición cada 6 h desde la IP
    # bloqueada podía estar renovando el bloqueo (55 pruebas en dos semanas sin que se levantara).
    for t in [t for t in cfg.carga() if t.get("bloqueo") and not t.get("manual")]:
        if time.time() - t["bloqueo"].get("probado", 0) < BLOQUEO_HORAS * 3600:
            continue
        try:
            st, _ = fetch.get(f"https://{t['host']}/", timeout=20)
            vuelve = st == 200
        except Exception:   # noqa: BLE001  (sigue sin responder)
            vuelve = False
        with cfg.cerrojo:                       # sobre la lista actual, por si la cambiaste mientras tanto
            lista = cfg.carga()
            for x in lista:
                if x["host"] == t["host"] and x.get("bloqueo"):
                    if vuelve:
                        x["activa"] = True
                        x.pop("bloqueo")
                        x["suave_hasta"] = time.time() + SUAVE_DIAS * 86400
                    else:
                        x["bloqueo"]["probado"] = time.time()
            cfg.guarda(lista)
        nombre = t.get("nombre") or t["host"]
        print(f"{nombre}:", "vuelve a responder; reactivada" if vuelve else "sigue sin responder")   # sin Telegram: solo límites y objetivos


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
    copia_de_seguridad()
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
        copia = sqlite3.connect(destino)
        with copia:
            origen.backup(copia)
        copia.close()
    finally:
        origen.close()
    viejas = sorted(f for f in os.listdir(carpeta) if f.startswith("buscatron-") and f.endswith(".db"))[:-COPIAS]
    for f in viejas:
        os.remove(os.path.join(carpeta, f))
    return destino


def _telegram(asunto, texto):
    from . import notifica
    a = ajustes.carga()
    if a.get("telegram_token") and a.get("telegram_chat"):
        notifica.envia(["telegram"], asunto, texto)


def rebajas(hoy=None):
    """Unos días antes de una campaña de rebajas (Black Friday, rebajas de enero, Prime Day…), un aviso por Telegram,
    una sola vez por campaña: quizá te convenga esperar para comprar."""
    from . import historico
    c = historico.proxima_campana(hoy)
    if not c or c["ya"]:
        return None
    clave = f"{c['nombre']} {c['desde'][:4]}"
    if ajustes.carga().get("rebaja_avisada") == clave:
        return None
    _telegram("BuscaTron · rebajas a la vista", f"Dentro de {c['dias']} día{'' if c['dias'] == 1 else 's'} empieza {c['nombre']}: "
              "si no corre prisa, quizá te convenga esperar para comprar. Tus vigiladas seguirán revisándose.")
    ajustes.guarda({"rebaja_avisada": clave})
    return clave


SALUD_DIAS = 7


def salud(ahora=None):
    """Una vez por semana: tiendas que solían dar resultados y en los últimos 7 días no han dado ninguno (o fallan). Un
    aviso por Telegram para que no te pierdas ofertas sin enterarte. Solo mira lo ya guardado: ninguna petición."""
    ahora = ahora or time.time()
    if ahora - float(ajustes.carga().get("ultima_salud") or 0) < SALUD_DIAS * 86400:
        return None
    lista = {t["host"]: t for t in cfg.carga() if t.get("activa", True) and not t.get("manual") and not t.get("bloqueo")}
    malas = []
    with bd.conecta() as c:
        for h, t in lista.items():
            antes = c.execute("SELECT COUNT(*) FROM estado_tiendas WHERE host=? AND encontrados>0 AND ts BETWEEN ? AND ?",
                              (h, ahora - 37 * 86400, ahora - SALUD_DIAS * 86400)).fetchone()[0]
            ahora_f = c.execute("SELECT encontrados, error FROM estado_tiendas WHERE host=? AND ts>? ORDER BY ts DESC",
                                (h, ahora - SALUD_DIAS * 86400)).fetchall()
            if antes and len(ahora_f) >= 3 and not any(f[0] for f in ahora_f):
                err = next((f[1] for f in ahora_f if f[1]), "")
                malas.append(f"• {t.get('nombre') or h}" + (f": {err}" if err else ""))
    ajustes.guarda({"ultima_salud": ahora})
    if malas:
        _telegram("BuscaTron · tiendas que han dejado de funcionar",
                  "Solían darte resultados y esta semana no han dado ninguno:\n" + "\n".join(malas)
                  + "\n\nMíralo en Ajustes → Estado de las tiendas.")
    return malas


def _bucle(pausa):
    while True:
        for tarea in (lambda: vigiladas(hilo=True), recordatorios, bloqueadas, limpieza, rebajas, salud):
            try:
                tarea()
            except Exception:
                traceback.print_exc()
        time.sleep(pausa)


def arranca(pausa=60):
    threading.Thread(target=_bucle, args=(pausa,), daemon=True, name="programador").start()
