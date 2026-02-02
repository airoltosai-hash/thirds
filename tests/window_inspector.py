# /tests/windows_inspector.py

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
EnumWindows = user32.EnumWindows
IsWindowVisible = user32.IsWindowVisible

def list_all_windows():
    """
    모든 최상위 창 목록 수집
    """
    windows_info = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
    def enum_callback(hwnd, lp):
        try:
            length = GetWindowTextLengthW(hwnd)
            if length == 0:
                title = "(타이틀 없음)"
            else:
                buf_title = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf_title, length + 1)
                title = buf_title.value
            
            buf_class = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, buf_class, 256)
            class_name = buf_class.value
            
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
    
    EnumWindows(enum_callback, 0)
    return windows_info

def print_windows_info():
    """
    현재 열려있는 모든 창 정보를 보기 좋게 출력
    """
    windows = list_all_windows()

    print("\n" + "="*100)
    print(" 현재 열려있는 창 목록")
    print("="*100)

    if not windows:
        print("열려있는 창이 없습니다.")
        return
    
    for i, w in enumerate(windows, 1):
        visible_str = "v" if w['visible'] else "x"
        print(f"\n[{i}] HWND: {w['hwnd_hex']}")
        print(f"  타이틀: {w['title']}")
        print(f"  클래스: {w['class']}")
        print(f"  보임: {visible_str}")

    print("\n" + "="*100)
    print(f"총 창 개수: {len(windows)}개")
    print("="*100 + "\n")

def list_all_windows_recursive():
    """
    데스크탑부터 시작해서 모든 창(자식 포함)을 재귀적으로 수집
    """
    all_windows = []

    def scan_hierarchy(hwnd):
        """재귀적으로 모든 창을 훑음"""
        if not user32.IsWindow(hwnd):
            return
        
        # 정보 추출
        length = GetWindowTextLengthW(hwnd)
        if length == 0:
            title = "(타이틀 없음)"
        else:
            buf = ctypes.create_unicode_buffer(length + 1)
            GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

        cls_buf = ctypes.create_unicode_buffer(256)
        GetClassNameW(hwnd, cls_buf, 256)
        class_name = cls_buf.value

        is_visible = bool(IsWindowVisible(hwnd))

        all_windows.append({
            'hwnd': hwnd,
            'hwnd_hex': f"0x{hwnd:X}",
            'title': title,
            'class': class_name,
            'visible': is_visible
        })

        # 자식으로 파고들이
        child = user32.GetWindow(hwnd, 5) # GW_CHILD
        while child:
            scan_hierarchy(child)
            child = user32.GetWindow(child, 2) # HW_HWNDNEXT

    # 데스크탑부터 시작
    desktop = user32.GetDesktopWindow()

    # 최상위 창들
    hwnd = user32.GetTopWindow(None)
    while hwnd:
        scan_hierarchy(hwnd)
        hwnd = user32.GetWindow(hwnd, 2) #GW_HWNDNEXT

    return all_windows

def print_all_system_children():
    """
    시스템 전체 모든 창(자식 포함)을 탐색해서 출력
    """
    print("\n" + "="*100)
    print(" PC 전체 모든 HWND 탐색 (자식 포함)")
    print("="*100)

    all_windows = list_all_windows_recursive()

    print(f"\n[총 {len(all_windows)}개의 창]\n ")

    for i, w in enumerate(all_windows, 1):
        if i <= 500: # 처음 500개만 표시
            visibility = 'v' if w['visible'] else 'x'
            title = w['title'][:40] if len(w['title']) > 40 else w['title']
            print(f"[{i:4d}] {w['hwnd_hex']:12s} | {w['class']:25s} | {visibility} | {title}")

    if len(all_windows) > 500:
        print(f"\n... 이하 {len(all_windows) - 500}개 생략...")

    print("\n" + "="*100)

def inspect_child_elements(hwnd):
    """
    특정 HWND의 모든 자식 요소를 상세히 검새
    """
    print("\n" + "="*100)
    print(f" HWND {hex(hwnd)} 의 자식 요소 검새")
    print("="*100)

    all_children = []

    def enum_child_proc(child_hwnd, lp):
        try:
            length = GetWindowTextLengthW(child_hwnd)
            if length == 0:
                title = "(없음)"
            else:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(child_hwnd, buf, length + 1)
                title = buf.value

            buf_class = ctypes.create_unicode_buffer(256)
            GetClassNameW(child_hwnd, buf_class, 256)
            class_name = buf_class.value

            all_children.append({
                'hwnd': child_hwnd,
                'hwnd_hex': f"0x{child_hwnd:X}",
                'title': title,
                'class': class_name
            })

        except:
            pass

        return True

    enum_child = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    callback = enum_child(enum_child_proc)

    user32.EnumChildWindows(hwnd, callback, 0)

    print(f"\n [총 {len(all_children)}개의 자식 요소]\n")

    for i, child in enumerate(all_children, 1):
        print(f"[{i}] {child['hwnd_hex']}")
        print(f"  클래스: {child['class']}")
        print(f"  타이틀: {child['title']}")
        print()

    print("="*100 + "\n")