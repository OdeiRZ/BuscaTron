"""Arranque con Windows: un acceso directo en la carpeta Inicio del usuario (no necesita administrador).
Lanza BuscaTron sin ventana (pythonw) y con icono en la bandeja."""
import os
import subprocess
import sys

from . import tiendas as cfg

NOMBRE = "BuscaTron.lnk"


def disponible():
    return sys.platform == "win32"


def ruta_acceso():
    return os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", NOMBRE)


def activo():
    return disponible() and os.path.exists(ruta_acceso())


def _pythonw():
    exe = sys.executable
    w = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return w if os.path.exists(w) else exe


def _q(texto):
    return str(texto).replace("'", "''")      # comillas simples para PowerShell


def activa():
    """Crea el acceso directo. Lanza RuntimeError si no se puede."""
    if not disponible():
        raise RuntimeError("el arranque automático solo existe en Windows")
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');$s.TargetPath='%s';$s.Arguments='-m buscatron --bandeja';"
          "$s.WorkingDirectory='%s';$s.IconLocation='%s';$s.WindowStyle=7;$s.Description='BuscaTron';$s.Save()"
          % (_q(ruta_acceso()), _q(_pythonw()), _q(cfg.RAIZ), _q(os.path.join(cfg.RAIZ, "buscatron", "icono.ico"))))
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not os.path.exists(ruta_acceso()):
        raise RuntimeError("no se pudo crear el acceso directo: " + (r.stderr.strip()[:150] or "error desconocido"))


def desactiva():
    if os.path.exists(ruta_acceso()):
        os.remove(ruta_acceso())
