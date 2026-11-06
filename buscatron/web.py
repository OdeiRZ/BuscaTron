"""Interfaz web local (solo biblioteca estándar)."""
import json
import os
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from . import ajustes, motor, notifica, programador, seguimiento, tiendas as cfg


def _pagina():
    with open(os.path.join(os.path.dirname(__file__), "pagina.html"), encoding="utf-8") as f:
        return f.read()


def _num(v):
    v = str(v).replace(",", ".").strip()
    return float(v) if v else None


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        rutas = {"/api/tiendas": cfg.carga, "/api/seguimientos": seguimiento.lista,
                 "/api/avisos": seguimiento.avisos, "/api/ajustes": ajustes.publico}
        if self.path in rutas:
            return self._json(rutas[self.path]())
        data = _pagina().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            return self._json(self._post(self.path, cuerpo))
        except (ValueError, KeyError) as e:
            return self._json({"error": str(e) or "datos no válidos"}, 400)

    def _post(self, ruta, c):
        if ruta == "/api/buscar":
            res, inf = motor.buscar(c.get("q", "").strip(), c.get("incluir", ""), c.get("excluir", ""),
                                    bool(c.get("sin_agotados")), c.get("tiendas"),
                                    _num(c.get("pmin", "")), _num(c.get("pmax", "")))
            return {"resultados": res[: int(c.get("top") or 50)], "total": len(res), "informe": inf}
        if ruta == "/api/tiendas":
            lista = cfg.carga()
            if c.get("anadir"):
                host = c["anadir"].replace("https://", "").replace("http://", "").strip("/ ")
                if host and all(t["host"] != host for t in lista):
                    lista.append({"host": host, "activa": True, "plantilla": None})
            if "activas" in c:
                for t in lista:
                    t["activa"] = t["host"] in c["activas"]
            cfg.guarda(lista)
            return lista
        if ruta == "/api/seguimientos":
            accion = c.get("accion", "guardar")
            if accion == "borrar":
                seguimiento.borra(int(c["id"]))
            elif accion == "revisar":
                threading.Thread(target=seguimiento.revisa, args=(int(c["id"]),), daemon=True).start()
            else:
                seguimiento.guarda(c)
            return seguimiento.lista()
        if ruta == "/api/ajustes":
            ajustes.guarda(c)
            return ajustes.publico()
        if ruta == "/api/detectar_chat":
            ajustes.guarda({k: c[k] for k in ("telegram_token",) if k in c})
            chat = notifica.detectar_chat()
            ajustes.guarda({"telegram_chat": chat})
            return ajustes.publico()
        if ruta == "/api/prueba_aviso":
            return notifica.envia([k for k in c.get("canales", []) if k in ("telegram", "correo")],
                                  "BuscaTron · prueba", "Si lees esto, los avisos funcionan.")
        raise KeyError("no encontrado")

    def log_message(self, *a):
        pass


class Servidor(ThreadingHTTPServer):
    # En Windows SO_REUSEADDR deja que dos procesos compartan puerto sin error.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def sirve(puerto=8790, host="127.0.0.1", abrir=False):
    try:
        servidor = Servidor((host, puerto), Handler)
    except OSError as e:
        raise SystemExit(f"No se pudo abrir el puerto {puerto} ({e.strerror}). "
                         f"¿Ya hay un BuscaTron abierto? Prueba otro: python -m buscatron --puerto {puerto + 1}")
    programador.arranca()
    url = f"http://{'127.0.0.1' if host in ('0.0.0.0', '') else host}:{puerto}"
    print(f"BuscaTron en {url}  (Ctrl+C o cierra la ventana para parar)")
    if abrir:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
