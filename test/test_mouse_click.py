# automation/test/test_mouse_click.py

import ctypes
import time

user32 = ctypes.windll.user32

def get_mouse_position():
    """
    현재 마우스 좌표 반환
    """
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def monitor_mouse_clicks():
    """
    마우스 클릭을 모니터링하고 좌표 출력
    """
    print("\n" + "="*80)
    print(" * 마우스 클릭 좌표 추적 시작")
    print("="*80)
    print("[INFO] 마우스를 클릭하세요. (종료: Ctrl+C)\n")
    click_count = 0

    prev_left_down = False
    prev_right_down = False
    prev_middle_down = False

    try:
        while True:
            left_button = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
            right_button = bool(user32.GetAsyncKeyState(0x02) & 0x8000)
            middle_button = bool(user32.GetAsyncKeyState(0x04) & 0x8000)
            x, y = get_mouse_position()

            if left_button and not prev_left_down:
                click_count += 1
                print(f"[{click_count}] 왼쪽 클릭 -> X: {x:4d} Y: {y:4d}")
                prev_left_down = True
            elif not left_button:
                prev_left_down = False

            if right_button and not prev_right_down:
                click_count += 1
                print(f"[{click_count}] 오른쪽 클릭 -> X: {x:4d} Y: {y:4d}")
                prev_right_down = True
            elif not right_button:
                prev_right_down = False

            if middle_button and not prev_middle_down:
                click_count += 1
                print(f"[{click_count}] 중간 클릭 -> X: {x:4d} Y: {y:4d}")
                prev_middle_down = True
            elif not middle_button:
                prev_middle_down = False

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print(f" * 모니터링 종료! (총 {click_count}회 클릭)")
        print()

if __name__ == "__main__":
    monitor_mouse_clicks()
