# /main.py

import ctypes
import tkinter as tk
import tkinter.font as font
import tkinter.messagebox as messagebox
import json
import os
import datetime
import re
import subprocess
from core.win_input import(
    user32,   # 포커스/FindWindow 등에 사용
    VK_MENU,  # ALT 트릭
    send_enter,
    send_ctrl_h,
    send_unicode_text,
    press_vk, release_vk
)
from core.login_manager import(
    type_password_to_login,
    auto_type_password_in_login
)
from core.hts_engine import HtsAutomation

# Setting 값 저장
SETTINGS_FILE = "config/settings.json"

# Windows API 상수
SW_MINIMIZE = 6

# 편집권한 프로그램 주소
SERVICE_ACCOUNT_EMAIL = "thirds@thirds-485008.iam.gserviceaccount.com"

class AutoLoginSettingsWindow(tk.Toplevel):
    def __init__(self, parent_cell):
        super().__init__(parent_cell)
        self.parent_cell = parent_cell
        self.title("자동로그인 설정")
        self.configure(bg='black')
        self.geometry("360x200")

        self.transient(parent_cell.winfo_toplevel())
        self.grab_set()

        frame = tk.Frame(self, bg='black', padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # 시작시간
        tk.Label(frame, text="시작시간", fg="white", bg="black").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_start = tk.Entry(frame, bg="gray20", fg="white", insertbackground="white")
        self.entry_start.grid(row=0, column=1, sticky="we", padx=5)
        default_start = self.parent_cell.task_data.get("start_time") or "00:00:00"
        self.entry_start.insert(0, default_start)

        # 인증서 비밀번호
        tk.Label(frame, text="인증서 비밀번호", fg="white", bg="black").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_cert = tk.Entry(frame, bg="gray20", fg="white", insertbackground="white", show="*")
        self.entry_cert.grid(row=1, column=1, sticky="we", padx=5)
        self.entry_cert.insert(0, self.parent_cell.task_data.get("cert_password", ""))

        frame.grid_columnconfigure(1, weight=1)

        # 버튼
        btns = tk.Frame(frame, bg="black", pady=10)
        btns.grid(row=2, column=0, columnspan=2)
        tk.Button(btns, text="저장", width=10, command=self.save_and_close).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="닫기", width=10, command=self.destroy).pack(side=tk.LEFT, padx=8)

        # 중앙 배치
        self.update_idletasks()
        px, py = self.master.winfo_rootx(), self.master.winfo_rooty()
        pw, ph = self.master.winfo_width(), self.master.winfo_height()
        ww, wh = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - ww)//2}+{py + (ph - wh)//2}")

    def save_and_close(self):
        start = self.entry_start.get().strip() or "00:00:00"
        cert = self.entry_cert.get()

        self.parent_cell.task_data["start_time"] = start
        self.parent_cell.task_data["cert_password"] = cert
        
        # 그리도 반영
        self.parent_cell.render_from_data()

        # 영구 저장
        if self.parent_cell.on_change_callback:
            self.parent_cell.on_change_callback()
        
        if hasattr(self.parent_cell, "restart_auto_login_schedule"):
            self.parent_cell.restart_auto_login_schedule()

        messagebox.showinfo("저장", "자동로그인 설정이 저장되었습니다.", parent=self)
        self.destroy()

class TaskSettingsWindow(tk.Toplevel):
    def __init__(self, parent_cell):
        super().__init__(parent_cell)
        self.parent_cell = parent_cell
        self.title("작업 설정")
        self.geometry("400x300")
        self.configure(bg='black')

        # 모달 처리 및 부모 창 중앙에 위치
        self.transient(parent_cell.winfo_toplevel())
        self.grab_set()

        main_frame = tk.Frame(self, padx=15, pady=15, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 입력 필드들
        field = ["닉네임", "시트이름", "시작시간", "종료시간", "간격(초)"]
        keys = ["nickname", "sheet_name", "start_time", "end_time", "interval"]
        self.entries = {}

        for i, (field, key) in enumerate(zip(field, keys)):
            label = tk.Label(main_frame, text=f"{field}:", fg="white", bg="black")
            label.grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(main_frame, bg="gray20", fg="white", insertbackground="white")
            entry.grid(row=i, column=1, sticky="we", padx=5)

            # 기본값 결정
            default = self.parent_cell.task_data.get(key, "")
            if key in ("start_time", "end_time"):
                default = default or "00:00:00"
            elif key == "interval":
                default = str(default or "0")
            
            entry.insert(0, default)
            self.entries[key] = entry

        main_frame.grid_columnconfigure(1, weight=1)

        # 저장/닫기 버튼
        btn_frame = tk.Frame(main_frame, bg="black", pady=20)
        btn_frame.grid(row=len(field), column=0, columnspan=2)

        save_btn = tk.Button(btn_frame, text="저장", width=10, command=self.save_and_close)
        save_btn.pack(side=tk.LEFT, padx=10)
        close_btn = tk.Button(btn_frame, text="닫기", width=10, command=self.destroy)
        close_btn.pack(side=tk.LEFT, padx=10)

        # 중앙 배치
        self.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        x = parent_x + (parent_width - win_width) // 2
        y = parent_y + (parent_height - win_height) // 2
        self.geometry(f"+{x}+{y}")

    def save_and_close(self):
        # 1. GridCell 의 task_data를 업데이트
        for key, entry in self.entries.items():
            val = entry.get()
            if key == "interval":
                try:
                    val = int(val)
                except:
                    val = 0
            if key in ("start_time", "end_time") and not val:
                val = "00:00:00"
            self.parent_cell.task_data[key] = val
            
        self.parent_cell.render_from_data()

        # 상태에 따라 예약 / 사이클 관리
        if self.parent_cell.task_data.get("status") == "활성":
            # 시작 / 종료 예약 재설정 ( 요구사항 : 시작시간이 이미 지났으면 시작하지 않음 )
            self.parent_cell._schedule_start_stop()
        else:
            # 비활성 : 모든 예약 / 타이머 정리
            self.parent_cell.stop_all_schedules()

        # 변경 데이터 파일에 저장
        if self.parent_cell.on_change_callback:
            self.parent_cell.on_change_callback() 


        # 2. GridCell의 닉네임 라벨을 업데이트
        self.parent_cell.text_left.config(text=self.parent_cell.task_data.get("nickname", "신규작업"))

        
        # 3. (중료) TestApp에서도 변경사항을 알려서 전체 데이터를 저장하게 해야 함 (나중에 구현)
        messagebox.showinfo("저장", "설정이 임시 저장 되었습니다.", parent=self)

        self.destroy()

class ActionMenuPopup(tk.Toplevel):
    def __init__(self, parent_cell, x, y):
        super().__init__(parent_cell)
        self.parent_cell = parent_cell

        # 창 테두리 제거 및 위치 설정
        self.overrideredirect(True)
        self.geometry(f"+{x}+{y}")

        # 메뉴가 열리면 다른 곳 클릭 못하게
        # self.grab_set()

        # 메뉴 프레임
        menu_frame = tk.Frame(self, bg="gray30", highlightbackground="gray50", highlightthickness=1)
        menu_frame.pack()

        if self.parent_cell.task_data.get("type") == "auto_login":
            actions = ["바로 실행", "준비"]
            commands = [
                # 바로 실행 -> 상태  ⭕ + 알림
                lambda: [self.parent_cell.execute_auto_login(), self.destroy()],
                # 준비 -> 상태 ❌
                lambda: [self.parent_cell.set_status("Ready", persist=False), self.destroy()],
            ]


        else:
            actions = ["바로 실행", "활성화", "비활성화", "삭제", "정산"]
            commands = [
                lambda: [self.parent_cell.quick_run(), self.destroy()],
                lambda: [self.parent_cell.set_status("활성"), self.destroy()],
                lambda: [self.parent_cell.set_status("비활성"), self.destroy()],
                lambda: [self.parent_cell.delete(), self.destroy()], 
                lambda: [self.parent_cell.perform_settlement(), self.destroy()],
            ]

        for action, command in zip(actions, commands):
            btn = tk.Button(menu_frame, text=action, bg="gray30", fg="white", activebackground="gray50",
                            relief="flat", anchor="w", command=lambda c=command: c()) # 메뉴 닫고 명령 실행
            btn.pack(fill=tk.X, padx=10, pady=5)

        # 메뉴 바깥을 클릭하면 닫히도록 바인딩
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set() # 팝업에 포커스 설정

    def show_info_and_close(self, title, message):
        messagebox.showinfo(title, message, parent=self.parent_cell)
        self.destroy()

class SettingWindow(tk.Toplevel):
    def __init__(self, parent, settings_data, save_callback):
        super().__init__(parent)

        self.settings_data = settings_data
        self.save_callback = save_callback

        self.title("Settings")

        # 부모 창 이 항상 위에 떠 있도록 설정
        self.transient(parent.winfo_toplevel())

        # 이 창이 모든 이벤트를 독점 하도록 설정 (모달)
        self.grab_set()

        self.geometry("400x250")
        self.resizable(False, False)
        #self.overrideredirect(True) # 윗줄 숨김

        self.update_idletasks() # 위젯 배치 끝내고 실제 크기 계산

        # 부모 창의 위치와 크기 얻기
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # 팝업(자기자신) 크기 얻기
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        
        # 중앙 위치 계산
        x = parent_x + (parent_width - win_width) // 2
        y = parent_y + (parent_height - win_height) // 2

        self.geometry(f"+{x}+{y}")


        # 색상 설정
        self.configure(bg='black')
        label_fg = 'white'
        entry_bg = 'gray20'
        entry_fg = 'white'
        btn_bg = 'gray30'
        btn_fg = 'white'
        btn_active_bg = 'gray50'
        btn_active_fg = 'white'

        # 메인 프레임 패딩
        main_frame = tk.Frame(self, padx=10, pady=10, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 메리츠 HTS 경로 입력
        label_meritz = tk.Label(main_frame, text="메리츠 HTS 경로:", fg=label_fg, bg='black')
        label_meritz.grid(row=0, column=0, sticky="w")
        self.entry_meritz = tk.Entry(main_frame, width=40, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        self.entry_meritz.grid(row=0, column=1, sticky="we", pady=5)

        # 구글시트 경로 입력
        label_google = tk.Label(main_frame, text="구글시트 경로:", fg=label_fg, bg='black')
        label_google.grid(row=1, column=0, sticky="w")
        self.entry_google = tk.Entry(main_frame, width=40, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        self.entry_google.grid(row=1, column=1, sticky="we", pady=5)

        # 구글시트 (편집권한, 테스트)
        btn_google_frame = tk.Frame(main_frame, bg='black')
        btn_google_frame.grid(row=2, column=1, sticky="w", pady=(0,20))

        btn_edit_perm = tk.Button(btn_google_frame, text="편집 권한", width=10, bg=btn_bg, fg=btn_fg,
                                activebackground=btn_active_bg, activeforeground=btn_active_fg, command=self.on_edit_permission)
        btn_edit_perm.pack(side=tk.LEFT, padx=5)
        btn_test = tk.Button(btn_google_frame, text="테스트", width=10, command=self.on_test)
        btn_test.pack(side=tk.LEFT, padx=5)

        # 하단버튼 (저장, 닫기)
        btn_bottom_frame = tk.Frame(main_frame, bg='black')
        btn_bottom_frame.grid(row=3, column=0, columnspan=2, pady=(0,10))

        btn_save = tk.Button(btn_bottom_frame, text="저장", width=12, bg=btn_bg, fg=btn_fg,
                            activebackground=btn_active_bg, activeforeground=btn_active_fg, command=self.on_save_settings)
        btn_save.pack(side=tk.LEFT, padx=10)
        btn_close = tk.Button(btn_bottom_frame, text="닫기", width=12, bg=btn_bg, fg=btn_fg,
                            activebackground=btn_active_bg, activeforeground=btn_active_fg, command=self.destroy)
        btn_close.pack(side=tk.LEFT, padx=10)

        self.entry_meritz.insert(0, self.settings_data.get("meritz_hts_path", ""))
        self.entry_google.insert(0, self.settings_data.get("google_sheet_path", ""))

    @staticmethod
    def _extract_spreadsheet_id(url_or_id: str) -> str:
        # 전체 URL이면 ID 추출, ID만 오면 그대로
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url_or_id or "")
        if m:
            return m.group(1)
        return (url_or_id or "").strip()

    @staticmethod
    def _check_edit_permission(sa_json_path: str, spreadsheet_url_or_id: str) -> bool:
        # Google Drive API로 capabilities.canEdit 확인 (비파괴)
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = Credentials.from_service_account_file(sa_json_path, scopes=scopes)
        service = build("drive", "v3", credentials=creds)
        file_id = SettingWindow._extract_spreadsheet_id(spreadsheet_url_or_id)
        file = service.files().get(fileId=file_id, fields="capabilities").execute()
        caps = file.get("capabilities", {})
        return bool(caps.get("canEdit", False))
        
    
    def on_save_settings(self):

        # 전달받은 딕셔너리를 직접 수정
        self.settings_data["meritz_hts_path"] = self.entry_meritz.get()
        self.settings_data["google_sheet_path"] = self.entry_google.get()
        
        # 저장 콜백 함수를 호출하여 TestApp이 파일에 저장하도록 함
        self.save_callback()
        
        messagebox.showinfo("저장 완료", "설정이 파일에 저장되었습니다.", parent=self)
        self.destroy() # 창 닫기

    def on_edit_permission(self):
        # 서비스 계정 이메일을 클립보드로 복사하고 안내
        sa_email = SERVICE_ACCOUNT_EMAIL
        try:
            self.clipboard_clear()
            self.clipboard_append(sa_email)
            messagebox.showinfo(
                "편집 권한",
                f"{sa_email}\n\n프로그램 주소가 클립보드로 복사되었습니다.\n구글시트 편집권한에 프로그램 주소를 등록해주세요.",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("편집 권한", f"클립보드 복사 중 오류: {e}", parent=self)
    
    def on_test(self):
        # settings에 저장된 구글시트 경로와 서비스 계정 JSON 경로를 사용
        url = (self.settings_data.get("google_sheet_path", "") or "").strip()
        sa_json = (self.settings_data.get("google_service_account_json", "") or "").strip()

        print("[DEBUG] google_sheet_path:", url)
        print("[DEBUG] google_service_account_json:", sa_json, "exists:", os.path.exists(sa_json))

        if not url:
            messagebox.showwarning("테스트", "구글시트 경로를 먼저 설정하세요.", parent=self)
            return
        if not sa_json or not os.path.exists(sa_json):
            messagebox.showwarning(
                "테스트",
                "서비스 계정 JSON 경로가 유효하지 않습니다.\nsettings.json의 main_settings.google_service_account_json을 설정하세요.",
                parent=self
            )
            return
        
        try:
            can_edit = SettingWindow._check_edit_permission(sa_json, url)
            messagebox.showinfo("테스트", "편집 권한 확인: 편집 가능" if can_edit else "편집 권한 확인: 편집 불가", parent=self)
        except ModuleNotFoundError:
            messagebox.showerror(
                "테스트",
                "필요 라이브러리가 없습니다.\n\npip install google-auth google-api-python-client",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("테스트", f"확인 중 오류: {e}", parent=self)
        

class HamburgerMenu(tk.Frame):
    def __init__(self, parent, app, width=300, height=700, **kwargs):
        super().__init__(parent, width=width, height=height, bg='gray20', **kwargs)
        self.app = app # TestApp 인스턴스 저장

        self.width = width
        self.height = height
        self.expanded = False
        self.place(x=-self.width, y=0, relheight=1)

        # 상단 정보
        top_frame = tk.Frame(self, bg='black')
        top_frame.pack(fill=tk.X, pady=10)

        icon = tk.Label(top_frame, text="★", font=("Arial", 24), bg='black', fg='white')
        icon.pack(side=tk.LEFT, padx=10)
        title = tk.Label(top_frame, text="Thirds v1.0", font=("Arial", 16), bg='black', fg='white')
        title.pack(side=tk.LEFT, padx=10)

        # 메뉴 버튼
        btn_home = tk.Button(self, text="Home", font=("Arial", 14), bg='gray30', fg='white', command=self.slide_out)
        btn_home.pack(fill=tk.X, padx=10, pady=5)

        btn_settings = tk.Button(self, text="Settings", font=("Arial", 14), bg='gray30', fg='white', command=self.open_settings)
        btn_settings.pack(fill=tk.X, padx=10, pady=5)
        
        btn_about = tk.Button(self, text="About", font=("Arial", 14), bg='gray30', fg='white')
        btn_about.pack(fill=tk.X, padx=10, pady=5)

    def open_settings(self):
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        self.settings_window = SettingWindow(
            parent=self,
            settings_data=self.app.settings["main_settings"],
            save_callback=self.app.save_all_settings
        )

    def toggle(self):
        if self.expanded:
            self.slide_out()
        else:
            self.slide_in()
            
    def slide_in(self):
        self.lift() # 최상위로 올리기
        x = self.winfo_x()
        
        if x < 0:
            x = min(x + 20, 0)
            self.place(x=x, y=0)
            self.after(10, self.slide_in)
        else:
            self.expanded = True
            

    def slide_out(self):
        x = self.winfo_x()
        if x > -self.width:
            x = max(x - 20, -self.width)
            self.place(x=x, y=0)
            self.after(10, self.slide_out)
        else:
            self.expanded = False

class GridCell(tk.Frame):
    def __init__(self, parent, task_data, delete_callback, on_change_callback=None):
        super().__init__(parent, bg='black')
        self.configure(highlightbackground="gray", highlightthickness=1)
        self.task_data = task_data

        self.delete_callback = delete_callback # 삭제를 위한 콜백 함수
        self.on_change_callback = on_change_callback # 저장을 위한 콜백 함수

        # 1 영역
        self.text_left=tk.Label(self, text=self.task_data.get("nickname", "신규작업"), anchor='w', fg='white', bg='black')
        self.text_left.grid(row=0, column=0, sticky="w", padx=5)
        

        # 3영역
        self.text_right=tk.Label(self, text="Right Text", anchor='e', fg='white', bg='black')
        self.text_right.grid(row=0, column=2, sticky="e", padx=5)

        # 4,5,6영역
        self.status=tk.Label(self, text="대기 중", anchor='w', fg='white', bg='black')
        self.status.grid(row=1, column=0, columnspan=3, sticky="we", padx=5, pady=5)        

        # 7영역
        self.info_frame = tk.Frame(self, bg='black')
        self.info_frame.grid(row=2, column=0, sticky="w", padx=5)
    
        if self.task_data.get("type") == "auto_login":
            
            # 상태 라벨 생성
            self.lbl_status = tk.Label(self.info_frame, text="", bg="black", fg="white", font=("Segoe UI Emoji", 10))
            self.lbl_status.pack(side=tk.LEFT, padx=(0,12))

            # 런타임 전용 상태 (파일에 저장하지 않음)
            self.runtime_status = "Ready"

            # 상태 표시
            self._update_auto_login_status_label()

            # 추가 : 오류 상태 플래그
            self._login_error_active = False

            # 초기 문구는 '대기 중'
            self._set_login_info("대기 중", fg="white")

            # 스케쥴 ID 초기화
            self._auto_login_after_id = None
            
            # 시작시간 스케줄링
            self.restart_auto_login_schedule()


        else:
            # 일반 작업 분기 초기화
            self._cycle_running = False     # 타이머 반복 실행 중 여부
            self._timer_id = None           # 타이머 after id
            self._start_after_id = None     # 시작시간 예약 id
            self._stop_after_id = None      # 종료시간 예약 id

            self.ICON_TIMER = "⏳"
            self.ICON_START = "⏰"
            self.ICON_END = "🌙"
            self.ICON_INT = "🔄"
            emoji_font = ("Segoe UI Emoji", 10)

            self.lbl_countdown = tk.Label(self.info_frame, text="", bg="black", fg="white", font=emoji_font)
            self.lbl_countdown.pack(side=tk.LEFT, padx=(0,12))

            self.lbl_start = tk.Label(self.info_frame, text="", bg="black", fg="white", font=emoji_font)
            self.lbl_start.pack(side=tk.LEFT, padx=(0,12))

            self.lbl_end = tk.Label(self.info_frame, text="", bg="black", fg="white", font=emoji_font)
            self.lbl_end.pack(side=tk.LEFT, padx=(0,12))

            self.lbl_interval = tk.Label(self.info_frame, text="", bg="black", fg="white", font=emoji_font)
            self.lbl_interval.pack(side=tk.LEFT, padx=(0,12))
        
        self.render_from_data()

        # 9영역
        self.btn_frame=tk.Frame(self, bg='black')
        self.btn_frame.grid(row=2, column=2, sticky="e", padx=5)
        self.btn1=tk.Button(self.btn_frame, text="🔎", width=3, command=self.open_task_settings)
        self.btn1.pack(side=tk.LEFT, padx=(0,5))
        self.btn2=tk.Button(self.btn_frame, text="⋯", width=3, command=self.open_action_menu)
        self.btn2.pack(side=tk.LEFT)

        # 빈 영역 없이 column 1 공간 확보 (사용 미사용 판단 필요)
        self.grid_columnconfigure(1, weight=1)    


    # 4 영역 라벨(정보 라인) 갱신 헬퍼
    def _set_info(self, text: str, fg="white"):
        if hasattr(self, "status"):
            self.status.config(text=text, fg=fg)

    def stop_all_schedules(self):
        # 일반 작업 타이머/예약 취소
        self.cancel_cycle(reset_label=True)
        self._cancel_start_stop()

        # 자동 로그인 예약 취소
        if self.task_data.get("type") == "auto_login":
            self.cancel_auto_login_schedule()

    def execute_trade(self):
        # 매수/매도 실행 (테스트:alert)
        messagebox.showinfo("실행", f"{self.task_data.get('nickname','작업')} 매수/매도 실행!", parent=self.winfo_toplevel())

    def perform_settlement(self):
        # 정산 실행 (테스트:alert)
        messagebox.showinfo("정산", f"{self.task_data.get('nickname','작업')} 정산 실행!", parent=self.winfo_toplevel())

    def quick_run(self):
        # 상태를 '활성' 으로 전환(저장됨)하고 사이클 시작
        self.set_status("활성")
        
        # 활성화 기본예약 (시작대기/종료예약) 이 잡혀있을 수 있으니 모두 취소하고, 
        # 바로 실행은 시작 대기 없이 즉시 타이머 시작하도록 설정
        self._cancel_start_stop()

        # 타이머 사이클 즉시 시작
        self._start_cycle_with_login()

        # 종료 예약 : 이미 시간이 지났으면 내일로 예약
        eh, em, es = self._parse_hms(self.task_data.get("end_time"))
        end_dt = self._next_dt(eh, em, es)
        now = datetime.datetime.now()

        delay_stop_ms = int((end_dt - now).total_seconds() * 1000)
        self._stop_after_id = self.after(delay_stop_ms, self._stop_and_settle)
    
    def _is_login_ready(self) -> bool:
        """
        로그인 대체(메모장) 준비 여부를 확인.
        - 최상위 로그인 창(메모장) 이 존재하면 True
        """
        try:
            from core.login_manager import _find_login_top_hwnd
            hwnd = _find_login_top_hwnd(timeout_sec=0.0)
            return bool(hwnd)
        except Exception:
            return False

    def _start_cycle_with_login(self):
        """
        사이클 시작 전 로그인 준비 여부를 확인하고,
        필요 시 자동 로그인을 선행한 뒤 사이클을 시작.
        """
        if self._is_login_ready():
            # 로그인 준비 완료 : 즉시 사이클 시작
            self.start_cycle()
            return

        # 로그인 준비 안됨 : 자동 로그인 선행
        self.execute_auto_login()

        # 1차 재확인(예: 1300ms 후)
        def _check_then_start():
            if self._is_login_ready():
                self.start_cycle()
            else:
                # 2차 재확인(예: 700ms 후)
                self.after(700, _final_check)
        
        def _final_check():
            if self._is_login_ready():
                self.start_cycle()
            else:
                messagebox.showwarning(
                    "자동로그인",
                    "로그인(메모장) 준비에 실패하여 사이클을 시작하지 않습니다.",
                    parent=self.winfo_toplevel()
                )
        self.after(1300, _check_then_start)


    def start_cycle(self):
        # 이미 실행 중이면 무시
        if self._cycle_running:
            return

        interval = self._get_interval()
        if interval <= 0:
            messagebox.showwarning("경고", "간격(초)이 0이어서 반복 실행을 시작 할 수 없습니다.", parent=self.winfo_toplevel())
            return

        self._cycle_running = True
        self._remaining = interval
        # 카운트다운 표시 시작
        self._update_countdown_label()
        self._schedule_tick()

    def cancel_cycle(self, reset_label=True):
        self._cycle_running = False
        # 타이머 취소
        if getattr(self, "_timer_id", None):
            try:
                self.after_cancel(self._timer_id)
            except:
                pass
            self._timer_id = None
        
        # 라벨 초기화
        if reset_label and hasattr(self, "lbl_countdown"):
            self.lbl_countdown.config(text="")

    def _parse_hms(self, s: str, default=(0, 0, 0)):
        try:
            h, m, sec = map(int, (s or "00:00:00").strip().split(":"))
            return h, m, sec
        except Exception:
            return default

    def _next_dt(self, h: int, m: int, s: int, now: datetime.datetime | None = None):
        if now is None:
            now = datetime.datetime.now()
        dt = now.replace(hour=h, minute=m, second=s, microsecond=0)
        if dt <= now:
            dt += datetime.timedelta(days=1)
        return dt
    
    def _get_interval(self) -> int:
        val = self.task_data.get("interval", 0)
        try:
            return int(val)
        except Exception:
            return 0

    def _schedule_tick(self):
        # 내부 tick 예약
        self._timer_id = self.after(1000, self._tick)

    def _update_countdown_label(self):
        if hasattr(self, "lbl_countdown"):
            if self._cycle_running and self._remaining > 0:
                self.lbl_countdown.config(text=f"⏳ {self._remaining}s")
            else:
                self.lbl_countdown.config(text="")

    def cancel_auto_login_schedule(self):
        if hasattr(self, "_auto_login_after_id") and self._auto_login_after_id:
            try:
                self.after_cancel(self._auto_login_after_id)
            except:
                pass
            self._auto_login_after_id = None

    def restart_auto_login_schedule(self):
        # 자동로그인 아닐 떄는 무시
        if self.task_data.get("type") != "auto_login":
            return
        # Disabled 상태면 스케쥴 안 함
        if getattr(self, "runtime_status", "Ready") != "Ready":
            self.cancel_auto_login_schedule()
            return
        
        # 기존 스케쥴 취소
        self.cancel_auto_login_schedule()

        # 시작시간 파싱
        start_str = self.task_data.get("start_time") or "00:00:00"
        try:
            h, m, s = map(int, start_str.split(":"))
        except:
            h, m, s = 0, 0, 0

        now = datetime.datetime.now()
        today_start = now.replace(hour=h, minute=m, second=s, microsecond=0)

        if today_start <= now:
            # 이미 지난 시간이라면 다음날로
            target = today_start + datetime.timedelta(days=1)
        else:
            target = today_start
        
        delay_ms = int((target - now).total_seconds() * 1000)
        # 안전 가드
        delay_ms = max(delay_ms, 0)

        self._auto_login_after_id = self.after(delay_ms, self._auto_login_trigger)
    
    def _auto_login_trigger(self):
        # Ready 상태에서만 실행 전환
        if getattr(self, "runtime_status", "Ready") == "Ready":
            self.execute_auto_login()
        # 다음 실행을 위해 다시 스케쥴 (매일)
        self.restart_auto_login_schedule()

    def render_from_data(self):
        # 1영역(닉네임)
        self.text_left.config(text=self.task_data.get("nickname", "신규작업"))

        # 3영역(시작시간 / 시트이름)
        if self.task_data.get("type") == "auto_login":
            # 3 영역에 시작시간 표시 (제거 가능)
            start_time = (self.task_data.get("start_time") or "00:00:00")
            self.text_right.config(text=f"\U0001F552 {start_time}") #⏰

            # 항상 Ready 로 시작(저장값 무시)
            self.runtime_status = "Ready"
            self._update_auto_login_status_label()
            # 스케쥴은 __init__에서 설정됨
            return

            # 상태 라벨은 set_status에서 설정
            current = self.task_data.get("status", "Ready")
            self.set_status(current, persist=False)

        else:
            # 일반 작업 : 시트이름, 시작/종료/간격 표시
            sheet_name = self.task_data.get("sheet_name", "")
            self.text_right.config(text=f"🔗 {sheet_name}")

            start_time = (self.task_data.get("start_time") or "00:00:00")
            end_time = (self.task_data.get("end_time") or "00:00:00")
            interval = self.task_data.get("interval", 0)
            try:
                interval = int(interval)
            except:
                interval = 0

            self.lbl_countdown.config(text=f"{self.ICON_TIMER}")
            self.lbl_start.config(text=f"{self.ICON_START} {start_time}")
            self.lbl_end.config(text=f"{self.ICON_END} {end_time}")
            self.lbl_interval.config(text=f"{self.ICON_INT} {interval}")


    def _tick(self):

        # 실행 중이 아니면 중단
        if not self._cycle_running:
            return

        # 1초마다 감소
        if self._remaining > 0:
            self._remaining -= 1
            self._update_countdown_label()
            self._schedule_tick()
        else:
            # 0이 되면 다시 interval로 리셋해 반복 동작
            self.execute_trade()
            interval = self._get_interval()

            if interval > 0 and self._cycle_running:
                self._remaining = interval
                self._update_countdown_label()
                self._schedule_tick()
            else:
                self.cancel_cycle()

    def _is_past_end_time(self):
        # 종료 시간이 유요하고, 현재 시간이 종료시간을 지난 경우
        end_str = self.task_data.get("end_time") or "00:00:00"
        try:
            h, m, s = map(int, end_str.split(":"))
        except:
            return False
        now = datetime.datetime.now()
        end_dt = now.replace(hour=h, minute=m, second=s, microsecond=0)
        return now >= end_dt

    def _schedule_start_stop(self):
        """
        상태가 '활성'일 때 시작/종료 예약을 설정합니다.
        - 시작/종료 시간은 '다음 발생 시각' 으로 계산하여 항상 미래로 예약
        - 정산은 종료 콜백에서만 수행
        """

        self._cancel_start_stop()

        sh, sm, ss = self._parse_hms(self.task_data.get("start_time"))
        eh, em, es = self._parse_hms(self.task_data.get("end_time"))
        now = datetime.datetime.now()
        start_today = now.replace(hour=sh, minute=sm, second=ss, microsecond=0)

        if now < start_today:
            delay_start_ms = int((start_today - now).total_seconds() * 1000)
            self._start_after_id = self.after(delay_start_ms, self._start_cycle_with_login)
        # Else : 이미 시작시간 지남 -> 아무것도 하지 않음

        # 종료 : 다음 발생 시각 (항상 미래)
        end_dt = self._next_dt(eh, em, es, now) 
        delay_stop_ms = int((end_dt - now).total_seconds() * 1000)
        self._stop_after_id = self.after(delay_stop_ms, self._stop_and_settle)

    def _stop_and_settle(self):
        self.cancel_cycle()
        self.perform_settlement()
        self.set_status("비활성")

    def _cancel_start_stop(self):
        # 시작/종료 예약 취소
        if getattr(self, "_start_after_id", None):
            try:
                self.after_cancel(self._start_after_id)
            except:
                pass
            self._start_after_id = None
        
        if getattr(self, "_stop_after_id", None):
            try:
                self.after_cancel(self._stop_after_id)
            except:
                pass
            self._stop_after_id = None

    def open_task_settings(self):
        # '자동로그인' 타입은 설정이 없을 수 있으므로 분기
        if self.task_data.get("type") == "auto_login":
            AutoLoginSettingsWindow(self)
            return
        TaskSettingsWindow(self)

    def open_action_menu(self):
        # 버튼의 화면상 절대 좌표를 계산
        x = self.btn2.winfo_rootx()
        y = self.btn2.winfo_rooty() + self.btn2.winfo_height()
        ActionMenuPopup(self, x, y)

    def _update_auto_login_status_label(self):
        # Ready -> ❌, Execution -> ⭕
        icon_map = {"Ready" : "❌", "Executing" : "⭕"}
        current = getattr(self, "runtime_status", "Ready").strip()

        # 매핑 실패 시 기본 ❌로 처리
        icon = icon_map.get(current, "❌")
        
        if hasattr(self, "lbl_status"):
            self.lbl_status.config(text=f"{icon} {current}")

    def execute_auto_login(self):
        """ HTS 인증서 자동 로그인 실행 - 상태 ⭕ 로 전환 """
        self.set_status("Executing", persist=False)
        
        try:
            # HTS 실행
            path = "C:\\HTS\\iMERITZ\\Main\\a.bat"
            if not os.path.exists(path):
                raise FileNotFoundError(f"경로 없음: {path}")
            
            # 비동기 실행(UI 블로킹 없음)
            print(f"[DEBUG] HTS 실행 : {path}")
            subprocess.Popen([path])

            # 단계별 자동화
            self.after(3000, self._step1_wait_main_login)  # 메인 로그인 대기

        except Exception as e:
            # 오류 플래그 활성화 + 메시지 유지
            self._login_error_active = True
            self._set_login_info(f"HTS 실행 오류: {e}", fg="tomato")
            messagebox.showerror("실행 오류", f"HTS 실행 실패: {e}", parent=self.winfo_toplevel())
        finally:
            # 일정 시간 후 Ready(❌)로 복귀 , 3초 후 상태 복귀 , 오류상태면 문구를 덮어쓰지 않음
            self.after(20000, lambda: self.set_status("Ready", persist=False))
    
    def _step1_wait_main_login(self):
        """ Step 1 : 메인 로그인 완료 대기 """
        print("[STEP 1] 메인 로그인 완료 대기")
        self._set_login_info("메인 로그인 진행 중...", fg="khaki")
        # 사용자가 ID/PW 입력 할 시간 제공 (3초 대기)
        self.after(3000, self._step2_select_certificate)

    def _step2_select_certificate(self):
        """ Step 2 : 인증서 자동 선택 """
        print("[STEP 2] 인증서 선택")
        self._set_login_info("인증서 선택 중...", fg="khaki")

        try:
            from core.login_manager import select_certificate_auto
            success = select_certificate_auto()

            if success:
                # 인증서 선택 성공 -> 비밀번호 입력 단계로
                self.after(2000, self._step3_input_password)
            else:
                self._login_error_active = True
                self._set_login_info("인증서 선택 실패", fg="tomato")

        except Exception as e:
            self._login_error_active = True
            self._set_login_info(f"오류: {e}", fg="tomato")

    def _step3_input_password(self):
        """ Step 3: 비밀번호 입력 """
        print("[STEP 3] 비밀번호 입력")
        self._set_login_info("비밀번호 입력 중...", fg="khaki")

        pwd = self.task_data.get("cert_password", "")
        self._do_login_attempt(pwd)

    def _do_login_attempt(self, pwd: str):
        """ 비밀번호 입력 시도 """
        try:
            from core.login_manager import type_password_in_login
            ok, code, msg = type_password_in_login(pwd, return_detail=True)
        except Exception as e:
            ok, code, msg = (False, "EXCEPTION", str(e))

        if ok:
            self._login_error_active = False
            self._set_login_info(" 로그인 완료!", fg="lightgreen")
            print("[SUCCESS] HTS 인증서 로그인 완료")
        else:
            # 오류 플래그 활성화 + 메시지 유지
            self._login_error_active = True

            # 코드별 메시지 매핑
            code_msg_map = {
                "NO_PASSWORD_WINDOW": "비밀번호 입력 창을 찾지 못했습니다.",
                "NO_INPUT_FIELD": "입력 필드를 찾지 못했습니다.",
                "EXCEPTION": "예외 발생",
            }
            base = code_msg_map.get(code, "로그인 실패")
            detail = f" ({msg})" if msg else ""
            self._set_login_info(base + detail, fg = "tomato")
            print(f"[ERROR] {base}{detail}")

    def _try_auto_type_password(self, pwd: str):
        ok = type_password_to_login(pwd)
        if not ok:
            self.after(300, lambda: self._retry_auto_type_password(pwd))

    def _retry_auto_type_password(self, pwd: str):
        ok = type_password_to_login(pwd)
        if not ok:
            messagebox.showwarning("자동입력", "메모장 포커스/입력에 실패했습니다.", parent=self.winfo_toplevel())

    def _set_login_info(self, text: str, fg: str = "white"):
        """
        자동 로그인(4영역)용 상태 문구 업데이트
        - Ready : '대기중'
        - Executing : '로그인중입니다.'
        - 오류 : 상세메시지
        """
        if hasattr(self, "status"): # 4영역 라벨
            self.status.config(text=text, fg=fg)

    def set_status(self, status_text, persist=True):
        
        if self.task_data.get("type") == "auto_login":
            
            # 파일에 저장하지 않는 런타임 상태
            self.runtime_status = status_text.strip() if status_text else "Ready"
            self._update_auto_login_status_label()

            if self.runtime_status == "Ready":
                # 오류가 활성화되어 있으면 '대기 중' 으로 덮어쓰지 않음
                if not getattr(self, "_login_error_active", False):
                    self._set_login_info("대기 중", fg="khaki")
                self.restart_auto_login_schedule()

            elif self.runtime_status == "Executing":
                # 새 시도 시작 -> 이전 오류 상태 해제, 진행 문구로 갱신
                self._login_error_active = False
                self._set_login_info("로그인중입니다.", fg="khaki")
            # Executing 에서는 스케쥴을 건드리지 않음(트리거에서 재스케쥴)
            return
        
        status_text = (status_text or "").strip()
        self.task_data['status'] = status_text

        if hasattr(self, "status"):
            self.status.config(text=f"Status: {status_text}")

        if status_text == "활성":
            # 시작/종료 예약 세팅 (현재 시간이 시작~종료 사이면 즉시 시작)
            self._schedule_start_stop()
        elif status_text == "비활성":
            # 예약/사이클 모두 취소
            self._cancel_start_stop()
            self.cancel_cycle(reset_label=True)

        if persist and self.on_change_callback:
            self.on_change_callback()

    def delete(self):
        """삭제 콜백 함수를 호출하여 자신을 삭제하도록 요청"""
        if messagebox.askyesno("삭제 확인", f"'{self.task_data.get('nickname')}' 작업을 정말 삭제하시겠습니까?", parent=self.winfo_toplevel()):
            self.stop_all_schedules()
            self.delete_callback(self)

class TestApp:
    def minimize_window(self, event=None):
        # 윈도우 핸들 얻기
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        # 윈도우 최소화 호출
        ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
    def close_window(self, event=None):
        # 종료 전에 저장이 필요하면 호출
        try:
            self.save_all_settings()
        except Exception as e:
            messagebox.showerror("저장 오류", f"설정 저장 중 오류가 발생했습니다:\n{e}", parent=self.root)
        finally:
            self.root.destroy()

    def save_all_settings(self):
        """모든 설정(self.settings)을 파일에 저장하는 단일 메서드, 
        자동로그인은 런타임 전용이므로 저장에서 제외"""
        try:
            # tasks를 저장하기 전에 auto_login의 status만 제외한 사본 구성
            self.settings["tasks"] = [
                {
                    k: v
                    for k, v in t.items()
                    if not (t.get("type") == "auto_login" and k == "status")
                }
                for t in self.tasks_data
            ]

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("저장 오류", f"설정 저장 중 오류가 발생했습니다:\n{e}", parent=self.root)

    def load_all_settings(self):
        """파일에서 모든 설정을 불러와 self.settings에 채우는 단일 메서드"""
        if os.path.exists(SETTINGS_FILE) and os.path.getsize(SETTINGS_FILE) > 0:
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    self.settings["main_settings"] = loaded_data.get("main_settings", {})
                    self.settings["tasks"] = loaded_data.get("tasks", [])
                    self.tasks_data = self.settings["tasks"] # 참조 다시 연결
            except (json.JSONDecodeError, Exception):
                pass

        if not self.settings["tasks"]:
            self.add_task(is_auto_login=True)
            self.save_all_settings() # 초기 작업 생성 후 저장
        else:
            for task_data in self.settings["tasks"]:
                self.add_task(task_data=task_data)


    def __init__(self, root):
        self.root = root
        root.title("Test App")

        window_width = 600
        window_height = 700
        
        self.center_window(root, window_width, window_height) # 중앙 배치
        #root.overrideredirect(True) # 상단 Bar 제거 (상단 Bar 제거시 작업표시줄에서 사라짐..)

        root.resizable(False, False)
        root.configure(bg="black")  # 전체 배경 검은색

        # --- Header ---
        header_frame = tk.Frame(root, bg="black", height=50)
        header_frame.pack(fill=tk.X)

        # 햄버거 버튼 (왼쪽, 흰 글씨)
        self.menu = HamburgerMenu(root, app=self) # 햄버거 메뉴 프레임 생성
        
        self.hamburger_btn = tk.Button(header_frame, text="☰", font=("Arial", 14), width=3,
                                       fg="white", bg="black", bd=0, activebackground="gray20", activeforeground="white",
                                       command=self.menu.toggle)
        self.hamburger_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # 프로그램명 (햄버거 버튼 우측, 흰 글씨)
        self.title_label = tk.Label(header_frame, text="Test", font=("Arial", 16), fg="white", bg="black")
        self.title_label.pack(side=tk.LEFT, padx=5)

        # 종료 버튼
        close_btn = tk.Button(header_frame, text="×", font=("Arial", 14, "bold"), width=3,
                            fg="white", bg="black", bd=0, command=self.close_window,
                            activebackground="red", activeforeground="white")
        close_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # 최소화 버튼
        min_btn = tk.Button(header_frame, text="―", font=("Arial", 14, "bold"), width=3,
                            fg="white", bg="black", bd=0, command=self.minimize_window,
                            activebackground="gray20", activeforeground="white")
        min_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # --- Main (New)
        main_container = tk.Frame(root, bg="black")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(main_container, bg="black", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)

        # GridCell 이 들어 갈 실제 프레임
        self.grid_frame = tk.Frame(canvas, bg="black")

        # 캔버스에 grid_frame을 창으로 추가
        self.grid_frame_window = canvas.create_window((0,0), window=self.grid_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(self.grid_frame_window, width=e.width))

        # 스크롤바와 캔버스 배치
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

         # grid_frame의 크기가 변경될 때 스크롤 영역을 재설정하는 바인딩
        self.grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # 캔버스에 마우스 휠 스크롤 바인딩
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # 메인 영역 클릭 시 메뉴 닫기
        main_container.bind("<Button-1>", self.hide_menu)
        canvas.bind("<Button-1>", self.hide_menu)


        # --- Footer (하단) ---
        footer_frame = tk.Frame(root, height=50, bg="black")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Footer 버튼 폰트, 크기 조절
        btn_font = font.Font(family="Helvetica", size=14, weight="bold", slant="italic")
        self.start_stop_btn = tk.Button(footer_frame, text="Start", width=20, command=self.toggle_start_stop,
                         fg="white", bg="black", bd=1, activebackground="gray20", activeforeground="white", font=btn_font)
        self.start_stop_btn.pack(pady=10) # 중앙에 배치

        # '+' 버튼 추가 (우측 하단)
        add_btn = tk.Button(footer_frame, text="+", font=("Arial", 20, "bold"), width=3, fg="white", bg="gray20", bd=0,
                            command=self.add_new_task, activebackground="gray40", activeforeground="white")
        add_btn.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor='se') #우측 하단에 배치        


        # 모든 설정을 담을 중앙 딕셔너리
        self.settings = {"main_settings": {}, "tasks": []}
        #self.tasks_data는 이제 self.settings['tasks']를 가리키는 참조가 됨
        self.tasks_data = self.settings["tasks"]

        self.rows = []
        self.is_running = False
        
        # 프로그램 시작 시 모든 설정을 불러옴
        self.load_all_settings()
        self._save_after_id = None

        self.hts = HtsAutomation()

    def add_task(self, task_data=None, is_auto_login=False):
        """GridCell을 하나 추가하는 메서드"""
        # is_auto_login=True : 기본 자동로그인 작업 생성
        # task_data 지정 시, 해당 데이터로 작업 생성 (파일 불러오기 등)
        # 그렇지 않으면 기본 신규 작업 생성
        
        if is_auto_login:
            # 자동 로그인용 기본 데이터
            new_task_data = {
                "type": "auto_login", 
                "nickname": "자동로그인", 
                "status": "Ready", 
                "start_time" : "00:00:00",
                "cert_password" : ""}
        elif task_data:
            # 파일에서 불러온 데이터
            new_task_data = task_data
        else:
            # '+' 버튼으로 새로 추가한 데이터
            task_num = len(self.tasks_data)
            new_task_data = {"type": "new_task", "nickname": f"신규작업 {task_num}", "status": "대기"}

        # 파일에서 불러온 데이터(task_data) 가 이미 리스트에 있다면 중복 추가하지 않음
        if task_data is None or new_task_data not in self.tasks_data:
            self.tasks_data.append(new_task_data)

        # GridCell 위젯 생성 및 배치, 삭제 콜백도 넘김
        grid_cell = GridCell(self.grid_frame, new_task_data, self.remove_task, on_change_callback=self.save_all_settings)
        grid_cell.pack(side=tk.TOP, fill=tk.X, pady=(0,5))
        self.rows.append(grid_cell)

        underline = tk.Frame(self.grid_frame, height=1, bg="gray")
        underline.pack(fill=tk.X)

    def add_new_task(self):
        """'+' 버튼 클릭 시 호출되는 메서드"""
        self.add_task()
        self.save_all_settings()

    def toggle_start_stop(self):
        if self.is_running:
            self.is_running = False
            self.start_stop_btn.config(text="Start")
        else:
            self.is_running = True
            self.start_stop_btn.config(text="Stop")
    
    def remove_task(self, grid_cell_to_remove):
        """GridCell을 UI와 데이터 리스트에서 삭제하는 메서드"""

        # 데이터 리스트에서 삭제
        self.tasks_data.remove(grid_cell_to_remove.task_data)

        # 위젯 리스트에서 삭제
        self.rows.remove(grid_cell_to_remove)

        # UI에서 위젯 제거
        # pack_slaves()를 순회하며 삭제할 위젯과 그 아래 구분선을 함께 찾아서 제거
        slaves = self.grid_frame.pack_slaves()
        for i, slave in enumerate(slaves):
            if slave == grid_cell_to_remove:
                slave.destroy() # Gridcell 제거
                if i > 0: # 구분선이 있다면
                    slaves[i-1].destroy() # 구분선 제거 (pack 순서는 역순임)
                break
        self.save_all_settings()


    def center_window(self, root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
    
    def hide_menu(self, event):
        if self.menu.expanded:
            self.menu.slide_out()

if __name__ == "__main__":
    root = tk.Tk()
    app = TestApp(root)
    root.mainloop()

