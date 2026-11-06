"""Icono de BuscaTron en la bandeja de Windows (junto al reloj), sin paquetes externos: solo funciones de Windows con ctypes.
Doble clic abre la web; el menú (clic) permite abrirla, ver u ocultar la ventana de mensajes y cerrar BuscaTron.
Si BuscaTron se inicia sin ventana (pythonw, arranque con Windows) no hay consola que ocultar."""
import atexit
import ctypes
import os
import sys
import threading
import webbrowser
from ctypes import wintypes

WM_APP_TRAY = 0x8001
WM_LBUTTONUP, WM_LBUTTONDBLCLK, WM_RBUTTONUP, WM_DESTROY, WM_NULL = 0x0202, 0x0203, 0x0205, 0x0002, 0x0000
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 1, 2, 4
SW_HIDE, SW_RESTORE = 0, 9
MENU_OPEN, MENU_CONSOLE, MENU_CLOSE = 1, 2, 3
ICONO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")

_state = {"hwnd": None, "nid": None, "ok": False, "puerto": 8790}

if sys.platform == "win32":
    user32, shell32, kernel32 = ctypes.windll.user32, ctypes.windll.shell32, ctypes.windll.kernel32
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.LPVOID]
    user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    user32.CreatePopupMenu.restype = wintypes.HMENU
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                    ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                    ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT), ("uFlags", wintypes.UINT),
                    ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON), ("szTip", wintypes.WCHAR * 128), ("dwState", wintypes.DWORD),
                    ("dwStateMask", wintypes.DWORD), ("szInfo", wintypes.WCHAR * 256), ("uVersion", wintypes.UINT),
                    ("szInfoTitle", wintypes.WCHAR * 64), ("dwInfoFlags", wintypes.DWORD), ("guidItem", ctypes.c_byte * 16),
                    ("hBalloonIcon", wintypes.HICON)]


def _consola():
    return kernel32.GetConsoleWindow() if sys.platform == "win32" else None


def muestra_consola(mostrar=True):
    h = _consola()
    if h:
        user32.ShowWindow(h, SW_RESTORE if mostrar else SW_HIDE)
        if mostrar:
            user32.SetForegroundWindow(h)


def _abrir():
    webbrowser.open("http://127.0.0.1:%d" % _state["puerto"])


def _menu(hwnd):
    h = user32.CreatePopupMenu()
    visible = bool(_consola() and user32.IsWindowVisible(_consola()))
    user32.AppendMenuW(h, 0, MENU_OPEN, "Abrir BuscaTron en el navegador")
    if _consola():
        user32.AppendMenuW(h, 0, MENU_CONSOLE, "Ocultar la ventana de mensajes" if visible else "Mostrar la ventana de mensajes")
    user32.AppendMenuW(h, 0, MENU_CLOSE, "Cerrar BuscaTron")
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    user32.SetForegroundWindow(hwnd)   # sin esto el menú no se cierra al hacer clic fuera
    eleccion = user32.TrackPopupMenu(h, 0x0100 | 0x0080 | 0x0002, pt.x, pt.y, 0, hwnd, None)   # TPM_RETURNCMD | TPM_NONOTIFY | TPM_RIGHTBUTTON
    user32.PostMessageW(hwnd, WM_NULL, 0, 0)
    user32.DestroyMenu(h)
    if eleccion == MENU_OPEN:
        _abrir()
    elif eleccion == MENU_CONSOLE:
        muestra_consola(not visible)
    elif eleccion == MENU_CLOSE:
        _quita()
        os._exit(0)


def _quita():
    if _state["ok"] and _state["nid"] is not None:
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(_state["nid"]))
        _state["ok"] = False


def _bucle(listo):
    @WNDPROC
    def proc(hwnd, msg, wparam, lparam):
        if msg == WM_APP_TRAY:
            ev = lparam & 0xFFFF
            if ev == WM_LBUTTONDBLCLK:
                _abrir()
            elif ev in (WM_RBUTTONUP, WM_LBUTTONUP):
                try:
                    _menu(hwnd)
                except Exception as e:   # noqa: BLE001  (un fallo del menú no debe tumbar la app)
                    print("Bandeja:", e)
            return 0
        if msg == WM_DESTROY:
            _quita()
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
    _state["proc"] = proc   # que no lo recoja el recolector de basura
    hinst = kernel32.GetModuleHandleW(None)
    wc = WNDCLASSW(lpfnWndProc=proc, hInstance=hinst, lpszClassName="BuscaTronBandeja")
    user32.RegisterClassW(ctypes.byref(wc))
    hwnd = user32.CreateWindowExW(0, "BuscaTronBandeja", "BuscaTron", 0, 0, 0, 0, 0, None, None, hinst, None)
    hicon = user32.LoadImageW(None, ICONO, 1, 0, 0, 0x0010 | 0x0040)   # IMAGE_ICON, LR_LOADFROMFILE | LR_DEFAULTSIZE
    nid = NOTIFYICONDATAW()
    nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    nid.hWnd, nid.uID, nid.uFlags, nid.uCallbackMessage, nid.hIcon = hwnd, 1, NIF_MESSAGE | NIF_ICON | NIF_TIP, WM_APP_TRAY, hicon
    nid.szTip = "BuscaTron · doble clic para abrir, clic para el menú"
    _state.update(hwnd=hwnd, nid=nid, ok=bool(hwnd and hicon and shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))))
    listo.set()
    if not _state["ok"]:
        return
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def inicia(puerto=8790, ocultar_consola=True):
    """Pone el icono en la bandeja y, si hay ventana de consola, la oculta. Devuelve False si no se pudo
    (entonces la consola sigue a la vista y BuscaTron funciona igual)."""
    if sys.platform != "win32":
        return False
    _state["puerto"] = puerto
    listo = threading.Event()
    threading.Thread(target=_bucle, args=(listo,), daemon=True, name="bandeja").start()
    listo.wait(5)
    if not _state["ok"]:
        return False
    atexit.register(_quita)
    if ocultar_consola:
        muestra_consola(False)
    return True
