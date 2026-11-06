"""Base de datos SQLite local."""
import os
import sqlite3

from . import tiendas as cfg

RUTA = os.path.join(cfg.RAIZ, "buscatron.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS precios(
    ts REAL, consulta TEXT, tienda TEXT, titulo TEXT, url TEXT, precio REAL, agotado INTEGER, seg_id INTEGER);
CREATE INDEX IF NOT EXISTS ix_precios_url ON precios(url, ts);
CREATE TABLE IF NOT EXISTS seguimientos(
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, consulta TEXT, incluir TEXT DEFAULT '', excluir TEXT DEFAULT '',
    pmin REAL, pmax REAL, objetivo REAL, bajo_historico REAL DEFAULT 0, sin_agotados INTEGER DEFAULT 1,
    canales TEXT DEFAULT 'app', cada_horas REAL DEFAULT 12, activo INTEGER DEFAULT 1, ultima REAL DEFAULT 0, estado TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS avisos(
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, seg_id INTEGER, titulo TEXT, tienda TEXT, url TEXT, precio REAL, motivo TEXT);
"""


def conecta(ruta=None):
    c = sqlite3.connect(ruta or RUTA, timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript(ESQUEMA)
    try:
        c.execute("ALTER TABLE precios ADD COLUMN seg_id INTEGER")  # bases creadas por el prototipo
    except sqlite3.OperationalError:
        pass
    return c
