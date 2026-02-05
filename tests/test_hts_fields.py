# /tests/test_hts_fields.py
import json
import ctypes
from ctypes import wintypes
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HTSController:
    def __init__(self):
        """초기화"""
        self.user32 = ctypes.windll.user32
        self.hwnd = None
        
        # 설정 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(current_dir), 'config', 'hts_controls.json')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        print(f"✓ 설정 파일 로드 완료")
    
    def open_popup_and_capture(self):
        """Ctrl+] 눌러서 팝업 열고 HWND 캡처"""
        print(f"\n{'='*60}")
        print("[1단계] 6100 팝업 열기")
        print(f"{'='*60}")
        
        # 기존 팝업이 있으면 닫기
        if self.hwnd:
            print("기존 팝업 닫는 중...")
            self.user32.PostMessageW(self.hwnd, 0x0010, 0, 0)  # WM_CLOSE
            time.sleep(0.5)
            self.hwnd = None
        
        # HTS 메인 창 찾기
        print("\nHTS 메인 창 검색 중...")
        
        main_hwnd = None
        
        def find_hts_window(hwnd, lparam):
            nonlocal main_hwnd
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                
                if 'iMeritz' in title and '6100' not in title and '주문' not in title:
                    if self.user32.IsWindowVisible(hwnd):
                        main_hwnd = hwnd
                        return False
            return True
        
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_proc = EnumWindowsProc(find_hts_window)
        self.user32.EnumWindows(enum_proc, 0)
        
        if not main_hwnd:
            print("✗ HTS 메인 창을 찾을 수 없습니다")
            return False
        
        # 창 정보 출력
        length = self.user32.GetWindowTextLengthW(main_hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(main_hwnd, buf, length + 1)
        title = buf.value
        
        print(f"✓ HTS 메인 윈도우 발견: {title}")
        
        # 창 활성화 (Alt+Tab 방식)
        print("\nHTS 창 활성화 중...")
        
        # 1. 최소화 해제
        self.user32.ShowWindow(main_hwnd, 9)  # SW_RESTORE
        time.sleep(0.3)
        
        # 2. Alt 누르기 (포그라운드 권한 획득)
        VK_MENU = 0x12  # Alt 키
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        
        # 3. SetForegroundWindow (Alt 누른 상태에서)
        self.user32.SetForegroundWindow(main_hwnd)
        time.sleep(0.1)
        
        # 4. Alt 떼기
        self.user32.keybd_event(VK_MENU, 0, 2, 0)  # KEYUP
        time.sleep(0.5)
        
        # 5. 마우스 클릭으로 확실히 포커스
        rect = wintypes.RECT()
        self.user32.GetWindowRect(main_hwnd, ctypes.byref(rect))
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        self.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.2)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.1)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        time.sleep(0.5)
        
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        # 6. 포커스 확인
        active_hwnd = self.user32.GetForegroundWindow()
        if active_hwnd == main_hwnd:
            print("✓ HTS 창 활성화 성공!")
        else:
            print("⚠ HTS 창 활성화 실패!")
            print("\n수동으로 HTS 창을 클릭해주세요!")
            print("5초 드립니다...")
            time.sleep(5)
        
        print("\n3초 후 Ctrl+]를 누릅니다...")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        # Ctrl+] 입력
        print("Ctrl+] 입력 중...")
        
        VK_CONTROL = 0x11
        VK_OEM_6 = 0xDD  # ] 키
        
        self.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.15)
        self.user32.keybd_event(VK_OEM_6, 0, 0, 0)
        time.sleep(0.15)
        self.user32.keybd_event(VK_OEM_6, 0, 2, 0)
        time.sleep(0.15)
        self.user32.keybd_event(VK_CONTROL, 0, 2, 0)
        
        print("✓ Ctrl+] 입력 완료")
        
        # 팝업이 뜰 때까지 대기
        print("\n팝업이 열릴 때까지 대기 중...")
        time.sleep(2.5)
        
        # 6100 팝업 찾기
        popup_hwnd = None
        
        def enum_callback(hwnd, lparam):
            nonlocal popup_hwnd
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                
                if '6100' in title or '해외주식' in title or '주문' in title:
                    if self.user32.IsWindowVisible(hwnd):
                        popup_hwnd = hwnd
                        return False
            return True
        
        EnumWindowsProc2 = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_proc2 = EnumWindowsProc2(enum_callback)
        self.user32.EnumWindows(enum_proc2, 0)
        
        if popup_hwnd:
            self.hwnd = popup_hwnd
            print(f"✓ 6100 팝업 자동 발견!")
        else:
            self.hwnd = self.user32.GetForegroundWindow()
            print(f"⚠ 팝업을 자동으로 찾지 못했습니다. 활성 창을 사용합니다")
        
        if not self.hwnd:
            print("✗ 창을 찾을 수 없습니다")
            return False
        
        # 창 제목 확인
        length = self.user32.GetWindowTextLengthW(self.hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(self.hwnd, buf, length + 1)
            title = buf.value
            
            print(f"\n[캡처된 창 정보]")
            print(f"  제목: {title}")
            print(f"  HWND: {hex(self.hwnd)}")
            
            if '6100' in title or '해외주식' in title or '주문' in title:
                print(f"  ✓ 올바른 창입니다!")
                return True
            else:
                print(f"  ⚠ 예상과 다른 창일 수 있습니다")
                confirm = input("  이 창을 사용하시겠습니까? (y/n): ").strip().lower()
                return confirm == 'y'
        
        return False
    
    def get_child_hwnd(self, field_name):
        """Control ID로 자식 HWND 찾기 (재귀)"""
        if not self.hwnd:
            return None
        
        control = self.config['controls'].get(field_name)
        if not control:
            return None
        
        target_id = control['id']
        target_class = control['class']
        found = [None]
        
        def enum_callback(hwnd, lparam):
            child_id = self.user32.GetDlgCtrlID(hwnd)
            
            if child_id == target_id:
                class_buf = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_buf, 256)
                class_name = class_buf.value
                
                if target_class in class_name or class_name in target_class:
                    found[0] = hwnd
                    return False
            
            if found[0] is None:
                self.user32.EnumChildWindows(hwnd, enum_proc, 0)
            
            return found[0] is None
        
        EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_proc = EnumChildProc(enum_callback)
        
        self.user32.EnumChildWindows(self.hwnd, enum_proc, 0)
        return found[0]
    
    def get_value(self, field_name):
        """필드 값 읽기"""
        child_hwnd = self.get_child_hwnd(field_name)
        if not child_hwnd:
            return None
        
        length = self.user32.GetWindowTextLengthW(child_hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(child_hwnd, buf, length + 1)
            return buf.value
        return ""
    
    def set_value(self, field_name, value):
        """필드 값 설정"""
        child_hwnd = self.get_child_hwnd(field_name)
        if not child_hwnd:
            print(f"  ✗ {field_name}: HWND를 찾을 수 없음")
            return False
        
        # 포커스 설정
        self.user32.SetFocus(child_hwnd)
        time.sleep(0.1)
        
        # 전체 선택
        EM_SETSEL = 0x00B1
        self.user32.SendMessageW(child_hwnd, EM_SETSEL, 0, -1)
        time.sleep(0.05)
        
        # 값 설정
        WM_SETTEXT = 0x000C
        result = self.user32.SendMessageW(child_hwnd, WM_SETTEXT, 0, str(value))
        
        # 변경 알림
        WM_COMMAND = 0x0111
        EN_CHANGE = 0x0300
        parent = self.user32.GetParent(child_hwnd)
        ctrl_id = self.user32.GetDlgCtrlID(child_hwnd)
        self.user32.SendMessageW(parent, WM_COMMAND, (EN_CHANGE << 16) | ctrl_id, child_hwnd)
        
        time.sleep(0.1)
        
        # 확인
        new_value = self.get_value(field_name)
        if new_value == str(value):
            print(f"  ✓ {field_name}: '{value}' 설정 성공")
            return True
        else:
            print(f"  ✗ {field_name}: 설정 실패 (현재값: {new_value})")
            return False
    
    def show_all_values(self):
        """모든 필드 값 표시"""
        if not self.hwnd:
            print("✗ 먼저 1번으로 팝업을 열어주세요")
            return
        
        print(f"\n{'='*60}")
        print("[현재 필드 값]")
        print(f"{'='*60}\n")
        
        for field_name, control in self.config['controls'].items():
            value = self.get_value(field_name)
            if value is not None:
                print(f"{control['desc']:15s} ({field_name:20s}): '{value}'")
            else:
                print(f"{control['desc']:15s} ({field_name:20s}): ✗ 찾을 수 없음")
    
    def test_field_properties(self):
        """필드 속성 확인"""
        if not self.hwnd:
            print("✗ 먼저 1번으로 팝업을 열어주세요")
            return
        
        print(f"\n{'='*60}")
        print("[order_quantity 필드 속성]")
        print(f"{'='*60}")
        
        child_hwnd = self.get_child_hwnd('order_quantity')
        if not child_hwnd:
            print("✗ HWND를 찾을 수 없음")
            return
        
        # 스타일 확인
        GWL_STYLE = -16
        style = self.user32.GetWindowLongW(child_hwnd, GWL_STYLE)
        
        WS_DISABLED = 0x08000000
        ES_READONLY = 0x0800
        
        print(f"\nHWND: {hex(child_hwnd)}")
        print(f"Style: {hex(style)}")
        print(f"  Disabled: {bool(style & WS_DISABLED)}")
        print(f"  ReadOnly: {bool(style & ES_READONLY)}")

    def set_value(self, field_name, value):
        """필드 값 설정 (마우스 클릭 + 키보드 입력)"""
        child_hwnd = self.get_child_hwnd(field_name)
        if not child_hwnd:
            print(f"  ✗ {field_name}: HWND를 찾을 수 없음")
            return False
        
        # 마우스 클릭으로 포커스
        rect = wintypes.RECT()
        self.user32.GetWindowRect(child_hwnd, ctypes.byref(rect))
        x = (rect.left + rect.right) // 2
        y = (rect.top + rect.bottom) // 2
        
        self.user32.SetCursorPos(x, y)
        time.sleep(0.2)
        
        # 마우스 클릭
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        time.sleep(0.3)
        
        # Ctrl+A로 전체 선택
        VK_CONTROL = 0x11
        VK_A = 0x41
        
        self.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        self.user32.keybd_event(VK_A, 0, 0, 0)
        time.sleep(0.05)
        self.user32.keybd_event(VK_A, 0, 2, 0)
        time.sleep(0.05)
        self.user32.keybd_event(VK_CONTROL, 0, 2, 0)
        time.sleep(0.2)
        
        # 문자 입력
        for char in str(value):
            if char.isdigit():
                vk_code = 0x30 + int(char)
            elif char.isalpha():
                vk_code = ord(char.upper())
            elif char == '.':
                vk_code = 0xBE
            else:
                continue
            
            self.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            self.user32.keybd_event(vk_code, 0, 2, 0)
            time.sleep(0.1)
        
        time.sleep(0.3)
        
        # 확인
        new_value = self.get_value(field_name)
        if new_value == str(value):
            print(f"  ✓ {field_name}: '{value}' 설정 성공")
            return True
        else:
            print(f"  ⚠ {field_name}: 입력 완료 (확인값: '{new_value}')")
            return True



    def test_quantity_input(self):
        """수량 입력 테스트"""
        if not self.hwnd:
            print("✗ 먼저 1번으로 팝업을 열어주세요")
            return
        
        print(f"\n{'='*60}")
        print("[수량 입력 테스트]")
        print(f"{'='*60}")
        
        # 현재 값 확인
        current = self.get_value('order_quantity')
        print(f"\n현재 수량: '{current}'")
        
        # 새 값 입력
        new_value = input("입력할 수량: ").strip()
        if not new_value:
            print("취소되었습니다")
            return
        
        # 창 활성화 대기
        print(f"\n3초 후 수량을 입력합니다...")
        print("6100 팝업이 보이는지 확인하세요!")
        
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        # 창 활성화
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.2)
        
        print(f"\n'{new_value}' 설정 중...")
        success = self.set_value('order_quantity', new_value)
        
        if success:
            print("\n✓ 수량 입력 성공!")
            print("화면에서 값이 변경되었는지 확인해주세요")
        else:
            print("\n✗ 수량 입력 실패")
    def find_quantity_field(self):
        """마우스로 수량 필드 찾기"""
        if not self.hwnd:
            print("✗ 먼저 1번으로 팝업을 열어주세요")
            return
        
        print(f"\n{'='*60}")
        print("[수량 필드 찾기]")
        print(f"{'='*60}")
        print("\n5초 후 마우스 커서 위치의 컨트롤을 찾습니다...")
        print("수량 입력 필드 위에 마우스를 올려놓으세요!")
        print("(이미지에서 '100' 표시된 필드)")
        
        for i in range(5, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        # 현재 마우스 위치
        point = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        print(f"\n마우스 위치: ({point.x}, {point.y})")
        
        # 해당 위치의 윈도우
        hwnd = self.user32.WindowFromPoint(point)
        
        print(f"\n[발견된 컨트롤]")
        print(f"  HWND: {hex(hwnd)}")
        
        ctrl_id = self.user32.GetDlgCtrlID(hwnd)
        print(f"  Control ID: {ctrl_id}")
        
        class_buf = ctypes.create_unicode_buffer(256)
        self.user32.GetClassNameW(hwnd, class_buf, 256)
        print(f"  Class: {class_buf.value}")
        
        length = self.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            text_buf = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, text_buf, length + 1)
            print(f"  Text: '{text_buf.value}'")
        else:
            print(f"  Text: (빈 값)")
        
        # 부모 확인
        parent = self.user32.GetParent(hwnd)
        print(f"\n[부모 정보]")
        print(f"  Parent HWND: {hex(parent)}")
        print(f"  Main HWND: {hex(self.hwnd)}")
        
        # JSON 매핑 제안
        print(f"\n[JSON 매핑 제안]")
        print(f'"order_quantity": {{')
        print(f'  "id": {ctrl_id},')
        print(f'  "class": "{class_buf.value}",')
        print(f'  "desc": "주문수량"')
        print(f'}}')
        
        print(f"\n현재 JSON의 order_quantity:")
        print(f'  ID: {self.config["controls"]["order_quantity"]["id"]}')
        print(f'  Class: {self.config["controls"]["order_quantity"]["class"]}')

    def run(self):
        """메인 루프"""
        while True:
            print(f"\n{'='*60}")
            print("HTS 컨트롤러")
            print(f"{'='*60}")
            print("1. Ctrl+] 눌러서 6100 팝업 열기")
            print("2. 현재 설정된 값 보기")
            print("3. 수량 입력 테스트")
            print("4. 수량 필드 속성 확인")
            print("5. 마우스로 수량 필드 찾기") 
            print("q. 종료")
            
            choice = input("\n선택: ").strip()
            
            if choice == '1':
                self.open_popup_and_capture()
            
            elif choice == '2':
                self.show_all_values()
            
            elif choice == '3':
                self.test_quantity_input()

            elif choice == '4':  # 추가
                self.test_field_properties()

            elif choice == '5':  # 추가
                self.find_quantity_field()
        
            elif choice.lower() == 'q':
                print("종료합니다")
                break
            
            else:
                print("잘못된 입력입니다")


if __name__ == "__main__":
    print("="*60)
    print("HTS 필드 테스트 프로그램 v2")
    print("="*60)
    
    controller = HTSController()
    controller.run()