"""Base de datos SQLite local."""
import os
import sqlite3

from . import tiendas as cfg

RUTA = os.path.join(cfg.RAIZ, "buscatron.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS precios(
    ts REAL, consulta TEXT, tienda TEXT, titulo TEXT, url TEXT, precio REAL, agotado INTEGER, seg_id INTEGER, preventa INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS ix_precios_url ON precios(url, ts);
CREATE TABLE IF NOT EXISTS seguimientos(
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, consulta TEXT, incluir TEXT DEFAULT '', excluir TEXT DEFAULT '',
    pmin REAL, pmax REAL, objetivo REAL, bajo_historico REAL DEFAULT 0, sin_agotados INTEGER DEFAULT 1,
    canales TEXT DEFAULT 'app', castellano INTEGER DEFAULT 1, opciones TEXT DEFAULT '{}', cada_horas REAL DEFAULT 12, activo INTEGER DEFAULT 1, ultima REAL DEFAULT 0, estado TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS busquedas(
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, consulta TEXT, firma TEXT, params TEXT, resultados TEXT, total INTEGER, informe TEXT, webs TEXT);
CREATE INDEX IF NOT EXISTS ix_busquedas ON busquedas(ts);
CREATE TABLE IF NOT EXISTS idiomas(url TEXT PRIMARY KEY, valor TEXT, codigo TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS fichas(url TEXT PRIMARY KEY, idioma TEXT, agotado INTEGER, preventa INTEGER, ts REAL);
CREATE TABLE IF NOT EXISTS ignorados(clave TEXT PRIMARY KEY, titulo TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS estado_tiendas(host TEXT, ts REAL, consulta TEXT, encontrados INTEGER, error TEXT);
CREATE INDEX IF NOT EXISTS ix_estado_tiendas ON estado_tiendas(host, ts);
CREATE TABLE IF NOT EXISTS objetivos(clave TEXT PRIMARY KEY, titulo TEXT, precio REAL, ts REAL);
CREATE TABLE IF NOT EXISTS recordatorios(host TEXT, ts_importado REAL, PRIMARY KEY(host, ts_importado));
CREATE TABLE IF NOT EXISTS importados(
    host TEXT, ts REAL, consulta TEXT, titulo TEXT, url TEXT, precio REAL, agotado INTEGER DEFAULT 0, preventa INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS ix_importados ON importados(host, ts);
CREATE TABLE IF NOT EXISTS avisos(
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, seg_id INTEGER, titulo TEXT, tienda TEXT, url TEXT, precio REAL, motivo TEXT, oculto INTEGER DEFAULT 0);
"""


def limpia(dias=180, ahora=None):
    """Compacta el historial: de los precios de hace más de `dias` deja uno por producto y día (el más bajo), y poda
    las tablas auxiliares. Devuelve cuántas filas se borraron de cada tabla."""
    import time
    ahora = ahora or time.time()
    corte = ahora - dias * 86400
    borradas = {}
    with conecta() as c:
        borradas["precios"] = c.execute("""DELETE FROM precios WHERE ts < ? AND rowid NOT IN (
            SELECT rid FROM (SELECT rowid rid, ROW_NUMBER() OVER (PARTITION BY url, CAST(ts / 86400 AS INTEGER) ORDER BY precio, rowid) n
                             FROM precios WHERE ts < ?) WHERE n = 1)""", (corte, corte)).rowcount
        borradas["fichas"] = c.execute("DELETE FROM fichas WHERE ts < ?", (ahora - 60 * 86400,)).rowcount
        borradas["idiomas"] = c.execute("DELETE FROM idiomas WHERE ts < ?", (ahora - 60 * 86400,)).rowcount
        borradas["importados"] = c.execute("DELETE FROM importados WHERE ts < ?", (ahora - 7 * 86400,)).rowcount
        borradas["recordatorios"] = c.execute("DELETE FROM recordatorios WHERE ts_importado < ?", (ahora - 7 * 86400,)).rowcount
        borradas["estado_tiendas"] = c.execute("""DELETE FROM estado_tiendas WHERE rowid NOT IN (
            SELECT rid FROM (SELECT rowid rid, ROW_NUMBER() OVER (PARTITION BY host ORDER BY ts DESC) n FROM estado_tiendas) WHERE n <= 30)""").rowcount
    return borradas


_preparadas = set()        # bases a las que ya se aplicó el esquema en esta ejecución


def conecta(ruta=None):
    ruta = ruta or RUTA
    c = sqlite3.connect(ruta, timeout=30)
    c.row_factory = sqlite3.Row
    if ruta not in _preparadas:
        _prepara(c)
        _preparadas.add(ruta)
    return c


def _prepara(c):
    """Crea las tablas que falten y añade las columnas nuevas a las bases de versiones anteriores."""
    c.executescript(ESQUEMA)
    try:
        c.execute("ALTER TABLE precios ADD COLUMN seg_id INTEGER")  # bases creadas por el prototipo
    except sqlite3.OperationalError:
        pass
    for tabla, columna in (("seguimientos", "castellano INTEGER DEFAULT 1"), ("seguimientos", "opciones TEXT DEFAULT '{}'"),
                           ("precios", "preventa INTEGER DEFAULT 0"), ("avisos", "oculto INTEGER DEFAULT 0"),
                           ("precios", "clave TEXT")):   # bases creadas por versiones anteriores
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna}")
        except sqlite3.OperationalError:
            pass
    c.execute("CREATE INDEX IF NOT EXISTS ix_precios_clave ON precios(clave, ts)")
    c.commit()
