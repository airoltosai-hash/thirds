# automation/window_inspector.py
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# Windows API 함수
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
EnumWIndows = user32.EnumWindows
IsWindowVisible = user32.IsWindowVisible


def list_all_windows():
    """
    현재 열려 있는 모든 창 수집
    """
    windows_info = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
    def enum_callback(hwnd, lp):
        try:
            # 창 타이틀 길이 가져오기
            length = GetWindowTextLengthW(hwnd)
            if length == 0:
                title = "(타이틀 없음)"
            else:
            
                # 창 타이틀 가져오기
                buf_title = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf_title, length + 1)
                title = buf_title.value

            # 창 클램스명 가져오기
            buf_class = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, buf_class, 256)
            class_name = buf_class.value

            # 보이는 창인지 확인
            is_visible = bool(IsWindowVisible(hwnd))

            windows_info.append({
                'hwnd': hwnd,
                'hwnd_hex': f"0x{hwnd:X}",
                'title': title,
                'class': class_name,
                'visible': is_visible
            })
        except:
            pass

        return True
    
    EnumWIndows(enum_callback, 0)
    return windows_info

def print_windows_info():
    """창 정보를 보기 좋게 출력"""

    windows = list_all_windows()

    print("\n" + "="*100)
    print("👜 현재 열려있는 모든 창")
    print("="*100)

    if not windows:
        print("열려있는 창이 없습니다.")
        return
# #32770
    for i, w in enumerate(windows, 1):
        visible_str = "⭕" if w['visible'] else "❌"
        #if "계좌평가" in w['title']:
        print(f"\n[{i}] HWND: {w['hwnd_hex']}")
        print(f"    점수: {w['hwnd']}")
        print(f"    타이틀: {w['title']}")
        print(f"    클래스: {w['class']}")
        print(f"    보이는 창: {visible_str}")

    print("\n" + "="*100)
    print(f"총 창 개수: {len(windows)}개")
    print("="*100 + "\n")

if __name__ == "__main__":
    print_windows_info()