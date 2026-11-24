"""Lista de seguimiento: búsquedas vigiladas y reglas de aviso."""
import json
import re
import statistics
import threading
import time

from . import bd, motor, notifica, progreso

CAMPOS = ("nombre", "consulta", "incluir", "excluir", "pmin", "pmax", "objetivo", "bajo_historico",
          "sin_agotados", "castellano", "opciones", "canales", "cada_horas", "activo")
OPCIONES = {"preventas": False, "con_envio": False, "segunda_mano": False, "abierta": False, "region": "es", "paginas": None, "idioma": None, "resumen": False, "alguna": "", "tipos": [], "sin_tiendas": []}
NO_SON_DE_BUSQUEDA = ("resumen", "tipos", "sin_tiendas")
# Lo que cambia el resultado de una revisión: si lo editas mientras se revisa, se repite con lo nuevo al acabar
# (el nombre, la frecuencia, los canales o pausarla no hacen falta).
DE_LA_BUSQUEDA = ("consulta", "incluir", "excluir", "pmin", "pmax", "objetivo", "bajo_historico", "sin_agotados", "castellano", "opciones")      # opciones del seguimiento que el motor no recibe
MIN_OBSERVACIONES = 4      # mínimo de precios previos de un artículo para fiarse de su media
REAVISO_DIAS = 30
RARO = 0.4                 # un 40 % por debajo de la mediana de las demás tiendas: «precio raro»
FICHAS_POR_AVISO = 4       # fichas que se leen por tienda antes de avisar (las más baratas; el resto, con lo ya sabido)
_cerrojo = threading.Lock()
_en_curso = {}         # id → cuándo empezó su revisión
_turno = threading.Lock()          # las revisiones, de una en una
_pegados_pendientes = {}           # id → tiendas pegadas mientras se revisaba


def _num(v):
    try:
        return float(str(v).replace(",", ".")) if str(v).strip() != "" else None
    except ValueError:
        return None


def opciones_de(seg):
    """Opciones de búsqueda de un seguimiento (JSON en la base de datos), completadas con los valores por defecto."""
    o = seg.get("opciones") or "{}"
    try:
        d = o if isinstance(o, dict) else json.loads(o)        # ya leídas (lista()) o tal cual en la base de datos
    except ValueError:
        d = {}
    return {k: d.get(k, v) for k, v in OPCIONES.items()}


def lista():
    with bd.conecta() as c:
        filas = [dict(r) for r in c.execute("SELECT * FROM seguimientos ORDER BY id")]
    with _cerrojo:
        en_curso = dict(_en_curso)
    for f in filas:
        f["opciones"] = opciones_de(f)      # para la web: un objeto, no un texto
        f["revisando"] = f["id"] in en_curso
        f["revisando_desde"] = en_curso.get(f["id"])     # para que la web diga cuánto lleva
    return filas


def _opciones(o):
    o = o if isinstance(o, dict) else {}
    region = o.get("region") if o.get("region") in ("es", "ue", "mundo") else "es"
    paginas = _num(o.get("paginas", ""))
    return {"preventas": bool(o.get("preventas")), "con_envio": bool(o.get("con_envio")), "segunda_mano": bool(o.get("segunda_mano")),
            "abierta": bool(o.get("abierta")), "region": region, "paginas": int(min(max(paginas, 1), 6)) if paginas else None,
            "idioma": o.get("idioma") if o.get("idioma") in ("castellano", "estricto", "todos") else None,
            "resumen": bool(o.get("resumen")), "alguna": str(o.get("alguna") or "").strip()[:500],
            "tipos": [t for t in motor.TIPOS if t in (o.get("tipos") or [])],
            "sin_tiendas": [h for h in (o.get("sin_tiendas") or []) if isinstance(h, str)][:300]}


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
    if v["pmin"] is not None and v["pmax"] is not None and v["pmin"] > v["pmax"]:
        raise ValueError("el precio mínimo es mayor que el máximo: no encontraría nada")
    with bd.conecta() as c:
        if not d.get("id"):
            cur = c.execute("INSERT INTO seguimientos(" + ",".join(CAMPOS) + ") VALUES(" + ",".join("?" * len(CAMPOS)) + ")",
                            [v[k] for k in CAMPOS])
            return cur.lastrowid
        if "activo" not in d:      # editar sin decir nada de la pausa la deja como estaba
            fila = c.execute("SELECT activo FROM seguimientos WHERE id=?", (d["id"],)).fetchone()
            v["activo"] = fila["activo"] if fila else 1
        c.execute("UPDATE seguimientos SET " + ",".join(f"{k}=?" for k in CAMPOS) + " WHERE id=?",
                  [v[k] for k in CAMPOS] + [d["id"]])
    limpia_avisos_por_filtros(int(d["id"]))      # los avisos que los filtros nuevos descartan, fuera
    return int(d["id"])


def borra(seg_id):
    """Borra el seguimiento y sus avisos (el historial de precios se conserva)."""
    with bd.conecta() as c:
        c.execute("DELETE FROM avisos WHERE seg_id=?", (seg_id,))
        c.execute("DELETE FROM seguimientos WHERE id=?", (seg_id,))


def avisos(limite=500):
    """Avisos visibles, del más reciente al más antiguo. «grupo»: el producto al que pertenece (vigilada + producto), para
    juntar en la página las variantes de nombre del mismo juego (Civil War en cinco tiendas, cinco títulos distintos)."""
    with bd.conecta() as c:
        filas = [dict(r) for r in c.execute("SELECT * FROM avisos WHERE oculto=0 ORDER BY ts DESC LIMIT ?", (limite,))]
        segs = {r["id"]: dict(r) for r in c.execute("SELECT id, consulta, opciones FROM seguimientos")}
    tiendas_ = {t["host"]: t for t in motor.cfg.carga()}
    objs = motor.objetivos()
    for a in filas:
        s = segs.get(a["seg_id"]) or {}
        g = motor.grupos([a["titulo"]], s.get("consulta") or "", opciones_de(s).get("alguna", "") if s else "")[0]["grupo"]
        a["grupo"] = f"{a['seg_id']}|{g}"
        k = motor.clave_objetivo({"grupo": g, "titulo": a["titulo"]}, objs)
        a["objetivo_producto"], a["objetivo_clave"] = (objs[k]["precio"], k) if k else (None, g)
        a["envio"] = motor.envio_de(tiendas_.get(a["tienda"], {}), a["precio"])      # None: no se sabe
    return filas


def borra_aviso(aviso_id):
    """Quita un aviso de la lista. Se oculta en vez de borrarse: BuscaTron recuerda que ya avisó de ese producto,
    así que no vuelve a avisar por Telegram salvo que baje más de precio (o pasen 30 días)."""
    with bd.conecta() as c:
        c.execute("UPDATE avisos SET oculto=1 WHERE id=?", (aviso_id,))


def borra_avisos(ids):
    """Quita varios avisos de una vez (los de un producto en todas sus tiendas)."""
    with bd.conecta() as c:
        c.executemany("UPDATE avisos SET oculto=1 WHERE id=?", [(int(i),) for i in ids])


def _edad(ts):
    h = (time.time() - ts) / 3600
    return "hace menos de 1 h" if h < 1 else f"hace {round(h)} h" if h < 48 else f"hace {round(h / 24)} días"


def vacia_avisos():
    """Vacía la lista. Se ocultan en vez de borrarse, como al quitar uno: si no, la siguiente revisión volvía a mandar
    por Telegram todo lo que sigue cumpliendo."""
    with bd.conecta() as c:
        c.execute("UPDATE avisos SET oculto=1")


def limpia_avisos(seg_id, res, informe):
    """Retira los avisos que ya no cumplen la búsqueda (agotado, otro idioma, fuera de precio…).
    Solo se tocan los de tiendas que han respondido en esta revisión: un fallo de red no borra nada."""
    vivas = {x["url"] for x in res}
    sin_respuesta = {h for h, i in informe.items() if i.get("caida")}
    abierta_fallida = bool(informe.get("Búsqueda abierta", {}).get("caida"))
    lista = motor.cfg.carga()
    mias = {t["host"] for t in lista}
    manuales = {t["host"] for t in lista if t.get("manual") or motor.cfg.nunca(t["host"])}
    with bd.conecta() as c:
        for r in c.execute("SELECT id, url, tienda FROM avisos WHERE seg_id=?", (seg_id,)).fetchall():
            if r["tienda"] in informe:
                intocable = r["tienda"] in sin_respuesta
            elif r["tienda"] in mias:  # tienda tuya que no se consultó (bloqueada o desactivada): no se sabe nada nuevo
                intocable = True
            else:                      # procede de la búsqueda abierta
                intocable = abierta_fallida
            if r["tienda"] in manuales:
                intocable = True       # «solo enlace»: si ya no está, es que caducó lo pegado, no que haya cambiado
            if r["url"] not in vivas and not intocable:
                c.execute("DELETE FROM avisos WHERE id=?", (r["id"],))


def _motivo(c, seg, x):
    """Devuelve el motivo del aviso o None. Si el producto tiene su propio objetivo (🎯), manda sobre el de la búsqueda."""
    propio = x.get("objetivo_producto")
    # «con envío incluido»: se compara lo que pagas (precio + envío) si se sabe el envío de la tienda
    con_envio = opciones_de(seg).get("con_envio") and x.get("envio") is not None
    p = round(x["precio"] + x["envio"], 2) if con_envio else x["precio"]
    cuesta = (f"cuesta {p:.2f} € con envío" if con_envio else f"cuesta {p:.2f} €").replace(".", ",")
    if propio is not None:
        if p <= propio:
            return cuesta + f", por debajo de tu objetivo para este producto de {propio:.2f} €".replace(".", ",")
    elif seg["objetivo"] is not None and p <= seg["objetivo"]:
        return cuesta + f", por debajo de tu objetivo de {seg['objetivo']:.2f} €".replace(".", ",")
    if seg["bajo_historico"]:
        previos = [r[0] for r in c.execute(
            "SELECT precio FROM precios WHERE url=? AND ts < ? AND agotado=0 AND preventa=0",
            (x["url"], min(x["_ts"], x.get("importado") or x["_ts"])))]       # lo pegado: solo lo visto antes de pegarlo
        if len(previos) >= MIN_OBSERVACIONES:
            med = statistics.median(previos)
            if x["precio"] <= med * (1 - seg["bajo_historico"] / 100):
                return f"un {(1 - x['precio'] / med) * 100:.0f} % más barato que su precio habitual ({med:.2f} €)".replace(".", ",")
    # vuelve a haber stock: la última vez que se vio estaba agotado (si tiene objetivo, solo cerca de él: hasta un 15 % más)
    if not x.get("agotado") and not x.get("importado"):
        ult = c.execute("SELECT agotado FROM precios WHERE url=? AND ts < ? AND seg_id=? ORDER BY ts DESC LIMIT 1",
                        (x["url"], x["_ts"], seg.get("id"))).fetchone()
        tope = x.get("objetivo_producto") or seg["objetivo"]
        if ult and ult[0] and (tope is None or p <= tope * 1.15):
            return f"vuelve a estar disponible a {x['precio']:.2f} €".replace(".", ",")
    return None


def _apunta_aviso(c, seg_id, x, ts):
    """¿Se avisa de este producto? No si ya hay un aviso suyo de los últimos REAVISO_DIAS a este precio o a uno más bajo.
    Si su aviso se retiró porque dejó de cumplir (p. ej. se agotó), al volver sí se avisa: es noticia. Lo usan las
    revisiones y lo pegado a mano, para que las dos decidan igual."""
    # El mismo producto de la misma tienda puede llegar por dos direcciones (su ficha, cuando la búsqueda salta a ella, o
    # el enlace del listado): también cuenta como ya avisado si coinciden tienda y nombre.
    ult = c.execute("SELECT precio, ts FROM avisos WHERE seg_id=? AND (url=? OR (tienda=? AND titulo=? AND ts<?)) AND NOT (pendiente=1 AND oculto=0) ORDER BY ts DESC LIMIT 1",
                    (seg_id, x["url"], x.get("tienda"), x.get("titulo"), ts)).fetchone()      # los no enviados no cuentan: se reintentan
    if ult and x["precio"] >= ult["precio"] - 0.005 and ts - ult["ts"] < REAVISO_DIAS * 86400:
        return False
    c.execute("DELETE FROM avisos WHERE seg_id=? AND url=? AND pendiente=1 AND oculto=0", (seg_id, x["url"]))   # lo sustituye el nuevo
    # los anteriores del mismo producto en esa tienda dejan de verse: si no, al quitar el nuevo reaparecía el viejo (más caro)
    c.execute("UPDATE avisos SET oculto=1 WHERE seg_id=? AND oculto=0 AND ts<? AND (url=? OR (tienda=? AND titulo=?))",
              (seg_id, ts, x["url"], x.get("tienda"), x.get("titulo")))     # solo de revisiones anteriores
    return True


def _vale(seg, opc, modo, x):
    """¿Cuenta esta oferta para la vigilada? No si está agotada (y no quieres agotados), es una preventa (y no las
    quieres) o no está en el idioma que pides. Una sola regla para avisos, pegados, límites de Amazon y resúmenes."""
    if (x.get("agotado") and seg["sin_agotados"]) or (x.get("preventa") and not opc.get("preventas")):
        return False
    return modo == "todos" or motor.permite(x.get("idioma", "?"), x.get("idioma_seguro", False), modo)


def _registra_avisos(c, seg, opc, modo, res, ts):
    """Los avisos nuevos de estos resultados para la vigilada: los apunta y los devuelve (con su motivo). La usan las
    revisiones y lo pegado a mano, para que las dos decidan exactamente igual."""
    nuevos = []
    # el precio habitual de cada producto entre tus tiendas (con 3 o más): para avisar de un precio sospechosamente bajo
    por_grupo = {}
    for x in res:
        if not x.get("agotado") and x.get("origen") != "segunda_mano":
            por_grupo.setdefault(x.get("grupo"), {}).setdefault(x["tienda"], x["precio"])
    vistos = [dict(r) for r in c.execute("SELECT tienda, titulo, precio FROM precios WHERE seg_id=? AND ts>=? AND agotado=0 AND preventa=0",
                                         (seg["id"], (seg.get("ultima") or ts) - 60))]      # lo pegado trae una sola tienda
    for v, g in zip(vistos, motor.grupos([v["titulo"] for v in vistos], seg["consulta"], opc.get("alguna", ""))):
        por_grupo.setdefault(g["grupo"], {}).setdefault(v["tienda"], v["precio"])
    medianas = {g: statistics.median(p.values()) for g, p in por_grupo.items() if g and len(p) >= 3}
    for x in res:
        x["_ts"] = ts
        motivo = _motivo(c, seg, x)
        if not motivo or not _vale(seg, opc, modo, x):
            continue
        med = medianas.get(x.get("grupo"))
        if med and x.get("origen") != "segunda_mano" and x["precio"] < med * (1 - RARO):
            motivo += (f" · ⚠️ {(1 - x['precio'] / med) * 100:.0f} % más barato que en tus demás tiendas ({med:.2f} €):"
                       " puede ser un chollo o un error, compruébalo").replace(".", ",", 1)
        if modo != "todos" and not (x.get("idioma") == "es" and x.get("idioma_seguro")):
            motivo += " · idioma sin confirmar"
        if x.get("importado"):          # no se consulta en directo: es lo que pegaste a mano
            motivo += f" · precio pegado a mano {_edad(x['importado'])}, sin comprobar en directo"
        if not _apunta_aviso(c, seg["id"], x, ts):
            continue
        c.execute("INSERT INTO avisos(ts,seg_id,titulo,tienda,url,precio,motivo) VALUES(?,?,?,?,?,?,?)",
                  (ts, seg["id"], x["titulo"], x["tienda"], x["url"], x["precio"], motivo))
        nuevos.append({**x, "motivo": motivo})
    return nuevos


def _envia_avisos(seg, nuevos, ts):
    """Manda los avisos nuevos por los canales de la vigilada. Si no llegan por ninguno, quedan pendientes y la
    siguiente revisión lo intenta otra vez (antes se daban por avisados y no se repetían en 30 días)."""
    canales = [k for k in seg["canales"].split(",") if k in ("telegram", "correo")]
    if not nuevos or not canales:
        return {}
    grupos = agrupa(nuevos)
    lineas = [linea_grupo(g, con_motivo=True) for g in grupos[:10]]
    if len(grupos) > 10:
        lineas.append(f"… y {len(grupos) - 10} productos más en la pestaña Avisos")
    envio = notifica.envia(canales, f"BuscaTron · {seg['nombre']}", "\n\n".join(lineas))
    if envio and all(v and "falta" not in v for v in envio.values()):     # «falta el token…»: no es pasajero, no se reintenta
        with bd.conecta() as c:
            c.executemany("UPDATE avisos SET pendiente=1 WHERE seg_id=? AND url=? AND ts=?", [(seg["id"], x["url"], ts) for x in nuevos])
    return envio


def revisa(seg_id, enviar=True):
    """Ejecuta un seguimiento ahora. Devuelve {'resultados': n, 'avisos': [...], 'envio': {...}}."""
    from . import servicio
    with _cerrojo:
        if seg_id in _en_curso or servicio.saliendo():      # ya en marcha, o BuscaTron reiniciándose: no se empieza
            return {"ocupado": True}
        _en_curso[seg_id] = time.time()
    try:
        with bd.conecta() as c:
            fila = c.execute("SELECT nombre, duracion FROM seguimientos WHERE id=?", (seg_id,)).fetchone()
        with progreso.tarea(f"vigilada:{seg_id}", "vigilada", fila["nombre"] if fila else "Vigilada", fila["duracion"] if fila else None):
            progreso.fase(progreso.actual(), "Esperando a que acabe otra revisión")
            with _turno:                  # una revisión consulta todas las tiendas: dos a la vez serían una ráfaga
                if servicio.saliendo():
                    return {"ocupado": True}
                with servicio.trabajo("revision"):     # cuenta como trabajo solo al empezar: un reinicio no espera a toda la cola
                    progreso.reinicia(progreso.actual())
                    return _vueltas(seg_id, enviar)
    finally:
        with _cerrojo:
            _en_curso.pop(seg_id, None)
            pendientes = _pegados_pendientes.pop(seg_id, set())
        for h in pendientes:              # pegaste mientras se revisaba: ahora sí pasa por sus avisos (solo esta vigilada)
            try:
                _pegado_diferido(seg_id, h, enviar)
            except Exception:             # noqa: BLE001  (no debe tapar el resultado o el error de la revisión)
                pass


def _vueltas(seg_id, enviar):
    """Revisa y, si la editaste mientras tanto, otra vez con lo nuevo (como mucho una vez más: cada vuelta consulta todas las tiendas)."""
    for vuelta in range(2):
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
        sin = set(opciones_de(seg).get("sin_tiendas") or [])
        hosts = [t["host"] for t in motor.cfg.carga() if (t.get("activa", True) or t.get("bloqueo")) and t["host"] not in sin] if sin else None
        res, informe = motor.buscar(seg["consulta"], seg["incluir"], seg["excluir"], bool(seg["sin_agotados"]),
                                    hosts, seg["pmin"], seg["pmax"], seg_id,
                                    castellano=bool(seg["castellano"]),
                                    **{k: v for k, v in opciones_de(seg).items() if k not in NO_SON_DE_BUSQUEDA})
        opc = opciones_de(seg)
        res = [x for x in res if tipo_vale(opc, x["titulo"])]
        limpia_avisos(seg_id, res, informe)
        modo = motor.modo_idioma(bool(seg["castellano"]), opc.get("idioma"))
        # Antes de avisar se mira la ficha de cada candidato: el listado no siempre dice si está agotado, si es una
        # preventa o en qué idioma está (Amazon traduce sus títulos).
        with bd.conecta() as c0:
            candidatos = [x for x in res if _motivo(c0, seg, {**x, "_ts": ts})]
        lista = motor.cfg.carga()
        por_tienda = {}
        for x in sorted(candidatos, key=lambda x: x["precio"]):
            if len(por_tienda.setdefault(x.get("tienda"), [])) < FICHAS_POR_AVISO:
                por_tienda[x.get("tienda")].append(x)
        progreso.fase(progreso.actual(), "Comprobando las fichas antes de avisar")
        for x in [x for xs in por_tienda.values() for x in xs]:
            f = motor.ficha(x, lista)
            if f["agotado"]:
                x["agotado"] = True
            if f["preventa"]:
                x["preventa"] = True
            if modo != "todos" and f["idioma"]:
                x["idioma"], x["idioma_seguro"], x["idioma_verificado"] = f["idioma"], True, True
        with bd.conecta() as c:
            nuevos = _registra_avisos(c, seg, opc, modo, res, ts)
            caidas = tiendas_caidas(informe)
            n = len(nuevos)
            estado = (f"{productos(res)}, {n} aviso{'' if n == 1 else 's'} nuevo{'' if n == 1 else 's'}"
                      + (f", {caidas} tienda{'' if caidas == 1 else 's'} sin respuesta" if caidas else ""))
            c.execute("UPDATE seguimientos SET ultima=?, estado=?, duracion=? WHERE id=?", (ts, estado, time.time() - ts, seg_id))
        envio = _envia_avisos(seg, nuevos, ts) if enviar else {}
        if enviar:
            # límites de Amazon con lo que de verdad vale: sin agotados, preventas (si no las quieres) ni otros idiomas
            envio = {**envio, **_avisa_limites(seg, [x for x in res if _vale(seg, opc, modo, x)])}
        return {"resultados": len(res), "avisos": nuevos, "envio": envio}, seg
    except Exception as e:
        # Se anota la revisión aunque falle: si no, el programador la repetiría cada minuto contra todas las tiendas
        # (una ráfaga así es lo que hace que una tienda bloquee tu conexión).
        with bd.conecta() as c:
            c.execute("UPDATE seguimientos SET ultima=?, estado=? WHERE id=?",
                      (time.time(), f"la revisión falló: {str(e)[:120] or e.__class__.__name__}", seg_id))
        raise


def _solo_enlace(host):
    t = next((t for t in motor.cfg.carga() if t["host"] == host), None)
    return bool(t and (t.get("manual") or motor.cfg.nunca(host)))


def _pegado_diferido(seg_id, host, enviar):
    if not _solo_enlace(host):            # la pasaste a automática mientras tanto: no se consulta por aquí
        return
    with bd.conecta() as c:
        seg = c.execute("SELECT * FROM seguimientos WHERE id=? AND activo=1", (seg_id,)).fetchone()
    if seg:
        from . import servicio
        with servicio.trabajo("pegado"):
            _avisa_pegados_en(dict(seg), host, enviar)


def avisa_pegados(host, enviar=True):
    """Lo que acabas de pegar de una tienda «solo enlace» pasa al momento por tus vigiladas activas y crea sus avisos, sin
    esperar a la próxima revisión. No consulta ninguna tienda: esa tienda no se consulta (solo devuelve lo pegado) y no
    se leen fichas. Devuelve el número de avisos nuevos."""
    if not _solo_enlace(host):            # nunca una tienda que se consulta en directo (sería una petición por vigilada)
        return 0
    with bd.conecta() as c:
        segs = [dict(r) for r in c.execute("SELECT * FROM seguimientos WHERE activo=1 ORDER BY id")]
    total = 0
    for seg in segs:
        with _cerrojo:          # si esa vigilada se está revisando, se hace al terminar (puede haber leído ya lo pegado)
            if seg["id"] in _en_curso:
                _pegados_pendientes.setdefault(seg["id"], set()).add(host)
                continue
        from . import servicio
        with servicio.trabajo("pegado"):
            total += _avisa_pegados_en(seg, host, enviar)
    return total


def _avisa_pegados_en(seg, host, enviar):
    """avisa_pegados para una vigilada. Devuelve el número de avisos nuevos."""
    opc = opciones_de(seg)
    if host in (opc.get("sin_tiendas") or []):       # esa tienda no la quieres en esta vigilada
        return 0
    busqueda = {k: v for k, v in opc.items() if k not in NO_SON_DE_BUSQUEDA}
    busqueda["abierta"] = False
    res, _ = motor.buscar(seg["consulta"], seg["incluir"], seg["excluir"], bool(seg["sin_agotados"]), [host],
                          seg["pmin"], seg["pmax"], seg["id"], castellano=bool(seg["castellano"]), **busqueda)
    res = [x for x in res if tipo_vale(opc, x["titulo"])]
    modo = motor.modo_idioma(bool(seg["castellano"]), opc.get("idioma"))
    ts = time.time()
    with bd.conecta() as c:
        nuevos = _registra_avisos(c, seg, opc, modo, res, ts)
    if enviar:
        _envia_avisos(seg, nuevos, ts)
    return len(nuevos)


ENVIO_ESTIMADO, GRATIS_ESTIMADO = 4.95, 50.0      # envío de una tienda de la que aún no se sabe


def _mejor_por_tienda(ofertas):
    """{tienda: {precio, url, titulo}}: la oferta más barata de este juego en cada tienda (para la compra conjunta)."""
    out = {}
    for x in ofertas:
        if not x.get("agotado") and (x["tienda"] not in out or x["precio"] < out[x["tienda"]]["precio"]):
            out[x["tienda"]] = {"precio": x["precio"], "url": x["url"], "titulo": x["titulo"]}
    return out


def compra_conjunta(grupos):
    """La forma más barata de comprar varios juegos de Mi lista a la vez, contando el envío de cada tienda con su «gratis
    desde» aplicado a lo que compras en ella. Prueba: cada juego donde sale más barato suelto, cada tienda que los tiene
    todos y cada pareja de tiendas (con 10 juegos y 30 tiendas son unos cientos de cuentas). Devuelve los planes, del
    más barato al más caro: [{total, envio, desconocido, pedidos: [{tienda, juegos: [...], subtotal, envio}]}]."""
    import itertools
    unicos = {}
    for p in mi_lista():
        if p["grupo"] not in set(grupos) or not p["por_tienda"]:
            continue
        u = unicos.setdefault(p["grupo"], {"grupo": p["grupo"], "por_tienda": {}})      # puede estar en dos vigiladas
        for h, o in p["por_tienda"].items():
            if h not in u["por_tienda"] or o["precio"] < u["por_tienda"][h]["precio"]:
                u["por_tienda"][h] = o
    lista = list(unicos.values())
    if not lista:
        return []
    tiendas_ = {t["host"]: t for t in motor.cfg.carga()}

    def coste(reparto):                    # reparto: {grupo: tienda}
        pedidos = {}
        for p in lista:
            h = reparto[p["grupo"]]
            pedidos.setdefault(h, []).append(p)
        total, envio_t, desconocido, out = 0.0, 0.0, [], []
        for h, ps in pedidos.items():
            sub = round(sum(p["por_tienda"][h]["precio"] for p in ps), 2)
            env = motor.envio_de(tiendas_.get(h, {}), sub)
            if env is None:                # sin dato: lo habitual (4,95 €, gratis desde 50 €), marcado como estimado
                desconocido.append(h)
                t = tiendas_.get(h, {})
                gratis = t.get("envio_gratis") if t.get("envio_gratis") is not None else (t.get("envio_auto") or {}).get("gratis_desde")
                env = ENVIO_ESTIMADO if sub < (gratis if gratis is not None else GRATIS_ESTIMADO) else 0.0
            total += sub + env
            envio_t += env
            out.append({"tienda": h, "subtotal": sub, "envio": env, "juegos": [
                {"grupo": p["grupo"], "titulo": p["por_tienda"][h]["titulo"], "precio": p["por_tienda"][h]["precio"],
                 "url": p["por_tienda"][h]["url"]} for p in ps]})
        return {"total": round(total, 2), "envio": round(envio_t, 2), "desconocido": desconocido,
                "pedidos": sorted(out, key=lambda o: -len(o["juegos"]))}

    planes = {}
    def prueba(reparto):
        if reparto and len(reparto) == len(lista):
            c = coste(reparto)
            planes[tuple(sorted((g, h) for g, h in reparto.items()))] = c
    prueba({p["grupo"]: min(p["por_tienda"], key=lambda h: p["por_tienda"][h]["precio"]) for p in lista})   # cada uno, el más barato
    todas = sorted({h for p in lista for h in p["por_tienda"]})
    for h in todas:                                                                                         # todo en una tienda
        if all(h in p["por_tienda"] for p in lista):
            prueba({p["grupo"]: h for p in lista})
    for a, b in itertools.combinations(todas, 2):                                                          # repartido entre dos
        if all(a in p["por_tienda"] or b in p["por_tienda"] for p in lista):
            prueba({p["grupo"]: min((h for h in (a, b) if h in p["por_tienda"]), key=lambda h: p["por_tienda"][h]["precio"])
                    for p in lista})
    return sorted(planes.values(), key=lambda c: c["total"])[:5]


def _desde(c, seg):
    """Desde cuándo cuentan los precios de una vigilada: su última revisión, o la última buena si la última falló."""
    if "falló" in (seg["estado"] or ""):
        return c.execute("SELECT COALESCE(MAX(ts), 0) FROM precios WHERE seg_id=?", (seg["id"],)).fetchone()[0]
    return (seg["ultima"] or 0) - 60


def mi_lista():
    """Una línea por juego de cada vigilada: su mejor oferta ahora (con envío si se sabe), en cuántas tiendas está, lo más
    barato que se le ha visto y tu objetivo. Sale de la última revisión de cada vigilada y de lo pegado vigente: no
    consulta ninguna tienda."""
    from . import importar
    objs = motor.objetivos()
    tiendas_ = {t["host"]: t for t in motor.cfg.carga()}
    manuales = [h for h, t in tiendas_.items() if (t.get("manual") or motor.cfg.nunca(h)) and (t.get("activa", True) or t.get("bloqueo"))]
    ocultos = set(motor.ignorados())
    with bd.conecta() as c:
        segs = [dict(r) for r in c.execute("SELECT * FROM seguimientos WHERE activo=1 ORDER BY nombre")]
        # historial de cada vigilada (lo que ella ha visto, con sus filtros): para el «mínimo visto»
        hist_de = {s["id"]: [dict(r) for r in c.execute(
            "SELECT titulo, precio, tienda FROM precios WHERE seg_id=? AND agotado=0 AND preventa=0", (s["id"],))] for s in segs}
        filas_de = {s["id"]: [dict(r) for r in c.execute(
            "SELECT tienda, titulo, url, precio, agotado, preventa, ts FROM precios WHERE seg_id=? AND ts>=?",
            (s["id"], _desde(c, s)))] for s in segs if s["ultima"]}
    out = []
    for seg in segs:
        if seg["id"] not in filas_de:
            continue
        opc = opciones_de(seg)
        modo = motor.modo_idioma(bool(seg["castellano"]), opc.get("idioma"))
        pegado = [{**x, "tienda": h} for h in manuales if opc.get("segunda_mano") or tiendas_[h].get("tipo") != "segunda_mano"
                  for x in importar.vigentes(h, seg["consulta"])]
        pegado = [x for x in pegado if modo == "todos" or motor.permite(*motor.idioma_de(x["titulo"]), modo)]
        vivas = filas_de[seg["id"]]
        stock, idi = motor.stock_de_fichas([x["url"] for x in vivas]), motor.idiomas_de_fichas([x["url"] for x in vivas])
        for x in vivas:                  # lo que dijo su ficha manda sobre el listado
            ago, pre = stock.get(x["url"], (None, None))
            x["agotado"], x["preventa"] = x["agotado"] or bool(ago), x["preventa"] or bool(pre)
        vivas = [x for x in vivas if modo == "todos" or x["url"] not in idi or motor.permite(idi[x["url"]], True, modo)]
        filas = [x for x in vivas + pegado if motor.clave_producto(x["titulo"]) not in ocultos]
        filas = [x for x in filas if cumple(seg, x["titulo"], x["precio"], x["tienda"])
                 and not (x.get("agotado") and seg["sin_agotados"]) and not (x.get("preventa") and not opc.get("preventas"))]
        if not filas:
            continue
        grupos = motor.grupos([x["titulo"] for x in filas], seg["consulta"], opc.get("alguna", ""))
        h = [x for x in hist_de[seg["id"]] if cumple(seg, x["titulo"], x["precio"], x["tienda"])]
        minimos, vistos = {}, {}
        for x, g in zip(h, motor.grupos([x["titulo"] for x in h], seg["consulta"], opc.get("alguna", ""))):
            minimos[g["grupo"]] = min(minimos.get(g["grupo"], x["precio"]), x["precio"])
            vistos.setdefault(g["grupo"], []).append(x["precio"])
        por = {}
        for x, g in zip(filas, grupos):
            envio = motor.envio_de(tiendas_.get(x["tienda"], {}), x["precio"])
            x = {**x, "envio": envio, "total": round(x["precio"] + (envio or 0), 2), "grupo": g["grupo"]}
            por.setdefault(g["grupo"], {}).setdefault(x["url"], x)       # una oferta por enlace
        for grupo, ofertas in por.items():
            o = sorted(ofertas.values(), key=lambda x: (bool(x.get("agotado")), x["total"] if opc.get("con_envio") else x["precio"]))
            k = motor.clave_objetivo({"grupo": grupo, "titulo": o[0]["titulo"]}, objs)
            obj = objs[k]["precio"] if k else None
            out.append({"seg_id": seg["id"], "vigilada": seg["nombre"], "activa": bool(seg["activo"]), "grupo": grupo,
                        "titulos": [x["titulo"] for x in o], "mejor": o[0], "ofertas": len(o),
                        "tiendas": len({x["tienda"] for x in o}), "minimo": min(minimos.get(grupo, o[0]["precio"]), o[0]["precio"]),
                        "mediana": statistics.median(vistos[grupo]) if len(vistos.get(grupo, [])) >= 5 else None,
                        "objetivo": obj if obj is not None else seg["objetivo"], "objetivo_propio": obj is not None, "objetivo_clave": k or grupo,
                        "con_envio": bool(opc.get("con_envio")), "revisada": seg["ultima"],
                        "por_tienda": _mejor_por_tienda(o)})
    return out


def tiendas_caidas(informe):
    """Tiendas que no respondieron (la búsqueda abierta no es una tienda)."""
    return sum(1 for h, i in informe.items() if i.get("caida") and h != "Búsqueda abierta")


def _avisa_limites(seg, res):
    """Telegram (o correo) solo si hay un cambio de límites: Amazon baja de su mínimo histórico o sube de su máximo (camelcamelcamel).
    Ya no se manda un resumen en cada revisión: si no ha cambiado nada, no se manda nada."""
    from . import referencia
    canales = [k for k in seg["canales"].split(",") if k in ("telegram", "correo")]
    if not canales:
        return {}
    cambios = referencia.limites_de(res)
    if not cambios:
        return {}
    envio = notifica.envia(canales, f"BuscaTron · {seg['nombre']} · cambio de límites", "\n\n".join(referencia.texto_limite(x) for x in cambios))
    if any(v is None for v in envio.values()):          # llegó por algún canal: no se repite
        referencia.marca_limites(cambios)
    return {"limites": [x["titulo"] for x in cambios], **envio}


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
    grupos = agrupa([x for x in res if _vale(seg, opc, modo, x)])
    caidas = tiendas_caidas(informe)
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


def tipo_vale(opciones, titulo):
    """¿Es de un tipo que la vigilada quiere? Sin tipos marcados (o con todos), vale cualquiera."""
    t = opciones.get("tipos") or []
    return not t or motor.tipo_de(titulo) in t


def cumple(seg, titulo, precio=None, tienda=None):
    """¿Este resultado guardado cumple los filtros ACTUALES de la vigilada (su búsqueda, «Solo títulos con», «Descarta», «al menos
    una de estas» y el rango de precio)? Los resultados de la última revisión se guardan tal cual salieron entonces: si luego se
    editan los filtros, hay que volver a pasarlos por ellos al leerlos, no esperar a la siguiente revisión.
    `seg`: la fila de la vigilada (con «opciones» como texto JSON o ya como dict)."""
    ex = motor.extract
    n = ex.normaliza(titulo)
    opciones = seg["opciones"] if isinstance(seg.get("opciones"), dict) else opciones_de(seg)
    palabras = ex.normaliza(f"{seg.get('consulta') or ''} {seg.get('incluir') or ''}").split()
    frases = [f for f in (ex.normaliza(x).strip() for x in (opciones.get("alguna") or "").split(",")) if f]
    if not all(ex.encaja(n, w) for w in palabras):
        return False
    if tienda and tienda in (opciones.get("sin_tiendas") or []):     # tienda que no quieres en esta vigilada
        return False
    if tienda and not motor.solo_juego(tienda, titulo, seg.get("consulta") or ""):
        return False
    if motor.es_no_juego(titulo) or not tipo_vale(opciones, titulo):
        return False
    if any(ex.encaja(n, w) for w in ex.normaliza(seg.get("excluir") or "").split()):
        return False
    if frases and not any(ex.encaja(n, f) for f in frases):
        return False
    if precio is not None and ((seg.get("pmin") is not None and precio < seg["pmin"]) or (seg.get("pmax") is not None and precio > seg["pmax"])):
        return False
    return True


def _fuera_de_objetivo(seg, aviso):
    """¿Aviso «por debajo de tu objetivo» que ya no lo está porque bajaste el objetivo (39 → 38: el de 38,65 € sobra)?"""
    m = aviso["motivo"] or ""
    de_objetivo = "por debajo de tu objetivo de" in m or m.startswith("≤ tu objetivo")       # el segundo, de versiones antiguas
    precio = aviso["precio"]
    final = re.match(r"cuesta ([\d.,]+) € con envío", m)
    if final:
        precio = float(final.group(1).replace(",", "."))
    return (de_objetivo and "para este producto" not in m and seg["objetivo"] is not None
            and precio > seg["objetivo"] + 0.005)


def limpia_avisos_por_filtros(seg_id):
    """Quita los avisos de esa vigilada que ya no cumplen sus filtros (se llama al editarla y guardar). Devuelve cuántos."""
    with bd.conecta() as c:
        fila = c.execute("SELECT * FROM seguimientos WHERE id=?", (seg_id,)).fetchone()
        if not fila:
            return 0
        seg = dict(fila)
        filas = c.execute("SELECT id, titulo, precio, tienda, motivo, oculto FROM avisos WHERE seg_id=?", (seg_id,)).fetchall()
        malos = [r["id"] for r in filas if not cumple(seg, r["titulo"], r["precio"], r["tienda"])]
        # por encima del objetivo nuevo: se ocultan (no se borran), así se recuerda que ya avisó y no se repite si vuelves a subirlo
        caros = [r["id"] for r in filas if r["id"] not in malos and not r["oculto"] and _fuera_de_objetivo(seg, r)]
        c.executemany("DELETE FROM avisos WHERE id=?", [(i,) for i in malos])
        c.executemany("UPDATE avisos SET oculto=1 WHERE id=?", [(i,) for i in caros])
    return len(malos) + len(caros)


def cubren(titulo, precio=None):
    """Nombres de las vigiladas activas que encontrarían este producto (aproximado: por las palabras de su búsqueda y sus
    filtros). Sirve para avisar de que un objetivo 🎯 no avisará si ninguna vigilada busca ese producto."""
    return [s["nombre"] for s in lista() if s["activo"] and cumple(s, titulo, precio)]


def pendientes(ahora=None):
    ahora = ahora or time.time()
    return [s["id"] for s in lista() if s["activo"] and ahora - s["ultima"] >= s["cada_horas"] * 3600]
