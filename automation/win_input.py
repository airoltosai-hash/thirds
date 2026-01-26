# automation/win_input.py
import ctypes
import time
from ctypes import wintypes


# WinAPI 상수/구조체
user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ULONG_PTR 호환 정의
try:
    ULONG_PTR = wintypes.ULONG_PTR
except AttributeError:
    import ctypes as _ct
    ULONG_PTR = _ct.c_ulong if _ct.sizeof(_ct.c_void_p) == 4 else _ct.c_ulonglong

# 상수
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_SHIFT    = 0x10
VK_CONTROL  = 0x11
VK_MENU     = 0x12
VK_RETURN   = 0X0D

# 구조체
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk"      , wintypes.WORD),
        ("wScan"    , wintypes.WORD),
        ("dwFlags"  , wintypes.DWORD),
        ("time"     , wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]
class INPUT_I(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]  # 마우스/하드웨어와 공유 유니온

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),  # 1 = KEYBOARD
                ("ii"  , INPUT_I),
    ]


def _send_input(inp: INPUT):
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def press_vk(vk: int):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.ii.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=0)
    _send_input(inp)
    
def release_vk(vk: int):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.ii.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
    _send_input(inp)

def send_vk(vk: int, hold_shift=False, hold_ctrl=False, hold_alt=False):
    # 보조키 누르기
    if hold_shift : press_vk(VK_SHIFT)
    if hold_ctrl  : press_vk(VK_CONTROL) 
    if hold_alt   : press_vk(VK_MENU) 
    # 본키
    press_vk(vk); release_vk(vk)
    # 보조키 뗴기
    if hold_alt   : release_vk(VK_MENU)
    if hold_ctrl  : release_vk(VK_CONTROL)
    if hold_shift : release_vk(VK_SHIFT)

def send_enter():
    send_vk(VK_RETURN)   

def send_ctrl_h():
    press_vk(VK_CONTROL)
    press_vk(ord('H')); release_vk(ord('H'))
    release_vk(VK_CONTROL)

def send_unicode_char(ch: str):
    code = ord(ch)
    # key down (UNICODE)
    inp_down = INPUT()
    inp_down.type = INPUT_KEYBOARD
    inp_down.ii.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0)
    _send_input(inp_down)
    # key up (UNICODE)
    inp_up = INPUT()
    inp_up.type = INPUT_KEYBOARD
    inp_up.ii.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
    _send_input(inp_up)

def send_unicode_text(text: str, delay_sec: float = 0.01):
    for ch in text:
        send_unicode_char(ch)
        time.sleep(delay_sec)



