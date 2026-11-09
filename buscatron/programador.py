"""Hilo de tareas periódicas: lanza las búsquedas vigiladas cuando les toca, recuerda por Telegram cuando van a caducar
los precios pegados a mano, mira si vuelve una tienda que te bloqueó y, una vez al día, compacta el historial."""
import threading
import time
import traceback

from . import ajustes, bd, fetch, importar, notifica, seguimiento, tiendas as cfg

LIMPIEZA_HORAS = 24
BLOQUEO_HORAS = 6          # una tienda que bloqueó tu conexión se prueba con UNA petición a su portada cada tanto


def bloqueadas():
    """Tiendas desactivadas porque bloquearon tu conexión (campo «bloqueo»): cada BLOQUEO_HORAS una sola petición a su
    portada; cuando vuelve a responder, se reactiva y te avisa por Telegram. Sin búsquedas: tan poco no renueva el
    bloqueo (Dungeon Marvels, 9/11/2026)."""
    for t in [t for t in cfg.carga() if t.get("bloqueo")]:
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
                    else:
                        x["bloqueo"]["probado"] = time.time()
            cfg.guarda(lista)
        nombre = t.get("nombre") or t["host"]
        print(f"{nombre}:", "vuelve a responder; reactivada" if vuelve else "sigue sin responder")
        if vuelve:
            notifica.envia(["telegram"], f"BuscaTron · {nombre}",
                           f"{nombre} vuelve a responder: la he reactivado y entra otra vez en tus búsquedas y vigiladas.")


def recordatorios():
    a = ajustes.carga()
    if not (a.get("telegram_token") and a.get("telegram_chat")):
        return
    lista = {t["host"]: t for t in cfg.carga()}
    for host, ts, queda, consulta in importar.por_caducar():
        t = lista.get(host, {})
        nombre = t.get("nombre") or host
        enlace = cfg.url_busqueda(t["plantilla"], consulta) if t.get("plantilla") else ""
        horas = max(1, round(queda / 3600))
        envio = notifica.envia(["telegram"], f"BuscaTron · {nombre}",
                       f"Los precios que pegaste a mano de {nombre} caducan dentro de {horas} h. Si quieres que sigan contando en tus "
                       f"búsquedas y avisos, vuelve a pegarlos («Tiendas que tienes que mirar tú» → «Pegar resultados»)."
                       + (f"\n{enlace}" if enlace else ""))
        if envio.get("telegram") is None:          # si no llegó (sin conexión…), se reintenta en la siguiente vuelta
            importar.marca_recordado(host, ts)


def limpieza():
    a = ajustes.carga()
    if time.time() - float(a.get("ultima_limpieza") or 0) < LIMPIEZA_HORAS * 3600:
        return
    borradas = bd.limpia()
    ajustes.guarda({"ultima_limpieza": time.time()})
    print("Limpieza del historial:", borradas)


def _bucle(pausa):
    while True:
        for tarea in (lambda: [seguimiento.revisa(sid) for sid in seguimiento.pendientes()], recordatorios, bloqueadas, limpieza):
            try:
                tarea()
            except Exception:
                traceback.print_exc()
        time.sleep(pausa)


def arranca(pausa=60):
    threading.Thread(target=_bucle, args=(pausa,), daemon=True, name="programador").start()
