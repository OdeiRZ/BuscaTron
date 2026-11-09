@echo off
cd /d "%~dp0"
title BuscaTron
rem Usa el entorno propio de BuscaTron (.venv, Python 3.13) si existe; si no, el python del sistema.
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
rem Reiniciar desde la web o la bandeja sale con el codigo 3: se vuelve a lanzar sin abrir otra pestaña (como PixelatIA.bat)
set "BUSCATRON_LANZADOR=bat"
set ARGS=--abrir --bandeja
:inicio
"%PY%" -m buscatron %ARGS%
if %errorlevel%==3 (
  set ARGS=--bandeja
  goto inicio
)
echo.
echo BuscaTron se ha detenido. Si ves un error arriba, copialo.
pause
