# automation/hts_automation.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# 임시로 메모장 대체 사용
from .login_automation import (
    type_password_to_login,
    auto_type_password_in_login,
)

@dataclass
class Order:
    side: str # "buy" | "sell"
    symbol: str
    qty: int
    price: Optional[float] = None

class HtsAutomation:
    def __init__(self):
        # TODO 실행/핸들캐싱/권한확인
        pass

    def login_with_cert(self, password: str) -> bool:
        # TODO HTS 로그인창 
        pass

    def cancel_all_unfilled(self) -> bool:
        # TODO HTS 취소 로직
        pass

    def read_current_price(self):
        # TODO HTS 현재가 읽기
        pass

    def place_order(self, order: Order) -> bool:
        # TODO HTS 주문 입력
        pass


