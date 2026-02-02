import window_inspector as wi

def find_price_main():
    """run_tests.py와 호환되는 메인 함수"""
    print("\n" + "="*100)
    print(" HTS 모든 창 목록 (호가창 찾기 - 키워드 필터링)")
    print("="*100 + "\n")

    windows = wi.list_all_windows_recursive()
    
    # 사용자님의 소중한 키워드들 복구!
    price_keywords = [
        "현재가", "호가", "가격", "Price", "Quote", "시세", "정보", "Market",
        "Info", "매도", "매수", "Bid", "Ask", "차트", "Chart", "시장", "[06000]"
    ]

    print(f"[총 {len(windows)}개의 창 탐색 중...]\n")

    target_hwnd = None
    for w in windows:
        # 키워드가 포함되어 있고, [06000]이 있는 창을 우선순위로 탐색
        if any(kw in w['title'] for kw in price_keywords):
            if "[06000]" in w['title']:
                print(f"✅ 타겟 창 발견: {w['hwnd_hex']} | {w['title']}")
                target_hwnd = w['hwnd']
                break

    if target_hwnd:
        wi.inspect_child_elements(target_hwnd)
    else:
        print("❌ 가격 관련 창을 찾을 수 없습니다.")

# run_tests.py가 main을 찾으므로 별칭 설정
main = find_price_main