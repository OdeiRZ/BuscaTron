"""Ajustes locales (config.json): canales de aviso. No se sube al repositorio."""
import json
import os

from . import tiendas as cfg

RUTA = os.path.join(cfg.RAIZ, "config.json")
SECRETOS = ("telegram_token", "smtp_clave")
DEFECTO = {"telegram_token": "", "telegram_chat": "", "smtp_servidor": "", "smtp_puerto": 587,
           "smtp_usuario": "", "smtp_clave": "", "correo_destino": "",
           "usar_navegador": True, "navegador_visible": False}


def carga():
    d = dict(DEFECTO)
    if os.path.exists(RUTA):
        with open(RUTA, encoding="utf-8") as f:
            d.update(json.load(f))
    return d


def guarda(nuevos):
    d = carga()
    for k, v in nuevos.items():
        if k in DEFECTO and not (k in SECRETOS and v == "********"):
            d[k] = v
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d


def publico():
    """Ajustes con los secretos enmascarados, para mostrarlos en la web."""
    d = carga()
    from . import navegador
    d = {k: ("********" if k in SECRETOS and v else v) for k, v in d.items()}
    d["navegador_disponible"] = navegador.disponible()
    return d
