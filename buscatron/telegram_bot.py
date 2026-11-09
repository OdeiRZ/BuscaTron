"""Órdenes por Telegram: escribe al bot y contesta. Solo obedece al chat configurado en Ajustes; cualquier otro se ignora.
  /buscar <texto>   busca en tus tiendas y responde con los 5 productos más baratos (también vale escribir el texto sin más)
  /vigiladas        tus búsquedas vigiladas, su última revisión y la próxima
  /revisar          revisa ahora todas las búsquedas vigiladas activas (los avisos llegan como siempre)
  /ayuda            esta ayuda"""
import json
import threading
import time
import traceback
import urllib.parse
import urllib.request

from . import ajustes, motor, notifica, seguimiento, servicio

ultimo_chat = None          # último chat que escribió al bot (lo usa «Detectar chat» en Ajustes)
_ocupado = threading.Lock()
AYUDA = ("BuscaTron te responde aquí:\n"
         "/buscar civil war — busca en tus tiendas y te manda los 5 productos más baratos (o escribe solo «civil war»)\n"
         "/vigiladas — tus búsquedas vigiladas y cuándo se revisan\n"
         "/revisar — revisa ahora todas tus búsquedas vigiladas\n"
         "/ayuda — esta ayuda")
ORDENES = [("buscar", "Buscar un producto en tus tiendas"), ("vigiladas", "Ver tus búsquedas vigiladas"),
           ("revisar", "Revisar ahora las búsquedas vigiladas"), ("ayuda", "Qué puedo hacer")]


def _api(token, metodo, datos=None, timeout=20):
    url = f"https://api.telegram.org/bot{token}/{metodo}"
    cuerpo = urllib.parse.urlencode(datos).encode() if datos else None
    with urllib.request.urlopen(urllib.request.Request(url, data=cuerpo), timeout=timeout) as r:
        return json.load(r)


def responde(texto):
    notifica.telegram(texto)                # si es largo, notifica lo parte en varios mensajes


def _hora(ts):
    return time.strftime("%d/%m %H:%M", time.localtime(ts)) if ts else "nunca"


def buscar(texto):
    if servicio.saliendo():
        return responde("BuscaTron se está reiniciando: vuelve a escribirme en un minuto.")
    if not _ocupado.acquire(blocking=False):
        return responde("Ya estoy con otra búsqueda; espera a que termine.")
    try:
        responde(f"Buscando «{texto}» en tus tiendas… (tarda alrededor de un minuto)")
        with servicio.trabajo("telegram"):
            res, informe = motor.buscar(texto, ocultar_agotados=True, idioma="castellano")
        grupos = seguimiento.agrupa(res)
        if not grupos:
            return responde(f"No he encontrado «{texto}» en tus tiendas (en castellano y con stock).")
        nombres = seguimiento._nombres()
        lineas = [f"«{texto}»: {seguimiento.productos(res)}. Los 5 más baratos:"]
        lineas += [seguimiento.linea_grupo(g, nombres=nombres) for g in grupos[:5]]
        responde("\n\n".join(lineas))
    finally:
        _ocupado.release()


def vigiladas():
    l = seguimiento.lista()
    if not l:
        return responde("No tienes búsquedas vigiladas. Créalas en la pestaña Vigiladas de BuscaTron.")
    lineas = []
    for s in l:
        if s["activo"]:
            prox = _hora(s["ultima"] + s["cada_horas"] * 3600) if s["ultima"] else "ahora"
            lineas.append(f"👁️ {s['nombre']}\nÚltima revisión: {_hora(s['ultima'])} — {s['estado'] or 'sin datos'}\nPróxima: {prox}")
        else:
            lineas.append(f"⏸️ {s['nombre']} (en pausa)")
    responde("\n\n".join(lineas))


def revisar():
    activas = [s for s in seguimiento.lista() if s["activo"]]
    if not activas:
        return responde("No hay búsquedas vigiladas activas.")
    responde(f"Revisando {len(activas)} búsqueda(s) vigilada(s). Los avisos te llegarán como siempre.")
    for s in activas:
        seguimiento.revisa(s["id"])
    responde("Revisión terminada.")


def atiende(texto):
    """Interpreta un mensaje del usuario."""
    t = (texto or "").strip()
    if not t:
        return
    orden, _, resto = t.partition(" ")
    orden = orden.split("@")[0].lower()
    if orden in ("/start", "/ayuda", "/help"):
        return responde(AYUDA)
    if orden == "/vigiladas":
        return vigiladas()
    if orden == "/revisar":
        return revisar()
    if orden == "/buscar":
        return buscar(resto.strip()) if resto.strip() else responde("Dime qué buscar, por ejemplo: /buscar civil war")
    if t.startswith("/"):
        return responde("No conozco esa orden.\n\n" + AYUDA)
    return buscar(t)


def _bucle():
    global ultimo_chat
    offset, menu_puesto = None, None
    while True:
        try:
            a = ajustes.carga()
            token = a.get("telegram_token")
            if not token:
                time.sleep(30)
                continue
            if menu_puesto != token:                     # el menú «/» de Telegram con las órdenes
                _api(token, "setMyCommands", {"commands": json.dumps([{"command": c, "description": d} for c, d in ORDENES])})
                menu_puesto, offset = token, None        # otro bot: su numeración de mensajes empieza de nuevo
            datos = {"timeout": 50, **({"offset": offset} if offset else {})}
            r = _api(token, "getUpdates", datos, timeout=65)
        except Exception:
            time.sleep(15)
            continue
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            m = u.get("message") or {}
            if not m.get("chat"):
                continue
            ultimo_chat = str(m["chat"]["id"])
            if ultimo_chat != str(a.get("telegram_chat") or ""):
                continue                                  # solo obedece a tu chat
            threading.Thread(target=_protegido, args=(m.get("text", ""),), daemon=True).start()


def _protegido(texto):
    try:
        atiende(texto)
    except Exception as e:
        traceback.print_exc()
        try:
            responde(f"No he podido hacerlo: {str(e)[:150]}")
        except Exception:
            pass


def arranca():
    threading.Thread(target=_bucle, daemon=True, name="telegram").start()
