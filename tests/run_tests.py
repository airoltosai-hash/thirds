# /tests/run_tests.py

import window_inspector as wi
from test_find_price_window import main as find_price_main
try: 
    from test_mouse_click import monitor_mouse_clicks
except: 
    pass

def show_menu():
    while True:
        print("\n" + "="*50)
        print("   HTS 자동화 테스트 통합 메뉴")
        print("="*50)
        print("1. 전체 부모 창 목록 확인")
        print("2. PC 전체 모든 자식 HWND 전수조사 (Total Scan)") # 모든 자식!
        print("3. 마우스 클릭 좌표 추적")
        print("4. 현재가 창 정밀 탐색 (참고용)")
        print("5. 특정 창의 자식 요소 파일 저장 ")
        print("6. 해외주식 주문창 데이터 추출 ")
        print("q. 종료")
        
        choice = input("원하는 메뉴 번호를 입력하세요: ").strip()

        if choice == '1': wi.print_windows_info()
        elif choice == '2':
            print("\n[실행] PC 전체 모든 HWND 자식 요소 탐색 시작...")
            filename = wi.print_all_system_children(save_to_file=True)
            if filename:
                print(f" {filename} 파일이 저장되었습니다!")
        elif choice == '3':
            try: monitor_mouse_clicks()
            except KeyboardInterrupt: print("\n종료")
        elif choice == '4': find_price_main()
        elif choice == '5':
            hwnd_input = input("부모 HWND를 입력하세요 (16진수, 예: 0x1a0b2c): ").strip()
            try:
                hwnd = int(hwnd_input, 16)
                filename, children = wi.inspect_child_elements_with_details_to_file(hwnd)
                print(f" {len(children)}개의 자식 요소를 {filename}에 저장했습니다!")
            except Exception as e:
                print(f" 오류 : {e}")
        elif choice == '6':
            hwnd_input = input("HWND를 입력하세요 (16진수)").strip()
            try:
                hwnd = int(hwnd_input, 16)
                wi.extract_all_text_from_window(hwnd)
            except:
                print("x 오류")

if __name__ == "__main__":
    show_menu()