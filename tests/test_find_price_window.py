# /tests/find_price_window.py

import window_inspector as wi

def find_price_main():
    """run_tests.py와 호환되는 메인 함수"""
    print("\n" + "="*100)
    print(" HTS 현재가 창 정밀 탐색")
    print("="*100 + "\n")

    windows = wi.list_all_windows_recursive()
    
    # 사용자님의 소중한 키워드들 복구!
    price_keywords = [
        "현재가", "호가", "가격", "Price", "Quote", "시세", "정보", "Market",
        "Info", "매도", "매수", "Bid", "Ask", "차트", "Chart", "시장", "[06000]"
    ]

    print(f"[총 {len(windows)}개의 창 탐색 중...]\n")

    target_hwnd = None
    found_windows = []

    for w in windows:
        # 키워드가 포함되어 있고, [06000]이 있는 창을 우선순위로 탐색
        if any(kw in w['title'] for kw in price_keywords):
            found_windows.append(w)
            print(f" {w['hwnd_hex']} | {w['class']:25s} | {w['title']}")

            if "[06000]" in w['title']:
                target_hwnd = w['hwnd']
    print()

    if not found_windows:
        print(" 가격 관련 창을 찾을 수 없습니다")
        return
    if target_hwnd:
        print(f"\n [06000] 타겟 창 발견!")
        wi.inspect_child_elements(target_hwnd)
    else:
        print(f"[06000] 창은 없지만 {len(found_windows)}개의 관련 창을 찾았습니다")

main = find_price_main