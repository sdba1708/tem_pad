import win32gui
from ctypes import wintypes
import ctypes
import yaml



def get_app_rect(width = 1600, height = 930, ofst_x = 0, ofst_y = 0): # WxH of app window
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
    
    # アプリウィンドウの幅に合わせて調整
    tmp_width = rect.right - rect.left
    tmp_height = rect.bottom - rect.top
    out_left = rect.left
    out_right = rect.right
    out_top = rect.top
    out_bottom = rect.bottom
    if tmp_width > width:
        tmp_diff = (tmp_width - width) // 2
        out_left += tmp_diff
        out_right -= tmp_diff
    if tmp_height > height:
        # 下方向へのずれはなぜかbottom側のみ
        tmp_diff = tmp_height - height
        out_bottom -= tmp_diff
    
    return tem_window, [out_left + ofst_x, out_right + ofst_x, out_top + ofst_y, out_bottom + ofst_y]

def get_config_data(yaml_path):
    config_data = None
    with open(yaml_path, 'r') as yml:
        config_data = yaml.safe_load(yml)
        
    if config_data is None:
        config_data = {'general': {'width': 1600, 'height': 930, 'link': 'temtetsu'}, 'det_win': {'ofst_x': 0, 'ofst_y': 0, 'dump': False}, 'win_pos': {'ofst_x': 0, 'ofst_y': 0}}
        
    return config_data

def save_config_data(yaml_path, config_data):
    with open(yaml_path, 'w') as yml:
        yaml.dump(config_data, yml, default_flow_style=False)
        
def is_num(s):
    try:
        float(s)
    except ValueError:
        return 0
    else:
        return int(s)
    
    