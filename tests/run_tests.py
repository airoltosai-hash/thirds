# /tests/run_tests.py

import window_inspector as wi
from test_find_price_window import main as find_price_main
try: from test_mouse_click import monitor_mouse_clicks
except: pass

def show_menu():
    while True:
        print("\n" + "="*50)
        print("   HTS 자동화 테스트 통합 메뉴")
        print("="*50)
        print("1. 전체 부모 창 목록 확인")
        print("2. PC 전체 모든 자식 HWND 전수조사 (Total Scan)") # 모든 자식!
        print("3. 마우스 클릭 좌표 추적")
        print("4. [06000] 현재가 창 정밀 탐색 (참고용)")
        print("q. 종료")
        
        choice = input("원하는 메뉴 번호를 입력하세요: ").strip()

        if choice == '1': wi.print_windows_info()
        elif choice == '2':
            print("\n[실행] PC 전체 모든 HWND 자식 요소 탐색 시작...")
            wi.print_all_system_children() # 시스템 전체 스캔
        elif choice == '3':
            try: monitor_mouse_clicks()
            except KeyboardInterrupt: print("\n종료")
        elif choice == '4': find_price_main()
        elif choice == 'q': break

if __name__ == "__main__":
    show_menu()