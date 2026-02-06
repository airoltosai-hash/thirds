import ctypes
import time
import win32api
import win32con
import win32gui
from ctypes import wintypes

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
        """현재가 가져오기"""
        if not self.hwnd:
            print("❌ 현재가 입력창을 찾을 수 없습니다!")
            return None
        
        # 현재가 입력창의 ID가 3930인 경우
        self.price_edit_hwnd = self.user32.FindWindowExW(self.hwnd, None, None, None)
        if not self.price_edit_hwnd:
            print("❌ 현재가 입력창을 찾을 수 없습니다!")
            return None
        
        WM_GETTEXT = 0x000D
        buffer_size = 256
        buffer = win32gui.PyMakeBuffer(buffer_size)
        length = win32gui.SendMessage(self.price_edit_hwnd, WM_GETTEXT, buffer_size, buffer)
        text = buffer[:length * 2].decode('utf-16le', errors='ignore')
        
        print(f"📊 현재가: {text}")
        return text

# ============================================
# 테스트 메뉴
# ============================================

def show_menu():
    """테스트 메뉴 출력"""
    print("\n" + "="*50)
    print("해외주식 주문창(6100) 테스트 메뉴")
    print("="*50)
    print("1. 해외주식 주문 창 열기")
    print("2. 현재가 가져오기")
    print("3. 수량 입력")
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