"""Lista de tiendas (tiendas.json, editable desde la interfaz) y plantillas de reserva."""
import json
import os
import threading
import time
from urllib.parse import quote_plus

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, "tiendas.json")
cerrojo = threading.RLock()     # leer-cambiar-guardar la lista, de uno en uno

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
# Tiendas cuyo listado no dice si queda stock (Zacatrus lo muestra todo como disponible): al buscar se lee la ficha de
# sus resultados más baratos.
STOCK_EN_FICHA = {"zacatrus.es"}

CONOCIDAS = {
    "www.masqueoca.com": "https://www.masqueoca.com/tienda/buscardo.asp?txtbusqueda={q}&dondebusco=1&vertodo=1&stockneg=1",
    "www.turolgames.com": "https://www.turolgames.com/es/buscar?controller=search&search_query={q}",  # necesita navegador (pantalla de carga con JS)
    # Solo responde a un navegador real. «i=toys» = sección Juguetes y juegos: sin ella, «Vantage» devolvía 166 relojes,
    # protectores y coches y el juego ni aparecía en las páginas leídas; con ella, 33 ofertas y el juego entre ellas.
    "www.amazon.es": "https://www.amazon.es/s?k={q}&i=toys&s=price-asc-rank",
    "bixoto.com": "https://bixoto.com/es?search={q}",
}


AMAZON_ANTES = "https://www.amazon.es/s?k={q}&s=price-asc-rank"

# Búsqueda de repaso: una página más, en todas las secciones y por relevancia, de la que solo se toman los juegos (por
# su título). Para los mal clasificados: Eternal Decks no está en «Juguetes y juegos» de Amazon.
REPASO = {"www.amazon.es": "https://www.amazon.es/s?k={q}"}


# Tiendas que bloquean cualquier acceso automático: no se consultan, solo se ofrece el enlace de búsqueda.
MANUALES = {
    "ferreteriaibermadrid.es": "https://ferreteriaibermadrid.es/#3273/fullscreen/m=and&q={q}",
    "bixoto.com": "https://bixoto.com/es?search={q}",     # bloquea la IP tras unas pocas consultas automáticas
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
        lista = lee_json(RUTA)
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
    if not ajustes.carga()["amazon_juguetes"]:       # una vez: Amazon solo en Juguetes y juegos, si tenía la dirección de siempre
        for t in lista:
            if t["host"] == "www.amazon.es" and t.get("plantilla") == AMAZON_ANTES:
                t["plantilla"] = CONOCIDAS["www.amazon.es"]
        guarda(lista)
        ajustes.guarda({"amazon_juguetes": True})
    for t in lista:
        t.setdefault("tipo", "tienda")
        if not t.get("plantilla") and t["host"] in CONOCIDAS:
            t["plantilla"] = CONOCIDAS[t["host"]]
        if t["host"] in MANUALES and "manual" not in t:
            t["manual"], t["plantilla"] = True, MANUALES[t["host"]]
    return lista


def lee_json(ruta):
    """Lee un JSON; en Windows, si justo se está reemplazando (escribe_json), se reintenta un momento después."""
    for intento in range(20):
        try:
            with open(ruta, encoding="utf-8") as f:
                return json.load(f)
        except PermissionError:
            time.sleep(0.05)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def escribe_json(ruta, datos):
    """Escribe en un archivo temporal y lo cambia por el bueno de una vez: quien lo lea a la vez ve el viejo o el nuevo,
    nunca uno a medias."""
    tmp = f"{ruta}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    for intento in range(20):
        try:
            os.replace(tmp, ruta)
            return
        except PermissionError:          # Windows: otro hilo lo tiene abierto justo ahora para leerlo
            time.sleep(0.05)
    os.replace(tmp, ruta)


def guarda(tiendas):
    with cerrojo:
        escribe_json(RUTA, tiendas)


def aplica_descubiertas(cambios):
    """Guarda lo que una búsqueda ha aprendido de cada tienda ({host: (plantilla, js)}) sobre la lista ACTUAL, no sobre
    la que había al empezar: así no se pierde lo que cambiaste mientras buscaba."""
    if not cambios:
        return
    with cerrojo:
        lista = carga()
        for t in lista:
            if t["host"] in cambios:
                t["plantilla"], js = cambios[t["host"]]
                if js:
                    t["js"] = True
                else:
                    t.pop("js", None)
        guarda(lista)
