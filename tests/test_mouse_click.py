import ctypes
import time
import sys

user32 = ctypes.windll.user32

def get_mouse_position():
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def monitor_mouse_clicks():
    print("\n" + "="*50)
    print(" 🖱️ 마우스 클릭 모니터링 시작")
    print(" (중단하려면 Ctrl+C를 누르세요)")
    print("="*50, flush=True) # 즉시 출력

    prev_left = False
    prev_right = False
    
    try:
        while True:
            left_down = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
            right_down = bool(user32.GetAsyncKeyState(0x02) & 0x8000)
            
            x, y = get_mouse_position()

            if left_down and not prev_left:
                # flush=True를 넣어줘야 클릭하자마자 화면에 찍힙니다.
                print(f"  📍 [LEFT CLICK]  X: {x:4d}, Y: {y:4d}", flush=True)
            
            if right_down and not prev_right:
                print(f"  📍 [RIGHT CLICK] X: {x:4d}, Y: {y:4d}", flush=True)

            prev_left = left_down
            prev_right = right_down
            
            time.sleep(0.01) # 반응 속도를 위해 대기 시간을 좀 더 줄였습니다.
            
    except KeyboardInterrupt:
        print("\n[중단] 모니터링을 종료합니다.", flush=True)

if __name__ == "__main__":
    monitor_mouse_clicks()