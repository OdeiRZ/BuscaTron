"""Análisis del precio de un artículo a partir de lo que BuscaTron ha visto de él: mínimo, máximo, dónde está hoy, las
bajadas que ha tenido y una estimación de cuándo puede repetirse una bajada o el mínimo.
Solo usa los datos propios (no consulta nada) y dice siempre cuánto se puede fiar: con pocos días de historial la
estimación no vale, y el módulo lo reconoce en vez de dar una fecha."""
import datetime
import statistics
import time

BAJADA = 0.04            # una bajada cuenta si es al menos un 4 % sobre el precio del día anterior
CERCA_MINIMO = 0.02      # «en su mínimo»: hasta un 2 % por encima
MIN_EVENTOS = 3          # bajadas (o visitas al mínimo) necesarias para estimar un intervalo
MAX_PUNTOS = 60


def euros(v):
    return f"{v:.2f}".replace(".", ",") + " €"


def dm(d):
    return d.strftime("%d/%m")


def por_dia(serie):
    """[(fecha, precio más bajo del día)] de [(ts, precio)]: varias consultas el mismo día cuentan como un dato."""
    dias = {}
    for ts, p in sorted(serie):
        d = datetime.date.fromtimestamp(ts)
        dias[d] = min(p, dias.get(d, p))
    return sorted(dias.items())


def _episodios(fechas, hueco=2):
    """Agrupa fechas seguidas (con huecos de hasta `hueco` días) en una sola: devuelve la primera de cada grupo."""
    out = []
    for d in sorted(fechas):
        if not out or (d - out[-1][1]).days > hueco:
            out.append([d, d])
        else:
            out[-1][1] = d
    return [i for i, _ in out]


def _intervalo(inicios, hoy):
    """Estima la próxima repetición a partir de los días entre `inicios` (fechas). None si no hay datos para ello."""
    if len(inicios) < MIN_EVENTOS:
        return None
    gaps = [(b - a).days for a, b in zip(inicios, inicios[1:])]
    m = statistics.median(gaps)
    ult = inicios[-1]
    return {"mediana": m, "min": min(gaps), "max": max(gaps), "eventos": len(inicios),
            "centro": ult + datetime.timedelta(days=round(m)), "desde": ult + datetime.timedelta(days=min(gaps)),
            "hasta": ult + datetime.timedelta(days=max(gaps)), "pasada": ult + datetime.timedelta(days=max(gaps)) < hoy}


def fiabilidad(eventos, span):
    if eventos < MIN_EVENTOS or span < 14:
        return "insuficiente"
    if eventos < 5 or span < 60:
        return "baja"
    if eventos < 8 or span < 120:
        return "media"
    return "alta"


def black_friday(anio):
    """El viernes después del cuarto jueves de noviembre."""
    d = datetime.date(anio, 11, 1)
    jueves = [d + datetime.timedelta(days=i) for i in range(30) if (d + datetime.timedelta(days=i)).weekday() == 3]
    return jueves[3] + datetime.timedelta(days=1)


def calendario(hoy, dias=60):
    """Fechas de ofertas generales próximas. Es una pista del calendario comercial, no sale de los datos del producto:
    las fechas aproximadas (Prime Day, rebajas) cambian cada año."""
    eventos = []
    for a in (hoy.year, hoy.year + 1):
        bf = black_friday(a)
        eventos += [("Black Friday", bf, False), ("Cyber Monday", bf + datetime.timedelta(days=3), False),
                    ("Rebajas de invierno", datetime.date(a, 1, 7), True), ("Prime Day (mediados de julio)", datetime.date(a, 7, 15), True),
                    ("Ofertas de otoño de Amazon (octubre)", datetime.date(a, 10, 10), True)]
    return [{"nombre": n, "fecha": f.isoformat(), "en_dias": (f - hoy).days, "aprox": ap}
            for n, f, ap in sorted(eventos, key=lambda e: e[1]) if 0 <= (f - hoy).days <= dias]


def analiza(serie, ahora=None):
    """serie: [(ts, precio)] de un artículo, nuevo y con stock. Devuelve el análisis, o None si no hay datos."""
    if not serie:
        return None
    ahora = ahora or time.time()
    hoy = datetime.date.fromtimestamp(ahora)
    dias = por_dia(serie)
    precios = [p for _, p in dias]
    actual = sorted(serie)[-1][1]
    mn, mx = min(precios), max(precios)
    f_mn = next(d for d, p in dias if p == mn)
    f_mx = next(d for d, p in dias if p == mx)
    primera, ultima = dias[0][0], dias[-1][0]
    span = (ultima - primera).days + 1
    cambia = mx > mn * 1.005
    a = {"n": len(serie), "n_dias": len(dias), "span_dias": span, "desde": primera.isoformat(), "hasta": ultima.isoformat(),
         "actual": actual, "minimo": mn, "fecha_minimo": f_mn.isoformat(), "maximo": mx, "fecha_maximo": f_mx.isoformat(),
         "media": round(statistics.mean(precios), 2), "mediana": round(statistics.median(precios), 2), "cambia": cambia,
         "posicion": round(100 * (actual - mn) / (mx - mn)) if cambia else None,
         "vs_mediana": round(100 * (actual / statistics.median(precios) - 1), 1),
         "en_minimo": cambia and actual <= mn * (1 + CERCA_MINIMO),
         "dias_desde_minimo": (hoy - f_mn).days}
    bajadas = [(d, a0, b0) for (d0, a0), (d, b0) in zip(dias, dias[1:]) if b0 <= a0 * (1 - BAJADA)]
    a["bajadas"] = [{"fecha": d.isoformat(), "de": x, "a": y, "pct": round(100 * (1 - y / x))} for d, x, y in bajadas]
    inicios_bajada = _episodios([d for d, _, _ in bajadas], hueco=1)
    visitas_minimo = _episodios([d for d, p in dias if cambia and p <= mn * (1 + CERCA_MINIMO)], hueco=2)
    a["proxima_bajada"] = _intervalo(inicios_bajada, hoy)
    a["proximo_minimo"] = _intervalo(visitas_minimo, hoy)
    a["visitas_minimo"] = len(visitas_minimo)
    eventos = max(len(inicios_bajada), len(visitas_minimo))
    a["fiabilidad"] = fiabilidad(eventos, span)
    a["calendario"] = calendario(hoy)
    paso = max(1, len(dias) // MAX_PUNTOS)
    ts_dia = {}
    for ts, _ in sorted(serie):
        ts_dia.setdefault(datetime.date.fromtimestamp(ts), ts)
    a["puntos"] = [{"ts": int(ts_dia[d]), "precio": p} for d, p in dias[::paso]]
    a["frases"] = frases(a, hoy)
    for k in ("proxima_bajada", "proximo_minimo"):
        if a[k]:
            a[k] = {x: (v.isoformat() if isinstance(v, datetime.date) else v) for x, v in a[k].items()}
    return a


def _f(s):
    return datetime.date.fromisoformat(s) if isinstance(s, str) else s


def frases(a, hoy):
    """El análisis en frases, listo para enseñarlo."""
    out = []
    if not a["cambia"]:
        out.append(f"Su precio no ha cambiado en los {a['span_dias']} días que BuscaTron lo ve ({euros(a['actual'])}).")
    else:
        if a["en_minimo"]:
            out.append(f"Ahora está en su mínimo visto ({euros(a['minimo'])}).")
        else:
            v = a["vs_mediana"]
            med = ("igual que la mediana" if abs(v) < 0.05 else f"un {abs(v):g} % {'por encima' if v > 0 else 'por debajo'} de la mediana").replace(".", ",")
            out.append(f"Ahora {euros(a['actual'])}: al {a['posicion']} % del recorrido entre su mínimo y su máximo, {med} ({euros(a['mediana'])}).")
        out.append(f"Mínimo {euros(a['minimo'])} ({dm(_f(a['fecha_minimo']))}) · máximo {euros(a['maximo'])} ({dm(_f(a['fecha_maximo']))}) · media {euros(a['media'])}.")
        if a["bajadas"]:
            u = a["bajadas"][-1]
            out.append(f"Ha tenido {len(a['bajadas'])} bajada{'s' if len(a['bajadas']) != 1 else ''} de al menos un {round(BAJADA * 100)} %; "
                       f"la última el {dm(_f(u['fecha']))} ({euros(u['de'])} → {euros(u['a'])}, −{u['pct']} %).")
        else:
            out.append(f"No ha tenido bajadas de al menos un {round(BAJADA * 100)} % desde que lo ve BuscaTron.")
    pb, pm = a["proxima_bajada"], a["proximo_minimo"]
    if a["cambia"] and (pb or pm):
        for nombre, p, detalle in (("una bajada", pb, "entre bajadas"), ("la vuelta al mínimo", pm, "entre visitas al mínimo")):
            if not p:
                continue
            if p["pasada"]:
                out.append(f"Estimación de {nombre}: lo habitual era cada {p['mediana']:g} días ({detalle}) y ya ha pasado más tiempo; "
                           "puede darse en cualquier momento.")
            else:
                out.append(f"Estimación de {nombre}: hacia el {dm(_f(p['centro']))} (entre el {dm(_f(p['desde']))} y el {dm(_f(p['hasta']))}); "
                           f"suelen pasar unos {p['mediana']:g} días {detalle} ({p['eventos']} vistos).")
    else:
        out.append("No hay bajadas suficientes para estimar cuándo volverá a bajar (hacen falta al menos "
                   f"{MIN_EVENTOS}); BuscaTron seguirá anotándolas cada vez que lo vea.")
    out.append(f"Fiabilidad de la estimación: {a['fiabilidad']}. Se basa en {a['n_dias']} día{'s' if a['n_dias'] != 1 else ''} de datos "
               f"(desde el {dm(_f(a['desde']))})" + ("; es poco tiempo, mejorará con las semanas." if a["span_dias"] < 30 else "."))
    if a["calendario"]:
        c = a["calendario"][0]
        cuando = "hoy" if c["en_dias"] == 0 else f"dentro de {c['en_dias']} días"
        out.append(f"Pista del calendario (general, no sale de este producto): {c['nombre']} "
                   f"{'hacia el' if c['aprox'] else 'el'} {dm(_f(c['fecha']))}, {cuando}.")
    return out
