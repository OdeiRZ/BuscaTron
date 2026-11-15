"""Leer el texto de una imagen que pegas tú (la gráfica de camelcamelcamel que ves en tu navegador), con el lector de texto
que trae Windows (es-ES). La imagen se guarda un instante en una carpeta temporal y se borra al terminar: BuscaTron no pide
nada a camelcamelcamel (que no deja leer sus datos a un programa), solo lee lo que le das."""
import base64
import os
import re
import subprocess
import tempfile

ESCALA = 3                      # el texto de una gráfica es pequeño: se amplía antes de leerlo (menos si la imagen ya es grande)
MAX_BYTES = 8 * 1024 * 1024
GUION = r"""
param($ruta, $escala)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType=WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Espera($op, $tipo) { $t = $asTask.MakeGenericMethod($tipo).Invoke($null, @($op)); [void]$t.Wait(-1); $t.Result }
$f = Espera ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ruta)) ([Windows.Storage.StorageFile])
$s = Espera ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$d = Espera ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
$tr = New-Object Windows.Graphics.Imaging.BitmapTransform
$tr.ScaledWidth = [uint32]($d.PixelWidth * $escala); $tr.ScaledHeight = [uint32]($d.PixelHeight * $escala)
$tr.InterpolationMode = [Windows.Graphics.Imaging.BitmapInterpolationMode]::Fant
$b = Espera ($d.GetSoftwareBitmapAsync([Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8, [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied, $tr, [Windows.Graphics.Imaging.ExifOrientationMode]::IgnoreExifOrientation, [Windows.Graphics.Imaging.ColorManagementMode]::DoNotColorManage)) ([Windows.Graphics.Imaging.SoftwareBitmap])
$motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('es-ES'))
if (-not $motor) { $motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
$r = Espera ($motor.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
($r.Lines | ForEach-Object { $_.Text }) -join "`n"
"""


def disponible():
    return os.name == "nt"


def escala_para(px):
    """Cuánto se amplía una imagen de `px` de ancho antes de leerla: las pequeñas, mucho; las grandes, casi nada."""
    return ESCALA if px < 1400 else 2 if px < 2400 else 1


def lee(datos):
    """Texto que se lee en una imagen (bytes PNG/JPG). Lanza ValueError si no se puede."""
    if not disponible():
        raise ValueError("el lector de texto de Windows solo existe en Windows")
    if not datos or len(datos) > MAX_BYTES:
        raise ValueError("la imagen está vacía o es demasiado grande")
    with tempfile.TemporaryDirectory(prefix="buscatron_ocr_") as carpeta:
        ruta, script = os.path.join(carpeta, "grafica.png"), os.path.join(carpeta, "ocr.ps1")
        with open(ruta, "wb") as f:
            f.write(datos)
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(GUION)
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script, ruta, str(escala_para(ancho(datos)))],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, creationflags=0x08000000)
        except (OSError, subprocess.SubprocessError) as e:
            raise ValueError(f"no se pudo ejecutar el lector de texto ({str(e)[:60]})")
    if r.returncode != 0:
        raise ValueError("el lector de texto de Windows no pudo leer la imagen: " + (r.stderr or "").strip()[:120])
    return r.stdout.strip()


def ancho(datos):
    """Ancho en píxeles de una imagen PNG (0 si no es PNG): las miniaturas no tienen letra legible."""
    if datos[:8] == b"\x89PNG\r\n\x1a\n" and len(datos) >= 24:
        return int.from_bytes(datos[16:20], "big")
    return 0


def decodifica(url_datos):
    """Los bytes de una imagen enviada por la página como «data:image/png;base64,…»."""
    m = re.match(r"data:image/(?:png|jpeg|jpg|webp|gif);base64,(.+)$", url_datos or "", re.S)
    if not m:
        raise ValueError("eso no es una imagen")
    try:
        return base64.b64decode(m.group(1), validate=False)
    except ValueError:
        raise ValueError("la imagen no se pudo leer")
