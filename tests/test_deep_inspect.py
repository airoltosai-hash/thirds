# /tests/test_deep_inspect.py

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def list_all_handles_raw():
    all_found = []

    # 모든 창과 컨트롤을 수집하는 콜백
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, lParam):
        # 1. 클래스명
        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)
        
        # 2. 타이틀
        length = user32.GetWindowTextLengthW(hwnd)
        title_buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buf, length + 1)
        
        all_found.append({
            "hwnd": hex(hwnd),
            "class": cls_buf.value,
            "title": title_buf.value
        })
        return True

    # [핵심] GetDesktopWindow()를 사용하여 진짜 바닥부터 훑습니다.
    desktop_hwnd = user32.GetDesktopWindow()
    print(f"🖥️ 데스크탑 메인 핸들: {hex(desktop_hwnd)}")
    
    # EnumChildWindows에 데스크탑 핸들을 넣으면 시스템 전체 자식이 나옵니다.
    user32.EnumChildWindows(desktop_hwnd, enum_proc, 0)

    # 결과 출력
    print(f"\n📢 탐색 완료: 총 {len(all_found)}개의 핸들을 발견했습니다.")
    print("-" * 80)
    
    for i, item in enumerate(all_found):
        # 일단 처음 1000개만 화면에 출력 (너무 많아서 렉 걸릴 수 있음)
        if i < 1000:
            print(f"[{i:4d}] {item['hwnd']:10s} | {item['class']:25s} | {item['title']}")
    
    print("-" * 80)
    print(f"위 리스트는 처음 100개만 보여준 것입니다. 전체 개수는 {len(all_found)}개입니다.")
    
    # 만약 [06000]이 어딘가 박혀있다면 여기서 찾아냅니다.
    targets = [x for x in all_found if "[06000]" in x['title']]
    if targets:
        print(f"\n🎯 [06000] 키워드 발견 ({len(targets)}개):")
        for t in targets:
            print(f"-> {t['hwnd']} | {t['class']} | {t['title']}")

if __name__ == "__main__":
    list_all_handles_raw()