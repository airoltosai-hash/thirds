import win32gui
import win32con
import win32api
import time

# 메시지 상수
TCM_GETCURSEL = 0x130B

print("2초 후 실행됩니다...")
time.sleep(2)

# iMeritz 메인 윈도우 찾기
main_hwnd = win32gui.FindWindow("iMeritz XII", "iMeritz")
if not main_hwnd:
    print("❌ iMeritz 창을 찾을 수 없습니다!")
    exit()

print(f"✅ 메인 윈도우: {hex(main_hwnd)}")

# 자식 윈도우에서 해외주식 주문창 찾기
def find_child_windows(parent):
    children = []
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        ctrl_id = win32gui.GetDlgCtrlID(hwnd) if hwnd else 0
        children.append((hwnd, title, cls, ctrl_id))
    win32gui.EnumChildWindows(parent, callback, None)
    return children

children = find_child_windows(main_hwnd)

# ITGEN_SCREEN_WINDOW 찾기
screen_hwnd = None
for hwnd, title, cls, ctrl_id in children:
    if cls == "ITGEN_SCREEN_WINDOW" and "6100" in title:
        screen_hwnd = hwnd
        print(f"✅ 주문창 발견: {hex(hwnd)} - {title}")
        break

if not screen_hwnd:
    print("❌ [6100] 해외주식 주문 창을 찾을 수 없습니다!")
    exit()

# ID=3810인 모든 탭 찾기
tab_children = find_child_windows(screen_hwnd)

all_tabs_3810 = []
for hwnd, title, cls, ctrl_id in tab_children:
    if ctrl_id == 3810 and "SysTabControl32" in cls:
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        all_tabs_3810.append((hwnd, rect, width, height))

# 가장 큰 탭 선택
all_tabs_3810.sort(key=lambda x: x[2] * x[3], reverse=True)
tab_hwnd, rect, width, height = all_tabs_3810[0]

print(f"✅ 탭: HWND={hex(tab_hwnd)}")
print(f"  위치: {rect}")
print(f"  크기: {width}x{height}")

# 현재 탭 확인
current_tab = win32gui.SendMessage(tab_hwnd, TCM_GETCURSEL, 0, 0)
tab_names = ["매수", "매도", "정정", "취소"]
print(f"\n현재 탭: {tab_names[current_tab]} (인덱스={current_tab})")

# 시작=18, 간격=36으로 탭 위치 계산
y = rect[1] + 10
tab_positions = []

print("\n각 탭 위치:")
for i in range(4):
    x_offset = 18 + (36 * i)
    x = rect[0] + x_offset
    tab_positions.append((x, y))
    print(f"  {tab_names[i]}: ({x}, {y}) - offset={x_offset}")

# 모든 탭을 순서대로 클릭 테스트
print("\n\n모든 탭을 순서대로 클릭합니다...")
current_pos = win32api.GetCursorPos()

for i in range(4):
    click_x, click_y = tab_positions[i]
    
    print(f"\n[{i+1}/4] {tab_names[i]} 탭 클릭: ({click_x}, {click_y})")
    
    win32api.SetCursorPos((click_x, click_y))
    time.sleep(0.3)
    
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    
    time.sleep(0.5)
    
    # 변경 확인
    new_tab = win32gui.SendMessage(tab_hwnd, TCM_GETCURSEL, 0, 0)
    print(f"  → 현재 탭: {tab_names[new_tab]} (인덱스={new_tab})")
    
    if new_tab == i:
        print(f"  ✅ {tab_names[i]} 탭 전환 성공!")
    else:
        print(f"  ❌ {tab_names[i]} 탭 전환 실패 (예상={i}, 실제={new_tab})")
    
    time.sleep(1)

win32api.SetCursorPos(current_pos)

print("\n\n테스트 완료! 모든 탭이 정확히 클릭되었나요?")