"""Lista de tiendas (tiendas.json, editable desde la interfaz) y plantillas de reserva."""
import json
import os
from urllib.parse import quote_plus

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
    "www.amazon.es": "https://www.amazon.es/s?k={q}&s=price-asc-rank",                                 # solo responde a un navegador real
    "bixoto.com": "https://bixoto.com/es?search={q}",
}


# Tiendas que bloquean cualquier acceso automático: no se consultan, solo se ofrece el enlace de búsqueda.
MANUALES = {
    "ferreteriaibermadrid.es": "https://ferreteriaibermadrid.es/#3273/fullscreen/m=and&q={q}",
}


# Segunda mano: solo se consultan si se activa «Incluir segunda mano». Wallapop y eBay devuelven un 403 a cualquier
# acceso automático (también con un navegador real), así que van como «solo enlace».
SEGUNDA_MANO = {
    "www.vinted.es": {"nombre": "Vinted", "plantilla": "https://www.vinted.es/catalog?search_text={q}&order=relevance"},
    "www.milanuncios.com": {"nombre": "Milanuncios", "plantilla": "https://www.milanuncios.com/anuncios/{q-}.htm?orden=baratos"},
    "es.wallapop.com": {"nombre": "Wallapop", "manual": True, "plantilla": "https://es.wallapop.com/app/search?keywords={q}&order_by=price_low_to_high"},
    "www.ebay.es": {"nombre": "eBay", "manual": True, "plantilla": "https://www.ebay.es/sch/i.html?_nkw={q}&_sop=15&LH_BIN=1"},
}


def url_busqueda(plantilla, consulta):
    """Rellena {q} (con +) y {q-} (con guiones, p. ej. Milanuncios) de una plantilla."""
    return plantilla.replace("{q-}", "-".join(consulta.split())).replace("{q}", quote_plus(consulta))


def carga():
    if os.path.exists(RUTA):
        with open(RUTA, encoding="utf-8") as f:
            lista = json.load(f)
    else:
        lista = [{"host": h, "activa": True, "plantilla": None} for h in INICIALES]
    from . import ajustes
    if not ajustes.carga()["segunda_mano_sembrada"]:    # se añaden una sola vez; si el usuario las quita, no vuelven
        existentes = {t["host"] for t in lista}
        for host, d in SEGUNDA_MANO.items():
            if host not in existentes:
                lista.append({"host": host, "nombre": d["nombre"], "activa": True, "plantilla": d["plantilla"],
                              "tipo": "segunda_mano", **({"manual": True} if d.get("manual") else {})})
        guarda(lista)
        ajustes.guarda({"segunda_mano_sembrada": True})
    if not ajustes.carga()["amazon_automatico"]:     # antes iba como «solo enlace»; con un Chrome real sí responde
        for t in lista:
            if t["host"] == "www.amazon.es":
                t["manual"], t["plantilla"], t["js"] = False, CONOCIDAS["www.amazon.es"], True
        guarda(lista)
        ajustes.guarda({"amazon_automatico": True})
    for t in lista:
        t.setdefault("tipo", "tienda")
        if not t.get("plantilla") and t["host"] in CONOCIDAS:
            t["plantilla"] = CONOCIDAS[t["host"]]
        if t["host"] in MANUALES and "manual" not in t:
            t["manual"], t["plantilla"] = True, MANUALES[t["host"]]
    return lista


def guarda(tiendas):
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(tiendas, f, ensure_ascii=False, indent=2)
