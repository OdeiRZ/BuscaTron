@echo off
cd /d "%~dp0"
title BuscaTron
python -m buscatron --abrir --bandeja
echo.
echo BuscaTron se ha detenido. Si ves un error arriba, copialo.
pause
