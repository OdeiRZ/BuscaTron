"""Búsqueda abierta: encuentra webs que no están en tu lista con un buscador gratuito (Bing, y DuckDuckGo de
respaldo) y lee el precio de las páginas halladas. Es menos precisa que las tiendas de tu lista: úsala para
descubrir sitios nuevos y, si alguno te gusta, añádelo a la lista."""
import base64
import gzip
import json
import time
import urllib.error
import urllib.request
import concurrent.futures as cf
import html as html_
import re
from urllib.parse import parse_qs, quote_plus, urlparse

from . import ajustes, extract, fetch

# Webs que nunca son una tienda (redes, enciclopedias, reseñas, buscadores…).
DESCARTADAS = {"youtube.com", "facebook.com", "instagram.com", "pinterest.com", "pinterest.es", "reddit.com", "twitter.com", "x.com",
               "tiktok.com", "wikipedia.org", "fandom.com", "boardgamegeek.com", "google.com", "google.es", "bing.com", "microsoft.com",
               "duckduckgo.com", "yahoo.com", "linkedin.com", "tripadvisor.es", "trustpilot.com", "twitch.tv", "wikia.com", "ludonauta.es"}
# Ya se ofrecen como «solo enlace»: bloquean cualquier acceso automático.
BLOQUEADAS = {"amazon.es", "amazon.com", "ebay.es", "ebay.com", "wallapop.com", "idealo.es", "milanuncios.com", "vinted.es", "pccomponentes.com",
              "bixoto.com", "ferreteriaibermadrid.es"}    # estas dos, nunca de forma automática (aunque las quites de tu lista)
TLD_UE = {"es", "fr", "de", "it", "pt", "nl", "be", "at", "ie", "pl", "se", "dk", "fi", "gr", "cz", "hu", "ro", "bg", "hr", "sk", "si", "lt",
          "lv", "ee", "lu", "mt", "cy", "eu", "cat", "eus", "gal"}
TLD_ES = {"es", "cat", "eus", "gal"}
POR_DOMINIO = 2       # como máximo, páginas por dominio


def _dominio(url):
    h = (urlparse(url).netloc or "").lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


def _region_ok(dominio, region):
    """España: .es y dominios genéricos (.com, .net…). UE: además otros países de la UE. Mundo: todos."""
    if region == "mundo":
        return True
    tld = dominio.rsplit(".", 1)[-1]
    if len(tld) != 2 and tld not in ("eus", "cat", "gal"):
        return True                         # .com, .net, .shop… no dicen nada del país
    return tld in (TLD_ES if region == "es" else TLD_UE)


def _desenvuelve_bing(href):
    href = html_.unescape(href)
    if "bing.com/ck/a" not in href:
        return href
    u = parse_qs(urlparse(href).query).get("u", [""])[0]
    if u.startswith("a1"):
        u = u[2:]
        try:
            return base64.urlsafe_b64decode(u + "=" * (-len(u) % 4)).decode("utf-8", "replace")
        except ValueError:
            return ""
    return ""


def _desenvuelve_ddg(href):
    href = html_.unescape(href)
    if "ad_domain" in href or "/y.js" in href:
        return ""                           # anuncio
    u = parse_qs(urlparse(href if href.startswith("http") else "https:" + href).query).get("uddg", [""])[0]
    return u


def relevante(titulo, url, consulta):
    """¿El resultado del buscador habla de lo que buscas? Su título (o su dirección) tiene todas las palabras de la búsqueda."""
    n = extract.normaliza(re.sub(r"<[^>]+>", " ", html_.unescape(titulo)) + " " + url)
    return all(extract.encaja(n, w) for w in extract.normaliza(consulta).split())


BRAVE = "https://api.search.brave.com/res/v1/web/search"


def brave(consulta, clave, region="es", castellano=True):
    """Resultados de Brave Search con tu clave (su API oficial): [(dirección, título y descripción)]. Lanza ValueError con
    el motivo si no responde (clave no válida, límite gastado…)."""
    url = f"{BRAVE}?q={quote_plus(consulta)}&count=20&country={'es' if region == 'es' else 'all'}&search_lang={'es' if castellano else 'en'}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "X-Subscription-Token": clave, "User-Agent": fetch.UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            datos = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                datos = gzip.decompress(datos)
    except urllib.error.HTTPError as e:
        raise ValueError({401: "la clave no es válida", 403: "la clave no tiene permiso", 422: "la clave no es válida",
                          429: "has gastado el límite de búsquedas de tu clave"}.get(e.code, f"HTTP {e.code}"))
    except OSError as e:
        raise ValueError(str(e)[:50])
    res = (json.loads(datos).get("web") or {}).get("results") or []
    return [(x.get("url", ""), f"{x.get('title', '')} {x.get('description', '')}") for x in res]


def _por_api(consulta, clave, region, castellano):
    urls, errores = [], []
    for i, q in enumerate([f"comprar {consulta}" + (" castellano" if castellano else " online"), f"{consulta} precio tienda online"]):
        if i:
            time.sleep(1.2)                       # el plan gratuito admite una consulta por segundo
        try:
            for u, texto in brave(q, clave, region, castellano):
                if u.startswith("http") and u not in urls and relevante(texto, u, consulta):
                    urls.append(u)
        except ValueError as e:
            errores.append(f"Brave: {e}")
            break
    return urls, errores


def buscadores(consulta, region="es", castellano=True, paginas=2):
    """Direcciones que devuelven los buscadores (Bing con dos formulaciones y varias páginas; DuckDuckGo si Bing da pocas).
    Solo se quedan los resultados cuyo título contiene tu búsqueda: el resto es ruido del buscador."""
    clave = ajustes.carga().get("busqueda_clave")
    errores_api = []
    if clave:                                     # con tu clave, un buscador de verdad; Bing solo si falla
        urls, errores_api = _por_api(consulta, clave, region, castellano)
        if urls or not errores_api:
            return urls, errores_api
    variantes = [f"comprar {consulta}" + (" castellano" if castellano else " online"), f"{consulta} precio tienda online"]
    sesgo = "&setlang=es&cc=ES" if region == "es" else ("&setlang=es" if castellano else "")
    urls, errores = [], list(errores_api)

    def anade(h, patron, desenvuelve):
        for href, titulo in re.findall(patron, h, re.S):
            u = desenvuelve(href)
            if u.startswith("http") and u not in urls and relevante(titulo, u, consulta):
                urls.append(u)

    for q in variantes:
        for pag in range(paginas):
            try:
                st, h = fetch.get(f"https://www.bing.com/search?q={quote_plus(q)}{sesgo}&first={pag * 10 + 1}", timeout=15)
            except Exception as e:
                errores.append(f"Bing: {str(e)[:40]}")
                break
            if st != 200:
                errores.append(f"Bing: HTTP {st}")
                break
            anade(h, r'<li class="b_algo".*?<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', _desenvuelve_bing)
    if len(urls) < 5:
        try:
            st, h = fetch.get(f"https://html.duckduckgo.com/html/?q={quote_plus(variantes[0])}&kl={'es-es' if region == 'es' else 'wt-wt'}", timeout=15)
            if st == 200:
                anade(h, r'class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', _desenvuelve_ddg)
            else:
                errores.append(f"DuckDuckGo: HTTP {st}")
        except Exception as e:
            errores.append(f"DuckDuckGo: {str(e)[:40]}")
    return urls, errores


def _lee_pagina(url, consulta):
    """Productos de una página hallada: ficha individual (JSON-LD/Open Graph) o listado de una tienda."""
    try:
        st, h = fetch.get(url, timeout=12)
    except Exception:
        return None, []
    if st != 200:
        return st, []
    palabras = extract.normaliza(consulta).split()
    items = extract.extrae(h, url, consulta)
    if not items:
        d = extract.datos_producto(h, url)
        if d and not str(d["url"] or url).startswith(("http://", "https://")):
            d = None                            # una dirección rara (javascript:…) no se enlaza nunca
        if d and d["moneda"] in ("EUR", "€", "") and all(extract.encaja(extract.normaliza(d["titulo"] + " " + url), w) for w in palabras):
            items = [{"titulo": d["titulo"] or extract.titulo_desde_url(url), "url": d["url"] or url, "precio": d["precio"],
                      "agotado": bool(d["agotado"]), "preventa": bool(d["preventa"]), "estado": ""}]
    for x in items:
        x["tienda"] = _dominio(url)
    return st, items


def busca(consulta, region="es", excluir_hosts=(), castellano=True, nav=None, max_webs=16):
    """Devuelve (productos, mensaje). `excluir_hosts`: dominios ya consultados como tiendas."""
    urls, errores = buscadores(consulta, region, castellano)
    if not urls:
        return [], "no se pudo usar el buscador de internet" + (f" ({'; '.join(errores)})" if errores else "")
    elegidas, por_dominio = [], {}
    for u in urls:
        d = _dominio(u)
        if (not d or d in excluir_hosts or any(d == x or d.endswith("." + x) for x in BLOQUEADAS) or any(d == x or d.endswith("." + x) for x in DESCARTADAS)
                or not _region_ok(d, region) or por_dominio.get(d, 0) >= POR_DOMINIO):
            continue
        por_dominio[d] = por_dominio.get(d, 0) + 1
        elegidas.append(u)
        if len(elegidas) >= max_webs:
            break
    items, vistos = [], set()
    with cf.ThreadPoolExecutor(6) as ex:
        for st, r in ex.map(lambda u: _lee_pagina(u, consulta), elegidas):
            for x in r:
                if x["url"] not in vistos:
                    vistos.add(x["url"])
                    items.append(x)
    return items, f"no encontré precios en las {len(elegidas)} webs revisadas" if not items else None
