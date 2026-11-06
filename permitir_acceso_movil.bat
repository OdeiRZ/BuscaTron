@echo off
rem Abre el puerto 8790 del cortafuegos de Windows SOLO para tu red local (Wi-Fi/LAN),
rem para poder usar BuscaTron desde el movil. Pide permisos de administrador.
setlocal
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Solicitando permisos de administrador...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
netsh advfirewall firewall delete rule name="BuscaTron (red local)" >nul 2>&1
netsh advfirewall firewall add rule name="BuscaTron (red local)" dir=in action=allow protocol=TCP localport=8790 remoteip=localsubnet profile=any
if %errorlevel% equ 0 (
  echo.
  echo Listo: regla "BuscaTron (red local)" creada para el puerto 8790, solo desde tu red local.
  echo En el movil, conectado a la misma Wi-Fi, abre la direccion que muestra BuscaTron al arrancar.
) else (
  echo.
  echo No se pudo crear la regla. Copia el error de arriba.
)
echo.
pause
