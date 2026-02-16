import ctypes
from ctypes import wintypes
import time
import win32api
import win32con
import win32gui
import win32ui
import re
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import os
import json  
from pywinauto import Application
from pywinauto.controls.win32_controls import ComboBoxWrapper

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PYWINAUTO_AVAILABLE = True


class OverseasOrderWindow:
    """해외주식 주문창(6100) 제어 클래스"""
    
    def __init__(self):
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.hwnd = None
        self.main_hwnd = None
        
        # 탭 설정
        self.tab_start_offset = 18
        self.tab_gap = 36
        self.tab_names = ["매수", "매도", "정정", "취소"]
        
        # 핸들 캐시
        self.tab_hwnd = None
        
        # 계좌 목록 캐시
        self._cached_accounts = None

        # JSON 파일 읽기
        json_path = r'C:\thirds\config\hts_controls.json'
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 공통 컨트롤
        self.window_name = config['window']['name']
        self.account_combo_id = config['controls']['common']['account_combo']['id']
        self.password_id = config['controls']['common']['password']['id']
        self.stock_code_id = config['controls']['common']['stock_code']['id']
        self.tab_control_id = config['controls']['common']['order_type_tab']['id']
        
        # 매수 탭 컨트롤
        self.buy_order_type_id = config['controls']['buy']['order_type']['id']
        self.buy_button_id = config['controls']['buy']['buy_button']['id']
        self.buy_quantity_id = config['controls']['buy']['quantity']['id']
        self.buy_price_id = config['controls']['buy']['limit_price']['id']
        
        # 매도 탭 컨트롤
        self.sell_order_type_id = config['controls']['sell']['order_type']['id']
        self.sell_quantity_id = config['controls']['sell']['quantity']['id']
        self.sell_price_id = config['controls']['sell']['limit_price']['id']
        
    def open_popup_and_capture(self):
        """Ctrl+] 눌러서 팝업 열고 HWND 캡처"""
        print(f"\n{'='*60}")
        print("[1단계] 6100 팝업 열기")
        print(f"{'='*60}")
        
        # 기존 팝업이 있으면 닫기
        if self.hwnd:
            self.user32.PostMessageW(self.hwnd, 0x0010, 0, 0)
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
        
        # 창 활성화
        self.user32.ShowWindow(main_hwnd, 9)
        time.sleep(0.3)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(main_hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.5)
        
        rect = wintypes.RECT()
        self.user32.GetWindowRect(main_hwnd, ctypes.byref(rect))
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        self.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.2)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.1)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.5)
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        # Ctrl+] 입력
        VK_CONTROL = 0x11
        VK_OEM_6 = 0xDD
        
        self.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.15)
        self.user32.keybd_event(VK_OEM_6, 0, 0, 0)
        time.sleep(0.15)
        self.user32.keybd_event(VK_OEM_6, 0, 2, 0)
        time.sleep(0.15)
        self.user32.keybd_event(VK_CONTROL, 0, 2, 0)
        
        print("✓ Ctrl+] 입력 완료")
        time.sleep(2.5)

        self.find_child_window(main_hwnd)

        if not self.hwnd:
            print("✗ 창을 찾을 수 없습니다")
            return False

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

    def switch_tab(self, tab_name):
        """탭 전환 (매수/매도/정정/취소)"""
        if tab_name not in self.tab_names:
            print(f"❌ 잘못된 탭 이름: {tab_name}")
            return False
        
        if not self.tab_hwnd:
            print(f"1) 탭 컨트롤 찾는 중...")
            tab_hwnd = self._find_control_by_id(self.tab_control_id)
            
            if not tab_hwnd:
                print(f"❌ 탭 컨트롤(ID: {self.tab_control_id})을 찾을 수 없습니다!")
                return False
            
            # 클래스 확인
            class_name = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(tab_hwnd, class_name, 256)
            if 'Tab' not in class_name.value:
                print(f"❌ 탭 컨트롤이 아닙니다: {class_name.value}")
                return False
            
            self.tab_hwnd = tab_hwnd
            print(f"✓ 탭 컨트롤 찾음: HWND={hex(tab_hwnd)}")
        
        target_index = self.tab_names.index(tab_name)
        
        rect = win32gui.GetWindowRect(self.tab_hwnd)
        x_offset = self.tab_start_offset + (self.tab_gap * target_index)
        click_x = rect[0] + x_offset
        click_y = rect[1] + 10
        
        print(f"2) {tab_name} 탭 클릭 위치: ({click_x}, {click_y})")
        
        current_pos = win32api.GetCursorPos()
        win32api.SetCursorPos((click_x, click_y))
        time.sleep(0.2)
        
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        time.sleep(0.3)
        win32api.SetCursorPos(current_pos)
        
        TCM_GETCURSEL = 0x130B
        new_tab = win32gui.SendMessage(self.tab_hwnd, TCM_GETCURSEL, 0, 0)
        
        if new_tab == target_index:
            print(f"✅ {tab_name} 탭으로 전환 성공!")
            return True
        else:
            print(f"⚠ {tab_name} 탭 클릭 완료 (확인: 인덱스={new_tab}, 목표={target_index})")
            return True
        
            # ==================== 공통 메서드 ====================
    
    def set_stock_code(self, stock_code):
        """종목코드 입력 (매수/매도 공통)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        print(f"1) 종목코드 입력창(ID: {self.stock_code_id}) 찾는 중...")
        stock_code_hwnd = self._find_control_by_id(self.stock_code_id)
        
        if not stock_code_hwnd:
            print(f"❌ 종목코드 입력창을 찾을 수 없습니다!")
            return False
        
        print(f"✓ 종목코드 입력창 찾음: HWND={hex(stock_code_hwnd)}")
        
        # 주문 창 활성화
        print("2) 주문 창 활성화 중...")
        self.user32.ShowWindow(self.hwnd, 9)
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # 좌표 계산 및 클릭
        rect = wintypes.RECT()
        self.user32.GetWindowRect(stock_code_hwnd, ctypes.byref(rect))
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        print(f"3) 종목코드 입력창 클릭: ({center_x}, {center_y})")
        
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        ctypes.windll.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.3)
        
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.3)
        
        # Ctrl+A로 전체 선택
        print("4) 기존 텍스트 전체 선택 (Ctrl+A)")
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
        
        # 종목코드 입력
        print(f"5) 종목코드 입력: {stock_code}")
        for char in stock_code.upper():
            vk_code = ord(char)
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        time.sleep(0.3)
        
        # Enter 입력
        print("6) Enter 입력")
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        
        # 마우스 원위치
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        print(f"✅ 종목코드 입력 완료: {stock_code}")
        return True

    def _find_control_by_id(self, control_id):
        """내부: Control ID로 컨트롤 찾기"""
        found_hwnd = None
        
        def enum_callback(hwnd, lparam):
            nonlocal found_hwnd
            if self.user32.GetDlgCtrlID(hwnd) == control_id:
                found_hwnd = hwnd
                return False
            return True
        
        EnumChildWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumChildWindows(self.hwnd, EnumChildWindowsProc(enum_callback), 0)
        
        return found_hwnd

    # ==================== 매수 전용 메서드 ====================
    
    def get_buy_price(self):
        """[매수] 현재가 가져오기"""
        return self._get_price("매수", self.buy_price_id)

    def set_buy_quantity(self, quantity):
        """[매수] 수량 입력"""
        return self._set_quantity("매수", self.buy_quantity_id, quantity)

    # ==================== 매도 전용 메서드 ====================
    
    def get_sell_price(self):
        """[매도] 현재가 가져오기"""
        return self._get_price("매도", self.sell_price_id)

    def set_sell_quantity(self, quantity):
        """[매도] 수량 입력"""
        return self._set_quantity("매도", self.sell_quantity_id, quantity)

    # ==================== 내부 공통 로직 ====================
    
    def _get_price(self, tab_name, control_id):
        """내부: 현재가 가져오기 공통 로직"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return None
        
        # 1. 탭 이동
        print(f"1) {tab_name} 탭으로 이동 중...")
        if not self.switch_tab(tab_name):
            return None
        time.sleep(0.5)
        
        # 2. 컨트롤 찾기
        print(f"2) [{tab_name}] 현재가 입력창(ID: {control_id}) 찾는 중...")
        found_hwnd = self._find_control_by_id(control_id)
        
        if not found_hwnd:
            print(f"❌ [{tab_name}] 현재가 입력창을 찾을 수 없습니다!")
            return None
        
        print(f"✓ [{tab_name}] 현재가 입력창 찾음: HWND={hex(found_hwnd)}")
        
        # 3. 텍스트 가져오기
        print(f"3) [{tab_name}] 현재가 가져오는 중...")
        buffer = ctypes.create_unicode_buffer(256)
        self.user32.SendMessageW(found_hwnd, 0x000D, 256, buffer)
        text = buffer.value
        
        if text:
            print(f"📊 [{tab_name}] 현재가: {text}")
        else:
            print(f"❌ [{tab_name}] 현재가를 가져올 수 없습니다!")
        
        return text

    def _set_quantity(self, tab_name, control_id, quantity):
        """내부: 수량 입력 공통 로직"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        # 1. 탭 이동
        print(f"1) {tab_name} 탭으로 이동 중...")
        if not self.switch_tab(tab_name):
            return False
        time.sleep(0.3)
        
        # 2. 컨트롤 찾기
        print(f"2) [{tab_name}] 수량 입력창(ID: {control_id}) 찾는 중...")
        quantity_hwnd = self._find_control_by_id(control_id)
        
        if not quantity_hwnd:
            print(f"❌ [{tab_name}] 수량 입력창을 찾을 수 없습니다!")
            return False
        
        print(f"✓ [{tab_name}] 수량 입력창 찾음: HWND={hex(quantity_hwnd)}")
        
        # 3. 주문 창 활성화
        print(f"3) 주문 창 활성화 중...")
        self.user32.ShowWindow(self.hwnd, 9)
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # 4. 수량 입력창 좌표 가져오기
        rect = wintypes.RECT()
        self.user32.GetWindowRect(quantity_hwnd, ctypes.byref(rect))
        
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        print(f"4) [{tab_name}] 수량 입력창 클릭: ({center_x}, {center_y})")
        
        # 마우스 위치 저장
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        # 5. 수량 입력창 클릭
        ctypes.windll.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.3)
        
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.3)
        
        # 6. Ctrl+A로 전체 선택
        print(f"5) 기존 수량 전체 선택 (Ctrl+A)")
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
        
        # 7. 수량 입력
        print(f"6) [{tab_name}] 수량 입력: {quantity}")
        quantity_str = str(quantity)
        for char in quantity_str:
            vk_code = ord(char)
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        time.sleep(0.3)
        
        # 마우스 원위치
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        print(f"✅ [{tab_name}] 수량 입력 성공: {quantity}")
        return True
    
    # ==================== OCR 헬퍼 메서드 ====================
    def _capture_printwindow(self, hwnd, rect):
        """PrintWindow로 특정 영역 캡처"""
        l, t, r, b = rect
        w, h = r - l, b - t
        
        if w <= 0 or h <= 0:
            return None
        
        PW_RENDERFULLCONTENT = 0x00000002
        hdc = win32gui.GetWindowDC(hwnd)
        
        try:
            srcdc = win32ui.CreateDCFromHandle(hdc)
            memdc = srcdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(srcdc, w, h)
            memdc.SelectObject(bmp)
            
            res = ctypes.windll.user32.PrintWindow(hwnd, memdc.GetSafeHdc(), PW_RENDERFULLCONTENT)
            
            bmpinfo = bmp.GetInfo()
            bmpstr = bmp.GetBitmapBits(True)
            img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), 
                                   bmpstr, 'raw', 'BGRX', 0, 1)
            
            try: memdc.DeleteDC()
            except: pass
            try: srcdc.DeleteDC()
            except: pass
            try: win32gui.DeleteObject(bmp.GetHandle())
            except: pass
            
            return img if res != 0 else None
            
        finally:
            try: win32gui.ReleaseDC(hwnd, hdc)
            except: pass

    
    def _preprocess_for_account(self, img):
        """계좌번호 인식을 위한 이미지 전처리"""
        if img is None:
            return None
        
        # 그레이스케일 변환
        gray = img.convert('L')
        
        # 크기 확대 (작은 텍스트 가독성 향상)
        scale = max(1, int(2000 / max(img.size)))
        if scale > 1:
            gray = gray.resize((gray.width * scale, gray.height * scale), Image.LANCZOS)
        
        # 선명도 향상
        gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        gray = ImageOps.autocontrast(gray, cutoff=1)
        
        # 이진화
        gray = gray.point(lambda p: 0 if p < 180 else 255)
        
        return gray
    
    def _ocr_account_from_image(self, img):
        """이미지에서 계좌번호 추출"""
        if img is None:
            return None
        
        proc = self._preprocess_for_account(img)
        
        # OCR 수행 (숫자와 하이픈만 인식)
        config = '--psm 7 -c tessedit_char_whitelist=0123456789-'
        txt = pytesseract.image_to_string(proc, config=config)
        txt = txt.strip()
        
        # 계좌번호 패턴 매칭 (예: 1234-5678-90)
        ACCOUNT_RE = re.compile(r'\b\d{4}-\d{4}-\d{2}\b')
        m = ACCOUNT_RE.search(txt)
        
        return m.group() if m else None

    # ==================== 비밀번호 입력 ====================
    
    def set_password(self, password):
        """비밀번호 입력 (매수/매도 공통)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        print(f"1) 비밀번호 입력창(ID: {self.password_id}) 찾는 중...")
        password_hwnd = self._find_control_by_id(self.password_id)
        
        if not password_hwnd:
            print(f"❌ 비밀번호 입력창을 찾을 수 없습니다!")
            return False
        
        print(f"✓ 비밀번호 입력창 찾음: HWND={hex(password_hwnd)}")
        
        # 주문 창 활성화
        print("2) 주문 창 활성화 중...")
        self.user32.ShowWindow(self.hwnd, 9)
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # 좌표 계산 및 클릭
        rect = wintypes.RECT()
        self.user32.GetWindowRect(password_hwnd, ctypes.byref(rect))
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        print(f"3) 비밀번호 입력창 클릭: ({center_x}, {center_y})")
        
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        ctypes.windll.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.3)
        
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.3)
        
        # Ctrl+A로 전체 선택
        print("4) 기존 비밀번호 전체 선택 (Ctrl+A)")
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)
        
        # 비밀번호 입력
        print(f"5) 비밀번호 입력 중... (****)")
        for char in password:
            vk_code = ord(char)
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        time.sleep(0.3)
        
        # 마우스 원위치
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        print(f"✅ 비밀번호 입력 완료")
        return True

    def get_account_list(self, force_refresh=False):
        """계좌번호 목록 조회 (OCR 방식 - 캐싱)
        
        Args:
            force_refresh: True면 캐시 무시하고 재조회
        """
        # ========== 캐시 확인 ==========
        if self._cached_accounts is not None and not force_refresh:
            print(f"\n[계좌 목록 - 캐시 사용]")
            print(f"{'='*60}")
            print(f"✅ 캐시된 계좌 목록 (총 {len(self._cached_accounts)}개)")
            for idx, acc in enumerate(self._cached_accounts):
                print(f"   [{idx}] {acc}")
            print(f"{'='*60}")
            return self._cached_accounts
        # ================================
        
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return []
        
        print(f"\n[계좌번호 목록 조회 - OCR]")
        print(f"{'='*60}")
        
        # ... 기존 조회 로직 동일 ...
        # (드롭다운 열기 → 캡처 → OCR → 드롭다운 닫기)
        
        print(f"1) 계좌 콤보박스(ID: {self.account_combo_id}) 찾는 중...")
        combo_hwnd = self._find_control_by_id(self.account_combo_id)
        
        if not combo_hwnd:
            print(f"❌ 계좌 콤보박스를 찾을 수 없습니다!")
            return []
        
        print(f"✓ 계좌 콤보박스 찾음: HWND={hex(combo_hwnd)}")
        
        rect = win32gui.GetWindowRect(combo_hwnd)
        print(f"2) 콤보박스 절대 좌표: {rect}")
        
        # ========== 드롭다운 열기 ==========
        print(f"3) 드롭다운 열기...")
        
        self.user32.ShowWindow(self.hwnd, 9)
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        dropdown_x = rect[2] - 10
        dropdown_y = (rect[1] + rect[3]) // 2
        
        print(f"   드롭다운 버튼 클릭: ({dropdown_x}, {dropdown_y})")
        
        self.user32.SetCursorPos(dropdown_x, dropdown_y)
        time.sleep(0.3)
        
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(1.0)
        
        print(f"   ✓ 드롭다운 열림")
        
        # ========== 캡처 및 OCR ==========
        print(f"\n4) 데스크톱 캡처 (드롭다운 영역)...")
        
        capture_rect = (
            rect[0],
            rect[1],
            rect[2] + 150,
            rect[3] + 200
        )
        
        print(f"   캡처 영역 (절대 좌표): {capture_rect}")
        
        accounts = []
        
        try:
            from PIL import ImageGrab
            
            img = ImageGrab.grab(bbox=capture_rect)
            
            if img:
                print(f"   ✓ 캡처 성공 (크기: {img.size})")
                
                img.save("debug_dropdown_original.png")
                print(f"   (원본: debug_dropdown_original.png)")
                
                proc = self._preprocess_for_account(img)
                proc.save("debug_dropdown_processed.png")
                print(f"   (전처리: debug_dropdown_processed.png)")
                
                print(f"\n5) OCR 수행...")
                config = '--psm 6 -c tessedit_char_whitelist=0123456789-'
                txt = pytesseract.image_to_string(proc, config=config)
                
                print(f"\n   OCR 원본 텍스트:")
                print(f"   {'-'*50}")
                for line in txt.split('\n'):
                    if line.strip():
                        print(f"   | {line}")
                print(f"   {'-'*50}")
                
                # 계좌번호 패턴 찾기
                ACCOUNT_RE = re.compile(r'\d{4}-\d{4}-\d{2}')
                matches = ACCOUNT_RE.findall(txt)
                
                if matches:
                    # 중복 제거 + 정렬
                    accounts = sorted(list(set(matches)))
                    print(f"\n   ✓ OCR 성공: {len(matches)}개 매칭 → 중복 제거 후 {len(accounts)}개")
                else:
                    print(f"\n   ⚠ 계좌번호 패턴 없음")
            else:
                print(f"   ❌ 캡처 실패")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # ========== 드롭다운 닫기 ==========
        print(f"\n6) 드롭다운 닫기 (ESC)...")
        win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.3)
        
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        # ========== 결과 및 캐싱 ==========
        print(f"\n{'='*60}")
        if accounts:
            # ========== 캐시 저장 ==========
            self._cached_accounts = accounts
            # ==============================
            
            print(f"✅ 계좌 목록 조회 성공 (총 {len(accounts)}개)")
            for idx, acc in enumerate(accounts):
                print(f"   [{idx}] {acc}")
            print(f"   → 캐시에 저장됨")  # ← 추가
        else:
            print(f"❌ 계좌번호를 찾을 수 없습니다!")
            print(f"   → debug_dropdown_original.png 확인 필요")
        
        return accounts
    
    def select_account_by_number(self, account_number):
        """계좌번호로 선택 (키보드 방식)"""
        if not self.hwnd:
            print("❌ 주문 창을 찾을 수 없습니다!")
            return False
        
        print(f"\n[계좌 선택: {account_number}]")
        print(f"{'='*60}")
        
        # 1. 캐시된 계좌 목록 사용
        print(f"1) 계좌 목록 확인...")
        
        if self._cached_accounts is None:
            print(f"   ⚠ 캐시 없음, 조회 시작...")
            accounts = self.get_account_list()
        else:
            print(f"   ✓ 캐시 사용: {self._cached_accounts}")
            accounts = self._cached_accounts
        
        if not accounts:
            print(f"❌ 계좌 목록을 가져올 수 없습니다!")
            return False
        
        # 2. 목표 계좌 인덱스 찾기
        try:
            target_index = accounts.index(account_number)
            print(f"✓ 목표 계좌: {account_number} (정렬 목록에서 인덱스 {target_index})")
        except ValueError:
            print(f"❌ 계좌 '{account_number}'를 목록에서 찾을 수 없습니다!")
            print(f"   사용 가능한 계좌: {accounts}")
            return False
        
        # 3. 콤보박스 찾기
        print(f"\n2) 계좌 콤보박스 찾는 중...")
        combo_hwnd = self._find_control_by_id(self.account_combo_id)
        
        if not combo_hwnd:
            print(f"❌ 계좌 콤보박스를 찾을 수 없습니다!")
            return False
        
        print(f"✓ 계좌 콤보박스 찾음: HWND={hex(combo_hwnd)}")
        
        rect = win32gui.GetWindowRect(combo_hwnd)
        
        # ========== 현재 선택 확인 (드롭다운 열기 전!) ==========
        print(f"\n3) 현재 선택된 계좌 확인 (드롭다운 닫힌 상태)...")
        
        current_index = 0
        
        try:
            from PIL import ImageGrab
            
            # 콤보박스 자체 캡처 (닫힌 상태)
            time.sleep(0.2)
            combo_img = ImageGrab.grab(bbox=(rect[0], rect[1], rect[2], rect[3]))
            
            current_account = self._ocr_account_from_image(combo_img)
            print(f"   현재 선택: {current_account}")
            
            if current_account:
                try:
                    current_index = accounts.index(current_account)
                    print(f"   현재 인덱스: {current_index}")
                except ValueError:
                    print(f"   ⚠ 현재 계좌를 목록에서 찾을 수 없음, 0으로 가정")
                    current_index = 0
            else:
                print(f"   ⚠ OCR 실패, 0으로 가정")
                current_index = 0
            
        except Exception as e:
            print(f"   ⚠ 현재 계좌 확인 실패: {e}, 0으로 가정")
            current_index = 0
        
        # ========== 이미 선택된 경우 ==========
        print(f"\n4) 선택 필요 여부 확인...")
        print(f"   현재 인덱스: {current_index} → 목표 인덱스: {target_index}")
        
        if current_index == target_index:
            print(f"   → 이미 선택된 계좌입니다!")
            print(f"✅ 계좌 선택 완료: {account_number}")
            print(f"\n{'='*60}")
            return True
        
        # ========== 주문 창 활성화 ==========
        print(f"\n5) 주문 창 활성화...")
        self.user32.ShowWindow(self.hwnd, 9)
        time.sleep(0.2)
        
        VK_MENU = 0x12
        self.user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        self.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        self.user32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.3)
        
        # ========== 콤보박스 클릭 (포커스) ==========
        print(f"\n6) 콤보박스에 포커스...")
        
        old_pos = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(old_pos))
        
        center_x = (rect[0] + rect[2]) // 2
        center_y = (rect[1] + rect[3]) // 2
        
        self.user32.SetCursorPos(center_x, center_y)
        time.sleep(0.2)
        
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.3)
        
        print(f"✓ 콤보박스 클릭 완료")
        
        # ========== 드롭다운 열기 ==========
        print(f"\n7) 드롭다운 열기...")
        dropdown_x = rect[2] - 10
        dropdown_y = center_y
        
        self.user32.SetCursorPos(dropdown_x, dropdown_y)
        time.sleep(0.2)
        
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.5)
        
        print(f"✓ 드롭다운 열림")
        
        # ========== 키보드로 이동 ==========
        print(f"\n8) 키보드로 계좌 선택...")
        print(f"   현재 인덱스: {current_index} → 목표 인덱스: {target_index}")
        
        # HOME 키로 맨 위로
        print(f"   → HOME 키 (맨 위로)")
        win32api.keybd_event(win32con.VK_HOME, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_HOME, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.3)
        
        # DOWN 키로 목표 인덱스까지 이동
        if target_index > 0:
            print(f"   → DOWN 키 {target_index}번")
            for i in range(target_index):
                win32api.keybd_event(win32con.VK_DOWN, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_DOWN, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.15)
        
        # ENTER로 선택 확정
        print(f"   → ENTER 키 (선택 확정)")
        time.sleep(0.2)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        
        print(f"✓ 키보드 조작 완료")
        
        # 마우스 원위치
        self.user32.SetCursorPos(old_pos.x, old_pos.y)
        
        # ========== 선택 확인 ==========
        print(f"\n9) 선택 결과 확인...")
        time.sleep(0.3)
        
        try:
            verify_img = ImageGrab.grab(bbox=(rect[0], rect[1], rect[2], rect[3]))
            selected = self._ocr_account_from_image(verify_img)
            
            if selected == account_number:
                print(f"✅ 계좌 선택 성공: {selected}")
                print(f"\n{'='*60}")
                return True
            else:
                print(f"⚠ 선택 확인 실패")
                print(f"   예상: {account_number}")
                print(f"   실제: {selected}")
                print(f"\n{'='*60}")
                return False
        except Exception as e:
            print(f"⚠ 선택 확인 중 오류: {e}")
        
        print(f"\n{'='*60}")
        return True

    
    def select_account(self, account_index):
        """계좌 선택 (인덱스 방식 - 래퍼)"""
        # 계좌 목록 조회
        accounts = self.get_account_list()
        
        if not accounts:
            print("❌ 계좌 목록을 가져올 수 없습니다!")
            return False
        
        if account_index < 0 or account_index >= len(accounts):
            print(f"❌ 잘못된 인덱스: {account_index} (0~{len(accounts)-1} 사용)")
            return False
        
        # 계좌번호로 선택
        target_account = accounts[account_index]
        return self.select_account_by_number(target_account)


    
def show_menu():
    """메뉴 출력"""
    print("\n" + "="*60)
    print("해외주식 주문창(6100) 테스트 메뉴")
    print("="*60)
    print("1. 해외주식 주문 창 열기")
    print("")
    print("[공통]")
    print("2. 종목코드 변경")
    print("3. 비밀번호 입력")
    print("4. 계좌번호 목록 조회")
    print("5. 계좌 선택")
    print("")
    print("[매수]")
    print("6. [매수] 현재가 가져오기")
    print("7. [매수] 수량 입력")
    print("")
    print("[매도]")
    print("8. [매도] 현재가 가져오기")
    print("9. [매도] 수량 입력")
    print("")
    print("[탭 전환]")
    print("10. 매수 탭으로 이동")
    print("11. 매도 탭으로 이동")
    print("12. 취소 탭으로 이동")
    print("")
    print("0. 종료")
    print("="*60)

def main():
    """메인 함수"""
    print("="*60)
    print("해외주식 주문창(6100) 테스트 프로그램")
    print("="*60)
    print("2초 후 시작합니다...")
    time.sleep(2)
    
    order_window = OverseasOrderWindow()
    
    while True:
        show_menu()
        choice = input("\n메뉴 선택: ").strip()
        
        if choice == '0':
            print("\n프로그램을 종료합니다.")
            break
            
        elif choice == '1':
            print("\n[1. 해외주식 주문 창 열기]")
            if order_window.open_popup_and_capture():
                print("✅ 주문 창 열기 성공!")
            else:
                print("❌ 주문 창 열기 실패!")
        
        elif choice == '2':
            print("\n[2. 종목코드 변경]")
            stock_code = input("종목코드 입력 (예: TSLA): ").strip().upper()
            if stock_code:
                order_window.set_stock_code(stock_code)
            else:
                print("❌ 종목코드를 입력해주세요!")
        
        elif choice == '3':
            print("\n[3. 비밀번호 입력]")
            password = input("비밀번호 입력 (4자리): ").strip()
            if password and len(password) == 4 and password.isdigit():
                order_window.set_password(password)
            else:
                print("❌ 4자리 숫자를 입력해주세요!")
        
        elif choice == '4':
            print("\n[4. 계좌번호 목록 조회]")
            accounts = order_window.get_account_list()
            if accounts:
                print(f"\n📋 총 {len(accounts)}개의 계좌:")
                for idx, acc in enumerate(accounts):
                    print(f"   [{idx}] {acc}")
        
        elif choice == '5':
            print("\n[5. 계좌 선택]")
            # 먼저 목록 표시
            accounts = order_window.get_account_list()
            if accounts:
                acc_idx = input(f"선택할 계좌 번호 (0~{len(accounts)-1}): ").strip()
                if acc_idx.isdigit() and 0 <= int(acc_idx) < len(accounts):
                    order_window.select_account(int(acc_idx))
                else:
                    print("❌ 올바른 번호를 입력해주세요!")
            else:
                print("❌ 계좌 목록을 먼저 조회해주세요!")
        
        elif choice == '6':
            print("\n[6. [매수] 현재가 가져오기]")
            price = order_window.get_buy_price()
            if price:
                print(f"✅ [매수] 현재가: {price}")
        
        elif choice == '7':
            print("\n[7. [매수] 수량 입력]")
            quantity = input("입력할 수량: ").strip()
            if quantity.isdigit():
                order_window.set_buy_quantity(int(quantity))
            else:
                print("❌ 올바른 숫자를 입력해주세요!")
        
        elif choice == '8':
            print("\n[8. [매도] 현재가 가져오기]")
            price = order_window.get_sell_price()
            if price:
                print(f"✅ [매도] 현재가: {price}")
        
        elif choice == '9':
            print("\n[9. [매도] 수량 입력]")
            quantity = input("입력할 수량: ").strip()
            if quantity.isdigit():
                order_window.set_sell_quantity(int(quantity))
            else:
                print("❌ 올바른 숫자를 입력해주세요!")
        
        elif choice == '10':
            print("\n[10. 매수 탭으로 이동]")
            if order_window.switch_tab("매수"):
                print("✅ 매수 탭 이동 성공!")
            else:
                print("❌ 매수 탭 이동 실패!")
        
        elif choice == '11':
            print("\n[11. 매도 탭으로 이동]")
            if order_window.switch_tab("매도"):
                print("✅ 매도 탭 이동 성공!")
            else:
                print("❌ 매도 탭 이동 실패!")

        elif choice == '12':  # ← 추가!
            print("\n[12. 취소 탭으로 이동]")
            if order_window.switch_tab("취소"):
                print("✅ 취소 탭 이동 성공!")
            else:
                print("❌ 취소 탭 이동 실패!")
        
        else:
            print("❌ 잘못된 선택입니다. 다시 선택해주세요.")
        
        # 다음 작업 전 대기
        time.sleep(0.5)


if __name__ == "__main__":
    main()