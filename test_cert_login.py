# test_cert_login.py

import subprocess
import time
import sys
sys.path.insert(0, '.')
from core.login_manager import type_password_in_login


print("="*80)
print("Step 2 테스트 : 비밀번호 자동 입력")
print("="*80)

# HTS 실행
print("HTS 실행 중...")
subprocess.Popen(["C:\\HTS\\iMERITZ\\Main\\a.bat"])

# 로그인 창이 뜰 때까지 대기
print(" 로그인 창이 뜰 떄까지 대기 중... (5초)")
time.sleep(5)


print("\n 다음 단계 :")
print(" 1. HTS 메인 로그인 창에서 ID/PW를 입력해주세요")
print(" 2. '인증서 선택' 팡벙비 뜨면 프로그램이 자동으로 첫 번째 인증서를 선택합니다.\n")
print(" 3. 그러면 비밀번호 입력 팝ㅇ버이 뜨고 프로그램이 자동으로 입력합니다.\n")


password = "55555testAA"

print(" 비밀번호 입력 팝업을 기다리는중... (최대 10초)")
ok, code, msg = type_password_in_login(password, return_detail=True)

print("\n" + "="*80)
print("결과: ")
print(f"  성공 : {ok}")
print(f"  코드 : {ok}")
print(f"  메시지 : {ok}")

if ok:
    print(" Step 2 성공!")
else:
    print(" Step 2 실패")
    
print("\n" + "="*80)

input("엔터를 누르면 종료됩니다...")
