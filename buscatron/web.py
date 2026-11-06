"""Interfaz web local (solo biblioteca estándar)."""
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from . import motor, tiendas as cfg



def _pagina():
    import os
    with open(os.path.join(os.path.dirname(__file__), "pagina.html"), encoding="utf-8") as f:
        return f.read()


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/tiendas":
            return self._json(cfg.carga())
        data = _pagina().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/api/buscar":
            num = lambda v: float(str(v).replace(",", ".")) if str(v).strip() else None
            try:
                res, inf = motor.buscar(
                    cuerpo.get("q", "").strip(), cuerpo.get("incluir", ""), cuerpo.get("excluir", ""),
                    bool(cuerpo.get("sin_agotados")), cuerpo.get("tiendas"),
                    num(cuerpo.get("pmin", "")), num(cuerpo.get("pmax", "")))
            except ValueError:
                return self._json({"error": "precio no válido"}, 400)
            return self._json({"resultados": res[: int(cuerpo.get("top") or 50)], "total": len(res), "informe": inf})
        if self.path == "/api/tiendas":
            lista = cfg.carga()
            if cuerpo.get("anadir"):
                host = cuerpo["anadir"].replace("https://", "").replace("http://", "").strip("/ ")
                if host and all(t["host"] != host for t in lista):
                    lista.append({"host": host, "activa": True, "plantilla": None})
            if "activas" in cuerpo:
                for t in lista:
                    t["activa"] = t["host"] in cuerpo["activas"]
            cfg.guarda(lista)
            return self._json(lista)
        self._json({"error": "no encontrado"}, 404)

    def log_message(self, *a):
        pass


def sirve(puerto=8790, host="127.0.0.1"):
    print(f"BuscaTron en http://{host}:{puerto}")
    ThreadingHTTPServer((host, puerto), Handler).serve_forever()
