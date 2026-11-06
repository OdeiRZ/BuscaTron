"""Lista de tiendas (tiendas.json, editable desde la interfaz) y plantillas de reserva."""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, "tiendas.json")

# Se prueban solo si la tienda no tiene formulario de búsqueda detectable.
PLANTILLAS = [
    "/buscar?controller=search&s={q}",
    "/catalogsearch/result/?q={q}",
    "/search?q={q}&type=product",
    "/?s={q}&post_type=product",
]

INICIALES = """juegosdelamesaredonda.com zacatrus.es dungeonmarvels.com jugamosuna.es
www.turolgames.com www.tiendasmgi.es ferreteriaibermadrid.es www.masqueoca.com
www.amazon.es gameria.es www.eltallerdelmodelista.com mathom.es jugamosotra.com
tablerum.com www.outletgames.es www.ludusbelli.com banduawargames.com
outlet-pc.es www.goblintrader.es""".split()


def carga():
    if os.path.exists(RUTA):
        with open(RUTA, encoding="utf-8") as f:
            return json.load(f)
    return [{"host": h, "activa": True, "plantilla": None} for h in INICIALES]


def guarda(tiendas):
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(tiendas, f, ensure_ascii=False, indent=2)
