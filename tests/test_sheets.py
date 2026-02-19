import os, re, json, sys, traceback
import asyncio
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from telegram import Bot


POSSIBLE_SETTINGS = [
    "../config/setting.json",
    "../config/settings.json",
    "config/setting.json",
    "config/settings.json",
    "settings.json",
]

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

async def send_telegram_message(chat_id, token, message):
    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=message)

def load_main_settings():
    for p in POSSIBLE_SETTINGS:
        p_abs = os.path.normpath(os.path.join(PROJECT_ROOT, os.path.relpath(p, "..")))
        print(f"[DEBUG] 확인 경로: {p_abs}")
        if os.path.exists(p_abs):
            print(f"[DEBUG] 설정 파일 찾음: {p_abs}")
            with open(p_abs, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("main_settings", data) if isinstance(data, dict) else {}
    return {}

def extract_spreadsheet_id(url_or_id: str) -> str:
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", (url_or_id or ""))
    if m:
        return m.group(1)
    return (url_or_id or "").strip()

def prepare_service(sa_json):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(sa_json, scopes=scopes)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

def list_sheet_titles(service, spreadsheet_id):
    resp = service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title").execute()
    sheets = resp.get("sheets", [])
    return [s.get("properties", {}).get("title", "") for s in sheets]

def get_cell_value(service, spreadsheet_id, sheet_name, cell):
    range_name = f"{sheet_name}!{cell}"
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    return values[0][0] if values else "값 없음"

def update_cell_value(service, spreadsheet_id, sheet_name, cell, value):
    range_name = f"{sheet_name}!{cell}"
    body = {
        "values": [[value]]
    }
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption="RAW", body=body).execute()

def get_row_values(service, spreadsheet_id, sheet_name, start_col, end_col, row, count):
    range_name = f"{sheet_name}!{start_col}{row}:{end_col}{row + count - 1}"
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])

def init():
    settings = load_main_settings()
    print("[DEBUG] settings loaded:", bool(settings))

    if not settings:
        print("ERROR: 설정 파일을 찾을 수 없습니다.")
        sys.exit(2)

    sheet_path = (settings.get("google_sheet_path") or "").strip()
    sa_json = (settings.get("google_service_account_json") or "").strip()
    if sa_json and not os.path.isabs(sa_json):
        sa_json = os.path.normpath(os.path.join(PROJECT_ROOT, sa_json))

    print(f"[DEBUG] google_sheet_path: '{sheet_path}'")
    print(f"[DEBUG] google_service_account_json: '{sa_json}' exists={os.path.exists(sa_json)}")

    if not sheet_path:
        print("ERROR: main_settings.google_sheet_path가 설정되어 있지 않습니다."); sys.exit(2)
    if not sa_json or not os.path.exists(sa_json):
        print(f"ERROR: 서비스 계정 JSON 파일 없음: {sa_json}"); sys.exit(2)

    spreadsheet_id = extract_spreadsheet_id(sheet_path)
    print(f"[DEBUG] spreadsheet_id: '{spreadsheet_id}'")
    if not spreadsheet_id:
        print("ERROR: 스프레드시트 ID를 추출할 수 없습니다."); sys.exit(2)

    try:
        service = prepare_service(sa_json)
        print("[DEBUG] API 호출 성공")
    except Exception as e:
        print("ERROR: Google API 준비 실패:", e); traceback.print_exc(); sys.exit(3)

    return service, spreadsheet_id

def print_main_menu():
    print()
    print("===== Test Menu =====")
    print("1) 전체 계좌 목록(시트명) 출력")
    print("2) 기본설정 불러오기")
    print("3) 매수/매도표 불러오기")
    print("4) 프로그램 매매정보 업데이트")
    print("5) 텔레그램 전송 테스트")
    print("q) 종료")
    print("=====================")
    print("명령을 입력하세요:", end=" ", flush=True)

def print_sub_menu():
    print()
    print("===== 하위 메뉴 =====")
    print("1. 계좌번호 불러오기")
    print("2. 종목코드 불러오기")
    print("3. 투자금 불러오기")
    print("4. 티어 분할(숫자) 불러오기")
    print("5. 1티어(USD) 불러오기")
    print("6. 1티어 갱신 체크 여부 불러오기")
    print("7. 텔레그램 ID 불러오기")
    print("8. 텔레그램 Token 불러오기")
    print("b) 뒤로가기")
    print("=====================")
    print("명령을 입력하세요:", end=" ", flush=True)

def print_update_menu():
    print()
    print("===== 프로그램 매매정보 업데이트 =====")
    print("1. 최근 업데이트")
    print("2. 현재티어 업데이트")
    print("3. 현재가 업데이트")
    print("4. 잔고 업데이트")
    print("5. 수량차 업데이트")
    print("6. 매수 업데이트")
    print("7. 매도 업데이트")
    print("b) 뒤로가기")
    print("================================")
    print("명령을 입력하세요:", end=" ", flush=True)

def main_loop():
    service, spreadsheet_id = init()
    sheet_titles = list_sheet_titles(service, spreadsheet_id)

    while True:
        print_main_menu()
        cmd = input().strip().lower()
        if cmd in ("q", "quit", "exit"):
            print("종료합니다.")
            break
        if cmd == "1":
            if not sheet_titles:
                print("스프레드시트에 시트(탭)가 없습니다.")
            else:
                print("Found sheets:")
                for i, t in enumerate(sheet_titles, 1):
                    print(f"  {i}. {t}")
        elif cmd == "2":
            print("시트 이름을 입력하세요:", end=" ", flush=True)
            sheet_name = input().strip()
            if sheet_name not in sheet_titles:
                print("유효하지 않은 시트 이름입니다. 다시 시도하세요.")
            else:
                while True:
                    print_sub_menu()
                    sub_cmd = input().strip().lower()
                    if sub_cmd == "b":
                        break
                    elif sub_cmd == "1":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E6")
                        print(f"계좌번호: {value}")
                    elif sub_cmd == "2":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E8")
                        print(f"종목코드: {value}")
                    elif sub_cmd == "3":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E10")
                        print(f"투자금: {value}")
                    elif sub_cmd == "4":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E12")
                        print(f"티어 분할(숫자): {value}")
                    elif sub_cmd == "5":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E14")
                        print(f"1티어(USD): {value}")
                    elif sub_cmd == "6":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E16")
                        print(f"1티어 갱신 체크 여부: {value}")
                    elif sub_cmd == "7":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E24")
                        print(f"텔레그램 ID: {value}")
                    elif sub_cmd == "8":
                        value = get_cell_value(service, spreadsheet_id, sheet_name, "E26")
                        print(f"텔레그램 Token: {value}")
                    else:
                        print("알 수 없는 명령입니다. 다시 시도하세요.")
        elif cmd == "3":
            print("시트 이름을 입력하세요:", end=" ", flush=True)
            sheet_name = input().strip()
            if sheet_name not in sheet_titles:
                print("유효하지 않은 시트 이름입니다. 다시 시도하세요.")
            else:
                tier_count = int(get_cell_value(service, spreadsheet_id, sheet_name, "E12"))
                data = get_row_values(service, spreadsheet_id, sheet_name, "V", "AC", 5, tier_count)
                headers = ["티어", "잔고량", "투자금", "티어평단", "매수가", "매수량", "매도가", "매도량"]
                print("\t".join(headers))
                for i, row in enumerate(data, 1):
                    print(f"{i}\t" + "\t".join(row))
        elif cmd == "4":
            print("시트 이름을 입력하세요:", end=" ", flush=True)
            sheet_name = input().strip()
            if sheet_name not in sheet_titles:
                print("유효하지 않은 시트 이름입니다. 다시 시도하세요.")
            else:
                while True:
                    print_update_menu()
                    update_cmd = input().strip().lower()
                    if update_cmd == "b":
                        break
                    elif update_cmd == "1":
                        current_time = datetime.now().strftime("%m-%d %H:%M:%S")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K4", current_time)
                        print(f"최근 업데이트: {current_time}")
                    elif update_cmd == "2":
                        value = input("현재티어 값을 입력하세요: ")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K6", value)
                        print(f"현재티어 업데이트: {value}")
                    elif update_cmd == "3":
                        value = input("현재가 값을 입력하세요: ")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K8", value)
                        print(f"현재가 업데이트: {value}")
                    elif update_cmd == "4":
                        value = input("잔고 값을 입력하세요: ")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K10", value)
                        print(f"잔고 업데이트: {value}")
                    elif update_cmd == "5":
                        value = input("수량차 값을 입력하세요: ")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K12", value)
                        print(f"수량차 업데이트: {value}")
                    elif update_cmd == "6":
                        value = input("매수 값을 입력하세요: ")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K14", value)
                        print(f"매수 업데이트: {value}")
                    elif update_cmd == "7":
                        value = input("매도 값을 입력하세요: ")
                        update_cell_value(service, spreadsheet_id, sheet_name, "K16", value)
                        print(f"매도 업데이트: {value}")
                    else:
                        print("알 수 없는 명령입니다. 다시 시도하세요.")
        elif cmd == "5":
            print("시트 이름을 입력하세요:", end=" ", flush=True)
            sheet_name = input().strip()
            if sheet_name not in sheet_titles:
                print("유효하지 않은 시트 이름입니다. 다시 시도하세요.")
            else:
                chat_id = get_cell_value(service, spreadsheet_id, sheet_name, "E24")
                token = get_cell_value(service, spreadsheet_id, sheet_name, "E26")
                message = f"{sheet_name}_test"
                try:
                    asyncio.run(send_telegram_message(chat_id, token, message))
                    print(f"텔레그램으로 '{message}' 메시지가 전송되었습니다.")
                except Exception as e:
                    print("ERROR: 텔레그램 메시지 전송 실패:", e)
        else:
            print("알 수 없는 명령입니다. 다시 시도하세요.")

if __name__ == "__main__":
    main_loop()