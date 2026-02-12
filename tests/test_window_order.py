import ctypes
from ctypes import wintypes
import time
import win32api
import win32con
import win32gui
import os
import json  
from pywinauto import Application
from pywinauto.controls.win32_controls import ComboBoxWrapper

PYWINAUTO_AVAILABLE = True


class OverseasOrderWindow:
    """해외주식 주문창(6100) 제어 클래스"""
    
    def __init__(self):
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.hwnd = None
        self.main_hwnd = None
        
        # 탭 설정 (시작=18, 간격=36)
        self.tab_start_offset = 18
        self.tab_gap = 36
        self.tab_names = ["매수", "매도", "정정", "취소"]
        
        # 현재가와 수량 입력창 핸들을 초기화합니다.
        self.price_edit_hwnd = None
        self.quantity_edit_hwnd = None
        self.tab_hwnd = None
        self.stock_code_hwnd = None  # 종목코드 입력창
        self.password_hwnd = None  # 비밀번호 입력창    
        self.account_combo_hwnd = None  # 계좌번호 콤보박스


        # JSON 파일 읽기
        json_path = r'C:\thirds\config\hts_controls.json'  # ← 수정!
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # ★ 수정된 부분
        self.window_name = config['window']['name']
        self.price_edit_id = config['controls']['limit_price']['id']  # 3930
        self.quantity_edit_id = config['controls']['order_quantity']['id']  # 3900
        self.buy_button_id = config['controls']['buy_button']['id']  # 3875
        self.tab_control_id = config['controls']['order_type_tab']['id']  # 3810 추가!
        self.stock_code_id = config['controls']['stock_code']['id']  # 3860 추가!
        self.password_id = config['controls']['password']['id']  # 3880
        self.account_combo_id = config['controls']['account_combo']['id']  # 3780 
        
    def open_popup_and_capture(self):
        """Ctrl+] 눌러서 팝업 열고 HWND 캡처"""
        print(f"\n{'='*60}")
        print("[1단계] 6100 팝업 열기")
        print(f"{'='*60}")
        
        # 기존 팝업이 있으면 닫기
        if self.hwnd:
            self.user32.PostMessageW(self.hwnd, 0x0010, 0, 0)  # WM_CLOSE
            time.sleep(0.5)
            self.hwnd = None
        
        # HTS 메인 창 찾기
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
        
        # 창 활성화 (Alt+Tab 방식)
        self.user32.ShowWindow(main_hwnd, 9)  # SW_RESTORE
        time.sleep(0.3)
        
        VK_MENU = 0x12  # Alt 키
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        
        self.user32.SetForegroundWindow(main_hwnd)
        time.sleep(0.1)
        
        self.user32.keybd_event(VK_MENU, 0, 2, 0)  # KEYUP
        time.sleep(0.5)
        
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
        
        active_hwnd = self.user32.GetForegroundWindow()
        if active_hwnd == main_hwnd:
            print("✓ HTS 창 활성화 성공!")
        else:
            print("⚠ HTS 창 활성화 실패!")
            return False
        
        # Ctrl+] 입력
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
        time.sleep(2.5)

        # 6100 팝업 찾기
        self.find_child_window(main_hwnd)

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
                print(f"  ⚠ 예상과 다른 창입니다.")

        return False

    def find_child_window(self, parent_hwnd):
        """부모 창의 자식 창을 찾습니다."""
        child_hwnd = None

        def enum_child_callback(hwnd, lparam):
            nonlocal child_hwnd
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                
                if '6100' in title or '해외주식' in title or '주문' in title:
                    if self.user32.IsWindowVisible(hwnd):
                        child_hwnd = hwnd
                        return False
            return True

        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_child_proc = EnumChildWindowsProc(enum_child_callback)
        self.user32.EnumChildWindows(parent_hwnd, enum_child_proc, 0)

        if child_hwnd:
            self.hwnd = child_hwnd
            print(f"✓ 자식 창 발견: HWND={hex(self.hwnd)}")
        else:
            print("⚠ 자식 창을 찾지 못했습니다.")

    def get_current_price(self):
        """현재가 가져오기 (ID: 3930)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return None
        
        # 모든 자식 컨트롤을 순회하면서 ID 3930 찾기
        control_id = 3930
        found_hwnd = None
        
        def enum_child_callback(hwnd, lparam):
            nonlocal found_hwnd
            # GetDlgCtrlID로 컨트롤 ID 확인
            ctrl_id = self.user32.GetDlgCtrlID(hwnd)
            if ctrl_id == control_id:
                found_hwnd = hwnd
                return False  # 찾았으면 중단
            return True
        
        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_child_proc = EnumChildWindowsProc(enum_child_callback)
        self.user32.EnumChildWindows(self.hwnd, enum_child_proc, 0)
        
        if not found_hwnd:
            print(f"❌ 현재가 입력창(ID: {control_id})을 찾을 수 없습니다!")
            print("디버깅: 모든 컨트롤 ID를 출력합니다...")
            
            # 디버깅: 모든 컨트롤 ID 출력
            def debug_enum_callback(hwnd, lparam):
                ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                if ctrl_id > 0:
                    # 클래스 이름 가져오기
                    class_name = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(hwnd, class_name, 256)
                    
                    # 텍스트 가져오기
                    text_buffer = ctypes.create_unicode_buffer(256)
                    self.user32.GetWindowTextW(hwnd, text_buffer, 256)
                    
                    print(f"  ID: {ctrl_id}, Class: {class_name.value}, Text: {text_buffer.value}")
                return True
            
            debug_proc = EnumChildWindowsProc(debug_enum_callback)
            self.user32.EnumChildWindows(self.hwnd, debug_proc, 0)
            return None
        
        self.price_edit_hwnd = found_hwnd
        
        # WM_GETTEXT 메시지로 텍스트 가져오기
        buffer_size = 256
        buffer = ctypes.create_unicode_buffer(buffer_size)
        length = self.user32.SendMessageW(self.price_edit_hwnd, 0x000D, buffer_size, buffer)
        
        text = buffer.value
        
        if text:
            print(f"📊 현재가: {text}")
        else:
            print("❌ 현재가를 가져올 수 없습니다!")
        
        return text
    
    def set_quantity(self, quantity):
        """수량 입력 (ID: 3900으로 직접 찾기)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        # 1. ID 3900인 수량 입력창 찾기 (모든 자식 컨트롤 순회)
        print(f"1) 수량 입력창(ID: {self.quantity_edit_id}) 찾는 중...")
        quantity_hwnd = None
        
        def enum_child_callback(hwnd, lparam):
            nonlocal quantity_hwnd
            ctrl_id = self.user32.GetDlgCtrlID(hwnd)
            if ctrl_id == self.quantity_edit_id:
                quantity_hwnd = hwnd
                return False  # 찾았으면 중단
            return True
        
        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_child_proc = EnumChildWindowsProc(enum_child_callback)
        self.user32.EnumChildWindows(self.hwnd, enum_child_proc, 0)
        
        if not quantity_hwnd:
            print(f"❌ 수량 입력창(ID: {self.quantity_edit_id})을 찾을 수 없습니다!")
            print("디버깅: 모든 컨트롤 ID를 출력합니다...")
            
            # 디버깅: 모든 컨트롤 ID 출력
            def debug_enum_callback(hwnd, lparam):
                ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                if ctrl_id > 0:
                    # 클래스 이름 가져오기
                    class_name = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(hwnd, class_name, 256)
                    
                    # 텍스트 가져오기
                    text_buffer = ctypes.create_unicode_buffer(256)
                    self.user32.GetWindowTextW(hwnd, text_buffer, 256)
                    
                    print(f"  ID: {ctrl_id}, Class: {class_name.value}, Text: {text_buffer.value}")
                return True
            
            debug_proc = EnumChildWindowsProc(debug_enum_callback)
            self.user32.EnumChildWindows(self.hwnd, debug_proc, 0)
            return False
        
        self.quantity_edit_hwnd = quantity_hwnd
        print(f"✓ 수량 입력창 찾음: HWND={hex(quantity_hwnd)}")
        
        # 2. 주문 창 활성화
        print("2) 주문 창 활성화 중...")
        self.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # 3. 수량 입력창 좌표 가져오기
        rect = wintypes.RECT()
        self.user32.GetWindowRect(self.quantity_edit_hwnd, ctypes.byref(rect))
        
        # 입력창 중앙 좌표 계산
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        print(f"3) 수량 입력창 좌표: ({center_x}, {center_y})")
        
        # 4. 수량 입력창 클릭
        print("4) 수량 입력창 클릭 중...")
        ctypes.windll.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.3)
        
        # 마우스 클릭
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        time.sleep(0.3)
        
        # 5. 기존 텍스트 전체 선택 (Ctrl+A)
        print("5) 기존 텍스트 선택 중...")
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
        
        # 6. 수량 입력 (키보드로 직접 입력)
        print(f"6) 수량 '{quantity}' 입력 중...")
        quantity_str = str(quantity)
        
        for char in quantity_str:
            vk_code = ord(char)
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        time.sleep(0.3)
        
        # 7. 입력 확인
        result_buffer = ctypes.create_unicode_buffer(256)
        WM_GETTEXT = 0x000D
        length = self.user32.SendMessageW(self.quantity_edit_hwnd, WM_GETTEXT, 256, result_buffer)
        current_text = result_buffer.value
        
        print(f"7) 입력 결과: '{current_text}'")
        
        if quantity_str in current_text:
            print(f"✅ 수량 입력 성공: {quantity}")
            return True
        else:
            print(f"⚠ 수량 입력 완료 (입력={quantity_str}, 현재={current_text})")
            return True

    def switch_tab(self, tab_name):
        """탭 전환 (매수/매도/정정/취소)"""
        if tab_name not in self.tab_names:
            print(f"❌ 잘못된 탭 이름: {tab_name}")
            return False
        
        # 1. 탭 컨트롤 찾기 (ID: 3810)
        if not self.tab_hwnd:
            print(f"1) 탭 컨트롤 찾는 중...")
            tab_control_id = 3810  # JSON에서 가져온 ID
            tab_hwnd = None
            
            def enum_child_callback(hwnd, lparam):
                nonlocal tab_hwnd
                ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                if ctrl_id == tab_control_id:
                    # 클래스 이름 확인
                    class_name = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(hwnd, class_name, 256)
                    if 'Tab' in class_name.value:  # SysTabControl32
                        tab_hwnd = hwnd
                        return False
                return True
            
            EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            enum_child_proc = EnumChildWindowsProc(enum_child_callback)
            self.user32.EnumChildWindows(self.hwnd, enum_child_proc, 0)
            
            if not tab_hwnd:
                print(f"❌ 탭 컨트롤(ID: {tab_control_id})을 찾을 수 없습니다!")
                print("디버깅: 모든 컨트롤 ID를 출력합니다...")
                
                # 디버깅: 모든 컨트롤 ID 출력
                def debug_enum_callback(hwnd, lparam):
                    ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                    if ctrl_id > 0:
                        class_name = ctypes.create_unicode_buffer(256)
                        self.user32.GetClassNameW(hwnd, class_name, 256)
                        text_buffer = ctypes.create_unicode_buffer(256)
                        self.user32.GetWindowTextW(hwnd, text_buffer, 256)
                        print(f"  ID: {ctrl_id}, Class: {class_name.value}, Text: {text_buffer.value}")
                    return True
                
                debug_proc = EnumChildWindowsProc(debug_enum_callback)
                self.user32.EnumChildWindows(self.hwnd, debug_proc, 0)
                return False
            
            self.tab_hwnd = tab_hwnd
            print(f"✓ 탭 컨트롤 찾음: HWND={hex(tab_hwnd)}")
        
        target_index = self.tab_names.index(tab_name)
        
        # 2. 탭 위치 계산
        rect = win32gui.GetWindowRect(self.tab_hwnd)
        x_offset = self.tab_start_offset + (self.tab_gap * target_index)
        click_x = rect[0] + x_offset
        click_y = rect[1] + 10
        
        print(f"2) {tab_name} 탭 클릭 위치: ({click_x}, {click_y})")
        
        # 3. 클릭
        current_pos = win32api.GetCursorPos()
        win32api.SetCursorPos((click_x, click_y))
        time.sleep(0.2)
        
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        time.sleep(0.3)
        win32api.SetCursorPos(current_pos)
        
        # 4. 확인
        TCM_GETCURSEL = 0x130B
        new_tab = win32gui.SendMessage(self.tab_hwnd, TCM_GETCURSEL, 0, 0)
        
        if new_tab == target_index:
            print(f"✅ {tab_name} 탭으로 전환 성공!")
            return True
        else:
            print(f"⚠ {tab_name} 탭 클릭 완료 (확인: 인덱스={new_tab}, 목표={target_index})")
            return True
    def set_stock_code(self, stock_code):
        """종목코드 입력 (ID: 3860)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        # 1. ID 3860인 종목코드 입력창 찾기
        print(f"1) 종목코드 입력창(ID: {self.stock_code_id}) 찾는 중...")
        stock_code_hwnd = None
        
        def enum_child_callback(hwnd, lparam):
            nonlocal stock_code_hwnd
            ctrl_id = self.user32.GetDlgCtrlID(hwnd)
            if ctrl_id == self.stock_code_id:
                stock_code_hwnd = hwnd
                return False  # 찾았으면 중단
            return True
        
        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_child_proc = EnumChildWindowsProc(enum_child_callback)
        self.user32.EnumChildWindows(self.hwnd, enum_child_proc, 0)
        
        if not stock_code_hwnd:
            print(f"❌ 종목코드 입력창(ID: {self.stock_code_id})을 찾을 수 없습니다!")
            print("디버깅: 모든 컨트롤 ID를 출력합니다...")
            
            # 디버깅: 모든 컨트롤 ID 출력
            def debug_enum_callback(hwnd, lparam):
                ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                if ctrl_id > 0:
                    class_name = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(hwnd, class_name, 256)
                    text_buffer = ctypes.create_unicode_buffer(256)
                    self.user32.GetWindowTextW(hwnd, text_buffer, 256)
                    print(f"  ID: {ctrl_id}, Class: {class_name.value}, Text: {text_buffer.value}")
                return True
            
            debug_proc = EnumChildWindowsProc(debug_enum_callback)
            self.user32.EnumChildWindows(self.hwnd, debug_proc, 0)
            return False
        
        self.stock_code_hwnd = stock_code_hwnd
        print(f"✓ 종목코드 입력창 찾음: HWND={hex(stock_code_hwnd)}")
        
        # 2. 주문 창 활성화
        print("2) 주문 창 활성화 중...")
        self.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # 3. 종목코드 입력창 좌표 가져오기
        rect = wintypes.RECT()
        self.user32.GetWindowRect(self.stock_code_hwnd, ctypes.byref(rect))
        
        # 입력창 중앙 좌표 계산
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        print(f"3) 종목코드 입력창 좌표: ({center_x}, {center_y})")
        
        # 4. 종목코드 입력창 클릭
        print("4) 종목코드 입력창 클릭 중...")
        ctypes.windll.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.3)
        
        # 마우스 클릭
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        time.sleep(0.3)
        
        # 5. 기존 텍스트 전체 선택 (Ctrl+A)
        print("5) 기존 텍스트 선택 중...")
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
        
        # 6. 종목코드 입력 (키보드로 직접 입력)
        print(f"6) 종목코드 '{stock_code}' 입력 중...")
        stock_code_str = str(stock_code)
        
        for char in stock_code_str:
            vk_code = ord(char.upper())  # 대문자로 변환
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        time.sleep(0.2)
        
        # 7. Enter 키 입력
        print("7) Enter 키 입력 중...")
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        
        # 8. 입력 확인
        result_buffer = ctypes.create_unicode_buffer(256)
        WM_GETTEXT = 0x000D
        length = self.user32.SendMessageW(self.stock_code_hwnd, WM_GETTEXT, 256, result_buffer)
        current_text = result_buffer.value
        
        print(f"8) 입력 결과: '{current_text}'")
        print(f"✅ 종목코드 입력 완료: {stock_code}")
        return True
    
    def set_password(self, password):
        """비밀번호 입력 (ID: 3880)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        # 1. ID 3880인 비밀번호 입력창 찾기
        print(f"1) 비밀번호 입력창(ID: {self.password_id}) 찾는 중...")
        password_hwnd = None
        
        def enum_child_callback(hwnd, lparam):
            nonlocal password_hwnd
            ctrl_id = self.user32.GetDlgCtrlID(hwnd)
            if ctrl_id == self.password_id:
                password_hwnd = hwnd
                return False  # 찾았으면 중단
            return True
        
        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_child_proc = EnumChildWindowsProc(enum_child_callback)
        self.user32.EnumChildWindows(self.hwnd, enum_child_proc, 0)
        
        if not password_hwnd:
            print(f"❌ 비밀번호 입력창(ID: {self.password_id})을 찾을 수 없습니다!")
            print("디버깅: 모든 컨트롤 ID를 출력합니다...")
            
            # 디버깅: 모든 컨트롤 ID 출력
            def debug_enum_callback(hwnd, lparam):
                ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                if ctrl_id > 0:
                    class_name = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(hwnd, class_name, 256)
                    text_buffer = ctypes.create_unicode_buffer(256)
                    self.user32.GetWindowTextW(hwnd, text_buffer, 256)
                    print(f"  ID: {ctrl_id}, Class: {class_name.value}, Text: {text_buffer.value}")
                return True
            
            debug_proc = EnumChildWindowsProc(debug_enum_callback)
            self.user32.EnumChildWindows(self.hwnd, debug_proc, 0)
            return False
        
        self.password_hwnd = password_hwnd
        print(f"✓ 비밀번호 입력창 찾음: HWND={hex(password_hwnd)}")
        
        # 2. 주문 창 활성화
        print("2) 주문 창 활성화 중...")
        self.user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # 3. 비밀번호 입력창 좌표 가져오기
        rect = wintypes.RECT()
        self.user32.GetWindowRect(self.password_hwnd, ctypes.byref(rect))
        
        # 입력창 중앙 좌표 계산
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        print(f"3) 비밀번호 입력창 좌표: ({center_x}, {center_y})")
        
        # 4. 비밀번호 입력창 클릭
        print("4) 비밀번호 입력창 클릭 중...")
        ctypes.windll.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.3)
        
        # 마우스 클릭
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        time.sleep(0.3)
        
        # 5. 기존 텍스트 전체 선택 (Ctrl+A)
        print("5) 기존 텍스트 선택 중...")
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
        
        # 6. 비밀번호 입력 (키보드로 직접 입력)
        print(f"6) 비밀번호 입력 중... (****)")
        password_str = str(password)
        
        for char in password_str:
            vk_code = ord(char)
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        time.sleep(0.3)
        
        print(f"✅ 비밀번호 입력 완료")
        return True

    def get_account_list(self):
        """계좌번호 목록 조회 - SysTabControl32 재귀 탐색"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return []
        
        print(f"\n[계좌번호 목록 조회]")
        print(f"{'='*60}")
        
        # 1. SysTabControl32 찾기 (ID=3810, 위치 49,210)
        print(f"1) SysTabControl32 찾기 (ID=3810)...")
        
        tab_control_hwnd = None
        
        def find_tab_control(hwnd, lparam):
            nonlocal tab_control_hwnd
            
            ctrl_id = self.user32.GetDlgCtrlID(hwnd)
            if ctrl_id == 3810:
                class_name = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_name, 256)
                
                if class_name.value == 'SysTabControl32':
                    rect = wintypes.RECT()
                    self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    
                    if rect.left == 49 and rect.top == 210:
                        print(f"  ✓ SysTabControl32 발견!")
                        print(f"     HWND: {hex(hwnd)}")
                        tab_control_hwnd = hwnd
                        return False
            
            return True
        
        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        enum_proc = EnumChildWindowsProc(find_tab_control)
        self.user32.EnumChildWindows(self.hwnd, enum_proc, 0)
        
        if not tab_control_hwnd:
            print(f"❌ SysTabControl32를 찾을 수 없습니다!")
            return []
        
        # 2. 모든 하위 컨트롤 재귀 탐색
        print(f"\n2) SysTabControl32의 모든 하위 컨트롤 재귀 탐색...")
        
        all_descendants = []
        
        def recursive_find(parent_hwnd, depth=0):
            """재귀적으로 모든 하위 자식 찾기"""
            def enum_callback(hwnd, lparam):
                class_name = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_name, 256)
                
                ctrl_id = self.user32.GetDlgCtrlID(hwnd)
                
                rect = wintypes.RECT()
                self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                
                text_buffer = ctypes.create_unicode_buffer(256)
                self.user32.GetWindowTextW(hwnd, text_buffer, 256)
                
                # WM_GETTEXT
                WM_GETTEXT = 0x000D
                WM_GETTEXTLENGTH = 0x000E
                
                text_len = self.user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
                wm_text = ""
                
                if text_len > 0:
                    buffer = ctypes.create_unicode_buffer(text_len + 1)
                    self.user32.SendMessageW(hwnd, WM_GETTEXT, text_len + 1, buffer)
                    wm_text = buffer.value
                
                all_descendants.append({
                    'hwnd': hwnd,
                    'depth': depth,
                    'id': ctrl_id,
                    'class': class_name.value,
                    'text': text_buffer.value,
                    'wm_text': wm_text,
                    'left': rect.left,
                    'top': rect.top,
                    'width': rect.right - rect.left,
                    'height': rect.bottom - rect.top
                })
                
                # 재귀
                recursive_find(hwnd, depth + 1)
                
                return True
            
            enum_proc_inner = EnumChildWindowsProc(enum_callback)
            self.user32.EnumChildWindows(parent_hwnd, enum_proc_inner, 0)
        
        # SysTabControl32부터 시작
        recursive_find(tab_control_hwnd, 0)
        
        print(f"  → 총 {len(all_descendants)}개 하위 컨트롤 발견\n")
        
        # 3. 모든 컨트롤 출력
        print(f"3) 모든 하위 컨트롤 목록:\n")
        
        for i, desc in enumerate(all_descendants):
            indent = "  " * desc['depth']
            print(f"[{i}] {indent}depth={desc['depth']}, ID={desc['id']}, Class={desc['class']}")
            print(f"{indent}위치: ({desc['left']}, {desc['top']}), 크기: ({desc['width']}, {desc['height']})")
            print(f"{indent}GetWindowText: '{desc['text']}'")
            
            if desc['wm_text']:
                print(f"{indent}WM_GETTEXT: '{desc['wm_text']}'")
            
            print()
        
        # 4. 계좌번호 형식 필터링
        print(f"\n4) 계좌번호 형식 필터링...\n")
        
        account_candidates = []
        
        for desc in all_descendants:
            for text in [desc['text'], desc['wm_text']]:
                if text and len(text) >= 10:
                    # 숫자-숫자 형식 또는 12자리 이상 숫자
                    clean_text = text.replace('-', '').replace('|', '').replace(' ', '')
                    if '-' in text or (len(clean_text) >= 12 and clean_text[:12].isdigit()):
                        account_candidates.append(desc)
                        
                        indent = "  " * desc['depth']
                        print(f"{indent}✓ [depth={desc['depth']}] ID={desc['id']}, Class={desc['class']}")
                        print(f"{indent}  텍스트: '{text}'")
                        print(f"{indent}  위치: ({desc['left']}, {desc['top']}), 크기: ({desc['width']}, {desc['height']})")
                        print()
                        break
        
        if account_candidates:
            print(f"\n✅ {len(account_candidates)}개 계좌번호 후보 발견!")
        else:
            print(f"\n❌ 계좌번호 형식을 찾을 수 없습니다!")
        
        return []

    def select_account(self, account_number):
        """계좌번호 선택"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        if not PYWINAUTO_AVAILABLE:
            print("❌ pywinauto가 설치되지 않았습니다!")
            return False
        
        print(f"\n계좌번호 선택: {account_number}")
        
        try:
            # 1. 주문창 연결
            app = Application(backend="win32").connect(handle=self.hwnd)
            order_window = app.window(handle=self.hwnd)
            
            # 2. 드롭다운 버튼 찾기 (위치로 구분)
            all_buttons = order_window.descendants(control_id=3785, class_name="Button")
            
            dropdown_btn = None
            for btn in all_buttons:
                rect = btn.rectangle()
                if 110 <= rect.left <= 112 and 147 <= rect.top <= 149:
                    dropdown_btn = btn
                    break
            
            if not dropdown_btn:
                print(f"❌ 드롭다운 버튼을 찾을 수 없습니다!")
                return False
            
            # 3. 드롭다운 열기
            dropdown_btn.click()
            time.sleep(1.5)
            
            # 4. 계좌 목록에서 선택
            all_combos = order_window.descendants(class_name="ComboBox")
            all_listboxes = order_window.descendants(class_name="ListBox")
            
            # ComboBox에서 선택
            for combo in all_combos:
                try:
                    if combo.is_visible():
                        items = combo.item_texts()
                        for i, item in enumerate(items):
                            # 계좌번호 매칭 (앞 12자리)
                            if item.startswith(account_number[:12]):
                                print(f"  ✓ 계좌 발견: {item}")
                                combo.select(i)
                                time.sleep(0.5)
                                print(f"  ✅ 계좌 선택 완료!")
                                return True
                except:
                    continue
            
            # ListBox에서 선택
            for listbox in all_listboxes:
                try:
                    if listbox.is_visible():
                        items = listbox.item_texts()
                        for i, item in enumerate(items):
                            if item.startswith(account_number[:12]):
                                print(f"  ✓ 계좌 발견: {item}")
                                listbox.select(i)
                                time.sleep(0.5)
                                print(f"  ✅ 계좌 선택 완료!")
                                return True
                except:
                    continue
            
            # ESC로 드롭다운 닫기
            order_window.type_keys("{ESC}")
            print(f"  ❌ 계좌번호를 찾을 수 없습니다: {account_number}")
            return False
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False


    def select_account(self, account_number):
        """계좌번호 선택"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        if not PYWINAUTO_AVAILABLE:
            print("❌ pywinauto가 설치되지 않았습니다!")
            return False
        
        print(f"\n계좌번호 선택: {account_number}")
        
        try:
            # 1. 주문창 연결
            app = Application(backend="win32").connect(handle=self.hwnd)
            order_window = app.window(handle=self.hwnd)
            
            # 2. 드롭다운 버튼 클릭
            dropdown_btn = order_window.child_window(control_id=3785, class_name="Button")
            dropdown_btn.click()
            time.sleep(1)
            
            # 3. 계좌 목록 가져오기
            all_combos = order_window.descendants(class_name="ComboBox")
            all_listboxes = order_window.descendants(class_name="ListBox")
            
            # ComboBox에서 선택
            for combo in all_combos:
                try:
                    if combo.is_visible():
                        items = combo.item_texts()
                        for i, item in enumerate(items):
                            # 계좌번호 매칭 (앞 12자리)
                            if item.startswith(account_number[:12]):
                                print(f"  ✓ 계좌 발견: {item}")
                                combo.select(i)
                                time.sleep(0.5)
                                print(f"  ✅ 계좌 선택 완료!")
                                return True
                except:
                    continue
            
            # ListBox에서 선택
            for listbox in all_listboxes:
                try:
                    if listbox.is_visible():
                        items = listbox.item_texts()
                        for i, item in enumerate(items):
                            if item.startswith(account_number[:12]):
                                print(f"  ✓ 계좌 발견: {item}")
                                listbox.select(i)
                                time.sleep(0.5)
                                print(f"  ✅ 계좌 선택 완료!")
                                return True
                except:
                    continue
            
            # ESC로 드롭다운 닫기
            order_window.type_keys("{ESC}")
            print(f"  ❌ 계좌번호를 찾을 수 없습니다: {account_number}")
            return False
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False

def show_menu():
    """테스트 메뉴 출력"""
    print("\n" + "="*50)
    print("해외주식 주문창(6100) 테스트 메뉴")
    print("="*50)
    print("1. 해외주식 주문 창 열기")
    print("2. 현재가 가져오기")
    print("3. 수량 입력")
    print("4. 종목코드 변경")  
    print("5. 비밀번호 입력")
    print("6. 계좌번호 목록 조회") 
    print("a. 매수 탭 이동")
    print("b. 매도 탭 이동")
    print("c. 정정 탭 이동")
    print("d. 취소 탭 이동")
    print("0. 종료")
    print("="*50)

def main():
    """메인 테스트 프로그램"""
    print("해외주식 주문창(6100) 테스트 프로그램")
    print("2초 후 시작합니다...\n")
    time.sleep(2)
    
    # 윈도우 초기화
    order_window = OverseasOrderWindow()
    
    # 주문 창 열기
    if not order_window.open_popup_and_capture():
        print("\n❌ 초기화 실패!")
        return
    
    print("\n✅ 초기화 완료!\n")
    
    # 메뉴 루프
    while True:
        show_menu()
        choice = input("\n선택: ").strip().lower()
        
        if choice == '0':
            print("프로그램을 종료합니다.")
            break
        
        print(f"\n2초 후 실행됩니다...")
        time.sleep(2)
        
        if choice == '1':
            print("\n[1. 해외주식 주문 창 열기]")
            if order_window.open_popup_and_capture():
                print("✅ 주문 창 열기 성공!")
            else:
                print("❌ 주문 창 열기 실패!")
            
        elif choice == '2':
            print("\n[2. 현재가 가져오기]")
            order_window.get_current_price()
            
        elif choice == '3':
            print("\n[3. 수량 입력]")
            quantity = input("입력할 수량: ").strip()
            if quantity.isdigit():
                order_window.set_quantity(int(quantity))
            else:
                print("❌ 숫자를 입력해주세요!")

        elif choice == '4':
            print("\n[4. 종목코드 변경]")
            stock_code = input("입력할 종목코드: ").strip()
            if stock_code:
                order_window.set_stock_code(stock_code)
            else:
                print("❌ 종목코드를 입력해주세요!")
        
        elif choice == '5':  # 추가!
            print("\n[5. 비밀번호 입력]")
            password = input("입력할 비밀번호: ").strip()
            if password:
                order_window.set_password(password)
            else:
                print("❌ 비밀번호를 입력해주세요!")

        elif choice == '6':  # 추가!
            print("\n[6. 계좌번호 목록 조회]")
            accounts = order_window.get_account_list()
            if accounts:
                print("\n[조회된 계좌 목록]")
                for acc in accounts:
                    print(f"  계좌번호: {acc['account_number']}")
                    
        elif choice == 'a':
            print("\n[a. 매수 탭 이동]")
            order_window.switch_tab("매수")
            
        elif choice == 'b':
            print("\n[b. 매도 탭 이동]")
            order_window.switch_tab("매도")
            
        elif choice == 'c':
            print("\n[c. 정정 탭 이동]")
            order_window.switch_tab("정정")
            
        elif choice == 'd':
            print("\n[d. 취소 탭 이동]")
            order_window.switch_tab("취소")
        
        else:
            print("❌ 잘못된 선택입니다!")
        
        time.sleep(1)

if __name__ == "__main__":
    main()