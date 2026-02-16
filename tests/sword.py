import pyautogui
import time

try:
    while True:
        pyautogui.press('/')  # Enter 키 누르기
        time.sleep(0.3)           # 0.3초 대기
        pyautogui.press('enter')  # Enter 키 누르기
        time.sleep(0.3)           # 0.3초 대기
        pyautogui.press('enter')  # Enter 키 누르기
        time.sleep(0.3)           # 0.3초 대기
except KeyboardInterrupt:
    print("매크로가 중단되었습니다.")