"""Búsqueda abierta: encuentra webs que no están en tu lista con un buscador gratuito (Bing, y DuckDuckGo de
respaldo) y lee el precio de las páginas halladas. Es menos precisa que las tiendas de tu lista: úsala para
descubrir sitios nuevos y, si alguno te gusta, añádelo a la lista."""
import base64
import concurrent.futures as cf
import html as html_
import re
from urllib.parse import parse_qs, quote_plus, urlparse

from . import extract, fetch

# Webs que nunca son una tienda (redes, enciclopedias, reseñas, buscadores…).
DESCARTADAS = {"youtube.com", "facebook.com", "instagram.com", "pinterest.com", "pinterest.es", "reddit.com", "twitter.com", "x.com",
               "tiktok.com", "wikipedia.org", "fandom.com", "boardgamegeek.com", "google.com", "google.es", "bing.com", "microsoft.com",
               "duckduckgo.com", "yahoo.com", "linkedin.com", "tripadvisor.es", "trustpilot.com", "twitch.tv", "wikia.com", "ludonauta.es"}
# Ya se ofrecen como «solo enlace»: bloquean cualquier acceso automático.
BLOQUEADAS = {"amazon.es", "amazon.com", "ebay.es", "ebay.com", "wallapop.com", "idealo.es", "milanuncios.com", "vinted.es", "pccomponentes.com"}
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


def buscadores(consulta, region="es", castellano=True, paginas=2):
    """Direcciones que devuelven los buscadores (Bing con dos formulaciones y varias páginas; DuckDuckGo si Bing da pocas)."""
    variantes = [f"comprar {consulta}" + (" castellano" if castellano else " online"), f"{consulta} precio tienda online"]
    sesgo = "&setlang=es&cc=ES" if region == "es" else ("&setlang=es" if castellano else "")
    urls, errores = [], []

    def anade(h, patron, desenvuelve):
        for href in re.findall(patron, h, re.S):
            u = desenvuelve(href)
            if u.startswith("http") and u not in urls:
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
            anade(h, r'<li class="b_algo".*?<h2[^>]*><a[^>]+href="([^"]+)"', _desenvuelve_bing)
    if len(urls) < 5:
        try:
            st, h = fetch.get(f"https://html.duckduckgo.com/html/?q={quote_plus(variantes[0])}&kl={'es-es' if region == 'es' else 'wt-wt'}", timeout=15)
            if st == 200:
                anade(h, r'class="result__a"[^>]+href="([^"]+)"', _desenvuelve_ddg)
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
        if d and d["moneda"] in ("EUR", "€", "") and all(w in extract.normaliza(d["titulo"] + " " + url) for w in palabras):
            items = [{"titulo": d["titulo"] or extract.titulo_desde_url(url), "url": d["url"] or url, "precio": d["precio"],
                      "agotado": d["agotado"], "preventa": d["preventa"], "estado": ""}]
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
        if (not d or d in excluir_hosts or d in BLOQUEADAS or any(d == x or d.endswith("." + x) for x in DESCARTADAS)
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
