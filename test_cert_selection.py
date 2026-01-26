# test_cert_selection.py

import subprocess
import time
import sys
sys.path.insert(0, '.')
from automation.login_automation import select_certificate_auto


print("="*80)
print("Step 1 테스트 : 인증서 자동 선택")
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

success = select_certificate_auto()

print("\n" + "="*80)
if success:
    print(" Step 1 성공!")
else:
    print(" Step 1 실패")
    
print("\n" + "="*80)

input("엔터를 누르면 종료됩니다...")
