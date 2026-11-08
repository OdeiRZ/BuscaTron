"""Envío de avisos por Telegram y correo (solo biblioteca estándar)."""
import json
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage

from . import ajustes


MAX_TELEGRAM = 4000        # Telegram rechaza los mensajes de más de 4096 caracteres


def trocea(texto, n=MAX_TELEGRAM):
    """Parte un texto largo en mensajes de hasta n caracteres, cortando entre párrafos (un producto por párrafo)."""
    trozos, actual = [], ""
    for p in texto.split("\n\n"):
        while len(p) > n:                      # un párrafo que no cabe ni solo
            if actual:
                trozos.append(actual)
                actual = ""
            trozos.append(p[:n])
            p = p[n:]
        if actual and len(actual) + 2 + len(p) > n:
            trozos.append(actual)
            actual = p
        else:
            actual = f"{actual}\n\n{p}" if actual else p
    return trozos + [actual] if actual else trozos


def telegram(texto, a=None):
    a = a or ajustes.carga()
    if not (a["telegram_token"] and a["telegram_chat"]):
        raise ValueError("falta el token o el chat de Telegram")
    url = f"https://api.telegram.org/bot{a['telegram_token']}/sendMessage"
    for trozo in trocea(texto):
        datos = urllib.parse.urlencode({"chat_id": a["telegram_chat"], "text": trozo,
                                        "disable_web_page_preview": "true"}).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=datos), timeout=20) as r:
            if not json.load(r).get("ok"):
                raise RuntimeError("Telegram rechazó el mensaje")


def detectar_chat(a=None):
    """Lee el último mensaje enviado al bot y devuelve su chat_id."""
    a = a or ajustes.carga()
    if not a["telegram_token"]:
        raise ValueError("falta el token de Telegram")
    from . import telegram_bot           # si el bot de órdenes está escuchando, es él quien recibe los mensajes
    if telegram_bot.ultimo_chat:
        return telegram_bot.ultimo_chat
    url =f"https://api.telegram.org/bot{a['telegram_token']}/getUpdates"
    with urllib.request.urlopen(url, timeout=20) as r:
        res = json.load(r).get("result", [])
    for u in reversed(res):
        m = u.get("message") or u.get("channel_post")
        if m:
            return str(m["chat"]["id"])
    raise ValueError("no hay mensajes: escribe algo a tu bot en Telegram y reintenta")


def correo(asunto, texto, a=None):
    a = a or ajustes.carga()
    if not (a["smtp_servidor"] and a["correo_destino"]):
        raise ValueError("falta el servidor SMTP o el correo de destino")
    m = EmailMessage()
    m["Subject"], m["From"], m["To"] = asunto, a["smtp_usuario"] or a["correo_destino"], a["correo_destino"]
    m.set_content(texto)
    puerto = int(a["smtp_puerto"])
    if puerto == 465:
        s = smtplib.SMTP_SSL(a["smtp_servidor"], puerto, timeout=25)
    else:
        s = smtplib.SMTP(a["smtp_servidor"], puerto, timeout=25)
        s.starttls()
    with s:
        if a["smtp_usuario"]:
            s.login(a["smtp_usuario"], a["smtp_clave"])
        s.send_message(m)


def envia(canales, asunto, texto):
    """Envía por los canales pedidos ('telegram', 'correo'). Devuelve {canal: error|None}."""
    informe = {}
    for c in canales:
        try:
            if c == "telegram":
                telegram(f"{asunto}\n\n{texto}")
            elif c == "correo":
                correo(asunto, texto)
            else:
                continue
            informe[c] = None
        except Exception as e:
            informe[c] = str(e)[:120]
    return informe
