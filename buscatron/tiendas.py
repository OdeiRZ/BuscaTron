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


# Buscadores que no se pueden descubrir desde la portada.
CONOCIDAS = {
    "www.masqueoca.com": "https://www.masqueoca.com/tienda/buscardo.asp?txtbusqueda={q}&dondebusco=1&vertodo=1&stockneg=1",
    "www.turolgames.com": "https://www.turolgames.com/es/buscar?controller=search&search_query={q}",  # necesita navegador (pantalla de carga con JS)
}


# Tiendas que bloquean cualquier acceso automático: no se consultan, solo se ofrece el enlace de búsqueda.
MANUALES = {
    "www.amazon.es": "https://www.amazon.es/s?k={q}&s=price-asc-rank",
    "ferreteriaibermadrid.es": "https://ferreteriaibermadrid.es/#3273/fullscreen/m=and&q={q}",
}


def carga():
    if os.path.exists(RUTA):
        with open(RUTA, encoding="utf-8") as f:
            lista = json.load(f)
    else:
        lista = [{"host": h, "activa": True, "plantilla": None} for h in INICIALES]
    for t in lista:
        if not t.get("plantilla") and t["host"] in CONOCIDAS:
            t["plantilla"] = CONOCIDAS[t["host"]]
        if t["host"] in MANUALES and "manual" not in t:
            t["manual"], t["plantilla"] = True, MANUALES[t["host"]]
    return lista


def guarda(tiendas):
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(tiendas, f, ensure_ascii=False, indent=2)
