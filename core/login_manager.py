# core/login_managers.py
import keyboard
from pynput.keyboard import Controller, Key
import time
import ctypes
import os
import json
from ctypes import wintypes

# Keyboard 임포트
kb = Controller()

# WinAPI 임포트
user32 = ctypes.windll.user32

# ===== 함수 미리 선언 =====
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
FindWindowW = user32.FindWindowW
FindWindowExW = user32.FindWindowExW
EnumWindows = user32.EnumWindows
EnumChildWindows = user32.EnumChildWindows

from core.win_input import (
    user32, VK_MENU, press_vk, release_vk,
    send_enter, send_ctrl_h, send_unicode_char
)

SETTINGS_FILE = "config/settings.json" 

WM_SETTEXT = 0x000C
WM_CHAR    = 0x0102

def load_hts_config():
    """ 설정 파일에서 HTS 로그인 창 설정 로드 """
    if not os.path.exists(SETTINGS_FILE):
        return {}
    
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
            return settings.get("main_settings", {})
    except:
        return {}
    
HTS_CONFIG = load_hts_config()

def find_login_top_hwnd(timeout_sec: float = 3.0):
    """
    로그인 창을 찾습니다. (Notepad 테스트용)
    """

    # 1) 고전/일반 : 최상위 클래스 'Notepad'
    hwnd = FindWindowW("Notepad", None)
    if hwnd:
        return hwnd
    
    # 2) Windows 11 스타일 : 최상위 'ApplicationFrameWindow' 안에 'Notepad' 자식
    frame = FindWindowW("ApplicationFrameWindow", None)
    if frame:
        child = FindWindowExW(frame, 0, "Notepad", None)
        if child:
            return child

    # 3) 타이틀 부분일치로 찾기 (로케일 대응)
    patterns = ["Notepad", "메모장", "제목 없음", "Untitled", "Windows 메모장"]
    found = wintypes.HWND(0)

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
    def _enum_proc(h, lp):
        buf = ctypes.create_unicode_buffer(256)
        GetWindowTextW(h, buf, 256)
        if any(p in buf.value for p in patterns):
                found.value = h
                return False
        return True

    t0 = time.time()
    while time.time() - t0 < timeout_sec and not found.value:
        EnumWindows(_enum_proc, 0)
        if found.value:
            break
        time.sleep(0.1)

    return found.value if found.value else None

def _find_login_edit_child(hwnd_top) -> int | None:
    """ Notepad 테스트용 - Edit 필드 찾기 """

    # 1) 고전
    edit = FindWindowExW(hwnd_top, 0, "Edit", None)
    if edit:
        return edit
    
    # 2) Win11 최신
    edit = FindWindowExW(hwnd_top, 0, "RichEditD2D", None)
    if edit:
        return edit

    # 3) 모든 자식 열거해서 'Edit/RichEdit' 포함 찾기
    found = ctypes.wintypes.HWND(0)

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.c_void_p)
    def _enum_child(h, lp):
        buf = ctypes.create_unicode_buffer(256)
        GetClassNameW(h, buf, 256)
        name = buf.value
        if("Edit" in name) or ("RichEdit" in name):
            found.value = h
            return False
        return True
    
    EnumChildWindows(hwnd_top, _enum_child, 0)
    return found.value if found.value else None

def find_cert_selection_popup(timeout_sec: float = 10.0) -> int | None:
    """
    인증서 선택 팝업을 찾습니다.

    Returns : 팝업 창의 핸들 또는 None
    """

    t0 = time.time()

    while time.time() - t0 < timeout_sec:
        # 인증서 선택 팝업의 특징적인 타이틀 패턴
        cert_patterns = [
            "인증서 선택",
            "Certificate Selection",
            "인증서",
            "Cert",
            "anN2"
        ]

        found = wintypes.HWND(0)

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
        def enum_proc(hwnd, lp):
            try:
                # 창 타이틀 가져오기
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf_title = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf_title, length + 1)
                    title = buf_title.value

                    # 패턴 매칭
                    if any(pattern in title for pattern in cert_patterns):
                        # 클래스명 확인 (Dialog)
                        buf_class = ctypes.create_unicode_buffer(256)
                        GetClassNameW(hwnd, buf_class, 256)
                        class_name = buf_class.value
                        
                        if "#32770" in class_name:
                            found.value = hwnd
                            return False
                        
            except:
                pass

            return True
        
        EnumWindows(enum_proc, 0)

        if found.value:
            print(f"[DEBUG] 인증서 팝업 찾은: 0x{found.value:X}")
            return found.value
        
        time.sleep(0.3)

    return None

def select_first_certificate(hwnd_cert_popup) -> bool:
    """
    인증서 팝업에서 첫 번째 인증서를 선택합니다.

    returns : 성공 여부
    """

    try:
        print("[INFO] 첫 번째 인증서 선택 중...")

        # ListBox 찾기
        list_hwnd = FindWindowExW(hwnd_cert_popup, 0, "ListBox", None)

        if not list_hwnd:
            # SysListView32 시도
            list_hwnd = FindWindowExW(hwnd_cert_popup, 0, "SysListView32", None)

        if not list_hwnd:
            print("[ERROR] 인증서 목록을 찾을 수 없습니다.")
            return False

        print(f"[DEBUG] 목록 제어 찾음: 0x{list_hwnd:X}")

        # 첫 번째 항목 선택
        # LB_SETCURSEL = 목록 항목 선택 메시지
        LB_SETCURSEL = 0x0186
        SendMessageW = user32.SendMessageW

        SendMessageW(list_hwnd, LB_SETCURSEL, 0, 0) # 첫 번째 항목 선택
        time.sleep(0.3)

    except Exception as e:
        print(f"[ERROR] 인증서 선택 실패: {e}")
        return False

def click_cert_confirm_button(hwnd_cert_popup) -> bool:
    """
    인증서 선택 팝업의 "확인" 버튼을 클릭합니다.
    
    Returns : 성공 여부
    """
    try:
        print("[INFO] 확인 버튼 클릭 중...")

        # "확인" 버튼 찾기
        confirm_patterns = ["확인", "OK", "선택", "Select"]

        found_button = wintypes.HWND(0)

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
        def enum_button(hwnd, lp):
            try:
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf_text = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf_text, length +1)
                    text = buf_text.value

                    # 버튼 텍스트 확인
                    if any(pattern in text for pattern in confirm_patterns):
                        # 버튼인지 확인
                        buf_class = ctypes.create_unicode_buffer(256)
                        GetClassNameW(hwnd, buf_class, 256)
                        class_name = buf_class.value

                        if "Button" in class_name:
                            found_button.value = hwnd
                            return False
            except:
                pass

            return True
        EnumChildWindows(hwnd_cert_popup, enum_button, 0)

        if not found_button.value:
            print("[ERROR] 확인 버튼을 찾을 수 없습니다.")
            return False
        
        print(f"[DEBUG] 확인 버튼 찾음: 0x{found_button.value:X}")

        # 버튼 클릭
        # BM_CLICK = 버튼 클릭 메시지
        BM_CLICK = 0x00F5
        SendMessageW = user32.SendMessageW

        SendMessageW(found_button.value, BM_CLICK, 0, 0)
        time.sleep(0.5)

        print("[SUCCESS] 확인 버튼 클릭 완료")
        return True
    
    except Exception as e:
        print(f"[ERROR] 버튼 클릭 실패: {e}")
        return False

def select_certificate_auto() -> bool:
    """
    인증서 선택 팝업에서 자동으로 첫 번째 인증서를 선택하고 확인합니다.
    
    Returns : 성공여부
    """

    try:
        print("[INFO] 인증서 자동 선택 시작...")

        # 1. 인증서 팝업 찾기
        print("[STEP 1] 인증서 선택 팝업 찾는 중...")
        hwnd_cert = find_cert_selection_popup(timeout_sec=10.0)

        if not hwnd_cert:
            print("[ERROR] 인증서 팝업을 찾을 수 없습니다.")
            return False
        
        print(f"[SUCCESS] 인증서 팝업 찾음: 0x{hwnd_cert:X}")

        # 2. 포그라운드로 가져오기
        print("[STEP2] 팝업 최상위로 설정 중...")
        SW_RESTORE = 9
        user32.ShowWindow(hwnd_cert, SW_RESTORE)
        time.sleep(0.2)

        press_vk(VK_MENU)
        user32.SetForegroundWindow(hwnd_cert)
        release_vk(VK_MENU)
        time.sleep(0.3)

        # 3. 첫 번째 인증서 선택
        # print("[STEP 3] 첫 번째 인증서 선택 중...")
        # if not select_first_certificate(hwnd_cert):
        #     print("[WARNING] 인증서 선택 실패, 계속 진행...")

        # 4. 확인 버튼 클릭
        # print("[STEP 4] 확인 버튼 클릭 중...")
        # if not click_cert_confirm_button(hwnd_cert):
        #    print("[ERROR] 확인 버튼 클릭 실패")
        #     return False
        
        # print("[SUCCESS] 인증서 자동 선택 완료!")
        return True
    
    except Exception as e:
        print(f"[ERROR] 인증서 선택 자동화 실패: {e}")
        return False

def find_cert_password_input_hwnd(timeout_sec: float = 10.0) -> int | None:
    """
    인증서 비밀번호 입력 창을 찾습니다.

    Args : timeout_sec : 최대 대기 시간(초)
    Returns : 비밀번호 입력 창의 핸들 또는 None
    """

    t0 = time.time()

    while time.time() - t0 < timeout_sec:
        # 비밀번호 입력 팝업의 특징적인 타이틀 패턴
        password_patterns = [
            "비밀번호", "암호", "Password", "패스워드",
            "인증", "Authenticate", "Certification"
        ]

        found = wintypes.HWND(0)

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
        def enum_proc(hwnd, lp):
            try:
                # 창 타이틀 가져오기
                length = GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf_title = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf_title, length + 1)
                    title = buf_title.value

                    # 패턴 매칭
                    if any(pattern in title for pattern in password_patterns):
                        # 클래스명도 확인 ( Dialog 또는 #32770)
                        buf_class = ctypes.create_unicode_buffer(256)
                        GetClassNameW(hwnd, buf_class, 256)
                        class_name = buf_class.value

                        if "#32770" in class_name or "Dialog" in class_name:
                            found.value = hwnd
                            return False
                        
            except:
                pass

            return True
        EnumWindows(enum_proc, 0)

        if found.value:
            print(f"[DEBUG] 비밀번호 입력 창 찾은: 0x{found.value:X}")
            return found.value
        
        time.sleep(0.3)

    return None

def find_password_input_field(hwnd_parent) -> int | None:
    """
    비밀번호 입력 창 내에서 실제 입력 필드(Edit 컨트롤)를 찾습니다.
    
    Args : hwnd_parent : 비밀번호 입력 창의 핸들
    Returns : Edit 필드의 핸들 또는 None
    """

    # 전략 1: Edit 클래스 직접 찾기
    edit_hwnd = FindWindowExW(hwnd_parent, 0, "Edit", None)
    if edit_hwnd:
        print(f"[DEBUG] Edit 필드 찾음: 0x{edit_hwnd:X}")
        return edit_hwnd
    
    # 전략 2: 모든 자식 위젯 열거
    found_edits = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
    def enum_child(hwnd, lp):
        try:
            buf_class = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, buf_class, 256)
            class_name = buf_class.value

            if "Edit" in class_name or "Input" in class_name:
                found_edits.append(hwnd)

        except:
            pass

        return True
    EnumChildWindows(hwnd_parent, enum_child, 0)

    if found_edits:
        # 여러 Edit 필드가 있으면 마지막 하나 (보통 입력 필드)
        result = found_edits[-1]
        print(f"[DEBUG] 입력 필드 찾음:  0x{result:X} (총 {len(found_edits)}개 중 마지막)")
        return result
    
    return None

def type_password_in_login(password: str, return_detail: bool = False):
    """
    HTS 인증서 비밀번호를 입력합니다.

    절차:
    1. 비밀번호 입력 창 찾기 (타이틀 기반)
    2. 입력 필드 찾기 (Edit 컨트롤)
    3. 비밀번호 입력 + Enter 키 전송

    Args:
        password : 입력할 비밀번호
        return_detail: True면 (ok, code, msg)반환

    Returns:
        bool 또는 (ok, code, msg) 튜플
    """

    try:
        # 1. 비밀번호 입력 창 찾기 (최대 10초 대기)
        print("[INFO] 비밀번호 입력 창을 찾는 중...")
        hwnd_pwd_window = find_cert_password_input_hwnd(timeout_sec=10.0)

        if not hwnd_pwd_window:
            result = (False, "NO_PASSWORD_WINDOW", "인증서 비밀번호 입력 창을 찾을 수 없습니다.")
            print(f"[ERROR] {result[2]}")
            return result if return_detail else False
        
        print(f"[SUCCESS 비밀번호 입력 창 찾음: 0x{hwnd_pwd_window}]")

        # 2. 포그라운드로 가져오기
        SW_RESTORE = 9
        user32.ShowWindow(hwnd_pwd_window, SW_RESTORE)
        time.sleep(0.3)

        # ALT 트릭으로 포커스 설정
        press_vk(VK_MENU)
        user32.SetForegroundWindow(hwnd_pwd_window)
        release_vk(VK_MENU)
        time.sleep(0.3)

        # 3. 입력 필드 찾기
        print("[INFO] 입력 필드를 찾는 중...")
        hwnd_input = find_password_input_field(hwnd_pwd_window)

        if not hwnd_input:
            result = (False, "NO_INPUT_FIELD", "비밀번호 입력 필드를 찾을 수 없습니다.")
            print(f"[ERROR] {result[2]}")
            return result if return_detail else False
        
        print(f"[SUCCESS] 입력 필드 찾은: 0x{hwnd_input:X}")

        # 4. 비밀번호 입력
        print(f"[INFO] 비밀번호 입력 중... (길이: {len(password)}자)")
        SendMessageW = user32.SendMessageW

        # 기존 텍스트 제거
        SendMessageW(hwnd_input, WM_SETTEXT, 0, "")
        time.sleep(0.1)
        
        # 비밀번호 입력
        print(password)
        for char in password:
            kb.type(char)
            time.sleep(0.05)
        time.sleep(0.5)
        
        # 5. Enter 키 전송
        print("[INFO] Enter 키 전송 중...")
        keyboard.press_and_release('enter')
        time.sleep(0.5)

        result = (True, "LOGIN_SUCCESS", "비밀번호 입력이 완료되었습니다.")
        print(f"[SUCCESS] {result[2]}")
        
        return result if return_detail else True
    
    except Exception as e:
        result = (False, "EXCEPTION", f"예외 발생: {str(e)}")
        print(f"[ERROR] {result[2]}")
        return result if return_detail else False

auto_type_password_in_login = type_password_in_login

def type_password_to_login(password: str) -> bool:
    """ Notepad 테스트용 """
    hwnd_top = find_login_top_hwnd(timeout_sec=3.0)
    if not hwnd_top:
        return False

    # 포그라운드 전환 (ALT 트릭)
    SW_RESTORE = 9
    user32.ShowWindow(hwnd_top, SW_RESTORE)
    press_vk(VK_MENU)
    user32.SetForegroundWindow(hwnd_top)
    release_vk(VK_MENU)
    
    edit_hwnd = _find_login_edit_child(hwnd_top)
    if not edit_hwnd:
        return False
    
    SendMessageW = user32.SendMessageW
    SendMessageW(edit_hwnd, WM_SETTEXT, 0, password)
    SendMessageW(edit_hwnd, WM_CHAR, 0x0D, 0)
    return True



