"""Cesta más barata: dado un conjunto de productos y sus ofertas en varias tiendas, calcula dónde comprar cada uno
para pagar lo menos posible en total, contando los gastos de envío de cada tienda y su «envío gratis a partir de X €».
A veces comprar varios en la misma tienda sale mejor que ir a la oferta más barata de cada uno."""
import itertools

MAX_OPCIONES = 6          # tiendas más baratas que se consideran por producto
MAX_COMBINACIONES = 200000


def _envio(t, subtotal):
    """(coste, desconocido) del envío de una tienda para ese subtotal."""
    gratis, coste = t.get("envio_gratis"), t.get("envio")
    if gratis is not None and subtotal >= gratis:
        return 0.0, False
    if coste is None:
        return 0.0, True
    return float(coste), False


def _evalua(eleccion, tiendas):
    por_tienda = {}
    for prod, oferta in eleccion:
        por_tienda.setdefault(oferta["tienda"], []).append((prod, oferta))
    plan, total, dudosos = [], 0.0, []
    for host, items in por_tienda.items():
        subtotal = round(sum(o["precio"] for _, o in items), 2)
        envio, desconocido = _envio(tiendas.get(host, {}), subtotal)
        if desconocido:
            dudosos.append(host)
        plan.append({"tienda": host, "productos": [{"titulo": p["titulo"], "precio": o["precio"], "url": o.get("url", "")} for p, o in items],
                     "subtotal": subtotal, "envio": round(envio, 2), "envio_desconocido": desconocido, "total": round(subtotal + envio, 2)})
        total += subtotal + envio
    plan.sort(key=lambda b: -b["total"])
    return round(total, 2), plan, dudosos


def calcula(productos, tiendas):
    """productos: [{titulo, ofertas: [{tienda, precio, url}]}]; tiendas: {host: {envio, envio_gratis, ...}}.
    Devuelve la mejor combinación, la de «cada uno en su tienda más barata» y el ahorro."""
    opciones = []
    for p in productos:
        mejor_por_tienda = {}
        for o in p.get("ofertas", []):
            if o.get("agotado") or o.get("precio") is None:
                continue
            if o["tienda"] not in mejor_por_tienda or o["precio"] < mejor_por_tienda[o["tienda"]]["precio"]:
                mejor_por_tienda[o["tienda"]] = o
        ofertas = sorted(mejor_por_tienda.values(), key=lambda o: o["precio"])[:MAX_OPCIONES]
        if ofertas:
            opciones.append((p, ofertas))
    if not opciones:
        return {"error": "ningún producto de la cesta tiene ofertas disponibles"}
    n = MAX_OPCIONES
    while n > 1 and _producto([len(o) for _, o in opciones], n) > MAX_COMBINACIONES:
        n -= 1
    opciones = [(p, o[:n]) for p, o in opciones]

    mejor = None
    for combo in itertools.product(*[[(p, o) for o in ofs] for p, ofs in opciones]):
        total, plan, dudosos = _evalua(combo, tiendas)
        clave = (total, len(plan))                           # a igual precio, menos tiendas (menos paquetes)
        if mejor is None or clave < mejor[0]:
            mejor = (clave, total, plan, dudosos)
    ingenuo_total, ingenuo_plan, _ = _evalua([(p, ofs[0]) for p, ofs in opciones], tiendas)
    _, total, plan, dudosos = mejor
    return {"total": total, "plan": plan, "envios_desconocidos": sorted(set(dudosos)),
            "ingenuo_total": ingenuo_total, "ingenuo_tiendas": len(ingenuo_plan), "ahorro": round(ingenuo_total - total, 2),
            "sin_ofertas": [p["titulo"] for p in productos if not any(p is q for q, _ in opciones)]}


def _producto(tamanos, n):
    r = 1
    for t in tamanos:
        r *= min(t, n)
    return r
