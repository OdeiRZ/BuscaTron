"""Interfaz web (solo biblioteca estándar). Accesible desde la red local con filtro de IP y PIN opcional."""
import hmac
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from hashlib import sha256
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from . import (ajustes, arranque, busquedas, extract, fetch, importar, motor, notifica, programador, referencia,
               seguimiento, telegram_bot, tiendas as cfg)

TAILSCALE = ipaddress.ip_network("100.64.0.0/10")
MAX_FALLOS, VENTANA_FALLOS = 5, 300      # intentos de PIN fallidos por IP y ventana (segundos)
_fallos = {}
_servidor = {"host": "127.0.0.1", "puerto": 8790}
TRABAJOS = {}                 # búsquedas en curso o recién terminadas: {id: {estado, resp, error, ts}}
_cerrojo_trabajos = threading.Lock()
VIDA_TRABAJO = 3600           # segundos que se guarda el resultado de una búsqueda para recogerlo

LOGIN = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>BuscaTron · Acceso</title>
<style>:root{color-scheme:light dark;--bg:#f3f4f8;--card:#fff;--tx:#1a1d26;--bd:#e5e7ee;--ac:#4f46e5}
@media(prefers-color-scheme:dark){:root{--bg:#0f1117;--card:#181b24;--tx:#e8eaf0;--bd:#2a2f3c;--ac:#8b93ff}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--tx);font:16px system-ui,sans-serif;padding:16px}
form{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:22px;width:100%;max-width:340px;text-align:center}
h1{margin:0 0 4px;font-size:22px}p{margin:0 0 16px;color:#6b7280;font-size:14px}
input,button{width:100%;min-height:46px;border-radius:10px;font:inherit;font-size:18px}
input{border:1px solid var(--bd);background:var(--bg);color:var(--tx);text-align:center;letter-spacing:4px;padding:0 12px}
button{margin-top:10px;border:0;background:var(--ac);color:#fff;font-weight:600;cursor:pointer}#e{color:#b42318;min-height:20px;margin-top:8px;font-size:14px}</style></head>
<body><form id="f"><h1>BuscaTron</h1><p>Introduce el PIN para entrar</p>
<input id="p" type="password" inputmode="numeric" autocomplete="current-password" autofocus aria-label="PIN"><button>Entrar</button><div id="e"></div></form>
<script>document.getElementById('f').onsubmit=async e=>{e.preventDefault();const r=await fetch('/api/login',{method:'POST',body:JSON.stringify({pin:document.getElementById('p').value})});
if(r.ok){location.reload();}else{const j=await r.json();document.getElementById('e').textContent=j.error||'Error';document.getElementById('p').value='';}};</script></body></html>"""


def _pagina():
    with open(os.path.join(os.path.dirname(__file__), "pagina.html"), encoding="utf-8") as f:
        return f.read()


def _archivo(nombre, tipo):
    def lee():
        with open(os.path.join(os.path.dirname(__file__), nombre), "rb") as f:
            return f.read(), tipo
    return lee


MANIFIESTO = {"name": "BuscaTron", "short_name": "BuscaTron", "description": "Compara precios en tus tiendas",
              "start_url": "/", "scope": "/", "display": "standalone", "background_color": "#0f1117", "theme_color": "#4f46e5", "lang": "es",
              "icons": [{"src": "/icono-192.png", "sizes": "192x192", "type": "image/png"},
                        {"src": "/icono-512.png", "sizes": "512x512", "type": "image/png"},
                        {"src": "/icono-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
SW = b"self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());" \
     b"self.addEventListener('fetch',()=>{});"   # sin caché: los precios tienen que venir siempre en directo
ESTATICOS = {"/manifest.webmanifest": lambda: (json.dumps(MANIFIESTO, ensure_ascii=False).encode(), "application/manifest+json; charset=utf-8"),
             "/sw.js": lambda: (SW, "text/javascript; charset=utf-8"),
             "/icono-192.png": _archivo("icono-192.png", "image/png"), "/icono-512.png": _archivo("icono-512.png", "image/png"),
             "/apple-touch-icon.png": _archivo("icono-192.png", "image/png")}


def _num(v):
    v = "" if v is None else str(v).replace(",", ".").strip()     # null en el JSON = campo vacío (antes: «'None'»)
    return float(v) if v else None


def ip_permitida(ip):
    """Solo equipos de la red local (o Tailscale): nunca direcciones públicas."""
    try:
        a = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return False
    if isinstance(a, ipaddress.IPv6Address) and a.ipv4_mapped:
        a = a.ipv4_mapped
    return a.is_loopback or a.is_private or a in TAILSCALE


def es_local(ip):
    try:
        return ipaddress.ip_address(ip.split("%")[0]).is_loopback
    except ValueError:
        return False


def token_sesion(pin):
    return hmac.new(ajustes.secreto().encode(), pin.encode(), sha256).hexdigest()


def busca(c):
    """Hace la búsqueda y devuelve la respuesta (y la guarda como búsqueda reciente)."""
    res, inf = motor.buscar(c.get("q", "").strip(), c.get("incluir", ""), c.get("excluir", ""),
                            bool(c.get("sin_agotados", True)), c.get("tiendas"),
                            _num(c.get("pmin", "")), _num(c.get("pmax", "")),
                            castellano=bool(c.get("castellano", True)), idioma=c.get("idioma") if c.get("idioma") in motor.MODOS_IDIOMA else None,
                            preventas=bool(c.get("preventas")), con_envio=bool(c.get("con_envio")), segunda_mano=bool(c.get("segunda_mano")),
                            abierta=bool(c.get("abierta")), region=c.get("region") if c.get("region") in ("es", "ue", "mundo") else "es",
                            paginas=int(_num(c.get("paginas", "")) or 0) or None, alguna=str(c.get("alguna") or ""))
    resp = {"resultados": res[:300], "total": len(res), "informe": inf,          # la página agrupa y enseña los N primeros
            "webs": sorted({x["tienda"] for x in res if x.get("origen") == "web"})}
    if c.get("guardar", True) and c.get("q", "").strip():        # se recuerda para no tener que repetirla
        resp["id"], resp["ts"] = busquedas.guarda(c, resp)
    return resp


def lanza_busqueda(c):
    """Empieza una búsqueda en segundo plano y devuelve su número al instante. La página la consulta con
    /api/trabajo: así, si el móvil corta la conexión (pantalla bloqueada, otra app, recarga), la búsqueda sigue."""
    tid = os.urandom(8).hex()
    with _cerrojo_trabajos:
        ahora = time.time()
        for k in [k for k, v in TRABAJOS.items() if ahora - v["ts"] > VIDA_TRABAJO]:
            del TRABAJOS[k]
        TRABAJOS[tid] = {"estado": "buscando", "ts": ahora}

    def corre():
        try:
            r = {"estado": "hecho", "resp": busca(c)}
        except Exception as e:                       # noqa: BLE001  (se le cuenta a la página)
            r = {"estado": "error", "error": str(e) or e.__class__.__name__}
        with _cerrojo_trabajos:
            TRABAJOS[tid].update(r, ts=time.time())
    threading.Thread(target=corre, daemon=True, name="busqueda-" + tid).start()
    return {"trabajo": tid}


def estado_trabajo(tid):
    with _cerrojo_trabajos:
        t = TRABAJOS.get(tid)
        if not t:
            return {"estado": "desconocido"}          # p. ej. BuscaTron se reinició: la página recurre a la última guardada
        return {k: v for k, v in t.items() if k != "ts"}


def analiza_direccion(entrada):
    """Devuelve (host, plantilla|None). Admite 'tienda.es' o una URL de búsqueda con {q}."""
    entrada = entrada.strip()
    plantilla = None
    if "{q}" in entrada:
        plantilla = entrada if entrada.startswith("http") else "https://" + entrada
        host = urlparse(plantilla).netloc
    else:
        host = entrada.replace("https://", "").replace("http://", "").split("/")[0].strip()
    if not host or "." not in host:
        raise ValueError("dirección no válida")
    return host, plantilla


def direcciones_red():
    """Direcciones IPv4 de este equipo, la de la Wi-Fi/LAN principal primero."""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        ips += [r[4][0] for r in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
    except OSError:
        pass
    vistas = []
    for i in ips:
        if i not in vistas and not i.startswith(("127.", "169.254.")):
            vistas.append(i)
    return [{"ip": i, "tipo": "Tailscale" if ipaddress.ip_address(i) in TAILSCALE else "red local"} for i in vistas]


_https = {"ts": 0, "url": None}


def direccion_https(puerto):
    """La dirección HTTPS de Tailscale que lleva a BuscaTron (si se publicó con «tailscale serve»), o None.
    Se consulta como mucho una vez cada 10 minutos."""
    if time.time() - _https["ts"] < 600:
        return _https["url"]
    url = None
    exe = shutil.which("tailscale") or os.path.expandvars(r"%ProgramFiles%\Tailscale\tailscale.exe")
    if os.path.exists(exe):
        try:
            r = subprocess.run([exe, "serve", "status", "--json"], capture_output=True, text=True, timeout=5,
                               creationflags=0x08000000 if os.name == "nt" else 0)      # sin ventana
            for host, w in (json.loads(r.stdout or "{}").get("Web") or {}).items():
                if any(h.get("Proxy", "").rstrip("/") in (f"http://127.0.0.1:{puerto}", f"http://localhost:{puerto}")
                       for h in (w.get("Handlers") or {}).values()):
                    url = "https://" + host.removesuffix(":443")
                    break
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    _https.update(ts=time.time(), url=url)
    return url


class Handler(BaseHTTPRequestHandler):
    def _enviar(self, cuerpo, tipo, codigo=200, cabeceras=None):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (cabeceras or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, obj, codigo=200, cabeceras=None):
        self._enviar(json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8", codigo, cabeceras)

    def _estado(self):
        """'ok' | 'denegado' (IP no permitida) | 'pin' (falta iniciar sesión)."""
        ip = self.client_address[0]
        if not ip_permitida(ip):
            return "denegado"
        if es_local(ip):
            return "ok"
        pin = ajustes.carga()["pin"]
        if not pin:
            return "ok"
        for parte in self.headers.get("Cookie", "").split(";"):
            k, _, v = parte.strip().partition("=")
            if k == "bt_sesion" and hmac.compare_digest(v, token_sesion(pin)):
                return "ok"
        return "pin"

    def do_GET(self):
        est = self._estado()
        if est == "denegado":
            return self._enviar("Acceso no permitido desde esta red.".encode(), "text/plain; charset=utf-8", 403)
        estatico = ESTATICOS.get(urlparse(self.path).path)
        if estatico:                                   # manifiesto e iconos de la app (también antes del PIN)
            return self._enviar(*estatico())
        if est == "pin":
            if self.path.startswith("/api/"):
                return self._json({"error": "pin"}, 401)
            return self._enviar(LOGIN.encode(), "text/html; charset=utf-8")
        url = urlparse(self.path)
        rutas = {"/api/tiendas": cfg.carga, "/api/seguimientos": seguimiento.lista, "/api/avisos": seguimiento.avisos,
                 "/api/ajustes": ajustes.publico, "/api/red": self._red,
                 "/api/arranque": lambda: {"disponible": arranque.disponible(), "activo": arranque.activo()},
                 "/api/historial": lambda: (motor.historial_producto(parse_qs(url.query)["grupo"][0]) if parse_qs(url.query).get("grupo")
                                            else motor.historial_de(parse_qs(url.query).get("url", [""])[0])),
                 "/api/objetivos": lambda: [dict(o, vigilan=seguimiento.cubren(o["titulo"], o["precio"])) for o in motor.objetivos().values()],
                 "/api/referencia": lambda: referencia.resumen("vigiladas" if parse_qs(url.query).get("ambito") == ["vigiladas"] else "avisos"),
                 "/api/vigilan": lambda: seguimiento.cubren(parse_qs(url.query)["titulo"][0], _num(parse_qs(url.query).get("precio", [""])[0])),
                 "/api/busquedas": lambda: (busquedas.obtiene(int(parse_qs(url.query)["id"][0])) or {"error": "búsqueda no encontrada"})
                 if "id" in parse_qs(url.query) else busquedas.lista()}
        if url.path in rutas:
            try:
                return self._json(rutas[url.path]())
            except (ValueError, KeyError) as e:
                return self._json({"error": str(e) or "datos no válidos"}, 400)
            except Exception as e:              # noqa: BLE001
                return self._fallo(e)
        self._enviar(_pagina().encode(), "text/html; charset=utf-8")

    def do_POST(self):
        est = self._estado()
        if est == "denegado":
            return self._json({"error": "acceso no permitido"}, 403)
        try:
            cuerpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/api/login":
                return self._login(cuerpo)
            if est == "pin":
                return self._json({"error": "pin"}, 401)
            return self._json(self._post(self.path, cuerpo))
        except (ValueError, KeyError) as e:
            return self._json({"error": str(e) or "datos no válidos"}, 400)
        except Exception as e:                  # noqa: BLE001  (p. ej. una web que no responde: se cuenta en vez de colgar la página)
            return self._fallo(e)

    def _fallo(self, e):
        traceback.print_exc()
        return self._json({"error": f"algo ha fallado: {str(e)[:150] or e.__class__.__name__}"}, 500)

    def _red(self):
        return {"escucha_red": _servidor["host"] not in ("127.0.0.1", "localhost"), "puerto": _servidor["puerto"],
                "direcciones": direcciones_red(), "pin": bool(ajustes.carga()["pin"]), "https": direccion_https(_servidor["puerto"])}

    def _login(self, c):
        ip, ahora = self.client_address[0], time.time()
        n, desde = _fallos.get(ip, (0, ahora))
        if ahora - desde > VENTANA_FALLOS:
            n, desde = 0, ahora
        if n >= MAX_FALLOS:
            return self._json({"error": "Demasiados intentos. Espera unos minutos."}, 429)
        pin = ajustes.carga()["pin"]
        if pin and hmac.compare_digest(str(c.get("pin", "")), pin):
            _fallos.pop(ip, None)
            return self._json({"ok": True}, 200, {
                "Set-Cookie": f"bt_sesion={token_sesion(pin)}; Path=/; Max-Age=2592000; HttpOnly; SameSite=Lax"})
        _fallos[ip] = (n + 1, desde)
        return self._json({"error": "PIN incorrecto"}, 401)

    def _post(self, ruta, c):
        if ruta == "/api/buscar" and c.get("asincrono"):
            return lanza_busqueda(c)
        if ruta == "/api/buscar":
            return busca(c)
        if ruta == "/api/ignorar":            # «ya lo tengo / no me interesa»
            if c.get("quitar"):
                motor.deja_de_ignorar(c["quitar"])
            elif (c.get("titulo") or "").strip():
                motor.ignora(c["titulo"].strip())
                return {"clave": motor.clave_producto(c["titulo"].strip()), "ignorados": list(motor.ignorados().values())}
            return {"ignorados": list(motor.ignorados().values())}
        if ruta == "/api/estado_tiendas":
            return motor.estado_tiendas()
        if ruta == "/api/objetivos":          # 🎯 precio objetivo de un producto
            if c.get("quitar"):
                motor.quita_objetivo(c["quitar"])
            elif c.get("grupo"):
                motor.pon_objetivo(c["grupo"], (c.get("titulo") or "").strip()[:200], _num(c.get("precio", "")))
            return list(motor.objetivos().values())
        if ruta == "/api/trabajo":
            return estado_trabajo(c.get("id", ""))
        if ruta == "/api/busquedas":
            accion = c.get("accion")
            if accion == "borrar":
                busquedas.borra(int(c["id"]))
            elif accion == "vaciar":
                busquedas.vacia()
            elif accion == "actualizar":
                busquedas.actualiza(int(c["id"]), c["resultados"])
            else:
                raise ValueError("acción no válida")
            return busquedas.lista()
        if ruta == "/api/tiendas":
            return self._tiendas(c)
        if ruta == "/api/seguimientos":
            accion = c.get("accion", "guardar")
            if accion == "borrar":
                seguimiento.borra(int(c["id"]))
            elif accion == "revisar":
                threading.Thread(target=seguimiento.revisa, args=(int(c["id"]),), daemon=True).start()
            else:
                seguimiento.guarda(c)
            return seguimiento.lista()
        if ruta == "/api/avisos":
            if c.get("accion") == "vaciar":
                seguimiento.vacia_avisos()
            elif c.get("accion") == "borrar":
                seguimiento.borra_aviso(int(c["id"]))
            return seguimiento.avisos()
        if ruta == "/api/arranque":           # solo desde este equipo: cambia el inicio de Windows del usuario
            if not es_local(self.client_address[0]) or self.headers.get("X-Forwarded-For"):   # tailscale serve llega como 127.0.0.1
                raise ValueError("el arranque con Windows solo se cambia desde el propio equipo")
            try:
                arranque.activa() if c.get("activar") else arranque.desactiva()
            except RuntimeError as e:
                raise ValueError(str(e))
            return {"disponible": arranque.disponible(), "activo": arranque.activo()}
        if ruta == "/api/importar":           # productos pegados a mano de una tienda que no se puede consultar sola
            t = next((t for t in cfg.carga() if t["host"] == c.get("host")), None)
            consulta = (c.get("consulta") or "").strip()
            if not t or not consulta:
                raise ValueError("falta la tienda o la búsqueda")
            base = cfg.url_busqueda(t["plantilla"], consulta) if t.get("plantilla") else "https://" + t["host"] + "/"
            items = importar.parsea(c.get("texto", ""), consulta, base)
            n = importar.guarda(t["host"], consulta, items, base) if items else 0
            return {"importados": n, "ejemplos": [{"titulo": x["titulo"], "precio": x["precio"]} for x in items[:5]], "caduca_horas": importar.CADUCA_HORAS}
        if ruta == "/api/envio_detectar":     # pista a partir de la portada de la tienda; el usuario la revisa y guarda
            st, h = fetch.get("https://" + c["host"] + "/")
            if st != 200:
                raise ValueError(f"la portada no responde (HTTP {st}); introduce el envío a mano")
            return extract.detecta_envio(h)
        if ruta == "/api/ajustes":
            pin = c.get("pin")
            if pin not in (None, "", "********") and len(pin) < 4:
                raise ValueError("El PIN debe tener al menos 4 caracteres")
            ajustes.guarda(c)
            return ajustes.publico()
        if ruta == "/api/detectar_chat":
            ajustes.guarda({k: c[k] for k in ("telegram_token",) if k in c})
            ajustes.guarda({"telegram_chat": notifica.detectar_chat()})
            return ajustes.publico()
        if ruta == "/api/prueba_aviso":
            return notifica.envia([k for k in c.get("canales", []) if k in ("telegram", "correo")],
                                  "BuscaTron · prueba", "Si lees esto, los avisos funcionan.")
        raise KeyError("no encontrado")

    def _tiendas(self, c):
        with cfg.cerrojo:                       # sin pisar lo que guarde a la vez una búsqueda en marcha
            return self._cambia_tiendas(c)

    def _cambia_tiendas(self, c):
        lista = cfg.carga()
        if c.get("anadir"):
            host, plantilla = analiza_direccion(c["anadir"])
            t = next((t for t in lista if t["host"] == host), None)
            if t is None:
                t = {"host": host, "nombre": "", "activa": True, "plantilla": None}
                lista.append(t)
            if c.get("nombre", "").strip():
                t["nombre"] = c["nombre"].strip()
            if plantilla:
                t["plantilla"] = plantilla
                t["manual"] = bool(c.get("manual"))
            if c.get("tipo") == "segunda_mano":
                t["tipo"] = "segunda_mano"
        if c.get("editar"):  # nombre, dirección y modo «solo enlace» de una tienda existente
            t = next((t for t in lista if t["host"] == c["editar"]), None)
            if t is None:
                raise ValueError("tienda no encontrada")
            if "nombre" in c:
                t["nombre"] = c["nombre"].strip()
            if c.get("url", "").strip():
                host, plantilla = analiza_direccion(c["url"])
                if host != t["host"]:
                    if any(o["host"] == host for o in lista):
                        raise ValueError("ya existe una tienda con esa dirección")
                    t["host"], t["plantilla"] = host, None   # otra web: se vuelve a descubrir su buscador
                    t.pop("js", None)
                if plantilla:
                    t["plantilla"] = plantilla
            if "manual" in c:
                t["manual"] = bool(c["manual"])
            for campo in ("envio", "envio_gratis"):      # gastos de envío de la tienda (vacío = no se sabe)
                if campo in c:
                    t[campo] = _num(c[campo]) if str(c[campo]).strip() else None
        if c.get("borrar"):
            lista = [t for t in lista if t["host"] != c["borrar"]]
        if "activas" in c:
            for t in lista:
                t["activa"] = t["host"] in c["activas"]
        cfg.guarda(lista)
        return lista

    def log_message(self, *a):
        pass


class Servidor(ThreadingHTTPServer):
    # En Windows SO_REUSEADDR deja que dos procesos compartan puerto sin error.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], ConnectionError):      # el móvil cortó la conexión (pantalla bloqueada, otra app…)
            return
        super().handle_error(request, client_address)


def _ya_hay_uno(puerto):
    """True si en ese puerto ya responde otro BuscaTron (p. ej. el que arranca con Windows)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/api/arranque", timeout=2) as r:
            return "disponible" in json.load(r)
    except (OSError, ValueError):
        return False


def sirve(puerto=8790, host="0.0.0.0", abrir=False, bandeja=False):
    try:
        servidor = Servidor((host, puerto), Handler)
    except OSError as e:
        if abrir and _ya_hay_uno(puerto):          # ya está en marcha: basta con abrir su web
            print(f"BuscaTron ya está abierto en http://127.0.0.1:{puerto}; se abre en el navegador.")
            webbrowser.open(f"http://127.0.0.1:{puerto}")
            return
        raise SystemExit(f"No se pudo abrir el puerto {puerto} ({e.strerror}). "
                         f"¿Ya hay un BuscaTron abierto? Prueba otro: python -m buscatron --puerto {puerto + 1}")
    _servidor.update(host=host, puerto=puerto)
    programador.arranca()
    telegram_bot.arranca()
    threading.Thread(target=motor.rellena_claves, daemon=True).start()
    local =f"http://127.0.0.1:{puerto}"
    print(f"BuscaTron en {local}  (Ctrl+C o cierra la ventana para parar)")
    if host not in ("127.0.0.1", "localhost"):
        for d in direcciones_red():
            print(f"  Desde el móvil ({d['tipo']}): http://{d['ip']}:{puerto}")
    if bandeja:
        from . import bandeja as icono
        print("Bandeja de Windows:", "icono activo" if icono.inicia(puerto) else "no disponible (la ventana sigue visible)")
    if abrir:
        threading.Timer(0.8, webbrowser.open, args=(local,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
