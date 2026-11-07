@echo off
cd /d "%~dp0"
title BuscaTron
rem Usa el entorno propio de BuscaTron (.venv, Python 3.13) si existe; si no, el python del sistema.
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" -m buscatron --abrir --bandeja
echo.
echo BuscaTron se ha detenido. Si ves un error arriba, copialo.
pause
