"""Lista de seguimiento: búsquedas vigiladas y reglas de aviso."""
import json
import statistics
import threading
import time

from . import bd, motor, notifica

CAMPOS = ("nombre", "consulta", "incluir", "excluir", "pmin", "pmax", "objetivo", "bajo_historico",
          "sin_agotados", "castellano", "opciones", "canales", "cada_horas", "activo")
OPCIONES = {"preventas": False, "con_envio": False, "segunda_mano": False, "abierta": False, "region": "es", "paginas": None, "idioma": None, "resumen": False, "alguna": ""}
NO_SON_DE_BUSQUEDA = ("resumen",)
# Lo que cambia el resultado de una revisión: si lo editas mientras se revisa, se repite con lo nuevo al acabar
# (el nombre, la frecuencia, los canales o pausarla no hacen falta).
DE_LA_BUSQUEDA = ("consulta", "incluir", "excluir", "pmin", "pmax", "objetivo", "bajo_historico", "sin_agotados", "castellano", "opciones")      # opciones del seguimiento que el motor no recibe
MIN_OBSERVACIONES = 4      # mínimo de precios previos de un artículo para fiarse de su media
REAVISO_DIAS = 30
_cerrojo = threading.Lock()
_en_curso = set()


def _num(v):
    try:
        return float(str(v).replace(",", ".")) if str(v).strip() != "" else None
    except ValueError:
        return None


def opciones_de(seg):
    """Opciones de búsqueda de un seguimiento (JSON en la base de datos), completadas con los valores por defecto."""
    try:
        d = json.loads(seg.get("opciones") or "{}")
    except ValueError:
        d = {}
    return {k: d.get(k, v) for k, v in OPCIONES.items()}


def lista():
    with bd.conecta() as c:
        filas = [dict(r) for r in c.execute("SELECT * FROM seguimientos ORDER BY id")]
    with _cerrojo:
        en_curso = set(_en_curso)
    for f in filas:
        f["opciones"] = opciones_de(f)      # para la web: un objeto, no un texto
        f["revisando"] = f["id"] in en_curso
    return filas


def _opciones(o):
    o = o if isinstance(o, dict) else {}
    region = o.get("region") if o.get("region") in ("es", "ue", "mundo") else "es"
    paginas = _num(o.get("paginas", ""))
    return {"preventas": bool(o.get("preventas")), "con_envio": bool(o.get("con_envio")), "segunda_mano": bool(o.get("segunda_mano")),
            "abierta": bool(o.get("abierta")), "region": region, "paginas": int(min(max(paginas, 1), 6)) if paginas else None,
            "idioma": o.get("idioma") if o.get("idioma") in ("castellano", "estricto", "todos") else None,
            "resumen": bool(o.get("resumen")), "alguna": str(o.get("alguna") or "").strip()[:500]}


def guarda(d):
    """Crea o actualiza (si trae id). Devuelve el id."""
    v = {"nombre": (d.get("nombre") or d.get("consulta") or "").strip(),
         "consulta": (d.get("consulta") or "").strip(),
         "incluir": d.get("incluir", ""), "excluir": d.get("excluir", ""),
         "pmin": _num(d.get("pmin", "")), "pmax": _num(d.get("pmax", "")),
         "objetivo": _num(d.get("objetivo", "")), "bajo_historico": _num(d.get("bajo_historico", "")) or 0,
         "sin_agotados": 1 if d.get("sin_agotados", True) else 0,
         "castellano": 1 if d.get("castellano", True) else 0,
         "opciones": json.dumps(_opciones(d.get("opciones"))),
         "canales": d.get("canales", "app") or "app",
         "cada_horas": max(0.25, _num(d.get("cada_horas", 12)) or 12),
         "activo": 1 if d.get("activo", True) else 0}
    if not v["consulta"]:
        raise ValueError("falta la búsqueda")
    with bd.conecta() as c:
        if d.get("id"):
            if "activo" not in d:      # editar sin decir nada de la pausa la deja como estaba
                fila = c.execute("SELECT activo FROM seguimientos WHERE id=?", (d["id"],)).fetchone()
                v["activo"] = fila["activo"] if fila else 1
            c.execute("UPDATE seguimientos SET " + ",".join(f"{k}=?" for k in CAMPOS) + " WHERE id=?",
                      [v[k] for k in CAMPOS] + [d["id"]])
            return int(d["id"])
        cur = c.execute("INSERT INTO seguimientos(" + ",".join(CAMPOS) + ") VALUES(" + ",".join("?" * len(CAMPOS)) + ")",
                        [v[k] for k in CAMPOS])
        return cur.lastrowid


def borra(seg_id):
    """Borra el seguimiento y sus avisos (el historial de precios se conserva)."""
    with bd.conecta() as c:
        c.execute("DELETE FROM avisos WHERE seg_id=?", (seg_id,))
        c.execute("DELETE FROM seguimientos WHERE id=?", (seg_id,))


def avisos(limite=100):
    with bd.conecta() as c:
        return [dict(r) for r in c.execute("SELECT * FROM avisos WHERE oculto=0 ORDER BY ts DESC LIMIT ?", (limite,))]


def borra_aviso(aviso_id):
    """Quita un aviso de la lista. Se oculta en vez de borrarse: BuscaTron recuerda que ya avisó de ese producto,
    así que no vuelve a avisar por Telegram salvo que baje más de precio (o pasen 30 días)."""
    with bd.conecta() as c:
        c.execute("UPDATE avisos SET oculto=1 WHERE id=?", (aviso_id,))


def _edad(ts):
    h = (time.time() - ts) / 3600
    return "hace menos de 1 h" if h < 1 else f"hace {round(h)} h" if h < 48 else f"hace {round(h / 24)} días"


def vacia_avisos():
    with bd.conecta() as c:
        c.execute("DELETE FROM avisos")


def limpia_avisos(seg_id, res, informe):
    """Retira los avisos que ya no cumplen la búsqueda (agotado, otro idioma, fuera de precio…).
    Solo se tocan los de tiendas que han respondido en esta revisión: un fallo de red no borra nada."""
    vivas = {x["url"] for x in res}
    sin_respuesta = {h for h, i in informe.items() if i.get("caida")}
    abierta_fallida = bool(informe.get("Búsqueda abierta", {}).get("caida"))
    with bd.conecta() as c:
        for r in c.execute("SELECT id, url, tienda FROM avisos WHERE seg_id=?", (seg_id,)).fetchall():
            if r["tienda"] in informe:
                intocable = r["tienda"] in sin_respuesta
            else:                      # procede de la búsqueda abierta
                intocable = abierta_fallida
            if r["url"] not in vivas and not intocable:
                c.execute("DELETE FROM avisos WHERE id=?", (r["id"],))


def _motivo(c, seg, x):
    """Devuelve el motivo del aviso o None. Si el producto tiene su propio objetivo (🎯), manda sobre el de la búsqueda."""
    propio = x.get("objetivo_producto")
    if propio is not None:
        if x["precio"] <= propio:
            return f"cuesta {x['precio']:.2f} €, por debajo de tu objetivo para este producto de {propio:.2f} €".replace(".", ",")
    elif seg["objetivo"] is not None and x["precio"] <= seg["objetivo"]:
        return f"cuesta {x['precio']:.2f} €, por debajo de tu objetivo de {seg['objetivo']:.2f} €".replace(".", ",")
    if seg["bajo_historico"]:
        previos = [r[0] for r in c.execute(
            "SELECT precio FROM precios WHERE url=? AND ts < ? AND agotado=0 AND preventa=0", (x["url"], x["_ts"]))]
        if len(previos) >= MIN_OBSERVACIONES:
            med = statistics.median(previos)
            if x["precio"] <= med * (1 - seg["bajo_historico"] / 100):
                return f"un {(1 - x['precio'] / med) * 100:.0f} % más barato que su precio habitual ({med:.2f} €)".replace(".", ",")
    return None


def revisa(seg_id, enviar=True):
    """Ejecuta un seguimiento ahora. Devuelve {'resultados': n, 'avisos': [...], 'envio': {...}}."""
    from . import servicio
    with _cerrojo:
        if seg_id in _en_curso or servicio.saliendo():      # ya en marcha, o BuscaTron reiniciándose: no se empieza
            return {"ocupado": True}
        _en_curso.add(seg_id)
    try:
        with servicio.trabajo("revision"):
            return _vueltas(seg_id, enviar)
    finally:
        with _cerrojo:
            _en_curso.discard(seg_id)


def _vueltas(seg_id, enviar):
    """Revisa y, si la editaste mientras tanto, otra vez con lo nuevo (como mucho tres vueltas)."""
    for vuelta in range(3):
        r, usada = _revisa(seg_id, enviar)
        with bd.conecta() as c:
            ahora = c.execute("SELECT * FROM seguimientos WHERE id=?", (seg_id,)).fetchone()
            if ahora is None:              # la borraste mientras se revisaba: que no queden sus avisos
                c.execute("DELETE FROM avisos WHERE seg_id=?", (seg_id,))
                return r
        if all(ahora[k] == usada[k] for k in DE_LA_BUSQUEDA):
            return r
    return r


def _revisa(seg_id, enviar):
    """Una revisión con la vigilada tal como está ahora. Devuelve (resultado, vigilada usada)."""
    try:
        with bd.conecta() as c:
            seg = c.execute("SELECT * FROM seguimientos WHERE id=?", (seg_id,)).fetchone()
        if not seg:
            raise ValueError("seguimiento inexistente")
        seg = dict(seg)
        ts = time.time()
        res, informe = motor.buscar(seg["consulta"], seg["incluir"], seg["excluir"], bool(seg["sin_agotados"]),
                                    None, seg["pmin"], seg["pmax"], seg_id,
                                    castellano=bool(seg["castellano"]),
                                    **{k: v for k, v in opciones_de(seg).items() if k not in NO_SON_DE_BUSQUEDA})
        limpia_avisos(seg_id, res, informe)
        opc = opciones_de(seg)
        modo = motor.modo_idioma(bool(seg["castellano"]), opc.get("idioma"))
        # Antes de avisar se mira la ficha de cada candidato: el listado no siempre dice si está agotado, si es una
        # preventa o en qué idioma está (Amazon traduce sus títulos).
        with bd.conecta() as c0:
            candidatos = [x for x in res if _motivo(c0, seg, {**x, "_ts": ts})]
        lista = motor.cfg.carga()
        for x in candidatos:
            f = motor.ficha(x, lista)
            if f["agotado"]:
                x["agotado"] = True
            if f["preventa"]:
                x["preventa"] = True
            if modo != "todos" and f["idioma"]:
                x["idioma"], x["idioma_seguro"], x["idioma_verificado"] = f["idioma"], True, True
        nuevos = []
        with bd.conecta() as c:
            for x in res:
                x["_ts"] = ts
                motivo = _motivo(c, seg, x)
                if not motivo:
                    continue
                if (x.get("agotado") and seg["sin_agotados"]) or (x.get("preventa") and not opc.get("preventas")):
                    continue                  # su ficha dice que está agotado o en preventa
                if modo != "todos" and not motor.permite(x.get("idioma", "?"), x.get("idioma_seguro", False), modo):
                    continue                  # su ficha dice que no está en castellano
                if modo != "todos" and not (x.get("idioma") == "es" and x.get("idioma_seguro")):
                    motivo += " · idioma sin confirmar"
                if x.get("importado"):      # no se consulta en directo: es lo que el usuario pegó a mano
                    motivo += f" · precio pegado a mano {_edad(x['importado'])}, sin comprobar en directo"
                ult = c.execute("SELECT precio, ts FROM avisos WHERE seg_id=? AND url=? ORDER BY ts DESC LIMIT 1",
                                (seg_id, x["url"])).fetchone()
                if ult and x["precio"] >= ult["precio"] - 0.005 and ts - ult["ts"] < REAVISO_DIAS * 86400:
                    continue
                c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                          (ts, seg_id, x["titulo"], x["tienda"], x["url"], x["precio"], motivo))
                nuevos.append({**x, "motivo": motivo})
            caidas = sum(1 for i in informe.values() if i.get("caida"))
            n = len(nuevos)
            estado = (f"{productos(res)}, {n} aviso{'' if n == 1 else 's'} nuevo{'' if n == 1 else 's'}"
                      + (f", {caidas} tienda{'' if caidas == 1 else 's'} sin respuesta" if caidas else ""))
            c.execute("UPDATE seguimientos SET ultima=?, estado=? WHERE id=?", (ts, estado, seg_id))
        envio = {}
        if nuevos and enviar:
            canales = [k for k in seg["canales"].split(",") if k in ("telegram", "correo")]
            grupos = agrupa(nuevos)
            lineas = [linea_grupo(g, con_motivo=True) for g in grupos[:10]]
            if len(grupos) > 10:
                lineas.append(f"… y {len(grupos) - 10} productos más en la pestaña Avisos")
            envio = notifica.envia(canales, f"BuscaTron · {seg['nombre']}", "\n\n".join(lineas))
        elif enviar and opc.get("resumen") and "telegram" in seg["canales"].split(","):
            envio = notifica.envia(["telegram"], f"BuscaTron · {seg['nombre']} · resumen", resumen(seg, opc, modo, res, informe))
        return {"resultados": len(res), "avisos": nuevos, "envio": envio}, seg
    except Exception as e:
        # Se anota la revisión aunque falle: si no, el programador la repetiría cada minuto contra todas las tiendas
        # (una ráfaga así es lo que hace que una tienda bloquee tu conexión).
        with bd.conecta() as c:
            c.execute("UPDATE seguimientos SET ultima=?, estado=? WHERE id=?",
                      (time.time(), f"la revisión falló: {str(e)[:120] or e.__class__.__name__}", seg_id))
        raise


def euros(v):
    return f"{v:.2f}".replace(".", ",") + " €"


def _nombres():
    return {t["host"]: t.get("nombre") or t["host"].replace("www.", "") for t in motor.cfg.carga()}


def productos(res):
    """«3 productos (10 ofertas)»: las mismas palabras que la página y el bot."""
    p, o = len(agrupa(res)), len(res)
    return f"{p} producto{'' if p == 1 else 's'} ({o} oferta{'' if o == 1 else 's'})"


def agrupa(items):
    """Agrupa por producto (la clave «grupo» del motor), cada grupo del más barato al más caro, los grupos por su mejor precio."""
    g = {}
    for x in items:
        g.setdefault(x.get("grupo") or x["url"], []).append(x)
    grupos = [sorted(v, key=lambda x: x["precio"]) for v in g.values()]
    return sorted(grupos, key=lambda v: v[0]["precio"])


def linea_grupo(g, con_motivo=False, nombres=None, otras=3):
    """«Título · 36,50 € en Bixoto (−19 % sobre su precio de mercado)», el motivo del aviso, el enlace y hasta `otras`
    tiendas más."""
    nombres = nombres or _nombres()
    x = g[0]
    partes = [f"{x['titulo']}\n{euros(x['precio'])} en {nombres.get(x.get('tienda'), x.get('tienda', ''))}"
              + (f" (−{x['descuento']} % sobre su precio de mercado, {euros(x['pvp'])})" if x.get("descuento") else "")]
    if con_motivo and x.get("motivo"):
        partes.append(x["motivo"])
    partes.append(x["url"])
    if len(g) > 1:
        lista = ", ".join(f"{euros(o['precio'])} en {nombres.get(o.get('tienda'), o.get('tienda', ''))}" for o in g[1:1 + otras])
        partes.append("También: " + lista + (f" y {len(g) - 1 - otras} más" if len(g) > 1 + otras else ""))
    return "\n".join(partes)


MAX_RESUMEN = 30           # productos por resumen; Telegram lo trocea si no cabe en un mensaje


def resumen(seg, opc, modo, res, informe, ofertas=3):
    """Mensaje de una revisión sin avisos nuevos: cada producto que cumple la búsqueda (del más barato al más caro) con
    sus `ofertas` ofertas más baratas."""
    validos = [x for x in res if not (x.get("agotado") and seg["sin_agotados"]) and not (x.get("preventa") and not opc.get("preventas"))
               and (modo == "todos" or motor.permite(x.get("idioma", "?"), x.get("idioma_seguro", False), modo))]
    grupos = agrupa(validos)
    caidas = sum(1 for i in informe.values() if i.get("caida"))
    lineas = [f"Sin avisos nuevos. Revisados {productos(res)}" + (f" ({caidas} tiendas sin respuesta)" if caidas else "") + "."]
    if grupos:
        nombres = _nombres()
        lineas.append(f"{'Tu producto' if len(grupos) == 1 else f'Tus {len(grupos)} productos'} y sus {ofertas} ofertas más baratas:")
        lineas += [linea_grupo(g, nombres=nombres, otras=ofertas - 1) for g in grupos[:MAX_RESUMEN]]
        if len(grupos) > MAX_RESUMEN:
            lineas.append(f"… y {len(grupos) - MAX_RESUMEN} productos más en BuscaTron")
    else:
        lineas.append("Ningún producto cumple ahora tu búsqueda.")
    return "\n\n".join(lineas)


def cubren(titulo, precio=None):
    """Nombres de las vigiladas activas que encontrarían este producto (aproximado: por las palabras de su búsqueda y sus
    filtros). Sirve para avisar de que un objetivo 🎯 no avisará si ninguna vigilada busca ese producto."""
    n = motor.extract.normaliza(titulo)
    nombres = []
    for s in lista():
        if not s["activo"]:
            continue
        palabras = motor.extract.normaliza(f"{s['consulta']} {s['incluir'] or ''}").split()
        frases = [f for f in (motor.extract.normaliza(x).strip() for x in s["opciones"]["alguna"].split(",")) if f]
        encaja = motor.extract.encaja
        if (all(encaja(n, w) for w in palabras) and not any(encaja(n, w) for w in motor.extract.normaliza(s["excluir"] or "").split())
                and (not frases or any(encaja(n, f) for f in frases))
                and not (precio is not None and s["pmin"] is not None and precio < s["pmin"])):
            nombres.append(s["nombre"])
    return nombres


def pendientes(ahora=None):
    ahora = ahora or time.time()
    return [s["id"] for s in lista() if s["activo"] and ahora - s["ultima"] >= s["cada_horas"] * 3600]
