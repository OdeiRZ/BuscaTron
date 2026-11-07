"""Hilo de tareas periódicas: lanza las búsquedas vigiladas cuando les toca, recuerda por Telegram cuando van a caducar
los precios pegados a mano y, una vez al día, compacta el historial."""
import threading
import time
import traceback

from . import ajustes, bd, importar, notifica, seguimiento, tiendas as cfg

LIMPIEZA_HORAS = 24


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
        notifica.envia(["telegram"], f"BuscaTron · {nombre}",
                       f"Los precios que pegaste a mano de {nombre} caducan dentro de {horas} h. Si quieres que sigan contando en tus "
                       f"búsquedas y avisos, vuelve a pegarlos («Tiendas que tienes que mirar tú» → «Pegar resultados»)."
                       + (f"\n{enlace}" if enlace else ""))
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
        for tarea in (lambda: [seguimiento.revisa(sid) for sid in seguimiento.pendientes()], recordatorios, limpieza):
            try:
                tarea()
            except Exception:
                traceback.print_exc()
        time.sleep(pausa)


def arranca(pausa=60):
    threading.Thread(target=_bucle, args=(pausa,), daemon=True, name="programador").start()
