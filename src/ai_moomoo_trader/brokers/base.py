from __future__ import annotations
from abc import ABC, abstractmethod
from ..models import AccountState, OrderPlan


class Broker(ABC):
    @abstractmethod
    def get_account_state(self) -> AccountState: ...

    @abstractmethod
    def place_order(self, order: OrderPlan) -> dict: ...
