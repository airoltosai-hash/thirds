# test_hts_window.py

import subprocess
import time
import sys
sys.path.insert(0, '.')
from automation.window_inspector import print_windows_info

# HTS 실행
print("HTS 실행 중...")
subprocess.Popen(["C:\\HTS\\iMERITZ\\Main\\a.bat"])

# 로그인 창이 뜰 때까지 대기
print(" 로그인 창이 뜰 떄까지 대기 중... (10초)")
for i in range(10):
    print(f" {10-i}초", end='\r')
    time.sleep(1)

print("\n" + "="*100)
print("현재 열려 있는 창 목록:")
print("="*100)
print_windows_info()

print("\n 위 목록에서 HTS 로그인 창을 찾아주세요!")
print("     - 클래스명 (class)")
print("     - 타이틀명 (title)")
print("     을 기록해두세요.\n")

input("엔터를 누르면 종료됩니다...")
