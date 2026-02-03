# /tests/windows_inspector.py

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
EnumWindows = user32.EnumWindows
IsWindowVisible = user32.IsWindowVisible

def extract_all_text_from_window(hwnd):
    """
    HWND 안의 모든 텍스트를 간단하게 추출
    """
    import ctypes
    from ctypes import wintypes
    from datetime import datetime

    user32 = ctypes.windll.user32

    all_texts = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def enum_child_proc(child_hwnd, lp):
        try:
            # 텍스트만 추출
            length = user32.GetWindowTextLengthW(child_hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(child_hwnd, buf, length + 1)
                text = buf.value.strip()

                if text: # 공백이 아니면 추가
                    all_texts.append(text)
        except:
            pass
            
        return True
    
    enum_child = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    callback = enum_child(enum_child_proc)

    user32.EnumChildWindows(hwnd, callback, 0)

    # 콘솔에 출력
    print("\n" + "="*80)
    print(f" HWND {hex(hwnd)}안의 모든 텍스트")
    print("="*80 + "\n")

    for i, text in enumerate(all_texts, 1):
        print(f"[{i:3d}] {text}")

    print("\n" + "="*80)
    print(f" 총 {len(all_texts)}개의 텍스트 추출됨")
    print("="*80 + "\n")

    # 파일로도 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"child_elements_{hex(hwnd)}_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*180 + "\n")
        f.write(f"HWND {hex(hwnd)}안의 모든 텍스트\n")
        f.write(f"저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        for i, text in enumerate(all_texts, 1):
            f.write(f"[{i:3d}] {text}\n")

        f.write("\n" + "="*80 + "\n")
        f.write(f"총 {len(all_texts)}개의 텍스트")
            

        print(f" 파일저장: {filename}\n")

    return all_texts

            



def extract_foreign_stock_data(hwnd):
    """
    해외주식 주문창([06100] 에서 모든 데이터 추출)
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    data = {}
    
    def enum_child_proc(child_hwnd, lp):
        try:
            # 텍스트 추출
            length = user32.GetWindowTextLengthW(child_hwnd)
            if length == 0:
                title = ""
            else:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(child_hwnd, buf, length + 1)
                title = buf.value

            # 클래스명
            buf_class = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(child_hwnd< buf_class, 256)
            class_name = buf_class.value

            # Control ID
            control_id = user32.GetDlgCtrlID(child_hwnd)

            # 위치
            rect = user32.GetWindowRect(child_hwnd)
            x, y = rect[0], rect[1]

            # 데이터 저장
            if title.strip(): # 텍스트가 있으면
                if control_id not in data:
                    data[control_id] = []

                data[control_id].append({
                    'hwnd': hex(child_hwnd),
                    'title' : title,
                    'class': class_name,
                    'position': (x, y)
                })
        except:
            pass
            
        return True

    enum_child = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    callback = enum_child(enum_child_proc)

    user32.EnumChildWindows(hwnd, callback, 0)

    return data

def print_foreign_stock_data(hwnd):
    """
    해외주식 주문창의 데이터를 정리해서 출력
    """
    data = extract_foreign_stock_data(hwnd)

    print("\n" + "="*100)
    print(" 해외주식 주문창 데이터 추출")
    print("="*100)

    print(f"\n[총 {len(data)}개의 Control ID 그룹]\n")
            
    for control_id in sorted(data.keys()):
        items = data[control_id]
        print(f"[Control ID: {control_id}]")
        for i, item in enumerate(item):
            print(f" [{i+1}] {item['title']:<30} | {item['class']:<20} | {item['position']}")
        print()

    print("="*100 + "\n")

def inspect_child_elements_with_details_to_file(hwnd):
    """
    특정 HWND의 모든 자식 요소를 상세 정보와 함께 파일로 저장
    """
    from datetime import datetime

    print("\n" + "="*180)
    print(f" HWND{hex(hwnd)} 의 자식 요소 상세 검사 (파일 저장)")
    print("="*180)

    all_children = []

    def enum_child_proc(child_hwnd, lp):
        try:
            # 기본 정보
            length = GetWindowTextLengthW(child_hwnd)
            if length == 0:
                title = "(없음)"
            else:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(child_hwnd, buf, length + 1)
                title = buf.value

            buf_class = ctypes.create_unicode_buffer(256)
            GetWindowTextW(child_hwnd, buf_class, 256)
            class_name = buf_class.value

            is_visible = bool(IsWindowVisible(child_hwnd))

            # 위치 및 크기
            rect = user32.GetWindowRect(child_hwnd)
            left, top, right, bottom = rect

            # 부모
            parent_hwnd = user32.GetParent(chlid_hwnd)

            # Control ID
            control_id = user32.GetDlgCtrlID(child_hwnd)

            # Style
            try:
                style = user32.GetWindowLongW(child_hwnd, -16)
                style_hex = f"0x{style:X}"
            except:
                style_hex = "Unknown"

            all_chlidren.append({
                'hwnd': child_hwnd,
                'hwnd_hex': f"0x{child_hwnd:X}",
                'title': title,
                'class': class_name,
                'visible': is_visible,
                'position': {'x': left, 'y': top},
                'size': {'width': right - left, 'height': bottom - top},
                'parent_hwnd': f"0x{parent_hwnd:X}",
                'control_id': control_id,
                'style': style_hex
            })
        except:
            pass

        return True
    
    enum_child = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    callback = enum_child(enum_child_proc)

    user32.EnumChildWindows(hwnd, callback, 0)

    print(f"\n[총 {len(all_children)}개의 자식 요소]\n")

    # 콘솔 출력
    print(f"{'No':>4} | {'HWND':>12} | {'Class':^30} | {'V'} | {'Title':<40} | {'Control ID':>8}")
    print("-"*180)

    for i, child in enumerate(all_children, 1):
        if i <= 50: # 처음 50개만 콘솔에
            visibility = 'v' if child['visible'] else 'x'
            title = child['title'][:40] if len(child['title']) > 40 else child['title']
            control_id = child['control_id'] if child['control_id'] != 0 else "N/A"

            print(f"{i:4d} | {child['hwnd_hex']:>12} | {child['class']:^30} | {visibility} | {title:<40} | {control_id:>8}")

    if len(all_children) > 50:
        print(f"... 이하{len(all_children) - 50} 개는 파일에 저장됨...")

    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"child_elements_{hex(hwnd)}_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*180 + "\n")
        f.write(f"자식 요소 상세 분석: {hex(hwnd)}\n")
        f.write(f"저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*180 + "\n\n")
        f.write(f"[총 {len(all_children)}개의 자식 요소]\n\n")

        # 테이블 헤더
        f.write(f"{'No':>4} | {'hwnd':>12} | {'class':^30} | {'V'} | {'Title':<40} | {'Control ID':>8} | {'위치':^20} | {'크기':^15} | {'Style':^12}\n")
        f.write("-"*200 + "\n")

        # 각 자식 요소
        for i, child in enumerate(all_children, 1):
            visibility = 'v' if child['visible'] else 'x'
            title = child['title'][:40] if len(child['title']) > 40 else child['title']
            control_id = child['control_id'] if child['control_id'] != 0 else "N/A"
            pos = f"({child['position']['x']}, {child['position']['y']})"
            size = f"{child['size']['width']}x{child['size']['height']}"

            f.write(f"{i:4d} | {child['hwnd_hex']:>12} | {child['class']:^30} | {visibility} | {title:<40} | {control_id:>8} | {pos:^20} | {size:^15} | {child['style']:^12}\n")

        # 상세 정보 섹션
        f.write("\n\n" + "="*180 + "\n")
        f.write("[상세 정보] \n")
        f.write("="*180 + "\n\n")

        for i, child in enumerate(all_children, 1):
            f.write(f"\n[{i}] {child['title']}\n")
            f.write(f"  HWND: {child['hwnd_hex']} ({child['hwnd']}) \n")
            f.write(f"  클래스: {child['class']} \n")
            f.write(f"  보임: {'v' if child['visible'] else 'x'} \n")
            f.write(f"  Control ID: {child['control_id']} \n")
            f.write(f"  위치: X={child['position']['x']}, Y={child['position']['y']} \n")
            f.write(f"  크기: {child['size']['width']}x{child['size']['height']} \n")
            f.write(f"  스타일: {child['style']} \n")
            f.write(f"  부모: {child['parent_hwnd']} \n")
            
        print(f"\n 파일 저장 완료: {filename}")
        print(f"   -> 이 파일을 열어서 현재갈ㄹ 찾아보세요! \n")

        return filename, all_children



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

def print_all_system_children(save_to_file=True):
    """
    시스템 전체 모든 창(자식 포함)을 탐색해서 출력
    """

    from datetime import datetime

    print("\n" + "="*150)
    print(" PC 전체 모든 HWND 탐색 (자식 포함)")
    print("="*150)

    all_windows = list_all_windows_recursive()

    print(f"\n[총 {len(all_windows)}개의 창]\n ")

    # 헤더
    header = f"{'No':>4} | {'HWND':>12} | {'Class':^25} | {'V'} | {'Text/Title':<80}"
    print(header)
    print("-"*150)

    # 파일 저장 준비
    if save_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hts_windows_list_{timestamp}.txt"
        file_handle = open(filename, 'w', encoding='utf-8')

        # 헤더 작성
        file_handle.write("="*150 + "\n")
        file_handle.write(" PC 전체 모든 HWND 탐색 결과 \n")
        file_handle.write(f" 저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file_handle.write("="*150 + "\n")
        file_handle.write(f"[총 {len(all_windows)}개의 창]\n\n")
        file_handle.write(header + "\n")
        file_handle.write("-"*150 + "\n")

    for i, w in enumerate(all_windows, 1):
        if i <= 1000: # 처음 1000개만 표시
            visibility = 'v' if w['visible'] else 'x'
            title = w['title'][:80] if len(w['title']) > 80 else w['title']
            
            line = f"{i:4d} {w['hwnd_hex']:12} | {w['class']:^25} | {visibility} | {title}"
            print(line)

    if len(all_windows) > 1000:
        print(f"\n... 이하 {len(all_windows) - 500}개 생략...")

    print("\n" + "="*150)

    if save_to_file:
        file_handle.write("\n" + "="*150 + "\n")

        # 상세 정보 섹션
        file_handle.write("\n\n[상세 정보 - 가격 관련 창들]\n\n")

       # price_keywords = [
       #     "현재가","호가","가격","Price","Quote","시세","매도","매수",
       #     "Bid","Ask","차트","[06000]"
       # ]

       # price_windows = [w for w in all_windows if any(kw in w['title'] for kw in price_keywords)]
       
        for idx, w in enumerate(all_windows, 1):
    
        #if price_windows:
        #    for idx, w in enumerate(price_windows, 1):
            file_handle.write(f"\n[{idx}] {w['title']}")
            file_handle.write(f"  HWND (16진수): {w['hwnd_hex']}\n")
            file_handle.write(f"  HWND (10진수): {w['hwnd']}\n")
            file_handle.write(f"  클래스: {w['class']}\n")
            file_handle.write(f"  보임: {'v' if w['visible'] else 'x'}\n")
        #else:
        #    file_handle.write("가격 관련 창을 찾을 수 없습니다.\n")

        file_handle.close()

        print(f"\n 파일 저장 완료: {filename}")
        return filename

    return None

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