import win32gui
from ctypes import wintypes
import ctypes
import time
def get_app_rect():
    tem_window = win32gui.FindWindow(None, 'Temtem')
    if tem_window == 0:
        return None, None
        
    f = ctypes.windll.dwmapi.DwmGetWindowAttribute
    rect = ctypes.wintypes.RECT()
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    f(  ctypes.wintypes.HWND(tem_window),
        ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect)
    )
    return tem_window, rect
    