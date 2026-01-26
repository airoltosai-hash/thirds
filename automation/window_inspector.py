# automation/window_inspector.py
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32

# 함수 미리 선언
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
EnumWIndows = user32.EnumWindows

def list_all_windows():
    """
    모든 최상위 창을 나열하고 정보 출력
    HTS로그인 창을 위한 디버깅용
    """
    windows_info = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
    def enum_callback(hwnd, lp):
        try:
            # 창 타이틀 길이 가져오기
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            
            # 창 타이틀 가져오기
            buf_title = ctypes.create_unicode_buffer(256)
            GetWindowTextW(hwnd, buf_title, length + 1)
            title = buf_title.value

            # 창 클램스명 가져오기
            buf_class = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, buf_class, 256)
            class_name = buf_class.value

            windows_info.append({
                'hwnd': hwnd,
                'title': title,
                'class': class_name
            })
        except Exception as e:
            pass

        return True
    
    EnumWIndows(enum_callback, 0)

    return windows_info

def print_windows_info():
    """창 정보를 보기 좋게 출력"""
    print("\n" + "="*100)
    print("현재 열려있는 모든 창")
    print("="*810)

    windows = list_all_windows()

    if not windows:
        print("열려있는 창이 없습니다.")
        return

    for i, w in enumerate(windows, 1):
        print(f"\n[{i}] 핸들: 0x{w['hwnd']:X}")
        print(f"    타이틀: {w['title']}")
        print(f"    클래스: {w['class']}")

    print("\n" + "="*100)
    print("총 창 개수:", len(windows))
    print("="*100)

if __name__ == "__main__":
    print_windows_info()