import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.kernel32

def print_all_system_children():
    """시스템의 모든 HWND를 강제로 전수조사합니다."""
    print("\n" + "="*100)
    print(f"{'HWND':12s} | {'Class':25s} | {'Text Content'}")
    print("="*100)

    found_count = 0
    # 윈도우 핸들 값은 보통 0x10000 단위 내외에서 생성되지만, 
    # 안전하게 존재하는 모든 윈도우를 확인하는 IsWindow API를 사용합니다.
    
    # 1. 최상위 바탕화면부터 모든 윈도우를 다 가져오는 가장 확실한 방법
    hwnd = user32.GetTopWindow(None)
    
    while hwnd:
        # 이 핸들로부터 시작해서 모든 형제, 자식을 다 훑음
        scan_hierarchy(hwnd)
        hwnd = user32.GetWindow(hwnd, 2) # GW_HWNDNEXT (다음 형제 창)

def scan_hierarchy(hwnd):
    """재귀적으로 모든 창을 훑음"""
    if not user32.IsWindow(hwnd):
        return

    # 정보 추출
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    
    cls_buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls_buf, 256)
    
    title = buf.value.strip()
    if title: # 텍스트가 있는 것만 출력
        print(f"{hex(hwnd):12s} | {cls_buf.value:25s} | {title}")

    # 자식으로 파고들기
    child = user32.GetWindow(hwnd, 5) # GW_CHILD
    while child:
        scan_hierarchy(child)
        child = user32.GetWindow(child, 2) # GW_HWNDNEXT