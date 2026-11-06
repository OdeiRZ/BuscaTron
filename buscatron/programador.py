"""Hilo que lanza los seguimientos cuando les toca."""
import threading
import time
import traceback

from . import seguimiento


def _bucle(pausa):
    while True:
        try:
            for sid in seguimiento.pendientes():
                seguimiento.revisa(sid)
        except Exception:
            traceback.print_exc()
        time.sleep(pausa)


def arranca(pausa=60):
    threading.Thread(target=_bucle, args=(pausa,), daemon=True, name="programador").start()
