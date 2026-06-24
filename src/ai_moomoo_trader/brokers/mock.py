from __future__ import annotations
from ..models import AccountState, OrderPlan, Position, Side
from .base import Broker


class MockBroker(Broker):
    def __init__(self, cash: float = 10_000):
        self.cash = cash
        self.positions: dict[str, Position] = {}

    def get_account_state(self) -> AccountState:
        position_value = sum(p.market_value for p in self.positions.values())
        return AccountState(cash=self.cash, equity=self.cash + position_value, positions=self.positions.copy())

    def place_order(self, order: OrderPlan) -> dict:
        price = order.limit_price or 0.0
        value = order.qty * price
        if order.side == Side.BUY:
            if value > self.cash:
                return {"ok": False, "error": "insufficient cash"}
            self.cash -= value
            existing = self.positions.get(order.symbol)
            if existing:
                new_qty = existing.qty + order.qty
                avg = (existing.qty * existing.avg_price + value) / new_qty
                self.positions[order.symbol] = Position(order.symbol, new_qty, avg)
            else:
                self.positions[order.symbol] = Position(order.symbol, order.qty, price)
        else:
            existing = self.positions.get(order.symbol)
            if not existing or existing.qty < order.qty:
                return {"ok": False, "error": "insufficient position"}
            self.cash += value
            remaining = existing.qty - order.qty
            if remaining <= 1e-9:
                self.positions.pop(order.symbol, None)
            else:
                self.positions[order.symbol] = Position(order.symbol, remaining, existing.avg_price)
        return {"ok": True, "order": order.__dict__}
