"""Ajustes locales (config.json): canales de aviso. No se sube al repositorio."""
import json
import os

from . import tiendas as cfg

RUTA = os.path.join(cfg.RAIZ, "config.json")
SECRETOS = ("telegram_token", "smtp_clave", "pin")
DEFECTO = {"telegram_token": "", "telegram_chat": "", "smtp_servidor": "", "smtp_puerto": 587,
           "smtp_usuario": "", "smtp_clave": "", "correo_destino": "",
           "usar_navegador": True, "navegador_visible": False, "pin": "", "secreto": "", "paginas": 3, "segunda_mano_sembrada": False, "amazon_automatico": False}


def carga():
    d = dict(DEFECTO)
    if os.path.exists(RUTA):
        with open(RUTA, encoding="utf-8") as f:
            d.update(json.load(f))
    return d


def secreto():
    """Clave interna (se crea una vez) para firmar las sesiones del PIN."""
    d = carga()
    if not d["secreto"]:
        import secrets
        d["secreto"] = secrets.token_hex(32)
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    return d["secreto"]


def guarda(nuevos):
    d = carga()
    for k, v in nuevos.items():
        if k in DEFECTO and k != "secreto" and not (k in SECRETOS and v == "********"):
            d[k] = v
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d


def publico():
    """Ajustes con los secretos enmascarados, para mostrarlos en la web."""
    d = carga()
    from . import navegador
    d.pop("secreto", None)
    d = {k: ("********" if k in SECRETOS and v else v) for k, v in d.items()}
    d["navegador_disponible"] = navegador.disponible()
    return d
